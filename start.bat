@echo off
REM Local AI Assistant - Windows Startup Script
REM This script starts both the FastAPI backend and Vite frontend

echo.
echo ========================================
echo   Local AI Assistant - Starting...
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

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
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

REM Setup frontend if needed
if not exist "client\node_modules" (
    echo.
    echo Installing frontend dependencies...
    cd client
    call npm install
    cd ..
)

REM Start backend
echo.
echo Starting FastAPI backend on http://localhost:8000...
start cmd /k "cd server & venv\Scripts\activate.bat & python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start frontend
echo.
echo Starting Vite frontend on http://localhost:5173...
start cmd /k "cd client & npm run dev"

echo.
echo ========================================
echo   Startup complete!
echo ========================================
echo.
echo Frontend:  http://localhost:5173
echo Backend:   http://localhost:8000
echo Ollama:    http://localhost:11434
echo.
echo Open your browser and navigate to: http://localhost:5173
echo.
echo Press CTRL+C in either terminal to stop the server
echo.
pause
