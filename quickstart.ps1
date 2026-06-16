# Quantum-Resistant Chaffing System - Quickstart
# Runs everything in THIS terminal. One URL: http://localhost:8000
#
# Usage:
#   .\quickstart.ps1           # Start the system (default)
#   .\quickstart.ps1 -train    # Force retrain ANFIS before starting
#   .\quickstart.ps1 -setup    # Only setup (install deps, create DB) — don't start

param(
    [switch]$train,
    [switch]$setup
)

$ProjectRoot = $PSScriptRoot
$VenvPath    = Join-Path $ProjectRoot "venv"
$VenvPython  = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip     = Join-Path $VenvPath "Scripts\pip.exe"

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Quantum-Resistant Chaffing System" -ForegroundColor Cyan
Write-Host "  Single URL: http://localhost:8000" -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Virtual Environment ───────────────────────────────────────────
if (-not (Test-Path $VenvPython)) {
    Write-Host "[1/5] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Could not create venv. Is Python 3.10+ installed?" -ForegroundColor Red
        exit 1
    }
    Write-Host "      Done." -ForegroundColor Green
} else {
    Write-Host "[1/5] Virtual environment: OK" -ForegroundColor Green
}

# ── Step 2: Install dependencies ──────────────────────────────────────────
Write-Host "[2/5] Installing dependencies..." -ForegroundColor Yellow
& $VenvPip install -r (Join-Path $ProjectRoot "requirements.txt") -q --no-warn-script-location
& $VenvPip install "pydantic[email]" -q --no-warn-script-location
Write-Host "      Done." -ForegroundColor Green

# ── Step 3: Create PostgreSQL database ────────────────────────────────────
Write-Host "[3/5] Checking PostgreSQL database..." -ForegroundColor Yellow
$dbCheck = & $VenvPython -c @"
import subprocess, sys
try:
    result = subprocess.run(
        ['psql', '-U', 'postgres', '-tc', 'SELECT 1 FROM pg_database WHERE datname=\'qr_chaffing\''],
        capture_output=True, text=True, timeout=5
    )
    if '1' not in result.stdout:
        create = subprocess.run(
            ['psql', '-U', 'postgres', '-c', 'CREATE DATABASE qr_chaffing;'],
            capture_output=True, text=True, timeout=5
        )
        if create.returncode == 0:
            print('CREATED')
        else:
            print('ERROR: ' + create.stderr.strip())
    else:
        print('EXISTS')
except Exception as e:
    print('SKIP: ' + str(e))
"@
Write-Host "      Database: $dbCheck" -ForegroundColor Green

# ── Step 4: .env file ──────────────────────────────────────────────────────
$EnvFile = Join-Path $ProjectRoot "backend\.env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "[4/5] Creating backend\.env..." -ForegroundColor Yellow
    $EnvExample = Join-Path $ProjectRoot "backend\.env.example"
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
    } else {
        @"
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/qr_chaffing
SECRET_KEY=56b821a66b6d48076cfde7788ba71a6364289f5904735f8602cc1f112e80e4136
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=true
DB_ENCRYPTION_KEY=aEvR_TgHpDKQ94y38ctYzDWCoeiT1YgSt1dHXP_inzY=
"@ | Out-File -FilePath $EnvFile -Encoding utf8
    }
    Write-Host "      .env created." -ForegroundColor Green
} else {
    Write-Host "[4/5] backend\.env: OK" -ForegroundColor Green
}

# ── Step 5: ANFIS Training ─────────────────────────────────────────────────
$SizeModel = Join-Path $ProjectRoot "src\neuro_fuzzy\models\anfis_size.pt"
if ($train -or (-not (Test-Path $SizeModel))) {
    Write-Host "[5/5] Training ANFIS models..." -ForegroundColor Yellow
    Set-Location $ProjectRoot
    & $VenvPython -m src.neuro_fuzzy.train_anfis 2>&1 | Where-Object { $_ -match "(Training|Packet|complete|ERROR)" }
    Write-Host "      ANFIS ready." -ForegroundColor Green
} else {
    Write-Host "[5/5] ANFIS weights: OK (use -train to retrain)" -ForegroundColor Green
}

# ── Exit if only setup ────────────────────────────────────────────────────
if ($setup) {
    Write-Host ""
    Write-Host "Setup complete. Run '.\quickstart.ps1' to start the server." -ForegroundColor Cyan
    exit 0
}

# ── Free port 8000 if already in use ─────────────────────────────────────
$oldProc = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($oldProc) {
    Write-Host "Freeing port 8000 (PID $($oldProc.OwningProcess))..." -ForegroundColor Yellow
    Stop-Process -Id $oldProc.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    Write-Host "      Port 8000 ready." -ForegroundColor Green
}

# ── Start unified server ──────────────────────────────────────────────────
Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  Starting server..." -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Open your browser at: http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "  API Docs:   http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host "  Health:     http://localhost:8000/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

Set-Location $ProjectRoot

# Run uvicorn from PROJECT ROOT so 'src' package is importable
& $VenvPython -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
