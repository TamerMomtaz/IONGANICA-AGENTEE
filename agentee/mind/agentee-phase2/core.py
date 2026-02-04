"""
🌊 A-GENTEE: THE WAVE — Core v5.0
"أنا الموجة... بسمع، بفكر، بتكلم، بفتكر"
"I am The Wave... I hear, I think, I speak, I remember"

The complete living system:
- THE MIND  🧠 (4 engines: Ollama, Claude, Gemini, OpenAI)
- THE VOICE 🗣️ (ElevenLabs + edge-tts + pyttsx3)
- THE EAR   👂 (Whisper API + speech_recognition)
- THE MEMORY 💾 (SQLite hot + Supabase cold)

&I Philosophy: AI + Human, not AI instead of Human.
"""

import os
import sys
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ─── Component Imports ────────────────────────────
try:
    from agentee.mind import Mind
    MIND_AVAILABLE = True
except ImportError as e:
    print(f"    ⚠️ Mind not available: {e}")
    MIND_AVAILABLE = False

try:
    from agentee.voice import TheVoice
    VOICE_AVAILABLE = True
except ImportError as e:
    print(f"    ⚠️ Voice not available: {e}")
    VOICE_AVAILABLE = False

try:
    from agentee.ear import TheEar
    EAR_AVAILABLE = True
except ImportError as e:
    print(f"    ⚠️ Ear not available: {e}")
    EAR_AVAILABLE = False

try:
    from agentee.memory import TheMemory
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"    ⚠️ Memory not available: {e}")
    MEMORY_AVAILABLE = False


# ─── ASCII Art ────────────────────────────────────
WAVE_BANNER = """
\033[36m
    ╭───╮     ╭───╮     ╭───╮     ╭───╮
   ╱     ╲   ╱     ╲   ╱     ╲   ╱     ╲
  ╱       ╲ ╱       ╲ ╱       ╲ ╱       ╲
─╱─────────╳─────────╳─────────╳─────────╲───
           ╲       ╱ ╲       ╱ ╲       ╱
            ╲     ╱   ╲     ╱   ╲     ╱
             ╰───╯     ╰───╯     ╰───╯
\033[0m
\033[1;36m  🌊 A-GENTEE v5.0 — THE WAVE — IONGANICA 🌊\033[0m
\033[90m  "AI + Human, not AI instead of Human"\033[0m
"""


class AGentee:
    """
    The Wave — A-GENTEE Core v5.0
    
    A complete AI companion that:
    - HEARS (The Ear)
    - THINKS (The Mind)
    - SPEAKS (The Voice)
    - REMEMBERS (The Memory)
    """

    VERSION = "5.0"

    def __init__(self):
        print(WAVE_BANNER)
        print(f"  Initializing A-GENTEE v{self.VERSION}...")
        print()
        
        # ── Initialize Mind ──
        self.mind = None
        if MIND_AVAILABLE:
            self.mind = Mind()
        else:
            print("    ❌ Mind unavailable — cannot think")
        
        # ── Initialize Voice ──
        self.voice = None
        if VOICE_AVAILABLE:
            self.voice = TheVoice()
            vs = self.voice.get_status()
            engines = vs["engines"]
            ready = sum(1 for v in engines.values() if "✅" in v)
            print(f"    🗣️ Voice v{self.voice.VERSION}: {ready}/{len(engines)} engines")
            for name, status in engines.items():
                print(f"        {name}: {status}")
        else:
            print("    ⚠️ Voice not available — text only mode")
        
        # ── Initialize Ear ──
        self.ear = None
        if EAR_AVAILABLE:
            self.ear = TheEar()
            es = self.ear.get_status()
            engines = es["engines"]
            ready = sum(1 for v in engines.values() if "✅" in v)
            print(f"    👂 Ear v{self.ear.VERSION}: {ready}/{len(engines)} engines")
            for name, status in engines.items():
                print(f"        {name}: {status}")
        else:
            print("    ⚠️ Ear not available — keyboard input only")
        
        # ── Initialize Memory ──
        self.memory = None
        if MEMORY_AVAILABLE:
            self.memory = TheMemory()
            ms = self.memory.get_status()
            print(f"    💾 Memory v{self.memory.VERSION}: Hot={ms['hot_memory']['path']}")
            print(f"        Cold: {ms['cold_memory']['supabase']}")
            total_records = sum(ms['hot_memory']['tables'].values())
            print(f"        Records: {total_records} across {len(ms['hot_memory']['tables'])} tables")
        else:
            print("    ⚠️ Memory not available — no persistence")
        
        # ── Session ──
        self.session_id = None
        if self.memory:
            self.session_id = self.memory.start_session()
        
        self.query_count = 0
        self.input_mode = "keyboard"  # 'keyboard' or 'voice'
        
        # ── Ready ──
        print()
        print("  ─────────────────────────────────────────")
        components = []
        if self.mind:    components.append("🧠Mind")
        if self.voice:   components.append("🗣️Voice")
        if self.ear:     components.append("👂Ear")
        if self.memory:  components.append("💾Memory")
        print(f"  Components: {' + '.join(components)}")
        print("  ─────────────────────────────────────────")
        print()
        print("  \033[1;36m🌊 A-GENTEE ready. The Wave is alive.\033[0m")
        print()
        print("  Commands:")
        print("    stats    — Show system statistics")
        print("    voice    — Toggle voice on/off")
        print("    mic      — Toggle microphone input")
        print("    memory   — Show memory status")
        print("    ideas    — Show stored ideas")
        print("    history  — Show recent conversations")
        print("    mode X   — Set voice personality (default/kahotia/professional/creative)")
        print("    quit     — Exit A-GENTEE")
        print()

    async def run(self):
        """Main interaction loop."""
        while True:
            try:
                # Get input (keyboard or microphone)
                user_input = await self._get_input()
                
                if user_input is None:
                    continue
                
                query = user_input.strip()
                if not query:
                    continue
                
                # ── Handle commands ──
                handled = await self._handle_command(query)
                if handled:
                    continue
                
                # ── Think (Mind) ──
                if not self.mind:
                    print("    ❌ No Mind available. Cannot process.")
                    continue
                
                # Build context from memory
                context_prompt = ""
                if self.memory:
                    context_prompt = self.memory.build_context_prompt(max_conversations=3)
                
                # Process with Mind
                response = await self.mind.process(query)
                
                # ── Remember (Memory) ──
                if self.memory and response:
                    # Store conversation
                    engine_used = ""
                    category = ""
                    
                    # Extract engine from response format if available
                    if hasattr(self.mind, 'last_engine'):
                        engine_used = self.mind.last_engine
                    if hasattr(self.mind, 'last_category'):
                        category = self.mind.last_category
                    
                    self.memory.store_conversation(
                        query=query,
                        response=response[:500] if response else "",
                        engine=engine_used,
                        category=category,
                        language=self._detect_language(query),
                        session_id=self.session_id or "",
                    )
                
                # ── Speak (Voice) ──
                if self.voice and self.voice.mode.value != "silent" and response:
                    # Speak the response (don't block — run in background)
                    # Only speak short responses to avoid long TTS
                    if len(response) < 500:
                        await self.voice.speak(response)
                    else:
                        # For long responses, speak just the first sentence
                        first_sentence = response.split('.')[0] + '.'
                        if len(first_sentence) < 200:
                            await self.voice.speak(first_sentence)
                
                self.query_count += 1
                
            except KeyboardInterrupt:
                print("\n")
                await self._shutdown()
                break
            except EOFError:
                await self._shutdown()
                break
            except Exception as e:
                print(f"\n    ⚠️ Error: {e}")
                import traceback
                traceback.print_exc()

    async def _get_input(self) -> str:
        """Get input from keyboard or microphone."""
        if self.input_mode == "voice" and self.ear:
            print("    🎤 Voice mode — speak or type (press Enter for keyboard):")
            
            # Simple approach: still use keyboard but offer voice option
            loop = asyncio.get_event_loop()
            user_input = await loop.run_in_executor(None, 
                lambda: input("\033[36m  🌊 Tee (type or 'v' for voice) → \033[0m"))
            
            if user_input.strip().lower() == 'v':
                # Voice input
                result = await self.ear.listen_push_to_talk()
                if result["text"]:
                    print(f"    🎤 Heard: {result['text']}")
                    return result["text"]
                else:
                    print("    ⚠️ Couldn't hear anything. Try again or type.")
                    return None
            else:
                return user_input
        else:
            # Keyboard input
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, 
                lambda: input("\033[36m  🌊 Tee → \033[0m"))

    async def _handle_command(self, query: str) -> bool:
        """Handle system commands. Returns True if handled."""
        cmd = query.lower().strip()
        
        if cmd == "quit" or cmd == "exit":
            await self._shutdown()
            sys.exit(0)
        
        elif cmd == "stats":
            await self._show_stats()
            return True
        
        elif cmd == "voice":
            if self.voice:
                if self.voice.mode.value == "silent":
                    self.voice.set_mode("voice")
                    print("    🗣️ Voice mode: ON")
                    await self.voice.speak("Voice activated.")
                else:
                    self.voice.set_mode("silent")
                    print("    🔇 Voice mode: OFF (silent)")
            else:
                print("    ⚠️ Voice system not available")
            return True
        
        elif cmd == "mic":
            if self.ear:
                if self.input_mode == "keyboard":
                    self.input_mode = "voice"
                    print("    🎤 Input mode: VOICE (press 'v' to speak)")
                else:
                    self.input_mode = "keyboard"
                    print("    ⌨️ Input mode: KEYBOARD")
            else:
                print("    ⚠️ Ear system not available")
            return True
        
        elif cmd == "memory":
            if self.memory:
                status = self.memory.get_status()
                print("    💾 MEMORY STATUS")
                print(f"    Hot: {status['hot_memory']['path']}")
                for table, count in status['hot_memory']['tables'].items():
                    print(f"      {table}: {count} records")
                print(f"    Cold: {status['cold_memory']['supabase']}")
                print(f"    Stats: {status['stats']}")
            else:
                print("    ⚠️ Memory not available")
            return True
        
        elif cmd == "ideas":
            if self.memory:
                ideas = self.memory.get_ideas(limit=10)
                if ideas:
                    print("    💡 STORED IDEAS")
                    for i, idea in enumerate(ideas, 1):
                        print(f"    {i}. [{idea['category']}] {idea['idea'][:80]}")
                else:
                    print("    No ideas stored yet.")
            else:
                print("    ⚠️ Memory not available")
            return True
        
        elif cmd == "history":
            if self.memory:
                convs = self.memory.get_recent_conversations(limit=5)
                if convs:
                    print("    📜 RECENT CONVERSATIONS")
                    for c in convs:
                        ts = c['timestamp'][:16]
                        print(f"    [{ts}] Tee: {c['query'][:60]}")
                        print(f"             → ({c['engine']}) {c['response'][:60]}")
                        print()
                else:
                    print("    No conversations stored yet.")
            else:
                print("    ⚠️ Memory not available")
            return True
        
        elif cmd.startswith("mode "):
            personality = cmd[5:].strip()
            if self.voice:
                self.voice.set_personality(personality)
                print(f"    🎭 Voice personality: {personality}")
            return True
        
        return False

    async def _show_stats(self):
        """Display comprehensive system stats."""
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║     🌊 A-GENTEE v5.0 SYSTEM STATS       ║")
        print("  ╚══════════════════════════════════════════╝")
        
        # Mind stats
        if self.mind:
            print("\n  🧠 THE MIND")
            if hasattr(self.mind, 'get_stats'):
                stats = self.mind.get_stats()
                for engine, count in stats.items():
                    print(f"    {engine}: {count} queries")
        
        # Voice stats
        if self.voice:
            print("\n  🗣️ THE VOICE")
            vs = self.voice.stats
            print(f"    Mode: {self.voice.mode.value}")
            print(f"    Personality: {self.voice.personality}")
            print(f"    ElevenLabs calls: {vs['elevenlabs_calls']}")
            print(f"    Edge-TTS calls: {vs['edge_tts_calls']}")
            print(f"    Chars spoken: {vs['chars_spoken']}")
        
        # Ear stats
        if self.ear:
            print("\n  👂 THE EAR")
            es = self.ear.stats
            print(f"    Input mode: {self.input_mode}")
            print(f"    Whisper calls: {es['whisper_calls']}")
            print(f"    Transcriptions: {es['transcriptions']}")
            print(f"    Seconds heard: {es['total_seconds_heard']:.1f}")
        
        # Memory stats
        if self.memory:
            print("\n  💾 THE MEMORY")
            ms = self.memory.get_status()
            for table, count in ms['hot_memory']['tables'].items():
                if count > 0:
                    print(f"    {table}: {count}")
            print(f"    Hot writes: {ms['stats']['hot_writes']}")
            print(f"    Hot reads: {ms['stats']['hot_reads']}")
        
        print(f"\n  📊 Session: {self.query_count} queries")
        print()

    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        total = len(text.replace(" ", ""))
        if total == 0:
            return "en"
        ratio = arabic_count / total
        if ratio > 0.5:
            return "ar"
        elif ratio > 0.1:
            return "mixed"
        return "en"

    async def _shutdown(self):
        """Graceful shutdown."""
        print("  🌊 The Wave recedes... until next time.")
        
        if self.memory and self.session_id:
            engines_used = {}
            if self.mind and hasattr(self.mind, 'get_stats'):
                engines_used = self.mind.get_stats()
            
            self.memory.end_session(
                self.session_id,
                queries_count=self.query_count,
                engines_used=engines_used,
            )
            print("  💾 Session saved to memory.")
        
        print("  أنا الموجة... راجع تاني. 🌊")


# ─── Entry Point ──────────────────────────────────
def main():
    agentee = AGentee()
    asyncio.run(agentee.run())


if __name__ == "__main__":
    main()
