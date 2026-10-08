@echo off
title PROJECT RAKSHAK 2.0 // PUBLIC ONLINE SHARE
echo =========================================================================
echo   PROJECT RAKSHAK 2.0 -- ONLINE PUBLIC LINK GENERATOR
echo   Share your live system with remote mentors, judges, or teammates
echo =========================================================================
echo.
echo Make sure Project Rakshak is running on port 8000 before proceeding!
echo (Run start_production.bat or run_rakshak.bat first if not already running)
echo.
echo Select tunnel method:
echo   [1] Localtunnel (Free, via npx, most popular)
echo   [2] Pinggy (Instant direct URL, uses Windows built-in SSH)
echo.
set /p choice="Enter choice [1 or 2]: "

if "%choice%"=="2" (
    echo.
    echo [*] Starting Pinggy tunnel on port 8000...
    echo [*] Copy the https://... URL shown below and send it to your mentor!
    echo =========================================================================
    ssh -p 443 -R0:localhost:8000 a.pinggy.io
    goto end
)

echo.
echo [*] Fetching your tunnel password (your public IP)...
curl -s https://loca.lt/mytunnelpassword
echo.
echo [*] If Localtunnel asks for a "Tunnel Password" in the browser,
echo     enter the IP address shown above.
echo.
echo [*] Starting Localtunnel on port 8000...
echo [*] Copy the https://... URL below and send it to your mentor!
echo =========================================================================
npx --yes localtunnel --port 8000

:end
pause
