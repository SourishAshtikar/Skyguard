#!/bin/bash
# ==============================================================================
# SkyGuard AI — Repository Clone & Local Service Startup Script
# ==============================================================================
# Backend:  localhost:8000  (Tunneled via external cloudflared container -> backend.ashnet.qzz.io)
# Frontend: localhost:3000  (Tunneled via external cloudflared container -> aws.ashnet.qzz.io)
# Repo URL: https://github.com/SourishAshtikar/Skyguard.git
# ==============================================================================

set -e

REPO_URL="https://github.com/SourishAshtikar/Skyguard.git"
REPO_DIR="Skyguard"
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_DOMAIN="backend.ashnet.qzz.io"
FRONTEND_DOMAIN="aws.ashnet.qzz.io"

echo "======================================================================"
echo " SkyGuard AI — Launching Backend & Frontend Services"
echo "======================================================================"

# 1. Clone repository if not running inside the repository directory
if [ ! -f "pyproject.toml" ] && [ ! -d "src/skyguard" ]; then
    if [ ! -d "$REPO_DIR" ]; then
        echo "[+] Cloning repository from $REPO_URL ..."
        git clone "$REPO_URL" "$REPO_DIR"
    fi
    echo "[+] Navigating into $REPO_DIR ..."
    cd "$REPO_DIR"
fi

PROJECT_ROOT="$(pwd)"

# 2. Python Virtual Environment & Backend Setup
echo "[+] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv || python -m venv venv
fi

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

echo "[+] Installing Backend Python dependencies..."
pip install --upgrade pip setuptools wheel --quiet
pip install -e . --quiet || pip install -r requirements.txt --quiet

# 3. Frontend Setup
echo "[+] Setting up Frontend Node dependencies..."
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi

# Trap signals for graceful shutdown of background processes
cleanup() {
    echo ""
    echo "[*] Shutting down SkyGuard AI services..."
    kill 0 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 4. Start Backend Server (localhost:8000)
echo "[+] Starting SkyGuard Backend server on http://localhost:$BACKEND_PORT ..."
cd "$PROJECT_ROOT"
PYTHONPATH=src python3 -m uvicorn skyguard.api.server:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 3

# 5. Start Frontend Server (localhost:3000)
echo "[+] Starting SkyGuard Frontend server on http://localhost:$FRONTEND_PORT ..."
cd "$PROJECT_ROOT/frontend"
VITE_API_BASE="https://$BACKEND_DOMAIN" npm run dev -- --port $FRONTEND_PORT --host &
FRONTEND_PID=$!

echo ""
echo "======================================================================"
echo " SkyGuard AI System Active & Running!"
echo "----------------------------------------------------------------------"
echo " Local Backend API:       http://localhost:$BACKEND_PORT"
echo " Local Frontend Web:      http://localhost:$FRONTEND_PORT"
echo " External Tunnel API:     https://$BACKEND_DOMAIN"
echo " External Tunnel Web:     https://$FRONTEND_DOMAIN"
echo "======================================================================"
echo " Press Ctrl+C to terminate services."
echo ""

wait
