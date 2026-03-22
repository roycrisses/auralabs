"""NIM API client wrapper — single point of contact with NVIDIA endpoints."""

from __future__ import annotations

import base64
from pathlib import Path

from langchain_openai import ChatOpenAI

from aura.config import MODEL_REGISTRY, get_api_key, get_base_url, get_byok, get_settings


def get_llm(
    agent_role: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """Return a ChatOpenAI instance configured for the given agent role.

    If a BYOK override exists for the role, uses that base_url/key/model.
    Otherwise falls back to the default configuration (OpenRouter or NVIDIA).
    """
    byok = get_byok(agent_role)

    if byok:
        return ChatOpenAI(
            base_url=byok["base_url"],
            api_key=byok["api_key"],
            model=byok["model"],
            temperature=temperature,
            max_tokens=max_tokens,
            model_kwargs={},
            timeout=120,
            max_retries=2,
            streaming=True,
        )

    model_id = MODEL_REGISTRY[agent_role]
    api_key = get_api_key(agent_role)
    base_url = get_base_url(agent_role)
    
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        model_kwargs={}, 
        timeout=120,
        max_retries=2,
        streaming=True,
    )
