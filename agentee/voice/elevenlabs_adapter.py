"""
THE VOICE - ElevenLabs Adapter
==============================
Speaks with Tee's cloned voice

A-GENTEE literally speaks with YOUR voice!
"""

import asyncio
import io
from typing import Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger

try:
    from elevenlabs import AsyncElevenLabs, Voice, VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False


@dataclass
class VoiceResponse:
    """Response from voice synthesis"""
    audio_data: bytes
    duration_ms: int
    cost: float


class ElevenLabsAdapter:
    """
    Adapter for ElevenLabs Voice Synthesis
    
    Uses Tee's cloned voice to speak responses.
    
    Features:
    - Multiple voice modes (default, kahotia, professional, creative)
    - Multilingual support (Arabic + English)
    - Cost tracking
    """
    
    # Approximate costs per character (vary by tier)
    COST_PER_CHAR = 0.00003  # ~$30 per 1M characters on Creator tier
    
    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.api_key = config.get('api_key')
        self.voice_id = config.get('voice_id')
        self.model_id = config.get('model_id', 'eleven_multilingual_v2')
        
        # Voice settings
        self.stability = config.get('stability', 0.5)
        self.similarity_boost = config.get('similarity_boost', 0.8)
        
        # Initialize client
        self.client = None
        if ELEVENLABS_AVAILABLE and self.api_key:
            self.client = AsyncElevenLabs(api_key=self.api_key)
        
        # Voice modes
        self.modes = {
            'default': {
                'stability': 0.5,
                'similarity_boost': 0.8,
                'style': 0.0,
                'use_speaker_boost': True
            },
            'kahotia': {
                'stability': 0.4,
                'similarity_boost': 0.9,
                'style': 0.3,  # More dramatic
                'use_speaker_boost': True
            },
            'professional': {
                'stability': 0.7,
                'similarity_boost': 0.75,
                'style': 0.0,
                'use_speaker_boost': True
            },
            'creative': {
                'stability': 0.3,
                'similarity_boost': 0.85,
                'style': 0.5,  # Most expressive
                'use_speaker_boost': True
            }
        }
    
    async def is_available(self) -> bool:
        """Check if ElevenLabs is configured"""
        return self.client is not None and self.voice_id is not None
    
    def _calculate_cost(self, text: str) -> float:
        """Estimate cost based on character count"""
        return len(text) * self.COST_PER_CHAR
    
    async def speak(
        self,
        text: str,
        mode: str = 'default',
        output_file: Optional[str] = None
    ) -> VoiceResponse:
        """
        Convert text to speech using Tee's cloned voice
        
        Args:
            text: Text to speak
            mode: Voice mode (default, kahotia, professional, creative)
            output_file: Optional path to save audio
            
        Returns:
            VoiceResponse with audio data
        """
        if not await self.is_available():
            raise Exception("ElevenLabs not configured")
        
        # Get mode settings
        mode_settings = self.modes.get(mode, self.modes['default'])
        
        try:
            # Generate audio
            audio = await self.client.generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=VoiceSettings(
                        stability=mode_settings['stability'],
                        similarity_boost=mode_settings['similarity_boost'],
                        style=mode_settings.get('style', 0.0),
                        use_speaker_boost=mode_settings.get('use_speaker_boost', True)
                    )
                ),
                model=self.model_id
            )
            
            # Collect audio bytes
            audio_bytes = b''
            async for chunk in audio:
                audio_bytes += chunk
            
            # Calculate cost
            cost = self._calculate_cost(text)
            
            # Estimate duration (~150 words per minute, ~5 chars per word)
            duration_ms = int((len(text) / 5 / 150) * 60 * 1000)
            
            logger.info(f"Generated speech: {len(text)} chars, ~{duration_ms}ms, ${cost:.4f}")
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'wb') as f:
                    f.write(audio_bytes)
                logger.info(f"Saved audio to {output_file}")
            
            return VoiceResponse(
                audio_data=audio_bytes,
                duration_ms=duration_ms,
                cost=cost
            )
            
        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            raise
    
    async def speak_arabic(self, text: str, mode: str = 'default') -> VoiceResponse:
        """
        Speak Arabic text
        
        The eleven_multilingual_v2 model handles Arabic natively.
        """
        return await self.speak(text, mode)
    
    async def speak_bilingual(
        self,
        arabic_text: str,
        english_text: str,
        mode: str = 'default'
    ) -> VoiceResponse:
        """
        Speak mixed Arabic/English content
        
        Useful for code-switching common in MENA conversations.
        """
        combined = f"{arabic_text} {english_text}"
        return await self.speak(combined, mode)


class FallbackVoice:
    """
    Fallback voice synthesis when ElevenLabs isn't available
    
    Uses edge-tts (free) or pyttsx3 (offline)
    """
    
    def __init__(self):
        self.edge_tts_available = False
        self.pyttsx3_available = False
        
        try:
            import edge_tts
            self.edge_tts_available = True
        except ImportError:
            pass
        
        try:
            import pyttsx3
            self.pyttsx3_available = True
        except ImportError:
            pass
    
    async def speak(self, text: str, output_file: str = None) -> bytes:
        """Generate speech using available fallback"""
        if self.edge_tts_available:
            return await self._speak_edge_tts(text, output_file)
        elif self.pyttsx3_available:
            return self._speak_pyttsx3(text, output_file)
        else:
            raise Exception("No voice synthesis available")
    
    async def _speak_edge_tts(self, text: str, output_file: str = None) -> bytes:
        """Use Edge TTS (free, online)"""
        import edge_tts
        
        # Use a natural-sounding voice
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        
        audio_bytes = b''
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(audio_bytes)
        
        return audio_bytes
    
    def _speak_pyttsx3(self, text: str, output_file: str = None) -> bytes:
        """Use pyttsx3 (offline)"""
        import pyttsx3
        
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        
        if output_file:
            engine.save_to_file(text, output_file)
            engine.runAndWait()
            with open(output_file, 'rb') as f:
                return f.read()
        else:
            # Just speak without saving
            engine.say(text)
            engine.runAndWait()
            return b''


class VoiceManager:
    """
    Manages all voice synthesis with automatic fallback
    
    Priority:
    1. ElevenLabs (Tee's cloned voice) - premium
    2. Edge TTS (free, online)
    3. pyttsx3 (free, offline)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        
        # Primary voice
        self.elevenlabs = ElevenLabsAdapter(config.get('elevenlabs', {}))
        
        # Fallback
        self.fallback = FallbackVoice()
    
    async def speak(
        self,
        text: str,
        mode: str = 'default',
        prefer_cloned: bool = True
    ) -> bytes:
        """
        Speak text with best available voice
        
        Args:
            text: Text to speak
            mode: Voice mode
            prefer_cloned: Try ElevenLabs first if available
            
        Returns:
            Audio bytes
        """
        if prefer_cloned and await self.elevenlabs.is_available():
            try:
                response = await self.elevenlabs.speak(text, mode)
                return response.audio_data
            except Exception as e:
                logger.warning(f"ElevenLabs failed, using fallback: {e}")
        
        # Use fallback
        return await self.fallback.speak(text)


# ============================================
# QUICK TEST
# ============================================

async def test_voice():
    """Quick test of voice adapters"""
    import os
    
    print("🌊 Testing Voice Components...")
    print("")
    
    # Test ElevenLabs
    print("1. Testing ElevenLabs...")
    elevenlabs = ElevenLabsAdapter({
        'api_key': os.environ.get('ELEVENLABS_API_KEY'),
        'voice_id': os.environ.get('ELEVENLABS_VOICE_ID')
    })
    
    if await elevenlabs.is_available():
        print("   ✅ ElevenLabs configured!")
        try:
            response = await elevenlabs.speak(
                "أنا الموجة. The Wave speaks.",
                output_file="test_voice.mp3"
            )
            print(f"   Generated: {len(response.audio_data)} bytes")
            print(f"   Cost: ${response.cost:.4f}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️ ElevenLabs not configured")
    
    print("")
    
    # Test fallback
    print("2. Testing Fallback Voice...")
    fallback = FallbackVoice()
    
    if fallback.edge_tts_available:
        print("   ✅ Edge TTS available")
        try:
            audio = await fallback.speak("Hello, I am A-GENTEE fallback voice.")
            print(f"   Generated: {len(audio)} bytes")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("   ⚠️ Edge TTS not available")
    
    if fallback.pyttsx3_available:
        print("   ✅ pyttsx3 available")
    else:
        print("   ⚠️ pyttsx3 not available")
    
    print("")
    print("🌊 Voice test complete!")


if __name__ == "__main__":
    asyncio.run(test_voice())
