# 🌊 A-GENTEE v5.1 — DROP-IN INSTALLER
# Replaces core.py and ear/__init__.py with voice input support
#
# Run from ANY directory — paths are hardcoded

$project = "C:\Users\Power of Tee\IONGANICA-AGENTEE\IONGANICA-AGENTEE"
$agentee = "$project\agentee"

Write-Host ""
Write-Host "  🌊 A-GENTEE v5.1 Drop-In Installer" -ForegroundColor Cyan
Write-Host "  ────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host ""

# Check project exists
if (-not (Test-Path $agentee)) {
    Write-Host "  ❌ Project not found at: $agentee" -ForegroundColor Red
    exit 1
}

# Step 1: Clear __pycache__
Write-Host "  🧹 Clearing __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path $project -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "     ✅ Cache cleared" -ForegroundColor Green

# Step 2: Backup existing files
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "  💾 Backing up existing files..." -ForegroundColor Yellow

if (Test-Path "$agentee\core.py") {
    Copy-Item "$agentee\core.py" "$agentee\core.py.backup_$timestamp"
    Write-Host "     ✅ core.py backed up" -ForegroundColor Green
}
if (Test-Path "$agentee\ear\__init__.py") {
    Copy-Item "$agentee\ear\__init__.py" "$agentee\ear\__init__.py.backup_$timestamp"
    Write-Host "     ✅ ear/__init__.py backed up" -ForegroundColor Green
}

# Step 3: Copy new files
Write-Host "  📦 Installing new files..." -ForegroundColor Yellow

# Get the directory where this script lives (where the zip was extracted)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Copy core.py
if (Test-Path "$scriptDir\core.py") {
    Copy-Item "$scriptDir\core.py" "$agentee\core.py" -Force
    Write-Host "     ✅ core.py v5.1 installed" -ForegroundColor Green
} else {
    Write-Host "     ❌ core.py not found in zip folder" -ForegroundColor Red
}

# Copy ear/__init__.py
if (Test-Path "$scriptDir\ear__init__.py") {
    Copy-Item "$scriptDir\ear__init__.py" "$agentee\ear\__init__.py" -Force
    Write-Host "     ✅ ear/__init__.py (Ultimate Ear v2.0) installed" -ForegroundColor Green
} else {
    Write-Host "     ❌ ear__init__.py not found in zip folder" -ForegroundColor Red
}

# Step 4: Verify
Write-Host ""
Write-Host "  🔍 Verifying..." -ForegroundColor Yellow

$coreContent = Get-Content "$agentee\core.py" -Raw
if ($coreContent -match "v5\.1") {
    Write-Host "     ✅ core.py is v5.1" -ForegroundColor Green
} else {
    Write-Host "     ⚠️ core.py version not confirmed" -ForegroundColor Yellow
}

$earContent = Get-Content "$agentee\ear\__init__.py" -Raw
if ($earContent -match "sounddevice") {
    Write-Host "     ✅ ear/__init__.py uses sounddevice (Ultimate Ear)" -ForegroundColor Green
} else {
    Write-Host "     ⚠️ ear/__init__.py might be old version" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  ─────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  🎉 Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  To launch:" -ForegroundColor White
Write-Host "     cd '$project'" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "     python -m agentee.core" -ForegroundColor Gray
Write-Host ""
Write-Host "  Then type 'v' and SPEAK! 🎤" -ForegroundColor Cyan
Write-Host "  ─────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host ""
