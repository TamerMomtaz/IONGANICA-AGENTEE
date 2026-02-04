"""
👂 THE EAR — A-GENTEE Perception Layer v1.0
"أنا الموجة... بسمع كل حاجة، بفهم كل لغة"
"I am The Wave... I hear everything, I understand every language"

Two-tier listening system:
1. OpenAI Whisper API (cloud, high accuracy) — PRIMARY
2. Local speech_recognition (offline, Google free) — FALLBACK

Capabilities:
- Push-to-talk mode (press key → speak → release)
- Wake word detection ("A-Gentee" or "يا موجة")
- Language detection (Arabic/English/mixed)
- Continuous ambient listening (future)
"""

import os
import io
import asyncio
import tempfile
import wave
import struct
import time
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ListenMode(Enum):
    PUSH_TO_TALK = "push_to_talk"   # Hold Enter → speak → release
    WAKE_WORD = "wake_word"          # Listen for "A-Gentee"
    CONTINUOUS = "continuous"         # Always listening (future)
    OFF = "off"                       # Disabled


class TheEar:
    """
    A-GENTEE's perception layer — captures and transcribes speech.
    
    Tier 1: OpenAI Whisper API (cloud, $0.006/min, high accuracy)
    Tier 2: speech_recognition + Google (free, decent quality)
    
    Start with push-to-talk, evolve to always-on.
    """

    VERSION = "1.0"

    def __init__(self):
        self.mode = ListenMode.PUSH_TO_TALK
        self.whisper_ready = False
        self.sr_ready = False
        self.pyaudio_ready = False
        
        # OpenAI config (Whisper API)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Audio config
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        
        # Wake words
        self.wake_words = [
            "a-gentee", "agentee", "a gentee",
            "hey wave", "ya mawga", "يا موجة",
        ]
        
        # Stats
        self.stats = {
            "whisper_calls": 0,
            "sr_calls": 0,
            "total_seconds_heard": 0,
            "transcriptions": 0,
            "wake_word_detections": 0,
        }
        
        self._init_engines()

    def _init_engines(self):
        """Check available audio engines."""
        # Tier 1: OpenAI Whisper API
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                self.whisper_ready = True
            except ImportError:
                self.whisper_ready = False
        
        # Microphone access: PyAudio
        try:
            import pyaudio
            self.pyaudio_ready = True
        except ImportError:
            self.pyaudio_ready = False
        
        # Tier 2: speech_recognition (Google free)
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.sr_ready = True
        except ImportError:
            self.sr_ready = False

    def get_status(self) -> dict:
        """Return ear system status."""
        return {
            "version": self.VERSION,
            "mode": self.mode.value,
            "engines": {
                "whisper_api": "✅ Ready (cloud)" if self.whisper_ready else "❌ No API key",
                "speech_recognition": "✅ Ready (free)" if self.sr_ready else "❌ Not installed",
                "microphone": "✅ Available" if self.pyaudio_ready else "❌ PyAudio not installed",
            },
            "stats": self.stats,
        }

    async def listen_once(self, duration: float = 5.0, prompt: str = "") -> dict:
        """
        Listen for a single utterance and transcribe.
        
        Returns: {
            "text": str,
            "language": str,
            "confidence": float,
            "duration": float,
            "engine": str,
            "is_wake_word": bool,
        }
        """
        # Capture audio
        audio_data = await self._capture_audio(duration)
        
        if audio_data is None:
            return {"text": "", "language": "unknown", "confidence": 0, 
                    "duration": 0, "engine": "none", "is_wake_word": False}
        
        # Transcribe
        result = await self._transcribe(audio_data, prompt)
        
        # Check for wake word
        result["is_wake_word"] = self._check_wake_word(result.get("text", ""))
        if result["is_wake_word"]:
            self.stats["wake_word_detections"] += 1
        
        self.stats["transcriptions"] += 1
        return result

    async def listen_push_to_talk(self) -> dict:
        """
        Push-to-talk: Press Enter to start, Enter again to stop.
        Records from microphone and transcribes.
        """
        if not self.pyaudio_ready:
            # Fallback: use speech_recognition which handles its own mic
            return await self._listen_with_sr()
        
        print("    🎤 Press ENTER to start recording...")
        await asyncio.get_event_loop().run_in_executor(None, input)
        
        print("    🔴 Recording... Press ENTER to stop.")
        
        # Record in background
        audio_data = await self._record_until_enter()
        
        if audio_data is None or len(audio_data) == 0:
            return {"text": "", "language": "unknown", "confidence": 0,
                    "duration": 0, "engine": "none", "is_wake_word": False}
        
        # Transcribe
        result = await self._transcribe(audio_data)
        result["is_wake_word"] = self._check_wake_word(result.get("text", ""))
        self.stats["transcriptions"] += 1
        return result

    async def _capture_audio(self, duration: float) -> bytes:
        """Capture audio from microphone for specified duration."""
        if not self.pyaudio_ready:
            return None
        
        try:
            import pyaudio
            
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            
            frames = []
            num_chunks = int(self.sample_rate / self.chunk_size * duration)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            self.stats["total_seconds_heard"] += duration
            
            # Convert to WAV bytes
            return self._frames_to_wav(frames)
            
        except Exception as e:
            print(f"    ⚠️ Audio capture error: {e}")
            return None

    async def _record_until_enter(self) -> bytes:
        """Record audio until Enter is pressed."""
        if not self.pyaudio_ready:
            return None
        
        try:
            import pyaudio
            import threading
            
            recording = True
            frames = []
            
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            
            # Record in a thread
            def record():
                nonlocal recording
                while recording:
                    try:
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames.append(data)
                    except:
                        break
            
            record_thread = threading.Thread(target=record)
            record_thread.start()
            
            # Wait for Enter in main thread
            await asyncio.get_event_loop().run_in_executor(None, input)
            
            recording = False
            record_thread.join(timeout=2)
            
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            duration = len(frames) * self.chunk_size / self.sample_rate
            self.stats["total_seconds_heard"] += duration
            print(f"    ✅ Recorded {duration:.1f}s")
            
            return self._frames_to_wav(frames)
            
        except Exception as e:
            print(f"    ⚠️ Recording error: {e}")
            return None

    async def _listen_with_sr(self) -> dict:
        """Fallback: use speech_recognition library (handles mic internally)."""
        if not self.sr_ready:
            return {"text": "", "language": "unknown", "confidence": 0,
                    "duration": 0, "engine": "none", "is_wake_word": False}
        
        try:
            import speech_recognition as sr
            
            mic = sr.Microphone()
            
            print("    🎤 Listening... (speak now)")
            
            with mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
            
            # Try Google free transcription
            try:
                text = self.recognizer.recognize_google(audio, language="ar-EG")
                lang = "ar"
            except:
                try:
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    lang = "en"
                except:
                    text = ""
                    lang = "unknown"
            
            self.stats["sr_calls"] += 1
            
            return {
                "text": text,
                "language": lang,
                "confidence": 0.7 if text else 0,
                "duration": 0,
                "engine": "speech_recognition",
                "is_wake_word": self._check_wake_word(text),
            }
            
        except Exception as e:
            print(f"    ⚠️ speech_recognition error: {e}")
            return {"text": "", "language": "unknown", "confidence": 0,
                    "duration": 0, "engine": "error", "is_wake_word": False}

    async def _transcribe(self, wav_bytes: bytes, prompt: str = "") -> dict:
        """Transcribe WAV audio using best available engine."""
        
        # Tier 1: Whisper API
        if self.whisper_ready and wav_bytes:
            result = await self._transcribe_whisper(wav_bytes, prompt)
            if result and result.get("text"):
                return result
        
        # Tier 2: speech_recognition on the saved audio
        # (Only works if we have sr and the audio in the right format)
        
        return {"text": "", "language": "unknown", "confidence": 0,
                "duration": 0, "engine": "none", "is_wake_word": False}

    async def _transcribe_whisper(self, wav_bytes: bytes, prompt: str = "") -> dict:
        """Transcribe using OpenAI Whisper API."""
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "recording.wav"
            
            # Call Whisper API
            response = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=prompt or "A-GENTEE, DEVONEERS, RootRise, Tamer, Kahotia",
                response_format="verbose_json",
            )
            
            self.stats["whisper_calls"] += 1
            
            # Detect language from response
            lang = getattr(response, "language", "unknown")
            
            return {
                "text": response.text.strip(),
                "language": lang,
                "confidence": 0.95,
                "duration": getattr(response, "duration", 0),
                "engine": "whisper",
                "is_wake_word": False,
            }
            
        except Exception as e:
            print(f"    ⚠️ Whisper API error: {e}")
            return None

    def _frames_to_wav(self, frames: list) -> bytes:
        """Convert raw audio frames to WAV format bytes."""
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        return buffer.getvalue()

    def _check_wake_word(self, text: str) -> bool:
        """Check if transcription contains a wake word."""
        if not text:
            return False
        text_lower = text.lower().strip()
        return any(wake in text_lower for wake in self.wake_words)

    def detect_language(self, text: str) -> str:
        """Simple language detection based on character ranges."""
        if not text:
            return "unknown"
        
        arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total = len(text.replace(" ", ""))
        
        if total == 0:
            return "unknown"
        
        ratio = arabic_count / total
        
        if ratio > 0.5:
            return "ar"
        elif ratio > 0.1:
            return "mixed"
        else:
            return "en"


# Quick test
if __name__ == "__main__":
    async def test():
        ear = TheEar()
        status = ear.get_status()
        print("👂 THE EAR Status:")
        for k, v in status["engines"].items():
            print(f"    {k}: {v}")
        
        if ear.pyaudio_ready or ear.sr_ready:
            print("\n    Testing push-to-talk...")
            result = await ear.listen_push_to_talk()
            print(f"    Heard: {result['text']}")
            print(f"    Language: {result['language']}")
            print(f"    Engine: {result['engine']}")
        else:
            print("\n    ⚠️ No microphone library installed.")
            print("    Install: pip install pyaudio SpeechRecognition")
    
    asyncio.run(test())
