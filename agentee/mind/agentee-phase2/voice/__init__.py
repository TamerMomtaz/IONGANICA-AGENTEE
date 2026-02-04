"""
🗣️ THE VOICE — A-GENTEE Output Layer v1.0
"أنا الموجة... بتكلم بصوتك، بس بعقلي"
"I am The Wave... Speaking with your voice, but with my mind"

Three-tier voice system:
1. ElevenLabs (Tee's cloned voice) — PRIMARY
2. Edge-TTS (Microsoft free voices) — FALLBACK
3. pyttsx3 (Offline local) — EMERGENCY

The Voice respects context:
- Voice mode: speaks aloud (default when alone)
- Silent mode: text only (when others detected)
- Whisper mode: quiet voice (late night)
"""

import os
import asyncio
import tempfile
import subprocess
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

load_dotenv()


class VoiceMode(Enum):
    VOICE = "voice"       # Full voice output
    SILENT = "silent"     # Text only, no audio
    WHISPER = "whisper"   # Quiet/low volume


class TheVoice:
    """
    A-GENTEE's output layer — speaks with Tee's cloned voice.
    
    Tier 1: ElevenLabs (cloned voice, premium)
    Tier 2: Edge-TTS (free Microsoft voices, good quality)
    Tier 3: pyttsx3 (offline, robotic but always works)
    """

    VERSION = "1.0"

    def __init__(self):
        self.mode = VoiceMode.VOICE
        self.elevenlabs_ready = False
        self.edge_tts_ready = False
        self.pyttsx3_ready = False
        
        # ElevenLabs config
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.elevenlabs_voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")
        self.elevenlabs_model = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        
        # Voice personality (adjustable)
        self.personality = "default"
        self.personalities = {
            "default":      {"stability": 0.5, "similarity": 0.75, "speed": 1.0},
            "kahotia":      {"stability": 0.3, "similarity": 0.8,  "speed": 0.9},
            "professional": {"stability": 0.7, "similarity": 0.7,  "speed": 1.1},
            "creative":     {"stability": 0.4, "similarity": 0.8,  "speed": 0.95},
            "whisper":      {"stability": 0.6, "similarity": 0.7,  "speed": 0.85},
        }
        
        # Stats
        self.stats = {
            "elevenlabs_calls": 0,
            "edge_tts_calls": 0,
            "pyttsx3_calls": 0,
            "chars_spoken": 0,
            "silent_skips": 0,
        }
        
        # Initialize available engines
        self._init_engines()

    def _init_engines(self):
        """Check which voice engines are available."""
        # Tier 1: ElevenLabs
        if self.elevenlabs_api_key and self.elevenlabs_voice_id:
            try:
                from elevenlabs import ElevenLabs
                self.el_client = ElevenLabs(api_key=self.elevenlabs_api_key)
                self.elevenlabs_ready = True
            except ImportError:
                self.elevenlabs_ready = False
            except Exception:
                self.elevenlabs_ready = False
        
        # Tier 2: Edge-TTS (always available after pip install)
        try:
            import edge_tts
            self.edge_tts_ready = True
        except ImportError:
            self.edge_tts_ready = False

        # Tier 3: pyttsx3 (offline)
        try:
            import pyttsx3
            self.pyttsx3_ready = True
        except ImportError:
            self.pyttsx3_ready = False

    def get_status(self) -> dict:
        """Return voice system status."""
        return {
            "version": self.VERSION,
            "mode": self.mode.value,
            "personality": self.personality,
            "engines": {
                "elevenlabs": "✅ Ready (Tee's voice)" if self.elevenlabs_ready else "❌ Not configured",
                "edge_tts": "✅ Ready (free backup)" if self.edge_tts_ready else "❌ Not installed",
                "pyttsx3": "✅ Ready (offline)" if self.pyttsx3_ready else "❌ Not installed",
            },
            "stats": self.stats,
        }

    def set_mode(self, mode: str):
        """Switch voice mode: 'voice', 'silent', 'whisper'."""
        try:
            self.mode = VoiceMode(mode.lower())
        except ValueError:
            print(f"⚠️ Unknown mode '{mode}'. Use: voice, silent, whisper")

    def set_personality(self, personality: str):
        """Switch voice personality."""
        if personality in self.personalities:
            self.personality = personality
        else:
            print(f"⚠️ Unknown personality '{personality}'. Options: {list(self.personalities.keys())}")

    async def speak(self, text: str, force_voice: bool = False) -> bool:
        """
        Main speak method — routes to best available engine.
        
        Returns True if audio was played, False if silent/failed.
        """
        if not text or not text.strip():
            return False

        # Silent mode — skip audio
        if self.mode == VoiceMode.SILENT and not force_voice:
            self.stats["silent_skips"] += 1
            return False

        self.stats["chars_spoken"] += len(text)

        # Try engines in priority order
        # Tier 1: ElevenLabs
        if self.elevenlabs_ready:
            success = await self._speak_elevenlabs(text)
            if success:
                self.stats["elevenlabs_calls"] += 1
                return True

        # Tier 2: Edge-TTS
        if self.edge_tts_ready:
            success = await self._speak_edge_tts(text)
            if success:
                self.stats["edge_tts_calls"] += 1
                return True

        # Tier 3: pyttsx3
        if self.pyttsx3_ready:
            success = self._speak_pyttsx3(text)
            if success:
                self.stats["pyttsx3_calls"] += 1
                return True

        # All engines failed
        return False

    async def _speak_elevenlabs(self, text: str) -> bool:
        """Speak using ElevenLabs — Tee's cloned voice."""
        try:
            from elevenlabs import ElevenLabs
            
            params = self.personalities.get(self.personality, self.personalities["default"])
            
            # Generate audio
            audio_generator = self.el_client.text_to_speech.convert(
                voice_id=self.elevenlabs_voice_id,
                text=text,
                model_id=self.elevenlabs_model,
                voice_settings={
                    "stability": params["stability"],
                    "similarity_boost": params["similarity"],
                }
            )
            
            # Save to temp file and play
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                for chunk in audio_generator:
                    f.write(chunk)
                temp_path = f.name
            
            await self._play_audio(temp_path)
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"    ⚠️ ElevenLabs error: {e}")
            return False

    async def _speak_edge_tts(self, text: str) -> bool:
        """Speak using Edge-TTS — free Microsoft voices."""
        try:
            import edge_tts
            
            # Detect language for voice selection
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
            
            if has_arabic:
                voice = "ar-EG-ShakirNeural"  # Egyptian Arabic
            else:
                voice = "en-US-GuyNeural"     # English male
            
            # Generate audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
            
            await self._play_audio(temp_path)
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"    ⚠️ Edge-TTS error: {e}")
            return False

    def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3 — offline, always works."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            params = self.personalities.get(self.personality, self.personalities["default"])
            rate = engine.getProperty('rate')
            engine.setProperty('rate', int(rate * params["speed"]))
            
            engine.say(text)
            engine.runAndWait()
            
            return True
            
        except Exception as e:
            print(f"    ⚠️ pyttsx3 error: {e}")
            return False

    async def _play_audio(self, filepath: str):
        """Play audio file cross-platform."""
        import platform
        system = platform.system()
        
        try:
            if system == "Windows":
                # Use Windows Media Player via PowerShell (silent, no window)
                cmd = (
                    f'powershell -Command "'
                    f"Add-Type -AssemblyName presentationCore; "
                    f"$player = New-Object System.Windows.Media.MediaPlayer; "
                    f"$player.Open('{filepath}'); "
                    f"Start-Sleep -Milliseconds 500; "
                    f"$player.Play(); "
                    f"Start-Sleep -Seconds ([math]::Ceiling($player.NaturalDuration.TimeSpan.TotalSeconds + 1)); "
                    f"$player.Close()"
                    f'"'
                )
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                
            elif system == "Darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    "afplay", filepath,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                
            else:  # Linux
                process = await asyncio.create_subprocess_exec(
                    "aplay", filepath,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.wait()
                
        except Exception as e:
            print(f"    ⚠️ Audio playback error: {e}")


# Quick test
if __name__ == "__main__":
    async def test():
        voice = TheVoice()
        status = voice.get_status()
        print("🗣️ THE VOICE Status:")
        for k, v in status["engines"].items():
            print(f"    {k}: {v}")
        
        await voice.speak("A-GENTEE is alive. The Wave speaks.")
    
    asyncio.run(test())
