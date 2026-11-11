@echo off
REM Local AI Assistant - Online launcher
REM Starts the FastAPI backend and a Tailscale Funnel so the GitHub Pages site can reach it.
REM The frontend is served by GitHub Pages, so no Vite server is started here.

set "TAILSCALE=C:\Program Files\Tailscale\tailscale.exe"
set "PUBLIC_URL=https://adits-laptop2.tailc3da84.ts.net"
set "PAGES_URL=https://aditfadhillah.github.io/Local-AI-Model-Chibot-/"

echo.
echo ========================================
echo   Local AI Assistant - Going online...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if Tailscale is installed
if not exist "%TAILSCALE%" (
    echo ERROR: Tailscale not found at %TAILSCALE%
    echo Please install Tailscale from https://tailscale.com/download
    pause
    exit /b 1
)

REM Check if Ollama is running
echo Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama doesn't appear to be running
    echo Please start Ollama before using the chat interface
    echo.
)

REM Setup backend if needed
if not exist "server\venv" (
    echo.
    echo Setting up Python virtual environment...
    cd server
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

REM Start backend (no --reload, so the public server stays stable)
echo.
echo Starting FastAPI backend on http://127.0.0.1:8000...
start "Chibot API" cmd /k "cd server & venv\Scripts\activate.bat & python -m uvicorn app:app --host 127.0.0.1 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Expose the backend through Tailscale Funnel
echo.
echo Starting Tailscale Funnel on port 8000...
start "Chibot Funnel" cmd /k ""%TAILSCALE%" funnel 8000"

echo.
echo ========================================
echo   Online!
echo ========================================
echo.
echo Site:      %PAGES_URL%
echo Backend:   %PUBLIC_URL%
echo Ollama:    http://localhost:11434
echo.
echo Close the "Chibot API" and "Chibot Funnel" windows to go offline.
echo Run "tailscale funnel reset" to remove the public URL immediately.
echo.
pause
