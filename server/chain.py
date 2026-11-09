"""LangChain logic layer: prompt template and streaming model call for /api/chat."""

import os
from contextlib import aclosing
from typing import AsyncIterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "{system}"),
        MessagesPlaceholder("history"),
    ]
)


def build_chain(model: str, base_url: str, max_output_tokens: int):
    """Build prompt | ChatOllama for one request. History is supplied per call."""
    llm = ChatOllama(
        model=model,
        base_url=base_url,
        num_predict=max_output_tokens,
        # Disable qwen3 "thinking" so hidden reasoning does not consume the output budget.
        reasoning=False,
        client_kwargs={"timeout": OLLAMA_TIMEOUT},
    )
    return PROMPT | llm


def to_lc_messages(messages: list[dict]) -> list[BaseMessage]:
    """Convert validated {role, content} dicts into LangChain message objects."""
    converted: list[BaseMessage] = []
    for msg in messages:
        if msg["role"] == "user":
            converted.append(HumanMessage(content=msg["content"]))
        else:
            converted.append(AIMessage(content=msg["content"]))
    return converted


async def stream_chat(chain, messages: list[dict]) -> AsyncIterator[str]:
    """Yield text tokens as the model generates them."""
    inputs = {"system": SYSTEM_PROMPT, "history": to_lc_messages(messages)}
    async with aclosing(chain.astream(inputs)) as chunks:
        async for chunk in chunks:
            if chunk.content:
                yield chunk.content
