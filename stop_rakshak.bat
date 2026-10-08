@echo off
title PROJECT RAKSHAK 2.0 // SHUTDOWN
echo =========================================================================
echo   SHUTTING DOWN PROJECT RAKSHAK 2.0 SERVERS & TUNNELS
echo =========================================================================
echo.
echo [*] Terminating Python backend servers...
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *Rakshak*" >nul 2>&1

echo [*] Terminating Vite frontend servers...
taskkill /F /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq *Rakshak*" >nul 2>&1

:: Free up ports 8000 and 5173 explicitly
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

echo [*] Ports 8000 and 5173 released.
echo [*] System successfully stopped.
echo =========================================================================
echo.
pause
