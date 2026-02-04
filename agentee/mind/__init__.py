"""
🌊 A-GENTEE: THE WAVE — Mind v4.2
Full 4-Engine Ensemble Brain

Engines:
  1. Ollama    — Simple queries, local (FREE)
  2. Claude    — Deep reasoning, creative, Arabic (Premium)
  3. Gemini    — Data analysis, research, summarization (Cheap) [NEW SDK: google-genai]
  4. OpenAI    — Creative fallback (Medium)

Changes in v4.2:
  - Gemini migrated from deprecated google-generativeai → google-genai
  - Fixes FutureWarning about deprecated package
  - Proper fallback chains when engines fail
  - Visible routing tags on every response
  - Session stats tracking with `stats` command
"""

import logging
from .router import route, get_estimated_cost
from .ollama_adapter import OllamaAdapter
from .claude_adapter import ClaudeAdapter
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger("agentee.mind")

# Engine display labels for visible response prefix
ENGINE_TAGS = {
    "ollama":  "🟢 [OLLAMA — FREE]",
    "claude":  "🧠 [CLAUDE — Premium]",
    "gemini":  "💎 [GEMINI — Data]",
    "openai":  "🌀 [OPENAI — Creative]",
}


class Mind:
    """
    The Ensemble Brain of A-GENTEE.
    Routes queries to the optimal model based on task type and cost.

    v4.2 — Migrated Gemini to new google-genai SDK, fixed all 4 engines.
    """

    VERSION = "4.2"

    def __init__(self):
        logger.info(f"🧠 Mind v{self.VERSION} initialized — Ensemble Brain active")

        # Initialize all 4 engines
        self.ollama = OllamaAdapter()
        self.claude = ClaudeAdapter()
        self.gemini = GeminiAdapter()
        self.openai = OpenAIAdapter()

        # Track which engines are available
        self.engines = {
            "ollama": self.ollama,
            "claude": self.claude,
            "gemini": self.gemini,
            "openai": self.openai,
        }

        self.available = {
            name: adapter.ready for name, adapter in self.engines.items()
        }

        # Cost tracking
        self.session_costs = {name: 0.0 for name in self.engines}
        self.session_queries = {name: 0 for name in self.engines}

        # Summary
        ready_count = sum(1 for v in self.available.values() if v)
        total_count = len(self.engines)
        logger.info(f"    └── Ensemble: {ready_count}/{total_count} engines online")

    def _make_tag(self, engine_name: str, category: str, cost: float) -> str:
        """Create the visible routing tag that appears before every response."""
        engine_tag = ENGINE_TAGS.get(engine_name, engine_name)
        cost_display = "FREE" if cost == 0 else f"~${cost:.3f}"
        return f"🧩 [{category}] → {engine_tag} ({cost_display})"

    async def think(self, query: str) -> str:
        """
        Process a query through the ensemble brain.
        Routes to optimal engine, with fallback chain.

        Args:
            query: User's input text

        Returns:
            Generated response string WITH routing tag prefix
        """
        # Handle stats command
        if query.strip().lower() == "stats":
            return self.get_stats()

        # Route the query
        engine_name, category, reason = route(query, self.available)

        # Calculate cost
        cost = get_estimated_cost(engine_name)
        cost_display = "FREE" if cost == 0 else f"~${cost:.3f}"

        # Log the routing decision
        logger.info(f"🧩 [{category}] → {engine_name} | {reason} ({cost_display})")

        # Build the visible tag
        visible_tag = self._make_tag(engine_name, category, cost)

        # Get the engine
        engine = self.engines.get(engine_name)

        if engine is None or not engine.ready:
            return f"{visible_tag}\n⚠️ Engine '{engine_name}' not available. Check API keys and Ollama status."

        # Generate response
        try:
            response = await engine.generate(query)

            # Track costs
            self.session_costs[engine_name] += cost
            self.session_queries[engine_name] += 1

            # Check if the response is an error/fallback signal
            if response.startswith("⚠️"):
                # Try fallback chain
                from .router import FALLBACK_CHAINS
                fallbacks = FALLBACK_CHAINS.get(engine_name, [])
                for fb_name in fallbacks:
                    fb_engine = self.engines.get(fb_name)
                    if fb_engine and fb_engine.ready:
                        fb_cost = get_estimated_cost(fb_name)
                        fb_tag = self._make_tag(fb_name, category, fb_cost)
                        logger.info(f"⚡ Fallback: {engine_name} failed → trying {fb_name}")
                        fb_response = await fb_engine.generate(query)
                        if not fb_response.startswith("⚠️"):
                            self.session_costs[fb_name] += fb_cost
                            self.session_queries[fb_name] += 1
                            return f"{fb_tag} (fallback)\n\n{fb_response}"
                # All fallbacks failed
                return f"{visible_tag}\n\n{response}"

            return f"{visible_tag}\n\n{response}"

        except Exception as e:
            logger.error(f"Engine error ({engine_name}): {e}")
            return f"{visible_tag}\n⚠️ Error: {str(e)}"

    def get_stats(self) -> str:
        """Generate session statistics."""
        total_queries = sum(self.session_queries.values())
        total_cost = sum(self.session_costs.values())
        free_queries = self.session_queries.get("ollama", 0)

        stats = f"""
╔══════════════════════════════════════════════════╗
║  🧠 ENSEMBLE BRAIN STATS — Mind v{self.VERSION}            ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  ENGINE        QUERIES    COST       STATUS      ║
║  ──────────    ───────    ────       ──────      ║"""

        for name, adapter in self.engines.items():
            queries = self.session_queries[name]
            cost = self.session_costs[name]
            status = "✅ Online" if self.available[name] else "⏸️ Offline"
            cost_str = "FREE" if cost == 0 and name == "ollama" else f"${cost:.4f}"
            stats += f"\n║  {name:<12}  {queries:<9}  {cost_str:<9}  {status:<10} ║"

        free_pct = (free_queries / total_queries * 100) if total_queries > 0 else 0

        stats += f"""
║                                                  ║
║  ────────────────────────────────────────         ║
║  Total Queries:  {total_queries:<5}                          ║
║  Total Cost:     ${total_cost:.4f}                        ║
║  Free Queries:   {free_pct:.0f}%                            ║
╚══════════════════════════════════════════════════╝"""

        return stats
