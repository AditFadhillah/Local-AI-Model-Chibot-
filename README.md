# Local AI Assistant

A practical local AI setup and web application that chats with a locally running model using Ollama. This project runs entirely on your computer without requiring external API keys.

## Features

- Chat with local AI models (no cloud API required)
- Easy model switching with the model selector
- Chat history persisted in browser local storage
- Markdown and code block rendering with syntax highlighting
- Streamed responses for progressive display
- Clean, responsive chat interface
- Windows-first setup and documentation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (React)                         │
│              Local AI Assistant Web Interface                │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTP API calls
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Python FastAPI Backend Server                   │
│          (Proxies requests to local Ollama)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                    HTTP requests
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Ollama (Local Model Runtime)                │
│      Running AI models (e.g., qwen3:8b)                     │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

### System
- Windows 10 or Windows 11
- At least 4GB RAM (8GB+ recommended for larger models)
- ~20GB disk space (depends on model size)

### Software
- [Ollama](https://ollama.ai) - Download and install from https://ollama.ai
- Python 3.10 or later - Download from https://www.python.org
- Node.js 16+ - Download from https://nodejs.org

## Quick Start

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

### 2. Pull a Model

Open a terminal and run one of:

```bash
# Recommended (8B parameters, good balance of speed and quality)
ollama pull qwen3:8b

# Other options (add each to ALLOWED_MODELS in server/.env before use)
ollama pull mistral:7b
ollama pull neural-chat:7b
```

The model download will take 5-15 minutes depending on your internet speed and model size.

### 3. Start Ollama Service

Ollama runs as a background service on Windows. The service starts automatically after installation. Verify it's running:

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response listing your models.

### 4. Clone or Navigate to Project

```bash
cd c:\Users\<YourUsername>\PROJECTS\Local-AI-Model-Chibot
```

### 5. Install Dependencies

#### Backend (Python)

```bash
cd server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend (Node.js)

```bash
cd ..\client
npm install
```

### 6. Start the Application

#### Terminal 1 - Start Backend (FastAPI)

```bash
cd server
venv\Scripts\activate
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### Terminal 2 - Start Frontend (Vite + React)

```bash
cd client
npm run dev
```

You should see:
```
  VITE v5.0.0  ready in 100 ms

  ➜  Local:   http://localhost:5173/
```

### 7. Open the Chat Interface

Open your browser and go to:
```
http://localhost:5173
```

Select your model from the dropdown, type a message, and press Enter or click Send!

## Troubleshooting

### "Backend server not available"

**Problem**: The error message appears when loading the page.

**Solution**:
1. Make sure the Python backend is running (Terminal 1 should show "Uvicorn running...")
2. Check that it's listening on `http://localhost:8000`
3. Verify with: `curl http://localhost:8000/health`

### "Ollama is not available"

**Problem**: A warning banner appears saying Ollama is not running.

**Solution**:
1. Open Ollama (it's in your Start Menu as "Ollama")
2. Wait 10 seconds for the service to start
3. Refresh your browser
4. Verify Ollama is running: `curl http://localhost:11434/api/tags`

If Ollama doesn't respond, try:
```bash
# On Windows, restart the Ollama service
net stop ollama
net start ollama
```

### No models appear in the dropdown

**Problem**: The model selector shows "Loading models..." but never loads.

**Solution**:
1. Verify you've pulled at least one model:
   ```bash
   ollama pull qwen3:8b
   ```
2. Check Ollama's models are accessible:
   ```bash
   curl http://localhost:11434/api/tags
   ```
3. Refresh the browser page

### Chat sends but model doesn't respond

**Problem**: Message appears but no assistant response.

**Solution**:
1. Check if Ollama has enough RAM (8GB recommended)
2. Check free RAM; `qwen3:8b` needs about 8GB
3. Check backend logs in Terminal 1 for errors
4. Verify the model name matches: `ollama list`

### "Failed to get response from model"

**Problem**: After sending a message, an error appears.

**Solution**:
1. The model might be slow. Wait 30 seconds and check browser console for details
2. Try sending a simpler prompt (e.g., "Hello")
3. Check Ollama logs: look in Ollama app window or system logs
4. Ensure Ollama has memory available: use Task Manager

### Browser console shows CORS errors

**Problem**: `Access-Control-Allow-Origin` errors appear.

**Solution**:
1. This shouldn't happen if the backend is running correctly
2. Hard refresh the browser (Ctrl+Shift+R on Windows)
3. Check backend is on `http://localhost:8000` (not `127.0.0.1`)
4. Restart both backend and frontend

### Port 8000 or 5173 already in use

**Problem**: "Address already in use" error when starting server/frontend.

**Solution**:
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill process with ID from above (replace XXXX)
taskkill /PID XXXX /F
```

Or change the port in `server/.env`:
```env
FASTAPI_PORT=8001
```

And in `client/vite.config.js`, update the proxy.

## Configuration

### Environment Variables

Edit `server/.env` to customize:

```env
# Ollama service URL (change if running on different machine/port)
OLLAMA_BASE_URL=http://localhost:11434

# FastAPI server configuration
FASTAPI_HOST=localhost
FASTAPI_PORT=8000
```

### Frontend Proxy

Edit `client/vite.config.js` to change backend URL for production:

```javascript
proxy: {
  '/api': {
    target: 'http://your-server:8000',  // Change here
    changeOrigin: true
  }
}
```

## Development

### Project Structure

```
local-ai-assistant/
├── client/                    # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx           # Main chat component
│   │   ├── index.css         # Global styles
│   │   ├── main.jsx          # React entry point
│   │   └── components/
│   │       ├── ChatMessage.jsx
│   │       ├── ChatMessage.css
│   │       ├── ModelSelector.jsx
│   │       └── ModelSelector.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── server/                    # Python FastAPI backend
│   ├── app.py                # Main FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env                  # Environment configuration
│   └── venv/                 # Virtual environment (after setup)
│
├── README.md                 # This file
└── .gitignore
```

### Running Tests

Frontend (no tests configured yet - feel free to add Vitest or Jest):
```bash
cd client
npm run build
```

Backend (simple health check):
```bash
curl http://localhost:8000/health
```

### Code Quality

Frontend:
- Uses React 18 with Hooks
- React Markdown for rendering
- React Syntax Highlighter for code blocks

Backend:
- FastAPI with async support
- HTTPX for streaming responses
- Pydantic for validation
- CORS enabled for development

## Features Walkthrough

### Chat History

Conversations are saved to browser local storage automatically. Refresh the page and your messages are still there. To clear, click the "Clear" button.

### Model Selection

The dropdown in the header shows all models installed in Ollama. Switch between models mid-conversation—each new message uses the selected model.

### Markdown Support

The assistant's responses support:
- Bold, italic, code spans
- Headers (#, ##, ###)
- Lists (bullet and numbered)
- Code blocks with syntax highlighting
- Links
- Blockquotes

### Streaming Responses

Model responses appear progressively (word by word) for a smooth experience. A typing indicator appears while waiting for the model.

## Performance Tips

1. **Smaller models are faster**: a model under 4B parameters responds faster than `qwen3:8b` but with less capability
2. **Quit other apps**: Close browser tabs, Visual Studio, etc., to free up RAM
3. **Close Ollama when not using**: Right-click system tray → Quit Ollama to free memory
4. **Use GPU acceleration** (if available): Ollama auto-detects NVIDIA/AMD GPUs
5. **Cold start**: First message is slower; subsequent messages are faster

## Next Steps

### Optional Enhancements

- Add message search/filtering
- Export conversations as markdown or PDF
- Add code copy buttons
- Implement user profiles/multiple conversations
- Add image upload support (if models support it)
- Deploy to a local Docker container

### Model Recommendations

- **qwen3:8b**: Default model, general-purpose (requires 8GB+ RAM)
- **mistral:7b**: Good all-arounder (requires 8GB+ RAM)
- **neural-chat:7b**: Conversational AI (requires 8GB+ RAM)
- **phi:2.7b**: Very lightweight, suitable for older hardware

## Security Notes

- **Local only**: No data leaves your computer (unless you add cloud features)
- **No authentication**: Not suitable for multi-user or production scenarios
- **CORS permissive**: Set `allow_origins=["*"]` for development convenience
- **Keep Ollama updated**: Run `ollama update` to get the latest models

## Limitations

- Only supports text input/output
- Models run sequentially (no parallel processing)
- Browser storage limits (typically 5-10MB) may limit conversation size
- Large models require significant RAM and are slower on CPU-only systems
- No persistent database (conversations lost on local storage clear)

## Support & Debugging

### Logs

**Backend logs** appear in Terminal 1 where you ran the FastAPI server.

**Browser console** (F12 → Console tab) shows frontend errors.

**Ollama logs**:
- Windows: Check Ollama app window (Alt+Tab to switch)
- Or: `%APPDATA%\Ollama\logs\` 

### Getting Help

1. Check the troubleshooting section above
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Check backend health: `curl http://localhost:8000/health`
4. Look at browser console errors (F12)
5. Try restarting all services

## License

This project is for personal use. Ollama and the models have their own licenses.

## Acknowledgments

- [Ollama](https://ollama.ai) - Local model runtime
- [FastAPI](https://fastapi.tiangolo.com) - Python web framework
- [React](https://react.dev) - UI library
- [Vite](https://vitejs.dev) - Frontend build tool
- Model providers: OpenAI, Meta, Mistral, Alibaba, etc.

---

**Enjoy your local AI assistant!** 🚀
