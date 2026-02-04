# 🧠 A-GENTEE Mind v4.0 — Full 4-Engine Ensemble

## What's New
- **Gemini adapter** — Data analysis, research, summarization (~$0.001/query)
- **OpenAI GPT adapter** — Creative fallback (~$0.005/query with gpt-4o-mini)
- **Router v4.0** — Full 4-engine routing with intelligent fallback chains
- **Cost tracking** — Session stats for all engines
- **Fallback chains** — If one engine fails, automatically tries the next

## The 4 Engines

| Engine | Role | Cost | Best For |
|--------|------|------|----------|
| **Ollama** | Local LLM | FREE | Simple queries, greetings |
| **Gemini** | Data Engine | ~$0.001 | Research, data analysis, summarization |
| **OpenAI** | Creative Fallback | ~$0.005 | Alternative creative, brainstorming |
| **Claude** | Primary Brain | ~$0.015 | Deep reasoning, Arabic, DEVONEERS context |

## Installation Steps

### Step 1: Stop A-GENTEE
```powershell
# Press Ctrl+C in the running PowerShell window
```

### Step 2: Delete Python Cache
```powershell
cd "C:\Users\Power of Tee\IONGANICA-AGENTEE\IONGANICA-AGENTEE"

# Delete every __pycache__ folder
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Delete every .pyc file  
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### Step 3: Install Gemini SDK
```powershell
.\venv\Scripts\Activate.ps1
pip install google-generativeai
```

### Step 4: Copy Files
Replace ALL files in `agentee\mind\` with the 6 files from this package:
- `__init__.py` (Mind v4.0)
- `router.py` (Router v4.0) 
- `ollama_adapter.py` (Ollama adapter)
- `claude_adapter.py` (Claude adapter)
- `gemini_adapter.py` (NEW — Gemini adapter)
- `openai_adapter.py` (NEW — OpenAI GPT adapter)

### Step 5: Update .env
Add these lines to your `.env` file:
```env
# Gemini (Google AI Studio key)
GEMINI_API_KEY=AIza...your-key-here
GEMINI_MODEL=gemini-2.0-flash

# OpenAI model for LLM (not Whisper)
OPENAI_MODEL=gpt-4o-mini
```

### Step 6: Restart
```powershell
python -m agentee.core
```

### Step 7: Verify
You should see:
```
🧠 Mind v4.0 initialized — Ensemble Brain active
    ├── Ollama:  ✅ Ready (FREE)
    ├── Claude:  ✅ Ready (Premium)
    ├── Gemini:  ✅ Ready (Data Engine)
    ├── OpenAI:  ✅ Ready (Creative Fallback)
    └── Ensemble: 4/4 engines online
```

### Step 8: Test
```
> hello                    → [SIMPLE] → ollama (FREE)
> research MENA markets    → [DATA] → gemini  
> help me design rootrise  → [COMPLEX] → claude
> تخيل كاهوتيا             → [CREATIVE] → claude
> summarize this data      → [DATA] → gemini
```

## Routing Logic (v4.0)

```
Query → Router v4.0
  ├── Creative keywords?  → Claude (Arabic, lyrics, art)
  ├── Complex keywords?   → Claude (design, analyze, DEVONEERS)
  ├── Data keywords?      → Gemini (research, summarize, data)
  ├── Arabic (10+ chars)? → Claude (best for Arabic nuance)
  ├── Long (200+ chars)?  → Claude (deep reasoning)
  ├── Simple pattern?     → Ollama (FREE)
  └── Default             → Ollama (FREE)
  
  Fallback chain if primary fails:
  Claude → Gemini → OpenAI → Ollama
```

## Type `stats` in A-GENTEE to see live cost tracking!
