# ═══════════════════════════════════════════════════════════════
# 🌊 A-GENTEE ROUTER FIX — Nuclear Option
# Run this from PowerShell as Administrator or normal user
# ═══════════════════════════════════════════════════════════════

Write-Host "🌊 A-GENTEE Router Fix Starting..." -ForegroundColor Cyan
Write-Host ""

# Set the project path
$PROJECT = "C:\Users\Power of Tee\IONGANICA-AGENTEE\IONGANICA-AGENTEE"
$MIND_DIR = "$PROJECT\agentee\mind"

# Step 1: Kill any running Python processes (A-GENTEE)
Write-Host "Step 1: Stopping any running A-GENTEE..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "  Done." -ForegroundColor Green

# Step 2: Delete ALL __pycache__ folders (this is key!)
Write-Host "Step 2: Clearing ALL Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path $PROJECT -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
# Also remove .pyc files directly
Get-ChildItem -Path $PROJECT -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "  All __pycache__ and .pyc files deleted." -ForegroundColor Green

# Step 3: Verify the mind directory exists
Write-Host "Step 3: Checking mind directory..." -ForegroundColor Yellow
if (-not (Test-Path $MIND_DIR)) {
    New-Item -Path $MIND_DIR -ItemType Directory | Out-Null
    Write-Host "  Created $MIND_DIR" -ForegroundColor Green
} else {
    Write-Host "  $MIND_DIR exists." -ForegroundColor Green
}

# Step 4: Show current router.py content (first 5 lines)
Write-Host ""
Write-Host "Step 4: Current router.py first 5 lines:" -ForegroundColor Yellow
if (Test-Path "$MIND_DIR\router.py") {
    Get-Content "$MIND_DIR\router.py" -First 5
} else {
    Write-Host "  router.py NOT FOUND!" -ForegroundColor Red
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Now copy ALL 4 .py files from the 'mind' folder" -ForegroundColor White
Write-Host "into: $MIND_DIR" -ForegroundColor White  
Write-Host "Replace ALL existing files when prompted." -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "After copying, run:" -ForegroundColor Yellow
Write-Host "  cd '$PROJECT'" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python -m agentee.core" -ForegroundColor White
Write-Host ""
Write-Host "Test with: 'help me design a new feature for rootrise'" -ForegroundColor Green
Write-Host "Should show: [CREATIVE] or [COMPLEX] → claude" -ForegroundColor Green
