@echo off
REM Local AI Assistant - Backend-only launcher (fallback)
REM Starts only the FastAPI backend on localhost. No frontend and no Funnel.
REM Use this if local-start.bat or launch-start.bat fail.

echo.
echo ========================================
echo   Local AI Assistant - Backend only...
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

REM Check if Ollama is running
echo Checking if Ollama is running...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama doesn't appear to be running
    echo Please start Ollama before using the API
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

REM Start backend
echo.
echo Starting FastAPI backend on http://127.0.0.1:8000...
start "Chibot API" cmd /k "cd server & venv\Scripts\activate.bat & python -m uvicorn app:app --host 127.0.0.1 --port 8000"

echo.
echo Backend:   http://127.0.0.1:8000
echo Health:    http://127.0.0.1:8000/health
echo.
echo Close the "Chibot API" window to stop the server.
echo.
pause
