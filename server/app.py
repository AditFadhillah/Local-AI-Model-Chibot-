"""
Local AI Assistant Backend

FastAPI server that proxies chat requests to Ollama and serves model information.
"""

import os
import json
from typing import List
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "localhost")

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]


class Model(BaseModel):
    name: str


class ModelsResponse(BaseModel):
    models: List[Model]


class HealthResponse(BaseModel):
    status: str
    ollama_available: bool


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
async def get_models():
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
            ]

            return ModelsResponse(models=models)
    except Exception as e:
        print(f"Error fetching models: {e}")
        raise HTTPException(
            status_code=503,
            detail="Could not fetch models from Ollama. Is Ollama running?",
        )


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Stream chat responses from Ollama.
    """
    if not request.model:
        raise HTTPException(status_code=400, detail="Model not specified")

    try:
        # Prepare the messages in Ollama format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
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
                        json={"model": request.model, "messages": messages, "stream": True},
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
