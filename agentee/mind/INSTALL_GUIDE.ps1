# ═══════════════════════════════════════════════════════════════
# 🌊 A-GENTEE MIND v4.2 — INSTALL GUIDE
# Fixes: Gemini (migrated to new SDK), OpenAI (verified working)
# ═══════════════════════════════════════════════════════════════

# ── STEP 1: Stop A-GENTEE ──────────────────────────────────────
# Press Ctrl+C in the terminal where A-GENTEE is running

# ── STEP 2: Navigate to project ────────────────────────────────
cd "C:\Users\Power of Tee\IONGANICA-AGENTEE\IONGANICA-AGENTEE"

# ── STEP 3: Activate venv ──────────────────────────────────────
.\venv\Scripts\Activate.ps1

# ── STEP 4: Uninstall old deprecated Gemini SDK ────────────────
pip uninstall google-generativeai -y

# ── STEP 5: Install NEW Gemini SDK ─────────────────────────────
pip install google-genai

# ── STEP 6: Delete ALL Python cache ────────────────────────────
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

# ── STEP 7: Copy the 6 files from the zip into agentee\mind\ ──
# Extract AGENTEE_MIND_v42.zip
# Copy ALL files into: agentee\mind\  (replace existing)
# Files: __init__.py, router.py, ollama_adapter.py, 
#        claude_adapter.py, gemini_adapter.py, openai_adapter.py

# ── STEP 8: Check your .env file ──────────────────────────────
# Make sure these lines exist in your .env:
#
#   ANTHROPIC_API_KEY=sk-ant-...
#   OPENAI_API_KEY=sk-...
#   GEMINI_API_KEY=AIza...
#   GEMINI_MODEL=gemini-2.0-flash
#   OPENAI_MODEL=gpt-4o-mini
#   OLLAMA_BASE_URL=http://localhost:11434
#   OLLAMA_MODEL=llama3.2
#
# If GEMINI_API_KEY or OPENAI_API_KEY are missing, those engines
# will show as ⏸️ Offline but everything else still works.

# ── STEP 9: Make sure Ollama is running ────────────────────────
# In a separate terminal: ollama serve
# (or check if it auto-starts as a service)

# ── STEP 10: Launch! ──────────────────────────────────────────
python -m agentee.core

# ── EXPECTED OUTPUT ────────────────────────────────────────────
# 🧠 Mind v4.2 initialized — Ensemble Brain active
#     ├── Ollama:  ✅ Ready (FREE) — model: llama3.2
#     ├── Claude:  ✅ Ready (Premium) — model: claude-sonnet-4-20250514
#     ├── Gemini:  ✅ Ready (Data Engine) — model: gemini-2.0-flash
#     ├── OpenAI:  ✅ Ready (Creative Fallback) — model: gpt-4o-mini
#     └── Ensemble: 4/4 engines online
# 🌊 A-GENTEE ready. The Wave is listening.

# ── TEST COMMANDS ──────────────────────────────────────────────
# hello                           → [SIMPLE]   → 🟢 OLLAMA (FREE)
# research MENA startup funding   → [DATA]     → 💎 GEMINI (~$0.001)
# help me design rootrise feature → [COMPLEX]  → 🧠 CLAUDE (~$0.015)
# تخيل كاهوتيا في المستقبل       → [CREATIVE] → 🧠 CLAUDE (~$0.015)
# stats                           → Shows all engine stats
