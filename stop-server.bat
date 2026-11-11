@echo off
REM Local AI Assistant - Stop launcher
REM Closes the windows opened by local-start.bat, launch-start.bat and start-server.bat,
REM then removes the public Tailscale Funnel URL.

set "TAILSCALE=C:\Program Files\Tailscale\tailscale.exe"

echo.
echo ========================================
echo   Local AI Assistant - Stopping...
echo ========================================
echo.

REM Close the backend, frontend and Funnel windows (and their child processes)
taskkill /FI "WINDOWTITLE eq Chibot API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Chibot Client*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Chibot Funnel*" /T /F >nul 2>&1

REM Remove the public URL. The Funnel config persists after its window closes.
if exist "%TAILSCALE%" (
    "%TAILSCALE%" funnel reset >nul 2>&1
    echo Tailscale Funnel reset.
) else (
    echo WARNING: Tailscale not found at %TAILSCALE%, Funnel was not reset.
)

echo.
echo Chibot windows closed. The public backend URL is no longer available.
echo.
pause
