"""
Local AI Assistant Backend

FastAPI server that proxies chat requests to Ollama and serves model information.
"""

import os
import json
import secrets
from typing import List, Literal
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _csv_env(name, default):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")

# Security settings
API_KEY = os.getenv("API_KEY", "")
ALLOWED_ORIGINS = _csv_env("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_MODELS = _csv_env("ALLOWED_MODELS", "qwen2.5:8b")
RATE_LIMIT = os.getenv("RATE_LIMIT", "20/hour")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 20))
MAX_CONTENT_CHARS = int(os.getenv("MAX_CONTENT_CHARS", 4000))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 512))

if not API_KEY:
    raise RuntimeError("API_KEY is not set. Add it to server/.env (see server/.env.example).")

limiter = Limiter(key_func=get_remote_address)

# Global state for Ollama availability check
ollama_available = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    print(f"Starting server... Ollama base URL: {OLLAMA_BASE_URL}")
    yield
    print("Shutting down server...")


# Initialize FastAPI app
app = FastAPI(
    title="Local AI Assistant API",
    description="Backend for local AI chat assistant powered by Ollama",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Restrict CORS to the configured frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# Pydantic models
class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_CONTENT_CHARS)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(max_length=100)
    messages: List[Message] = Field(min_length=1, max_length=MAX_MESSAGES)


class Model(BaseModel):
    name: str


class ModelsResponse(BaseModel):
    models: List[Model]


class HealthResponse(BaseModel):
    status: str
    ollama_available: bool


def verify_api_key(x_api_key: str = Header(default="")):
    """
    Reject requests whose X-API-Key header does not match the configured key.
    """
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check if the server and Ollama are available.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            ollama_available = response.status_code == 200
    except Exception as e:
        print(f"Ollama health check failed: {e}")
        ollama_available = False

    return HealthResponse(
        status="ok",
        ollama_available=ollama_available,
    )


@app.get("/api/models", response_model=ModelsResponse)
async def get_models(_: None = Depends(verify_api_key)):
    """
    Fetch the list of available models from Ollama.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()

            # Extract model names
            models = [
                Model(name=model["name"])
                for model in data.get("models", [])
                if model["name"] in ALLOWED_MODELS
            ]

            return ModelsResponse(models=models)
    except Exception as e:
        print(f"Error fetching models: {e}")
        raise HTTPException(
            status_code=503,
            detail="Could not fetch models from Ollama. Is Ollama running?",
        )


@app.post("/api/chat")
@limiter.limit(RATE_LIMIT)
async def chat(
    request: Request,
    payload: ChatRequest,
    _: None = Depends(verify_api_key),
):
    """
    Stream chat responses from Ollama.
    """
    if payload.model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Model not allowed")

    try:
        # Prepare the messages in Ollama format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in payload.messages
        ]

        async def generate():
            """
            Stream the response from Ollama line by line.
            """
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST",
                        f"{OLLAMA_BASE_URL}/api/chat",
                        json={
                            "model": payload.model,
                            "messages": messages,
                            "stream": True,
                            "options": {"num_predict": MAX_OUTPUT_TOKENS},
                        },
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    chunk = json.loads(line)
                                    yield f"data: {json.dumps(chunk)}\n"
                                except json.JSONDecodeError:
                                    pass
            except httpx.ReadTimeout:
                yield f"data: {json.dumps({'error': 'Request timeout - model response took too long'})}\n"
            except Exception as e:
                print(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Local AI Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "health": "GET /health",
            "models": "GET /api/models",
            "chat": "POST /api/chat",
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=FASTAPI_HOST,
        port=FASTAPI_PORT,
        reload=True,
        log_level="info",
    )
