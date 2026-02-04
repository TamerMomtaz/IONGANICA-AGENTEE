"""
🌊 A-GENTEE: THE WAVE — Core v5.1
"أنا الموجة... بسمع، بفكر، بتكلم، بفتكر"
"I am The Wave... I hear, I think, I speak, I remember"

The complete living system:
- THE MIND  🧠 (4 engines: Ollama, Claude, Gemini, OpenAI)
- THE VOICE 🗣️ (ElevenLabs + edge-tts + pyttsx3)
- THE EAR   👂 (sounddevice + Whisper API — ULTIMATE EAR v2.0)
- THE MEMORY 💾 (SQLite hot + Supabase cold)

v5.1 Changes:
- 'v' command properly triggers push-to-talk voice input
- 'mic' toggles always-on ambient listening
- 'listen' captures system audio (audiobooks, meetings)
- Ear compatible with Ultimate Ear v2.0 (sounddevice, no PyAudio)
- Fixed Ear init to work with new get_stats() API

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
\033[1;36m  🌊 A-GENTEE v5.1 — THE WAVE — IONGANICA 🌊\033[0m
\033[90m  "AI + Human, not AI instead of Human"\033[0m
"""


class AGentee:
    """
    The Wave — A-GENTEE Core v5.1
    
    A complete AI companion that:
    - HEARS (The Ear — Ultimate Ear v2.0)
    - THINKS (The Mind — 4-engine ensemble)
    - SPEAKS (The Voice — ElevenLabs + fallbacks)
    - REMEMBERS (The Memory — SQLite + Supabase)
    """

    VERSION = "5.1"

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
            try:
                vs = self.voice.get_status()
                engines = vs.get("engines", {})
                ready = sum(1 for v in engines.values() if "✅" in str(v))
                print(f"    🗣️ Voice v{self.voice.VERSION}: {ready}/{len(engines)} engines")
                for name, status in engines.items():
                    print(f"        {name}: {status}")
            except Exception as e:
                print(f"    🗣️ Voice initialized (status: {e})")
        else:
            print("    ⚠️ Voice not available — text only mode")
        
        # ── Initialize Ear (Ultimate Ear v2.0) ──
        self.ear = None
        if EAR_AVAILABLE:
            try:
                self.ear = TheEar()
                # Ultimate Ear v2.0 uses get_stats(), not get_status()
                if hasattr(self.ear, 'get_stats'):
                    es = self.ear.get_stats()
                    mic_ok = "✅" if es.get("available") else "❌"
                    whisper_ok = "✅" if es.get("whisper_ready") else "❌"
                    print(f"    👂 Ear v{self.ear.VERSION}: Mic {mic_ok} | Whisper {whisper_ok}")
                    if es.get("system_device") is not None:
                        print(f"        Stereo Mix: ✅ (device {es['system_device']})")
                    else:
                        print(f"        Stereo Mix: ❌ (enable in Sound settings)")
                elif hasattr(self.ear, 'get_status'):
                    # Backward compat with old Ear
                    es = self.ear.get_status()
                    engines = es.get("engines", {})
                    print(f"    👂 Ear v{self.ear.VERSION}")
                    for name, status in engines.items():
                        print(f"        {name}: {status}")
                else:
                    print(f"    👂 Ear initialized")
            except Exception as e:
                print(f"    ⚠️ Ear init issue: {e}")
                self.ear = None
        else:
            print("    ⚠️ Ear not available — keyboard input only")
        
        # ── Initialize Memory ──
        self.memory = None
        if MEMORY_AVAILABLE:
            self.memory = TheMemory()
            try:
                ms = self.memory.get_status()
                print(f"    💾 Memory v{self.memory.VERSION}: Hot={ms['hot_memory']['path']}")
                print(f"        Cold: {ms['cold_memory']['supabase']}")
                total_records = sum(ms['hot_memory']['tables'].values())
                print(f"        Records: {total_records} across {len(ms['hot_memory']['tables'])} tables")
            except Exception as e:
                print(f"    💾 Memory initialized ({e})")
        else:
            print("    ⚠️ Memory not available — no persistence")
        
        # ── Session ──
        self.session_id = None
        if self.memory:
            try:
                self.session_id = self.memory.start_session()
            except Exception:
                pass
        
        self.query_count = 0
        
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
        print("    v        — \033[1;32mVoice input (speak to me!)\033[0m")
        print("    mic      — Toggle always-on ambient listening")
        print("    listen   — Capture system audio (audiobooks, meetings)")
        print("    stats    — Show system statistics")
        print("    voice    — Toggle voice output on/off")
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
                # Get keyboard input
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None,
                    lambda: input("\033[36m  🌊 Tee → \033[0m"))
                
                query = user_input.strip()
                if not query:
                    continue
                
                # ── Handle commands (including voice input) ──
                handled = await self._handle_command(query)
                if handled:
                    continue
                
                # ── Process query through Mind ──
                await self._process_query(query)
                
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

    async def _process_query(self, query: str):
        """Process a text query through Mind, display, speak, remember."""
        if not self.mind:
            print("    ❌ No Mind available. Cannot process.")
            return
        
        # Think
        response = await self.mind.think(query)
        
        # Display
        if response:
            print(f"\n    \033[1;33m🌊 A-GENTEE:\033[0m {response}\n")
        
        # Track engine
        engine_used = ""
        category = ""
        if hasattr(self.mind, 'session_queries'):
            for eng, cnt in self.mind.session_queries.items():
                prev = getattr(self, f'_prev_{eng}', 0)
                if cnt > prev:
                    setattr(self, f'_prev_{eng}', cnt)
                    engine_used = eng
                    break
        
        # Remember
        if self.memory and response:
            try:
                self.memory.store_conversation(
                    query=query,
                    response=response[:500] if response else "",
                    engine=engine_used,
                    category=category,
                    language=self._detect_language(query),
                    session_id=self.session_id or "",
                )
            except Exception as e:
                pass  # Don't crash on memory errors
        
        # Speak
        if self.voice and response:
            try:
                mode_val = self.voice.mode.value if hasattr(self.voice.mode, 'value') else str(self.voice.mode)
                if mode_val != "silent":
                    if len(response) < 500:
                        await self.voice.speak(response)
                    else:
                        first_sentence = response.split('.')[0] + '.'
                        if len(first_sentence) < 200:
                            await self.voice.speak(first_sentence)
            except Exception as voice_err:
                print(f"    🔇 Voice hiccup: {str(voice_err)[:80]}")
        
        self.query_count += 1

    async def _handle_command(self, query: str) -> bool:
        """Handle system commands. Returns True if handled."""
        cmd = query.lower().strip()
        
        # ════════════════════════════════════════════
        # VOICE INPUT — 'v' triggers push-to-talk
        # ════════════════════════════════════════════
        if cmd == "v":
            if self.ear and hasattr(self.ear, 'push_to_talk'):
                ear_ok = getattr(self.ear, 'available', False)
                whisper_ok = getattr(self.ear, 'whisper_available', False)
                
                if ear_ok and whisper_ok:
                    transcript = await self.ear.push_to_talk()
                    if transcript:
                        # Process the spoken text as a query
                        await self._process_query(transcript)
                    else:
                        print("    🔇 Didn't catch that. Try 'v' again.")
                else:
                    print("    ⚠️ Voice input not ready:")
                    if not ear_ok:
                        print("       sounddevice not working — pip install sounddevice numpy")
                    if not whisper_ok:
                        print("       Whisper not ready — check OPENAI_API_KEY in .env")
            else:
                print("    ⚠️ Ear not available for voice input")
            return True
        
        # ════════════════════════════════════════════
        # MIC — toggle always-on ambient listening
        # ════════════════════════════════════════════
        if cmd == "mic":
            if self.ear and hasattr(self.ear, 'start_ambient'):
                if getattr(self.ear, 'is_ambient', False):
                    await self.ear.stop_ambient()
                    print("    👂 Ambient listening: OFF")
                else:
                    await self.ear.start_ambient()
                    print("    👂 Ambient listening: ON — I hear everything now")
            else:
                print("    ⚠️ Ear not available for ambient listening")
            return True
        
        # ════════════════════════════════════════════
        # LISTEN — capture system audio
        # ════════════════════════════════════════════
        if cmd == "listen":
            if self.ear and hasattr(self.ear, 'listen_system'):
                text = await self.ear.listen_system(duration=30.0)
                if text:
                    print(f"\n    📝 Captured: {text[:300]}...")
                    # Analyze through Mind
                    if self.mind:
                        analysis = await self.mind.think(
                            f"I just captured this audio playing on my computer. "
                            f"Summarize key points and insights: '{text[:1000]}'"
                        )
                        if analysis:
                            print(f"\n    \033[1;33m🌊 A-GENTEE:\033[0m {analysis}\n")
            else:
                print("    ⚠️ System audio capture not available")
            return True
        
        # ════════════════════════════════════════════
        # QUIT
        # ════════════════════════════════════════════
        if cmd == "quit" or cmd == "exit":
            await self._shutdown()
            sys.exit(0)
        
        # ════════════════════════════════════════════
        # STATS
        # ════════════════════════════════════════════
        if cmd == "stats":
            await self._show_stats()
            return True
        
        # ════════════════════════════════════════════
        # VOICE toggle
        # ════════════════════════════════════════════
        if cmd == "voice":
            if self.voice:
                mode_val = self.voice.mode.value if hasattr(self.voice.mode, 'value') else str(self.voice.mode)
                if mode_val == "silent":
                    self.voice.set_mode("voice")
                    print("    🗣️ Voice mode: ON")
                    try:
                        await self.voice.speak("Voice activated.")
                    except:
                        pass
                else:
                    self.voice.set_mode("silent")
                    print("    🔇 Voice mode: OFF (silent)")
            else:
                print("    ⚠️ Voice system not available")
            return True
        
        # ════════════════════════════════════════════
        # MEMORY
        # ════════════════════════════════════════════
        if cmd == "memory":
            if self.memory:
                try:
                    status = self.memory.get_status()
                    print("    💾 MEMORY STATUS")
                    print(f"    Hot: {status['hot_memory']['path']}")
                    for table, count in status['hot_memory']['tables'].items():
                        print(f"      {table}: {count} records")
                    print(f"    Cold: {status['cold_memory']['supabase']}")
                    print(f"    Stats: {status['stats']}")
                except Exception as e:
                    print(f"    💾 Memory active ({e})")
            else:
                print("    ⚠️ Memory not available")
            return True
        
        # ════════════════════════════════════════════
        # IDEAS
        # ════════════════════════════════════════════
        if cmd == "ideas":
            if self.memory:
                try:
                    ideas = self.memory.get_ideas(limit=10)
                    if ideas:
                        print("    💡 STORED IDEAS")
                        for i, idea in enumerate(ideas, 1):
                            print(f"    {i}. [{idea['category']}] {idea['idea'][:80]}")
                    else:
                        print("    No ideas stored yet.")
                except Exception as e:
                    print(f"    Ideas error: {e}")
            else:
                print("    ⚠️ Memory not available")
            return True
        
        # ════════════════════════════════════════════
        # HISTORY
        # ════════════════════════════════════════════
        if cmd == "history":
            if self.memory:
                try:
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
                except Exception as e:
                    print(f"    History error: {e}")
            else:
                print("    ⚠️ Memory not available")
            return True
        
        # ════════════════════════════════════════════
        # MODE
        # ════════════════════════════════════════════
        if cmd.startswith("mode "):
            personality = cmd[5:].strip()
            if self.voice:
                self.voice.set_personality(personality)
                print(f"    🎭 Voice personality: {personality}")
            return True
        
        # Not a command — return False so it gets processed by Mind
        return False

    async def _show_stats(self):
        """Display comprehensive system stats."""
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║     🌊 A-GENTEE v5.1 SYSTEM STATS       ║")
        print("  ╚══════════════════════════════════════════╝")
        
        # Mind stats
        if self.mind:
            print("\n  🧠 THE MIND")
            if hasattr(self.mind, 'session_queries') and isinstance(self.mind.session_queries, dict):
                for engine, count in self.mind.session_queries.items():
                    icon = "🟢" if engine == "ollama" else "🧠" if engine == "claude" else "💎" if engine == "gemini" else "🔵"
                    print(f"    {icon} {engine}: {count} queries")
            elif hasattr(self.mind, 'get_stats'):
                stats = self.mind.get_stats()
                if isinstance(stats, dict):
                    for engine, count in stats.items():
                        print(f"    {engine}: {count} queries")
                else:
                    print(f"    {stats}")
        
        # Voice stats
        if self.voice:
            print("\n  🗣️ THE VOICE")
            try:
                vs = self.voice.stats if hasattr(self.voice, 'stats') else {}
                mode_val = self.voice.mode.value if hasattr(self.voice.mode, 'value') else str(self.voice.mode)
                print(f"    Mode: {mode_val}")
                print(f"    Personality: {getattr(self.voice, 'personality', 'default')}")
                print(f"    ElevenLabs calls: {vs.get('elevenlabs_calls', 0)}")
                print(f"    Edge-TTS calls: {vs.get('edge_tts_calls', 0)}")
                print(f"    Chars spoken: {vs.get('chars_spoken', 0)}")
            except Exception as e:
                print(f"    Voice active ({e})")
        
        # Ear stats
        if self.ear:
            print("\n  👂 THE EAR")
            try:
                if hasattr(self.ear, 'get_stats'):
                    es = self.ear.get_stats()
                    print(f"    Available: {'✅' if es.get('available') else '❌'}")
                    print(f"    Whisper: {'✅' if es.get('whisper_ready') else '❌'}")
                    print(f"    Recordings: {es.get('recordings', 0)}")
                    print(f"    Transcriptions: {es.get('transcriptions', 0)}")
                    print(f"    Arabic: {es.get('arabic_segments', 0)} | English: {es.get('english_segments', 0)}")
                    print(f"    Audio processed: {es.get('total_audio_seconds', 0):.1f}s")
                    print(f"    Ambient mode: {'🟢 ON' if es.get('is_ambient') else '⚪ OFF'}")
                    sys_dev = es.get('system_device')
                    print(f"    Stereo Mix: {'✅ device ' + str(sys_dev) if sys_dev is not None else '❌ not found'}")
                else:
                    es = self.ear.stats if hasattr(self.ear, 'stats') else {}
                    print(f"    Recordings: {es.get('recordings', 0)}")
                    print(f"    Transcriptions: {es.get('transcriptions', 0)}")
            except Exception as e:
                print(f"    Ear active ({e})")
        
        # Memory stats
        if self.memory:
            print("\n  💾 THE MEMORY")
            try:
                ms = self.memory.get_status()
                for table, count in ms['hot_memory']['tables'].items():
                    if count > 0:
                        print(f"    {table}: {count}")
                print(f"    Hot writes: {ms['stats']['hot_writes']}")
                print(f"    Hot reads: {ms['stats']['hot_reads']}")
            except Exception as e:
                print(f"    Memory active ({e})")
        
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
        
        # Stop ambient listening if active
        if self.ear and getattr(self.ear, 'is_ambient', False):
            try:
                await self.ear.stop_ambient()
            except:
                pass
        
        # Save session
        if self.memory and self.session_id:
            engines_used = {}
            if self.mind and hasattr(self.mind, 'session_queries'):
                engines_used = dict(self.mind.session_queries)
            elif self.mind and hasattr(self.mind, 'get_stats'):
                result = self.mind.get_stats()
                engines_used = result if isinstance(result, dict) else {}
            
            try:
                self.memory.end_session(
                    self.session_id,
                    queries_count=self.query_count,
                    engines_used=engines_used,
                )
                print("  💾 Session saved to memory.")
            except Exception as e:
                print(f"  ⚠️ Could not save session: {e}")
        
        print("  أنا الموجة... راجع تاني. 🌊")


# ─── Entry Point ──────────────────────────────────
def main():
    agentee = AGentee()
    asyncio.run(agentee.run())


if __name__ == "__main__":
    main()
