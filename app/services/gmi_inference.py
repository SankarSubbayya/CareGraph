"""
GMI Cloud inference client for CareGraph.

Uses GMI Cloud's OpenAI-compatible API (https://api.gmi-serving.com/v1)
as the LLM backend for all AI features.

API docs: https://docs.gmicloud.ai/inference-engine/api-reference/llm-api-reference
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def chat_completion(
    messages: list[dict],
    *,
    temperature: float = 0.3,
    max_tokens: int = 2000,
    response_format: dict | None = None,
) -> str:
    """Send a chat completion request to GMI Cloud and return the response text.

    Args:
        messages: List of {"role": "...", "content": "..."} dicts.
        temperature: Sampling temperature (0-2). Lower = more deterministic.
        max_tokens: Maximum tokens in response.
        response_format: Optional {"type": "json_object"} to force JSON output.

    Returns:
        The assistant's response text, or empty string on failure.
    """
    if not settings.gmi_api_key:
        logger.debug("GMI_API_KEY not set — skipping inference")
        return ""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.gmi_api_key}",
    }

    payload: dict = {
        "model": settings.gmi_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if response_format:
        payload["response_format"] = response_format

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.gmi_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.warning("GMI Cloud API error %s: %s", e.response.status_code, e.response.text[:200])
        return ""
    except Exception as e:
        logger.warning("GMI Cloud inference failed: %s", e)
        return ""


async def query(prompt: str, *, system: str = "", temperature: float = 0.3) -> str:
    """Simple helper: send a system + user prompt and get a response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return await chat_completion(messages, temperature=temperature)
