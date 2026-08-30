@echo off
echo ===============================================================================
echo   Stopping Sovereign-X Background Services...
echo ===============================================================================

:: 1. Gracefully terminate backend uvicorn processes on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Stopping Backend PID %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Gracefully terminate Vite dev server processes on port 5173
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo Stopping Frontend PID %%a on port 5173...
    taskkill /F /PID %%a >nul 2>&1
)

echo [+] Sovereign-X services cleanly terminated.
