# ==============================================================================
# SkyGuard AI — Repository Clone & Local Service Startup Script (CPU-Only)
# ==============================================================================
# Backend:  localhost:8000
# Frontend: localhost:3000
# Repo URL: https://github.com/SourishAshtikar/Skyguard.git
# ==============================================================================

$ErrorActionPreference = "Stop"

$RepoUrl = if ($env:REPO_URL) { $env:REPO_URL } else { "https://github.com/SourishAshtikar/Skyguard.git" }
$RepoDir = if ($env:REPO_DIR) { $env:REPO_DIR } else { "Skyguard" }
$BackendPort = if ($env:BACKEND_PORT) { $env:BACKEND_PORT } else { 8000 }
$FrontendPort = if ($env:FRONTEND_PORT) { $env:FRONTEND_PORT } else { 3000 }

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SkyGuard AI — Launching Backend & Frontend Services (CPU Mode)" -ForegroundColor Cyan
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

# 2. Python Virtual Environment Setup (CPU Only)
Write-Host "[+] Setting up Python virtual environment..." -ForegroundColor Green
if (-not (Test-Path "venv")) {
    python -m venv venv
}

& "$ProjectRoot\venv\Scripts\Activate.ps1"

Write-Host "[+] Installing Backend Python dependencies (CPU-only, no NVIDIA packages)..." -ForegroundColor Green
pip install --upgrade pip setuptools wheel --quiet
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu --quiet
pip install -r requirements.txt --quiet
pip install -e . --no-deps --quiet

Write-Host "[+] Purging redundant NVIDIA/CUDA packages if present..." -ForegroundColor Green
Get-PipPackage | Where-Name "nvidia-*" | Uninstall-PipPackage -Yes -ErrorAction SilentlyContinue

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
$FrontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev -- --port $FrontendPort --host" -PassThru -NoNewWindow

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SkyGuard AI System Active & Running (CPU Mode)!" -ForegroundColor Green
Write-Host "----------------------------------------------------------------------" -ForegroundColor Cyan
Write-Host " Local Backend API:       http://localhost:$BackendPort"
Write-Host " Local Frontend Web:      http://localhost:$FrontendPort"
Write-Host "======================================================================" -ForegroundColor Cyan
