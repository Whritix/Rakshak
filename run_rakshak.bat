@echo off
title PROJECT RAKSHAK 2.0 // LAUNCHER
echo =========================================================================
echo   PROJECT RAKSHAK 2.0 -- SOVEREIGN DEFENSE C4ISR PLATFORM
echo =========================================================================
echo.
echo [*] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Rakshak Backend (FastAPI)" cmd /k ".\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [*] Starting Vite Frontend on http://localhost:5173 ...
start "Rakshak Frontend (Vite)" cmd /k "npm --prefix frontend run dev"

echo.
echo [*] Waiting for services to initialize...
timeout /t 3 /nobreak >nul

echo [*] Opening Tactical Console in browser...
start http://localhost:5173

echo.
echo =========================================================================
echo   SYSTEM ONLINE:
echo   - Frontend: http://localhost:5173
echo   - Backend API: http://127.0.0.1:8000
echo   - Swagger Docs: http://127.0.0.1:8000/docs
echo =========================================================================
echo.
pause
