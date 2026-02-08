# mind/router.py — A-GENTEE Mind Router v4.3 (Opus Tier)
# Upgrade: Adds Opus as premium tier for deep reasoning + synthesis tasks
# Compatible with existing claude_adapter.py — just pass model param

"""
ROUTING LOGIC v4.3 — Now with Opus Tier

Query → Analyze → Category → Engine + Model:

  "Hello"                          → simple    → Gemini Flash     ($0.001)
  "What's the GDP of Egypt?"       → data      → Gemini Flash     ($0.001)
  "Design RootRise agents"         → complex   → Claude Sonnet    ($0.015)
  "اكتب لي قصيدة عن الموج"        → arabic    → Claude Sonnet    ($0.015)
  "Write a poem about The Wave"    → creative  → Claude Sonnet    ($0.015)
  "Long detailed analysis..."      → long      → Claude Sonnet    ($0.015)
  
  === NEW: Opus Tier (auto-detected OR manual override) ===
  "Synthesize my factory + book + RootRise insights"  → synthesis  → Claude Opus ($0.075)
  "Deep analysis across all my domains"               → deep       → Claude Opus ($0.075)
  model_override="claude-opus" from frontend           → any        → Claude Opus ($0.075)
  
  [If primary fails]               → fallback  → OpenAI          ($0.020)

COST IMPACT:
  Without Opus: ~$30-35/mo
  With Opus (10 queries/day): ~$55-60/mo
  With Opus (3-5 queries/day): ~$40-45/mo — RECOMMENDED
"""

import re

# Patterns that suggest the query needs Opus-level reasoning
OPUS_PATTERNS = [
    # Cross-domain synthesis
    r'(?:synthesize|combine|connect|integrate).+(?:domain|area|project|work)',
    r'(?:across|between).+(?:factory|book|rootrise|writing|dba|plant)',
    # Deep multi-step reasoning
    r'(?:deep|thorough|comprehensive)\s+(?:analysis|review|assessment|evaluation)',
    r'(?:strategy|strategic)\s+(?:plan|analysis|recommendation|direction)',
    # Philosophy + technical fusion (Tee's sweet spot)
    r'(?:philosophy|philosophical).+(?:technical|code|system|architecture)',
    r'(?:uncertainty|consciousness|&i).+(?:implement|design|build)',
    # Investment / high-stakes decisions
    r'(?:investor|pitch|presentation|board).+(?:prepare|create|draft|review)',
    r'(?:ebrd|grant|funding|venture).+(?:application|proposal|strategy)',
    # Book writing - the serious creative work
    r'(?:chapter|book|manuscript).+(?:write|draft|structure|outline)',
    r'(?:مش\s*كتاب|مش\s*خلصانة|كتاب)',
]

SIMPLE_PATTERNS = [
    r'^(hi|hello|hey|مرحبا|ازيك|صباح|مساء|سلام)[\s!?.]*$',
    r'^(thanks|thank you|شكرا|تمام|ok|okay|good|great)[\s!?.]*$',
    r'^(yes|no|yeah|nah|أيوا|لا)[\s!?.]*$',
    r'^(how are you|what\'?s up|كيفك|عامل ايه)[\s!?.]*$',
    r'^what (is|are|was|were) ',
    r'^(who|when|where) (is|are|was|were) ',
    r'^(define|meaning of) ',
]

CREATIVE_PATTERNS = [
    r'(write|compose|create|draft|brainstorm)',
    r'(poem|story|song|lyrics|letter|essay)',
    r'(imagine|creative|artistic|poetic)',
    r'(اكتب|ألف|قصيدة|أغنية|شعر|خاطرة)',
]

DATA_PATTERNS = [
    r'(data|statistics|numbers|figure|chart|graph)',
    r'(gdp|population|market|revenue|growth|rate)',
    r'(compare|comparison|versus|vs\.?)',
    r'(list|rank|top \d+)',
    r'(how much|how many|percentage|ratio)',
]

ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF]')


def detect_category(query: str, model_override: str = None) -> dict:
    """
    Analyze query and return routing decision.
    
    Returns:
        {
            "category": str,       # simple|data|complex|creative|arabic|long|synthesis|deep
            "engine": str,         # gemini|claude|claude-opus|openai
            "model": str,          # specific model string
            "reason": str,         # why this routing was chosen
            "cost_tier": str,      # low|medium|premium
        }
    """
    q = query.strip().lower()
    q_len = len(query.strip())
    
    # ─── MANUAL OPUS OVERRIDE (from frontend toggle) ───
    if model_override == "claude-opus":
        return {
            "category": "manual-opus",
            "engine": "claude-opus",
            "model": "claude-opus-4-5-20250414",
            "reason": "Manual Opus mode activated by Tee",
            "cost_tier": "premium",
        }
    
    # ─── AUTO-DETECT OPUS TIER ───
    for pattern in OPUS_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE):
            return {
                "category": "synthesis",
                "engine": "claude-opus",
                "model": "claude-opus-4-5-20250414",
                "reason": f"Auto-escalated to Opus: matched synthesis pattern",
                "cost_tier": "premium",
            }
    
    # ─── SIMPLE QUERIES → GEMINI (cheap) ───
    for pattern in SIMPLE_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE):
            return {
                "category": "simple",
                "engine": "gemini",
                "model": "gemini-2.0-flash",
                "reason": "Simple/greeting pattern detected",
                "cost_tier": "low",
            }
    
    # ─── ARABIC → CLAUDE SONNET ───
    arabic_chars = len(ARABIC_PATTERN.findall(query))
    if arabic_chars >= 10:
        return {
            "category": "arabic",
            "engine": "claude",
            "model": "claude-sonnet-4-5-20250514",
            "reason": f"Arabic content detected ({arabic_chars} chars)",
            "cost_tier": "medium",
        }
    
    # ─── CREATIVE → CLAUDE SONNET ───
    for pattern in CREATIVE_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE):
            return {
                "category": "creative",
                "engine": "claude",
                "model": "claude-sonnet-4-5-20250514",
                "reason": "Creative task detected",
                "cost_tier": "medium",
            }
    
    # ─── DATA → GEMINI ───
    for pattern in DATA_PATTERNS:
        if re.search(pattern, q, re.IGNORECASE):
            return {
                "category": "data",
                "engine": "gemini",
                "model": "gemini-2.0-flash",
                "reason": "Data/research query detected",
                "cost_tier": "low",
            }
    
    # ─── LONG QUERIES → CLAUDE SONNET ───
    if q_len > 200:
        return {
            "category": "long",
            "engine": "claude",
            "model": "claude-sonnet-4-5-20250514",
            "reason": f"Long query ({q_len} chars) needs deep processing",
            "cost_tier": "medium",
        }
    
    # ─── COMPLEX (default for non-simple) → CLAUDE SONNET ───
    if q_len > 50:
        return {
            "category": "complex",
            "engine": "claude",
            "model": "claude-sonnet-4-5-20250514",
            "reason": "Complex query, routing to Claude",
            "cost_tier": "medium",
        }
    
    # ─── DEFAULT → GEMINI ───
    return {
        "category": "general",
        "engine": "gemini",
        "model": "gemini-2.0-flash",
        "reason": "Default routing to Gemini",
        "cost_tier": "low",
    }


# ─── USAGE EXAMPLE ───
# In mind/__init__.py, update the think() method:
#
# async def think(self, query: str, model_override: str = None) -> dict:
#     routing = detect_category(query, model_override)
#     
#     if routing["engine"] == "claude-opus":
#         # Use Claude adapter with Opus model
#         response = await self.claude.generate(
#             query, 
#             model=routing["model"]  # claude-opus-4-5-20250414
#         )
#     elif routing["engine"] == "claude":
#         response = await self.claude.generate(
#             query,
#             model=routing["model"]  # claude-sonnet-4-5-20250514
#         )
#     elif routing["engine"] == "gemini":
#         response = await self.gemini.generate(query)
#     else:
#         response = await self.openai.generate(query)
#     
#     return {
#         "response": response,
#         "engine": routing["engine"],
#         "category": routing["category"],
#         "cost_tier": routing["cost_tier"],
#     }
#
# In api/think.py, pass model_override from request body:
#
# @router.post("/think")
# async def think(request: ThinkRequest):
#     result = await mind.think(
#         query=request.query,
#         model_override=request.model_override  # None or "claude-opus"
#     )
#     return result
