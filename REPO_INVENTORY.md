# REPO_INVENTORY.md — IONGANICA-AGENTEE

_Read-only inventory for the SMTs rename/archive decision. No secret values appear below — env-var **names** and file paths only._

## 1. Identity
- **Remote (origin):** `…/TamerMomtaz/IONGANICA-AGENTEE` (HTTP git proxy)
- **Default branch:** `main`
- **Last commit:** `f1d2787` — 2026-02-08 — _aGentTee_ (**oldest of the three app repos**)
- **Total commits:** 9
- **Contributors (`git shortlog -sn`):** 4 TamerMomtaz · 4 unknown · 1 aGentTee
- **Branches:** `main`, `claude/smts-repo-inventory-dna-hs8j9a` (+ matching `origin/*`)

## 2. Stack
- **Python 3.12+ local desktop assistant** ("A-GENTEE Mind v4.0 / v5.1 — The Wave"). No web server, no `package.json`, no HTTP API — runs as a local daemon.
- **4-engine ensemble:** `anthropic`, `openai`, `google-genai`, **`ollama` (local)**. **Voice:** `elevenlabs`, `edge-tts`. **Ear:** `sounddevice` + `numpy`. **Memory:** `httpx` (Supabase REST) + local SQLite.
- **Structure:** `agentee/` (`core.py`, `growth_matrix.py`, `auto_documenter.py`, `factory/`, `mind/` [router + 4 adapters], `ear/`, `eye/`, `hands/`, `memory/`, `voice/`) · `config/settings.yaml` (central config) · `scripts/setup.sh`.
- **Windows-oriented scaffold:** PowerShell installers committed (`agentee/INSTALL.ps1`, `agentee/FIX_ROUTER.ps1`, `agentee/mind/INSTALL_GUIDE.ps1`) + handoff/upgrade `.md` notes.

## 3. Supabase wiring
- **No `supabase/` dir, no `config.toml`, 0 migrations, no seed.** Supabase appears only as "cold memory" via REST. `config/settings.yaml` → `supabase.{url, anon_key, service_key}` are all `${ENV}` placeholders.

## 4. Deploy wiring
- **None.** No Vercel / Railway / Procfile / Docker. Intended to run as a **local Windows daemon** (`settings.yaml` → `daemon.enabled: true`, `auto_start: true`).

## 5. Env hygiene
- **Env-var NAMES referenced in code:** `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `ELEVENLABS_API_KEY`, `ELEVENLABS_MODEL`, `ELEVENLABS_VOICE_ID`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `SUPABASE_URL`, `SUPABASE_KEY`. `settings.yaml` also interpolates `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`.
- **Committed env files:** none (`.env` gitignored). `config/settings.yaml` uses `${ENV_VAR}` interpolation — no inline secrets.
- **Secret scan:** one hit at `agentee/AGENTEE_HANDOFF_v4.md:179` → a **documentation placeholder** (`ANTHROPIC_API_KEY=sk-ant-...` with a literal `...`), **not a real key.** No real hardcoded keys.
- **Messiness markers:** duplicate/typo file `agentee/ear__init__.py` sitting next to `agentee/ear/__init__.py`; committed `.ps1` install scripts; `__pycache__`-oriented install docs.

## 6. Noise verdict
**ARCHIVE.** Oldest (9 commits, Feb 2026), Windows-desktop PowerShell scaffold with duplicate-file cruft, functionally superseded by the cloud FastAPI backend. Archive it and start SMTs fresh — mine `mind/router.py` + `config/settings.yaml` as reference patterns only.
