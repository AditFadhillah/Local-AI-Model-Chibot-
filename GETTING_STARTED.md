# Getting Started - Local AI Assistant

## 5-Minute Quick Start

### Prerequisites
- Ollama installed and running
- Python 3.10+ installed
- Node.js 16+ installed

### Steps

#### 1. Pull a Model (first time only)
```bash
ollama pull qwen3:8b
```

#### 2. Open Project Folder
```bash
cd c:\Users\<YourUsername>\PROJECTS\Local-AI-Model-Chibot
```

#### 3. Run the Startup Script
Local development (backend and Vite frontend):
```bash
local-start.bat
```

Online (backend and Tailscale Funnel, for the GitHub Pages site):
```bash
launch-start.bat
```

Backend only (fallback, no frontend or Funnel):
```bash
start-server.bat
```

To stop everything (closes the Chibot windows and removes the public URL):
```bash
stop-server.bat
```

Or manually in two terminals:

**Terminal 1 (Backend):**
```bash
cd server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd client
npm install
npm run dev
```

#### 4. Open Browser
Go to: `http://localhost:5173`

#### 5. Chat!
- Select model from dropdown
- Type a message
- Press Enter or click Send
- Enjoy!

---

## Going Online (GitHub Pages)

The public site runs on GitHub Pages, and the backend stays on your PC behind Tailscale Funnel.

1. Run `launch-start.bat`. It starts the backend and the Funnel in their own windows.
2. Open the site: `https://aditfadhillah.github.io/Local-AI-Model-Chibot-/`
3. When you are done, run `stop-server.bat`. It closes the windows and removes the public URL, so the site is offline immediately.

The site only works while the PC is on and the server is running. Check the public backend with `https://adits-laptop2.tailc3da84.ts.net/health`.

Logs for public requests show `forwarded=` and `origin=` fields. See the Logs section in [README.md](README.md).

---

## Switching Models

Once you have the app running, you can easily switch models:

1. Pull the model from Ollama:
   ```bash
   ollama pull mistral:7b
   ```

2. Add the model name to `ALLOWED_MODELS` in `server/.env` (comma-separated, e.g. `qwen3:8b,mistral:7b`)

3. Restart the backend, then select the model in the dropdown

## Full Setup Instructions

### 1. Install Ollama
- Download from https://ollama.ai
- Run the installer
- Ollama will start automatically

### 2. Install Python
- Download from https://www.python.org (3.10 or higher)
- During installation, check **"Add Python to PATH"**
- Verify: `python --version`

### 3. Install Node.js
- Download from https://nodejs.org (LTS version recommended)
- Run the installer
- Verify: `node --version` and `npm --version`

### 4. Clone/Navigate to Project
```bash
cd c:\Users\<YourUsername>\PROJECTS\Local-AI-Model-Chibot
git clone <repo-url> .
```

### 5. Pull First Model
```bash
ollama pull qwen3:8b
```

Wait for download to complete (5-15 minutes depending on internet speed). This is a general-purpose 8B parameter model with good speed and quality balance.

### 6. Setup Backend

```bash
cd server

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies (with Device Guard workaround for Windows)
pip install --only-binary :all: -r requirements.txt
```

### 7. Setup Frontend

```bash
cd client
npm install
```

### 8. Start Services

**Terminal 1 - Backend:**
```bash
cd server
venv\Scripts\activate
python -m uvicorn app:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 - Frontend:**
```bash
cd client
npm run dev
```

Expected output:
```
  VITE v5.0.0  ready in 100 ms
  ➜  Local:   http://localhost:5173/
```

### 9. Open Chat

Open browser to: `http://localhost:5173`

---

## Verify Everything Works

1. **Ollama** - Run in PowerShell:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   Should return JSON with your models

2. **Backend** - Run in PowerShell:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"ok","ollama_available":true,"default_model":"qwen3:8b","default_model_available":true,"uptime_seconds":42}`

   Each chat is logged in the "Chibot API" window and in `server/logs/chibot.log`, one summary line per request.

3. **Frontend** - Open `http://localhost:5173` in browser
   - Should load without errors
   - Model dropdown should show available models

4. **Chat** - Send a test message:
   - "Hello"
   - "What is 2+2?"
   - "Write a Python function that..."

---

## Common Issues

| Issue | Solution |
|-------|----------|
| "Ollama not available" | Start Ollama app, wait 10 sec, refresh browser |
| "Backend not available" | Check Terminal 1 is running FastAPI |
| "No models in dropdown" | Pull a model: `ollama pull qwen3:8b` |
| "Port 8000 in use" | Change `FASTAPI_PORT` in `server/.env` |
| "Response is slow" | Close other apps to free RAM; `qwen3:8b` needs about 8GB. Laptop CPU/GPU limits can add 30+ seconds before the first token |

---

## Next Steps

- Explore different models: `ollama list`, `ollama pull mistral:7b`
- Configure options in `server/.env`
- Customize frontend styling in `client/src/index.css`
- Add more features (image upload, conversation export, etc.)

---

## Project Structure

```
Local-AI-Model-Chibot/
├── client/              ← React frontend (port 5173)
├── server/              ← Python backend (port 8000)
├── README.md            ← Full documentation
├── GETTING_STARTED.md   ← This file
├── local-start.bat      ← Local development launcher
├── launch-start.bat     ← Online launcher (backend + Funnel)
├── start-server.bat     ← Backend-only fallback launcher
└── stop-server.bat      ← Stops Chibot windows and resets the Funnel
```

---

**Ready to chat with AI locally?** 🚀
