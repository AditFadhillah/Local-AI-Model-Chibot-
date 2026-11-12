"""
Local AI Assistant Backend

FastAPI server that proxies chat requests to Ollama and serves model information.
"""

import asyncio
import os
import json
import logging
import secrets
import time
import uuid
from logging.handlers import RotatingFileHandler
from typing import List, Literal, Optional
from contextlib import aclosing, asynccontextmanager

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

# Must run before importing chain, which reads env vars at import time
load_dotenv()

from chain import build_chain, stream_chat  # noqa: E402


def _csv_env(name, default):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")

# Security settings
API_KEY = os.getenv("API_KEY", "")
ALLOWED_ORIGINS = _csv_env("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_MODELS = _csv_env("ALLOWED_MODELS", "qwen3:8b")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
RATE_LIMIT = os.getenv("RATE_LIMIT", "20/hour")
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", 20))
MAX_CONTENT_CHARS = int(os.getenv("MAX_CONTENT_CHARS", 10000))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 2048))
# How long an Ollama availability/model check is reused before asking Ollama again
STATUS_CACHE_SECONDS = float(os.getenv("STATUS_CACHE_SECONDS", 30))

if not API_KEY:
    raise RuntimeError("API_KEY is not set. Add it to server/.env (see server/.env.example).")

limiter = Limiter(key_func=get_remote_address)

# Logs go to server/logs/chibot.log (rotated) and the console. Message content is never logged.
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("chibot")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    _file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "chibot.log"), maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    _file_handler.setFormatter(_log_format)
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(_log_format)
    logger.addHandler(_file_handler)
    logger.addHandler(_console_handler)


_started_at = time.monotonic()

# Cached result of the last Ollama /api/tags call: (checked_at, available, model_names)
_ollama_status_cache: tuple[float, bool, list[str]] | None = None
_ollama_status_lock = asyncio.Lock()


async def get_ollama_status(force: bool = False) -> tuple[bool, list[str]]:
    """
    Return (ollama_available, model_names), reusing the last check for STATUS_CACHE_SECONDS.
    """
    global _ollama_status_cache
    now = time.monotonic()
    if not force and _ollama_status_cache and now - _ollama_status_cache[0] < STATUS_CACHE_SECONDS:
        return _ollama_status_cache[1], _ollama_status_cache[2]

    async with _ollama_status_lock:
        # Another request may have refreshed the cache while this one waited for the lock
        now = time.monotonic()
        if not force and _ollama_status_cache and now - _ollama_status_cache[0] < STATUS_CACHE_SECONDS:
            return _ollama_status_cache[1], _ollama_status_cache[2]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                response.raise_for_status()
                names = [model["name"] for model in response.json().get("models", [])]
                available = True
        except Exception as e:
            logger.warning("Ollama status check failed: %s", e)
            names, available = [], False

        _ollama_status_cache = (time.monotonic(), available, names)
        logger.info("Ollama status refreshed: available=%s models=%d", available, len(names))
        return available, names


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    logger.info("Starting server... Ollama base URL: %s", OLLAMA_BASE_URL)
    yield
    logger.info("Shutting down server...")


# Initialize FastAPI app
app = FastAPI(
    title="Local AI Assistant API",
    description="Backend for local AI chat assistant powered by Ollama",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Log the rate-limit rejection, then return the standard slowapi 429 response.
    """
    logger.warning("req=%s rejected: rate limit exceeded (%s)", request.state.request_id, exc.detail)
    return await _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Assign a request ID and log method, path, status, duration, client, forwarded IP, and origin.
    """
    request.state.request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "req=%s %s %s %d %.0fms client=%s forwarded=%s origin=%s",
        request.state.request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        get_remote_address(request),
        request.headers.get("x-forwarded-for", "-"),
        request.headers.get("origin", "-"),
    )
    return response

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
    default: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    ollama_available: bool
    default_model: str
    default_model_available: bool
    uptime_seconds: int


class StatusResponse(BaseModel):
    ollama_available: bool
    models: List[Model]
    default: Optional[str] = None


def verify_api_key(request: Request, x_api_key: str = Header(default="")):
    """
    Reject requests whose X-API-Key header does not match the configured key.
    """
    if not secrets.compare_digest(x_api_key.encode(), API_KEY.encode()):
        logger.warning(
            "req=%s rejected: %s",
            request.state.request_id,
            "missing API key" if not x_api_key else "invalid API key",
        )
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def allowed_models(names: list[str]) -> list[Model]:
    return [Model(name=name) for name in names if name in ALLOWED_MODELS]


def default_model(models: list[Model]) -> Optional[str]:
    names = {model.name for model in models}
    return OLLAMA_MODEL if OLLAMA_MODEL in names else None


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Report whether Ollama is up and the default model is installed. Public, so it returns no model list.
    """
    available, names = await get_ollama_status()
    model_ready = OLLAMA_MODEL in names
    return HealthResponse(
        status="ok" if available and model_ready else "degraded",
        ollama_available=available,
        default_model=OLLAMA_MODEL,
        default_model_available=model_ready,
        uptime_seconds=int(time.monotonic() - _started_at),
    )


@app.get("/api/status", response_model=StatusResponse)
async def get_status(_: None = Depends(verify_api_key)):
    """
    Return Ollama availability, the allowed models, and the default model in one call.
    """
    available, names = await get_ollama_status()
    models = allowed_models(names)
    return StatusResponse(
        ollama_available=available,
        models=models,
        default=default_model(models),
    )


@app.get("/api/models", response_model=ModelsResponse)
async def get_models(_: None = Depends(verify_api_key)):
    """
    Fetch the list of allowed models. Kept for compatibility; prefer /api/status.
    """
    available, names = await get_ollama_status()
    if not available:
        raise HTTPException(
            status_code=503,
            detail="Could not fetch models from Ollama. Is Ollama running?",
        )
    models = allowed_models(names)
    return ModelsResponse(models=models, default=default_model(models))


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

    request_id = request.state.request_id
    try:
        # Stateless: the client sends the full history on every request
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in payload.messages
        ]
        chain = build_chain(payload.model, OLLAMA_BASE_URL, MAX_OUTPUT_TOKENS)
        prompt_chars = sum(len(msg["content"]) for msg in messages)

        async def generate():
            """
            Stream tokens from the LangChain chain as SSE chunks.
            Stops generation if the client disconnects. Logs one summary line per chat.
            """
            started = time.perf_counter()
            first_token_ms = None
            chunks = 0
            output_chars = 0
            outcome = "completed"
            try:
                async with aclosing(stream_chat(chain, messages)) as tokens:
                    async for token in tokens:
                        if await request.is_disconnected():
                            outcome = "disconnected"
                            break
                        if first_token_ms is None:
                            first_token_ms = (time.perf_counter() - started) * 1000
                        chunks += 1
                        output_chars += len(token)
                        chunk = {"message": {"role": "assistant", "content": token}}
                        yield f"data: {json.dumps(chunk)}\n"
            except (GeneratorExit, asyncio.CancelledError):
                # Client closed the stream before the reply finished
                outcome = "cancelled"
                raise
            except httpx.ReadTimeout:
                outcome = "timeout"
                yield f"data: {json.dumps({'error': 'Request timeout - model response took too long'})}\n"
            except Exception as e:
                outcome = "error"
                logger.error("req=%s streaming error: %s", request_id, e)
                yield f"data: {json.dumps({'error': str(e)})}\n"
            finally:
                logger.info(
                    "req=%s chat model=%s messages=%d prompt_chars=%d ttft=%s total=%.0fms "
                    "chunks=%d output_chars=%d outcome=%s",
                    request_id,
                    payload.model,
                    len(messages),
                    prompt_chars,
                    f"{first_token_ms:.0f}ms" if first_token_ms is not None else "-",
                    (time.perf_counter() - started) * 1000,
                    chunks,
                    output_chars,
                    outcome,
                )

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error("req=%s chat error: %s", request_id, e)
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
            "status": "GET /api/status",
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
