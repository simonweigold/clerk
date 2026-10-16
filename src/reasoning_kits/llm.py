"""LLM client wrapping LiteLLM for multi-provider support.

LiteLLM provides a unified interface for OpenAI, Anthropic, Mistral, Gemini,
OpenRouter, and Vertex. Set the appropriate API key env var and LiteLLM
routes the call.
"""

import os
from typing import Any

import litellm


def get_default_model() -> str:
    """Return the default model name from env or fallback."""
    return os.environ.get("RK_DEFAULT_MODEL", "gpt-5.4-nano")


def completion(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.0,
    **kwargs: Any,
) -> Any:
    """Synchronous LLM completion via LiteLLM."""
    return litellm.completion(
        model=model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        **kwargs,
    )


async def acompletion(
    model: str,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.0,
    **kwargs: Any,
) -> Any:
    """Async LLM completion via LiteLLM."""
    return await litellm.acompletion(
        model=model,
        messages=messages,
        tools=tools,
        temperature=temperature,
        **kwargs,
    )