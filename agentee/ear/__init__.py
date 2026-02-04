"""
THE ULTIMATE EAR v2.0
Always-On Audio Intelligence - sounddevice (no PyAudio needed!)

Works on Python 3.14
Auto-detects Arabic/English
Push-to-talk + Always-on modes
Captures mic + system audio (Stereo Mix)
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

# Audio capture
try:
    import sounddevice as sd
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Whisper (cloud)
try:
    from openai import OpenAI
    WHISPER_API = True
except ImportError:
    WHISPER_API = False


@dataclass
class TranscriptResult:
    """Result from a transcription"""
    text: str
    language: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        flag = "\U0001f1ea\U0001f1ec" if self.language == "ar" else "\U0001f1ec\U0001f1e7" if self.language == "en" else "\U0001f310"
        return f"[{flag}] {self.text}"


class TheEar:
    """
    THE ULTIMATE EAR v2.0

    Modes:
      push_to_talk()  - Record while speaking, stop on silence
      listen_once()   - Record for N seconds, return transcript
      start_ambient() - Always-on background listening
      listen_system() - Capture system audio (Stereo Mix)

    All transcription uses OpenAI Whisper API.
    Audio capture uses sounddevice (works on Python 3.14).
    """

    VERSION = "2.0"

    def __init__(self):
        self.available = AUDIO_AVAILABLE
        self.whisper_available = WHISPER_API
        self.openai_client = None

        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.dtype = "float32"

        # Device IDs
        self.mic_device = None
        self.system_device = None

        # State
        self.is_recording = False
        self.is_ambient = False
        self._ambient_task = None

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
        self.history = deque(maxlen=50)

        # Initialize
        self._init_devices()
        self._init_whisper()

        status = "Ready" if (self.available and self.whisper_available) else "Limited"
        logger.info(f"TheEar v{self.VERSION} - {status}")

    def _init_devices(self):
        if not self.available:
            return
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            self.mic_device = default_input

            for i, dev in enumerate(devices):
                name = dev.get('name', '').lower()
                if 'stereo mix' in name and dev.get('max_input_channels', 0) > 0:
                    self.system_device = i
                    break
        except Exception as e:
            logger.error(f"Device detection error: {e}")

    def _init_whisper(self):
        if not WHISPER_API:
            self.whisper_available = False
            return

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.whisper_available = False
            return

        try:
            self.openai_client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Whisper init error: {e}")
            self.whisper_available = False

    def _record_audio(self, duration, device=None):
        """Record audio for a fixed duration."""
        if not self.available:
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
            sd.wait()
            return audio.flatten()
        except Exception as e:
            logger.error(f"Recording error: {e}")
            self.stats["errors"] += 1
            return None

    def _record_until_silence(self, max_duration=30.0, silence_threshold=0.01,
                               silence_duration=1.5, device=None):
        """Record until silence is detected."""
        if not self.available:
            return None
        dev = device if device is not None else self.mic_device
        chunk_duration = 0.5
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

                energy = float(np.sqrt(np.mean(chunk_flat ** 2)))

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

    async def _transcribe(self, audio_array):
        """Transcribe numpy audio array using Whisper API."""
        if not self.whisper_available or self.openai_client is None:
            return None

        try:
            # Save to temp WAV file
            tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            tmp_path = tmp.name

            # Convert float32 to int16
            audio_int16 = (audio_array * 32767).astype(np.int16)

            with wave.open(tmp_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            tmp.close()

            # Call Whisper API
            with open(tmp_path, 'rb') as audio_file:
                response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    prompt="A-GENTEE, DEVONEERS, RootRise, Tamer, Kahotia",
                    response_format="verbose_json",
                )

            # Clean up
            os.unlink(tmp_path)

            text = response.text.strip() if hasattr(response, 'text') else ""
            lang = getattr(response, "language", "unknown")
            dur = getattr(response, "duration", len(audio_array) / self.sample_rate)

            self.stats["transcriptions"] += 1
            self.stats["total_audio_seconds"] += dur

            if lang == "arabic" or lang == "ar":
                self.stats["arabic_segments"] += 1
                lang = "ar"
            elif lang == "english" or lang == "en":
                self.stats["english_segments"] += 1
                lang = "en"

            result = TranscriptResult(text=text, language=lang, duration=dur)
            self.history.append(result)
            return result

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            self.stats["errors"] += 1
            try:
                os.unlink(tmp_path)
            except:
                pass
            return None

    async def listen_once(self, duration=5.0):
        """Record for N seconds and transcribe."""
        print(f"    Listening for {duration:.0f} seconds...")
        self.is_recording = True
        self.stats["recordings"] += 1

        audio = await asyncio.get_event_loop().run_in_executor(
            None, self._record_audio, duration
        )
        self.is_recording = False

        if audio is None or len(audio) == 0:
            print("    No audio captured")
            return None

        energy = float(np.sqrt(np.mean(audio ** 2)))
        if energy < 0.005:
            print("    Too quiet - no speech detected")
            return None

        print("    Transcribing...")
        result = await self._transcribe(audio)
        if result:
            return result.text
        return None

    async def push_to_talk(self):
        """Record until silence (max 30s). Returns transcript text."""
        print("    Speak now... (I'll stop when you pause)")
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
            print("    No audio captured")
            return None

        duration = len(audio) / self.sample_rate
        energy = float(np.sqrt(np.mean(audio ** 2)))

        if energy < 0.005:
            print("    Too quiet - no speech detected")
            return None

        print(f"    Transcribing {duration:.1f}s of audio...")
        result = await self._transcribe(audio)

        if result:
            print(f"    Heard: {result.text}")
            return result.text
        return None

    async def listen_system(self, duration=30.0):
        """Capture system audio via Stereo Mix."""
        if self.system_device is None:
            print("    Stereo Mix not found. Enable in Windows Sound settings:")
            print("    Right-click speaker > Sounds > Recording > Show Disabled > Enable Stereo Mix")
            return None

        print(f"    Capturing system audio for {duration:.0f}s...")
        self.is_recording = True
        self.stats["recordings"] += 1

        audio = await asyncio.get_event_loop().run_in_executor(
            None, self._record_audio, duration, self.system_device
        )
        self.is_recording = False

        if audio is None or len(audio) == 0:
            print("    No audio captured from system")
            return None

        print("    Transcribing system audio...")
        result = await self._transcribe(audio)
        if result:
            return result.text
        return None

    async def start_ambient(self, on_transcript=None):
        """Start always-on ambient listening."""
        if not self.available:
            print("    Cannot start ambient - sounddevice not available")
            return
        if self.is_ambient:
            print("    Already in ambient mode")
            return

        self.is_ambient = True
        self._ambient_task = asyncio.create_task(self._ambient_loop(on_transcript))
        print("    Ambient listening started")

    async def stop_ambient(self):
        """Stop ambient listening."""
        self.is_ambient = False
        if self._ambient_task:
            self._ambient_task.cancel()
            try:
                await self._ambient_task
            except asyncio.CancelledError:
                pass
        print("    Ambient listening stopped")

    async def _ambient_loop(self, on_transcript=None):
        """Background loop for ambient listening with VAD."""
        chunk_duration = 0.5
        speech_buffer = []
        silent_chunks = 0
        is_speaking = False
        silence_threshold = 0.01
        max_silent_chunks = 3

        # Calibrate
        print("    Calibrating ambient noise... (stay quiet 2s)")
        await asyncio.sleep(0.5)
        cal = await asyncio.get_event_loop().run_in_executor(None, self._record_audio, 2.0)
        if cal is not None:
            noise_floor = float(np.sqrt(np.mean(cal ** 2)))
            silence_threshold = max(noise_floor * 2.5, 0.005)
            print(f"    Calibrated (threshold: {silence_threshold:.4f})")

        while self.is_ambient:
            try:
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None, self._record_audio, chunk_duration
                )
                if chunk is None:
                    await asyncio.sleep(0.1)
                    continue

                energy = float(np.sqrt(np.mean(chunk ** 2)))

                if energy > silence_threshold:
                    if not is_speaking:
                        is_speaking = True
                        speech_buffer = []
                    speech_buffer.append(chunk)
                    silent_chunks = 0
                else:
                    if is_speaking:
                        speech_buffer.append(chunk)
                        silent_chunks += 1
                        if silent_chunks >= max_silent_chunks:
                            is_speaking = False
                            full_audio = np.concatenate(speech_buffer)
                            dur = len(full_audio) / self.sample_rate
                            if dur >= 0.5:
                                result = await self._transcribe(full_audio)
                                if result and result.text:
                                    if on_transcript:
                                        on_transcript(result)
                                    else:
                                        print(f"\n    Heard: {result}\n")
                            speech_buffer = []
                            silent_chunks = 0

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ambient loop error: {e}")
                await asyncio.sleep(1)

    def get_stats(self):
        """Get ear statistics."""
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

    def get_recent(self, n=10):
        """Get recent transcripts."""
        return list(self.history)[-n:]


if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    async def _test():
        ear = TheEar()
        print(f"\nUltimate Ear v{ear.VERSION}")
        stats = ear.get_stats()
        print(f"Available: {stats['available']}")
        print(f"Whisper: {stats['whisper_ready']}")
        print(f"Mic: {stats['mic_device']}")
        print(f"System: {stats['system_device']}")

        if stats['available'] and stats['whisper_ready']:
            print("\nTesting push-to-talk...")
            text = await ear.push_to_talk()
            if text:
                print(f"Got: {text}")
            else:
                print("No transcript")

    asyncio.run(_test())
