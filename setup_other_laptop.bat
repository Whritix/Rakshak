@echo off
title PROJECT RAKSHAK 2.0 // AUTOMATED SETUP & LAUNCHER
echo =========================================================================
echo   PROJECT RAKSHAK 2.0 -- SOVEREIGN DEFENSE C4ISR PLATFORM
echo   AUTOMATED 1-CLICK SETUP FOR NEW LAPTOP / TEAMMATE
echo =========================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH!
    echo Please install Python 3.10, 3.11, or 3.12 from python.org and check "Add Python to PATH".
    pause
    exit /b
)
echo [*] Python detected.

:: 2. Check or Create Virtual Environment
if not exist ".venv" (
    echo [*] Creating fresh Python virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
)

:: 3. Install/Verify Dependencies
echo [*] Checking and installing Python dependencies...
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some dependencies had warnings, continuing to launch...
)

echo.
echo =========================================================================
echo   SETUP COMPLETE!
echo   Launching Air-Gapped Unified Defense Console on http://127.0.0.1:8000 ...
echo =========================================================================
echo.

:: 4. Auto-launch browser
start http://127.0.0.1:8000

:: 5. Start Unified Server
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
pause
