# Chibot Technical Architecture

```mermaid
flowchart LR
    subgraph Client["Browser: laptop or phone"]
        UI["React + Vite chat UI"]
    end

    subgraph Hosting["GitHub"]
        Pages["GitHub Pages<br/>static site built by GitHub Actions"]
    end

    subgraph Home["Home PC"]
        Funnel["Tailscale Funnel<br/>public HTTPS URL"]
        API["FastAPI backend<br/>API key, CORS, rate limit, logs"]
        Chain["LangChain<br/>prompt and streaming"]
        Ollama["Ollama<br/>qwen3:8b model"]
        Log[("chibot.log")]
    end

    UI -- "loads page" --> Pages
    UI -- "HTTPS /api/chat (streamed)" --> Funnel
    Funnel -- "forwards to 127.0.0.1:8000" --> API
    API --> Chain
    Chain -- "HTTP localhost:11434" --> Ollama
    Ollama -- "tokens" --> Chain
    Chain -- "streamed tokens" --> API
    API -- "request summary" --> Log
    API -- "streamed response" --> Funnel
    Funnel -- "streamed response" --> UI
```

## Request Flow

1. The browser loads the chat page from GitHub Pages.
2. The page sends the message to the backend's Funnel URL with the API key.
3. Tailscale Funnel forwards the request to FastAPI on the home PC.
4. FastAPI checks the key, origin, rate limit, and input size, then calls LangChain.
5. LangChain sends the prompt to Ollama, which runs `qwen3:8b` locally.
6. Tokens stream back through FastAPI and Funnel to the browser.
7. Each request is written to `server/logs/chibot.log` with a request ID and outcome.
