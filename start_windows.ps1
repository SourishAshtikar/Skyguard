# ==============================================================================
# SkyGuard AI — Repository Clone & Local Service Startup Script
# ==============================================================================
# Backend:  localhost:8000  (Tunneled via external cloudflared container -> backend.ashnet.qzz.io)
# Frontend: localhost:3000  (Tunneled via external cloudflared container -> aws.ashnet.qzz.io)
# Repo URL: https://github.com/SourishAshtikar/Skyguard.git
# ==============================================================================

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/SourishAshtikar/Skyguard.git"
$RepoDir = "Skyguard"
$BackendPort = 8000
$FrontendPort = 3000
$BackendDomain = "backend.ashnet.qzz.io"
$FrontendDomain = "aws.ashnet.qzz.io"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SkyGuard AI — Launching Backend & Frontend Services" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Clone repository if not running inside the repo
if (-not (Test-Path "pyproject.toml") -and -not (Test-Path "src\skyguard")) {
    if (-not (Test-Path $RepoDir)) {
        Write-Host "[+] Cloning repository from $RepoUrl ..." -ForegroundColor Green
        git clone $RepoUrl $RepoDir
    }
    Write-Host "[+] Navigating into $RepoDir ..." -ForegroundColor Green
    Set-Location $RepoDir
}

$ProjectRoot = Get-Location

# 2. Python Virtual Environment Setup
Write-Host "[+] Setting up Python virtual environment..." -ForegroundColor Green
if (-not (Test-Path "venv")) {
    python -m venv venv
}

& "$ProjectRoot\venv\Scripts\Activate.ps1"

Write-Host "[+] Installing Backend Python dependencies..." -ForegroundColor Green
pip install --upgrade pip setuptools wheel --quiet
pip install -e . --quiet

# 3. Frontend Setup
Write-Host "[+] Setting up Frontend Node dependencies..." -ForegroundColor Green
Set-Location "$ProjectRoot\frontend"
if (-not (Test-Path "node_modules")) {
    npm install
}

# 4. Start Backend Server (localhost:8000)
Write-Host "[+] Starting Backend on http://localhost:$BackendPort ..." -ForegroundColor Green
Set-Location $ProjectRoot
$env:PYTHONPATH = "src"
$BackendProcess = Start-Process -FilePath "$ProjectRoot\venv\Scripts\uvicorn.exe" -ArgumentList "skyguard.api.server:app --host 0.0.0.0 --port $BackendPort" -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# 5. Start Frontend Server (localhost:3000)
Write-Host "[+] Starting Frontend on http://localhost:$FrontendPort ..." -ForegroundColor Green
Set-Location "$ProjectRoot\frontend"
$env:VITE_API_BASE = "https://$BackendDomain"
$FrontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev -- --port $FrontendPort --host" -PassThru -NoNewWindow

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SkyGuard AI System Active & Running!" -ForegroundColor Green
Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host " Local Backend API:       http://localhost:$BackendPort"
Write-Host " Local Frontend Web:      http://localhost:$FrontendPort"
Write-Host " External Tunnel API:     https://$BackendDomain"
Write-Host " External Tunnel Web:     https://$FrontendDomain"
Write-Host "======================================================================" -ForegroundColor Cyan
