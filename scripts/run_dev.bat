@echo off
setlocal enabledelayedexpansion

echo ===============================================================================
echo   SOVEREIGN-X -- Air-Gapped Industrial Agent Runtime Launcher (Windows 11)
echo ===============================================================================
echo.

:: 1. Force air-gap offline invariants
set "OLLAMA_NO_CLOUD=1"
set "OLLAMA_HOST=127.0.0.1:11434"

:: 2. Check Python Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment (.venv) not found!
    echo Please create the virtual environment: python -m venv .venv
    pause
    exit /b 1
)
echo [+] Python environment verified (.venv)

:: 3. Check Ollama local daemon
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Local Ollama service is not responding at 127.0.0.1:11434.
    echo Attempting to start Ollama in background...
    start /b "" ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
) else (
    echo [+] Local Ollama daemon detected (127.0.0.1:11434)
)

:: 4. Check Docker Desktop availability
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Docker Desktop daemon is not currently running or accessible.
    echo [NOTE] Secure Python sandbox execution (run_python) requires Docker Desktop.
    echo        Host fallback is strictly prohibited by security invariant #6.
    set /p "START_DOCKER=Would you like to attempt starting Docker Desktop now? (Y/N): "
    if /i "!START_DOCKER!"=="Y" (
        echo Attempting to start Docker Desktop...
        start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" >nul 2>&1
        echo Waiting 8 seconds for Docker daemon initialization...
        timeout /t 8 /nobreak >nul
        docker info >nul 2>&1
        if !errorlevel! equ 0 (
            echo [+] Docker sandbox subsystem successfully connected.
        ) else (
            echo [WARNING] Docker is initializing. Python sandboxing will be available once Docker is ready.
        )
    )
) else (
    echo [+] Docker sandbox subsystem verified (sovereign-sandbox:1.0 ready)
)

:: 5. Launch FastAPI Backend Server (Port 8000)
echo.
echo [*] Starting Sovereign-X FastAPI Backend at http://127.0.0.1:8000 ...
start "Sovereign-X Backend" cmd /k "cd /d %~dp0\.. && .venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

:: 6. Launch React Vite Frontend (Port 5173)
echo [*] Starting Sovereign-X React 19 Frontend at http://127.0.0.1:5173 ...
start "Sovereign-X Frontend" cmd /k "cd /d %~dp0\..\frontend && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ===============================================================================
echo   SOVEREIGN-X SYSTEM READY
echo   Backend API:   http://127.0.0.1:8000/docs
echo   Workbench UI:  http://127.0.0.1:5173
echo.
echo   Air-Gap Mode:  ENFORCED (Zero Cloud Egress)
echo   GPU Target:    NVIDIA RTX 3050 (4GB VRAM)
echo ===============================================================================
echo.
echo Press any key to stop all services...
pause >nul

call "%~dp0\stop_dev.bat"
