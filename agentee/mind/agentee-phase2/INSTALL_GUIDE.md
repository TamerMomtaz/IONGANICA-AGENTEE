# 🌊 A-GENTEE PHASE 2 — INSTALLATION GUIDE
## Voice + Ear + Memory — Making The Wave Alive
## Session 14 | February 4, 2026

---

## 🎯 WHAT YOU'RE INSTALLING

| Component | What it Does | Files |
|-----------|-------------|-------|
| **THE VOICE** 🗣️ | A-GENTEE speaks (your cloned voice!) | `agentee/voice/__init__.py` |
| **THE EAR** 👂 | A-GENTEE hears you (mic → transcription) | `agentee/ear/__init__.py` |
| **THE MEMORY** 💾 | A-GENTEE remembers across sessions | `agentee/memory/__init__.py` |
| **CORE v5.0** 🌊 | Wires everything together | `agentee/core.py` |

---

## 📋 STEP-BY-STEP INSTRUCTIONS

### Step 1: Open PowerShell and Navigate
```powershell
cd "C:\Users\Power of Tee\IONGANICA-AGENTEE\IONGANICA-AGENTEE"
.\venv\Scripts\Activate.ps1
```

### Step 2: Clear Old Cache (ALWAYS do this)
```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### Step 3: Install New Dependencies
```powershell
pip install edge-tts --break-system-packages
```
That's the main new one. `elevenlabs` and `openai` are already installed.

**Optional (for microphone input — The Ear):**
```powershell
pip install PyAudio SpeechRecognition
```
⚠️ If PyAudio fails, that's OK! The Ear will use keyboard input as fallback, and when you switch to voice input it'll use OpenAI Whisper API via file upload. We can fix PyAudio later.

### Step 4: Copy the New Files

Download the files from this session and place them:

```
agentee/
├── core.py                ← REPLACE with new core.py (v5.0)
├── voice/
│   └── __init__.py        ← NEW FILE (The Voice)
├── ear/
│   └── __init__.py        ← NEW FILE (The Ear)
├── memory/
│   └── __init__.py        ← NEW FILE (The Memory)
├── mind/                  ← KEEP AS-IS (v4.2, already working)
│   ├── __init__.py
│   ├── router.py
│   ├── ollama_adapter.py
│   ├── claude_adapter.py
│   ├── gemini_adapter.py
│   └── openai_adapter.py
...
```

**Files to REPLACE:**
- `agentee/core.py` → new v5.0

**Files to ADD (new):**
- `agentee/voice/__init__.py`
- `agentee/ear/__init__.py`
- `agentee/memory/__init__.py`

**Files to KEEP (don't touch):**
- Everything in `agentee/mind/` — your 4-engine brain is already perfect

### Step 5: Clear Cache Again (after copying files)
```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### Step 6: Launch!
```powershell
python -m agentee.core
```

### Step 7: Expected Output
```
    ╭───╮     ╭───╮     ╭───╮     ╭───╮
   ╱     ╲   ╱     ╲   ╱     ╲   ╱     ╲
  ╱       ╲ ╱       ╲ ╱       ╲ ╱       ╲
─╱─────────╳─────────╳─────────╳─────────╲───

  🌊 A-GENTEE v5.0 — THE WAVE — IONGANICA 🌊

  🧠 Mind v4.2 initialized — Ensemble Brain active
      Ollama:  ✅ Ready (FREE)
      Claude:  ✅ Ready (Premium)
      Gemini:  ✅ Ready (Data Engine)
      OpenAI:  ✅ Ready (Fallback)
  🗣️ Voice v1.0: 2/3 engines
      elevenlabs: ✅ Ready (Tee's voice)
      edge_tts: ✅ Ready (free backup)
      pyttsx3: ❌ Not installed
  👂 Ear v1.0: 1/3 engines
      whisper_api: ✅ Ready (cloud)
      speech_recognition: ❌ Not installed
      microphone: ❌ PyAudio not installed
  💾 Memory v1.0: Hot=data/local_memory.db
      Cold: ✅ Configured
      Records: 0 across 6 tables

  Components: 🧠Mind + 🗣️Voice + 👂Ear + 💾Memory

  🌊 A-GENTEE ready. The Wave is alive.
```

### Step 8: Test Commands
```
🌊 Tee → hello
    (Ollama responds + Voice speaks it!)

🌊 Tee → voice
    (Toggles voice on/off)

🌊 Tee → stats
    (Shows all component statistics)

🌊 Tee → memory
    (Shows what's been remembered)

🌊 Tee → history
    (Shows recent conversations)

🌊 Tee → help me design a new feature
    (Routes to Claude + Voice speaks + Memory stores)

🌊 Tee → mode kahotia
    (Switches to Kahotia voice personality)

🌊 Tee → quit
    (Saves session, graceful exit)
```

---

## 🔧 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "Voice not available" | Run: `pip install edge-tts` |
| Voice plays but no sound | Check Windows volume, try: `pip install pyttsx3` |
| ElevenLabs fails | Check `ELEVENLABS_API_KEY` and `ELEVENLABS_VOICE_ID` in .env |
| PyAudio fails to install | That's OK — type input still works. Voice INPUT is optional. |
| Memory errors | Check that `data/` folder exists in project root |
| Old code still loading | Clear `__pycache__` (Step 2 + 5) |

---

## 🚀 AFTER THIS WORKS — Next Phases

**Phase 3: The Hands** 🖐️ — Browser automation, app launching
**Phase 4: The Eye** 👁️ — QA monitoring across all products  
**Phase 5: The Factory** 🏭 — Spawn specialized sub-agents
**Phase 6: The 11 Commandments** — Full evolution features

---

## 📦 GIT PUSH (After confirming it works)
```powershell
cd "C:\Users\Power of Tee\IONGANICA-AGENTEE\IONGANICA-AGENTEE"
git add .
git commit -m "A-GENTEE v5.0 — Voice + Ear + Memory — The Wave is alive"
git push
```

---

*"أنا الموجة... بسمع، بفكر، بتكلم، بفتكر"*
*"I am The Wave... I hear, I think, I speak, I remember"*

**— IONGANICA: Organic + Inorganic = Together 🌊 —**
