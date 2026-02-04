"""
🌊 A-GENTEE: THE WAVE — Mind Router v4.2
Full 4-Engine Ensemble Routing

Routing Priority (checked in this order):
1. CREATIVE → Claude (Arabic, lyrics, philosophy, art, imagination)
2. COMPLEX  → Claude (design, analyze, architecture, DEVONEERS context)
3. DATA     → Gemini (research, summarize, data, compare, statistics)
4. ARABIC   → Claude (10+ Arabic chars — best for Arabic nuance)
5. LONG     → Claude (200+ chars — deep reasoning needed)
6. SIMPLE   → Ollama (short queries, greetings — FREE)
7. DEFAULT  → Ollama (catch-all — FREE)

Fallback chain if primary engine fails:
Claude → Gemini → OpenAI → Ollama
Gemini → Claude → OpenAI → Ollama
OpenAI → Claude → Gemini → Ollama
"""

import re
import logging

logger = logging.getLogger("agentee.mind")

# ─── KEYWORD SETS ───────────────────────────────────────────────

CREATIVE_KEYWORDS = [
    # English creative
    "imagine", "compose", "lyrics", "poem", "story", "write me",
    "creative", "artistic", "kahotia", "philosophy", "philosophical",
    "inspire", "muse", "art", "paint", "draw", "visualize",
    "sing", "song", "melody", "verse", "metaphor",
    # Arabic creative
    "تخيل", "أكتب", "شعر", "أغنية", "كاهوتيا", "فلسفة",
    "إبداع", "فن", "رسم", "ألهم", "خيال", "موجة",
    "كلمات", "لحن", "قصيدة", "حكاية", "رواية",
]

COMPLEX_KEYWORDS = [
    # English complex
    "design", "architect", "analyze", "strategy", "plan",
    "help me build", "help me design", "help me create",
    "rootrise", "devoneers", "pantheon", "crema",
    "transform", "business model", "pitch", "investor",
    "explain in detail", "deep dive", "comprehensive",
    "compare and contrast", "pros and cons",
    "refactor", "debug", "code review", "architecture",
    # Arabic complex
    "صمم", "خطة", "استراتيجية", "تحليل", "ساعدني",
    "روتريز", "ديفونيرز", "بانثيون",
]

DATA_KEYWORDS = [
    # English data/research
    "research", "summarize", "data", "statistics", "numbers",
    "trends", "market", "survey", "report", "findings",
    "compare", "benchmark", "metrics", "KPI", "analysis",
    "funding", "accelerator", "grant", "opportunity",
    "ISO", "standard", "compliance", "regulation",
    # Arabic data
    "بحث", "بيانات", "إحصائيات", "تقرير", "اتجاهات",
    "سوق", "مقارنة", "تمويل", "منح",
]

SIMPLE_PATTERNS = [
    "hello", "hi", "hey", "good morning", "good night",
    "thanks", "thank you", "ok", "okay", "yes", "no",
    "bye", "goodbye", "see you", "quit", "exit",
    "مرحبا", "أهلا", "شكرا", "مع السلامة",
    "صباح الخير", "مساء الخير",
]

# ─── COST ESTIMATES ─────────────────────────────────────────────

COST_PER_QUERY = {
    "ollama": 0.0,
    "claude": 0.015,
    "gemini": 0.001,
    "openai": 0.020,
}

# ─── FALLBACK CHAINS ───────────────────────────────────────────

FALLBACK_CHAINS = {
    "claude": ["gemini", "openai", "ollama"],
    "gemini": ["claude", "openai", "ollama"],
    "openai": ["claude", "gemini", "ollama"],
    "ollama": [],  # Ollama is the last resort
}


def _has_arabic(text: str) -> bool:
    """Check if text contains Arabic characters."""
    return bool(re.search(r'[\u0600-\u06FF]', text))


def _keyword_match(query_lower: str, keywords: list) -> bool:
    """Check if any keyword appears in the query."""
    for kw in keywords:
        if kw.lower() in query_lower:
            return True
    return False


def route(query: str, available: dict) -> tuple:
    """
    Route a query to the optimal engine.

    Args:
        query: User's input text
        available: Dict of {engine_name: bool} availability

    Returns:
        Tuple of (engine_name, category, reason)
    """
    query_lower = query.lower().strip()
    query_len = len(query.strip())

    # ─── 1. CREATIVE CHECK (highest priority) ───────────────
    if _keyword_match(query_lower, CREATIVE_KEYWORDS):
        if available.get("claude", False):
            return ("claude", "CREATIVE", "Creative/artistic content — Claude excels here")
        return _fallback("claude", available, "CREATIVE", "Creative content")

    # ─── 2. COMPLEX CHECK ────────────────────────────────────
    if _keyword_match(query_lower, COMPLEX_KEYWORDS):
        if available.get("claude", False):
            return ("claude", "COMPLEX", "Complex reasoning — escalating to Claude")
        return _fallback("claude", available, "COMPLEX", "Complex reasoning")

    # ─── 3. DATA/RESEARCH CHECK ──────────────────────────────
    if _keyword_match(query_lower, DATA_KEYWORDS):
        if available.get("gemini", False):
            return ("gemini", "DATA", "Data/research task — Gemini is cost-effective")
        return _fallback("gemini", available, "DATA", "Data/research task")

    # ─── 4. ARABIC CONTENT (10+ chars) ──────────────────────
    if _has_arabic(query) and query_len >= 10:
        if available.get("claude", False):
            return ("claude", "ARABIC", "Arabic content — Claude has best Arabic nuance")
        return _fallback("claude", available, "ARABIC", "Arabic content")

    # ─── 5. LONG QUERIES (200+ chars) ───────────────────────
    if query_len >= 200:
        if available.get("claude", False):
            return ("claude", "LONG", "Long query — deep reasoning needed")
        return _fallback("claude", available, "LONG", "Long query")

    # ─── 6. SIMPLE PATTERNS (short queries only) ────────────
    if query_len < 30:
        for pattern in SIMPLE_PATTERNS:
            if pattern in query_lower:
                if available.get("ollama", False):
                    return ("ollama", "SIMPLE", "Simple query — handled locally (FREE)")
                return _fallback("ollama", available, "SIMPLE", "Simple query")

    # ─── 7. DEFAULT → Ollama (FREE) ─────────────────────────
    if available.get("ollama", False):
        return ("ollama", "DEFAULT", "Default routing — Ollama (FREE)")
    return _fallback("ollama", available, "DEFAULT", "Default routing")


def _fallback(preferred: str, available: dict, category: str, reason: str) -> tuple:
    """
    Find an available fallback engine when the preferred one is unavailable.
    """
    chain = FALLBACK_CHAINS.get(preferred, [])
    for fallback in chain:
        if available.get(fallback, False):
            return (fallback, category, f"{reason} — {preferred} unavailable, using {fallback}")

    # Absolute last resort
    for engine_name, is_available in available.items():
        if is_available:
            return (engine_name, category, f"{reason} — fallback to {engine_name}")

    return ("ollama", category, f"{reason} — no engines available!")


def get_estimated_cost(engine_name: str) -> float:
    """Get estimated cost per query for an engine."""
    return COST_PER_QUERY.get(engine_name, 0.0)
