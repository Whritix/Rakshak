@echo off
title PROJECT RAKSHAK 2.0 // SOVEREIGN AIR-GAPPED DEPLOYMENT
echo =========================================================================
echo   PROJECT RAKSHAK 2.0 -- SOVEREIGN DEFENSE MULTIMODAL C4ISR
echo =========================================================================
echo.
echo   [*] Deploying unified local production stack...
echo   [*] Air-gapped: Zero cloud connection required
echo   [*] Database: Local SQLite WAL (backend\rakshak.db)
echo   [*] Models: YOLO11-Tactical FP16 (Vessel + Multiclass)
echo   [*] Web Console: http://127.0.0.1:8000
echo.
echo Press Ctrl+C anytime to terminate.
echo =========================================================================
echo.
echo [*] Opening browser to http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
pause
