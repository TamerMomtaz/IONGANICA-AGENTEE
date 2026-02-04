"""
🌊 A-GENTEE: THE ULTIMATE EAR v2.0
Always-On Audio Intelligence — sounddevice (no PyAudio needed!)

Works on Python 3.14 ✅
Auto-detects Arabic/English ✅
Push-to-talk + Always-on modes ✅
Captures mic + system audio (Stereo Mix) ✅

Author: A-GENTEE / Tee
Version: 2.0
"""

import asyncio
import logging
import os
import queue
import threading
import time
import tempfile
import wave
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger("agentee.ear")

# ── Audio capture ────────────────────────────────────────────
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# ── Whisper (cloud) ──────────────────────────────────────────
try:
    from openai import OpenAI
    WHISPER_API = True
except ImportError:
    WHISPER_API = False


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class TranscriptResult:
    """Result from a transcription"""
    text: str
    language: str  # 'en', 'ar', 'unknown'
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        flag = "🇪🇬" if self.language == "ar" else "🇬🇧" if self.language == "en" else "🌐"
        return f"[{flag}] {self.text}"


# ═══════════════════════════════════════════════════════════════
#  THE ULTIMATE EAR
# ═══════════════════════════════════════════════════════════════

class TheEar:
    """
    🌊 THE ULTIMATE EAR v2.0

    Modes:
      • push_to_talk()  — Record while holding, transcribe on release
      • listen_once()   — Record for N seconds, return transcript
      • start_ambient() — Always-on background listening
      • listen_system()— Capture system audio (Stereo Mix)

    All transcription uses OpenAI Whisper API (best Arabic + English).
    Audio capture uses sounddevice (works on Python 3.14).
    """

    VERSION = "2.0"

    def __init__(self):
        self.available = AUDIO_AVAILABLE
        self.whisper_available = WHISPER_API
        self.openai_client = None

        # Audio settings
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.channels = 1
        self.dtype = np.float32

        # Device IDs (detected from Tee's machine, with fallbacks)
        self.mic_device = None       # Will auto-detect
        self.system_device = None    # Stereo Mix for system audio

        # State
        self.is_recording = False
        self.is_ambient = False
        self._ambient_task = None
        self._audio_buffer = []

        # Stats
        self.stats = {
            "recordings": 0,
            "transcriptions": 0,
            "total_audio_seconds": 0.0,
            "arabic_segments": 0,
            "english_segments": 0,
            "errors": 0,
        }

        # History
        self.history: deque = deque(maxlen=50)

        # Initialize
        self._init_devices()
        self._init_whisper()

        status = "✅ Ready" if (self.available and self.whisper_available) else "⚠️ Limited"
        logger.info(f"👂 TheEar v{self.VERSION} — {status}")
        if self.available:
            logger.info(f"   Mic device: {self.mic_device}")
            if self.system_device is not None:
                logger.info(f"   System audio device: {self.system_device} (Stereo Mix)")

    def _init_devices(self):
        """Detect available audio devices"""
        if not self.available:
            return

        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]

            # Use default input as mic
            self.mic_device = default_input

            # Look for Stereo Mix (system audio capture)
            for i, dev in enumerate(devices):
                name = dev.get('name', '').lower()
                if 'stereo mix' in name and dev.get('max_input_channels', 0) > 0:
                    self.system_device = i
                    break

        except Exception as e:
            logger.error(f"Device detection error: {e}")

    def _init_whisper(self):
        """Initialize OpenAI Whisper API client"""
        if not WHISPER_API:
            logger.warning("⚠️ openai package not installed — transcription unavailable")
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not set — transcription unavailable")
            self.whisper_available = False
            return

        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("   Whisper: OpenAI API ✅")
        except Exception as e:
            logger.error(f"Whisper init error: {e}")
            self.whisper_available = False

    # ─── RECORDING METHODS ─────────────────────────────────────

    def _record_audio(self, duration: float, device: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Record audio for a fixed duration.
        Returns numpy array of audio samples.
        """
        if not self.available:
            print("    ⚠️ sounddevice not available. Install: pip install sounddevice numpy")
            return None

        dev = device if device is not None else self.mic_device
        try:
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                device=dev
            )
            sd.wait()  # Block until recording is done
            return audio.flatten()
        except Exception as e:
            logger.error(f"Recording error: {e}")
            self.stats["errors"] += 1
            return None

    def _record_until_silence(self, max_duration: float = 30.0,
                               silence_threshold: float = 0.01,
                               silence_duration: float = 1.5,
                               device: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Record until silence is detected or max_duration reached.
        Good for push-to-talk style recording.
        """
        if not self.available:
            return None

        dev = device if device is not None else self.mic_device
        chunk_duration = 0.5  # Check every 0.5 seconds
        chunk_samples = int(chunk_duration * self.sample_rate)
        max_chunks = int(max_duration / chunk_duration)

        all_audio = []
        silent_chunks = 0
        required_silent = int(silence_duration / chunk_duration)

        try:
            for i in range(max_chunks):
                chunk = sd.rec(
                    chunk_samples,
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    device=dev
                )
                sd.wait()
                chunk_flat = chunk.flatten()
                all_audio.append(chunk_flat)

                # Check energy level
                energy = np.sqrt(np.mean(chunk_flat ** 2))

                if energy < silence_threshold:
                    silent_chunks += 1
                    if silent_chunks >= required_silent and len(all_audio) > required_silent:
                        break
                else:
                    silent_chunks = 0

            if all_audio:
                return np.concatenate(all_audio)
            return None

        except Exception as e:
            logger.error(f"Recording error: {e}")
            self.stats["errors"] += 1
            return None

    # ─── TRANSCRIPTION ─────────────────────────────────────────

    async def _transcribe(self, audio: np.ndarray) -> Optional[TranscriptResult]:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.whisper_available or self.openai_client is None:
            print("    ⚠️ Whisper API not available")
            return None

        # Save to temp WAV file
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name

            # Write WAV
            audio_int16 = (audio * 32767).astype(np.int16)
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            # Call Whisper API in thread pool
            loop = asyncio.get_event_loop()

            def _call_whisper():
                with open(temp_path, "rb") as audio_file:
                    return self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )

            result = await loop.run_in_executor(None, _call_whisper)

            text = result.text.strip() if result.text else ""
            if not text:
                return None

            # Language detection
            lang = getattr(result, 'language', 'en')
            duration = len(audio) / self.sample_rate

            # Update stats
            self.stats["transcriptions"] += 1
            self.stats["total_audio_seconds"] += duration
            if lang == "ar":
                self.stats["arabic_segments"] += 1
            else:
                self.stats["english_segments"] += 1

            transcript = TranscriptResult(
                text=text,
                language=lang,
                duration=duration
            )

            # Store in history
            self.history.append(transcript)

            return transcript

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            self.stats["errors"] += 1
            return None

        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except:
                    pass

    # ─── PUBLIC METHODS ────────────────────────────────────────

    async def listen_once(self, duration: float = 5.0) -> Optional[str]:
        """
        Record for `duration` seconds and return transcript text.
        Simple one-shot recording.
        """
        print(f"    🎤 Listening for {duration:.0f} seconds...")
        self.is_recording = True
        self.stats["recordings"] += 1

        audio = await asyncio.get_event_loop().run_in_executor(
            None, self._record_audio, duration
        )

        self.is_recording = False

        if audio is None or len(audio) == 0:
            print("    ⚠️ No audio captured")
            return None

        # Check if there's actual sound
        energy = np.sqrt(np.mean(audio ** 2))
        if energy < 0.005:
            print("    🔇 Too quiet — no speech detected")
            return None

        print("    🔄 Transcribing...")
        result = await self._transcribe(audio)

        if result:
            return result.text
        return None

    async def push_to_talk(self) -> Optional[str]:
        """
        Record until silence is detected (max 30 seconds).
        Returns transcript text.

        Good for: "speak your question, pause, get transcript"
        """
        print("    🎤 Speak now... (I'll stop when you pause)")
        self.is_recording = True
        self.stats["recordings"] += 1

        audio = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._record_until_silence(
                max_duration=30.0,
                silence_threshold=0.01,
                silence_duration=1.5
            )
        )

        self.is_recording = False

        if audio is None or len(audio) == 0:
            print("    ⚠️ No audio captured")
            return None

        duration = len(audio) / self.sample_rate
        energy = np.sqrt(np.mean(audio ** 2))

        if energy < 0.005:
            print("    🔇 Too quiet — no speech detected")
            return None

        print(f"    🔄 Transcribing {duration:.1f}s of audio...")
        result = await self._transcribe(audio)

        if result:
            flag = "🇪🇬" if result.language == "ar" else "🇬🇧"
            print(f"    {flag} Heard: {result.text}")
            return result.text
        return None

    async def listen_system(self, duration: float = 30.0) -> Optional[str]:
        """
        Capture system audio (Stereo Mix) for `duration` seconds.
        Use this for audiobooks, YouTube, meetings playing on speakers.
        """
        if self.system_device is None:
            print("    ⚠️ Stereo Mix not found. Enable it in Windows Sound settings:")
            print("       Right-click speaker icon → Sounds → Recording → Show Disabled Devices")
            print("       Right-click 'Stereo Mix' → Enable")
            return None

        print(f"    🔊 Capturing system audio for {duration:.0f}s...")
        self.is_recording = True
        self.stats["recordings"] += 1

        audio = await asyncio.get_event_loop().run_in_executor(
            None, self._record_audio, duration, self.system_device
        )

        self.is_recording = False

        if audio is None or len(audio) == 0:
            print("    ⚠️ No audio captured from system")
            return None

        print(f"    🔄 Transcribing system audio...")
        result = await self._transcribe(audio)

        if result:
            return result.text
        return None

    # ─── ALWAYS-ON AMBIENT MODE ────────────────────────────────

    async def start_ambient(self, on_transcript: Optional[Callable] = None):
        """
        Start always-on ambient listening.
        Transcripts are passed to on_transcript callback.
        """
        if not self.available:
            print("    ⚠️ Cannot start ambient — sounddevice not available")
            return

        if self.is_ambient:
            print("    👂 Already in ambient mode")
            return

        self.is_ambient = True
        self._ambient_task = asyncio.create_task(
            self._ambient_loop(on_transcript)
        )
        print("    👂 Ambient listening started — I hear everything now")

    async def stop_ambient(self):
        """Stop ambient listening"""
        self.is_ambient = False
        if self._ambient_task:
            self._ambient_task.cancel()
            try:
                await self._ambient_task
            except asyncio.CancelledError:
                pass
        print("    👂 Ambient listening stopped")

    async def _ambient_loop(self, on_transcript: Optional[Callable] = None):
        """Background loop for ambient listening with VAD"""
        chunk_duration = 0.5  # seconds
        chunk_samples = int(chunk_duration * self.sample_rate)
        speech_buffer = []
        silent_chunks = 0
        is_speaking = False
        silence_threshold = 0.01
        max_silent_chunks = 3  # 1.5 seconds of silence

        # Calibrate noise floor
        print("    🔇 Calibrating ambient noise... (stay quiet for 2 seconds)")
        await asyncio.sleep(0.5)
        cal_audio = await asyncio.get_event_loop().run_in_executor(
            None, self._record_audio, 2.0
        )
        if cal_audio is not None:
            noise_floor = np.sqrt(np.mean(cal_audio ** 2))
            silence_threshold = max(noise_floor * 2.5, 0.005)
            print(f"    ✅ Calibrated (threshold: {silence_threshold:.4f})")

        while self.is_ambient:
            try:
                # Record one chunk
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, self._record_audio, chunk_duration
                )

                if chunk is None:
                    await asyncio.sleep(0.1)
                    continue

                energy = np.sqrt(np.mean(chunk ** 2))

                if energy > silence_threshold:
                    # Speech detected
                    if not is_speaking:
                        is_speaking = True
                        speech_buffer = []
                    speech_buffer.append(chunk)
                    silent_chunks = 0
                else:
                    # Silence
                    if is_speaking:
                        speech_buffer.append(chunk)  # Include trailing silence
                        silent_chunks += 1

                        if silent_chunks >= max_silent_chunks:
                            # End of speech — transcribe
                            is_speaking = False
                            full_audio = np.concatenate(speech_buffer)
                            duration = len(full_audio) / self.sample_rate

                            if duration >= 0.5:  # Min 0.5s of speech
                                result = await self._transcribe(full_audio)
                                if result and result.text:
                                    if on_transcript:
                                        on_transcript(result)
                                    else:
                                        print(f"\n    👂 {result}\n")

                            speech_buffer = []
                            silent_chunks = 0

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ambient loop error: {e}")
                await asyncio.sleep(1)

    # ─── STATS & INFO ──────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get ear statistics"""
        return {
            **self.stats,
            "available": self.available,
            "whisper_ready": self.whisper_available,
            "is_recording": self.is_recording,
            "is_ambient": self.is_ambient,
            "mic_device": self.mic_device,
            "system_device": self.system_device,
            "history_count": len(self.history),
        }

    def get_recent(self, n: int = 10) -> List[TranscriptResult]:
        """Get recent transcripts"""
        return list(self.history)[-n:]


# ═══════════════════════════════════════════════════════════════
#  QUICK TEST
# ═══════════════════════════════════════════════════════════════

async def _test():
    """Quick test of The Ear"""
    from dotenv import load_dotenv
    load_dotenv()

    ear = TheEar()
    print("\n🎤 Testing push-to-talk (speak, then pause)...\n")
    text = await ear.push_to_talk()
    if text:
        print(f"\n✅ Got: {text}")
    else:
        print("\n⚠️ No transcript")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_test())
