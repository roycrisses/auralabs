"""Aura configuration — API keys, model registry, hardware profile."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

KEYS_FILE = Path(r"D:\automation\AI keys and tetails.txt")

MODEL_REGISTRY: dict[str, str] = {
    "router": "stepfun/step-3.5-flash:free",
    "kernel": "stepfun/step-3.5-flash:free",
    "researcher": "stepfun/step-3.5-flash:free",
    "creator": "stepfun/step-3.5-flash:free",
    "vision": "stepfun/step-3.5-flash:free",
    "reward": "stepfun/step-3.5-flash:free",
}

# Map each model to which API key it should use (index into parsed keys list).
# Keys are extracted in order from the file — if a model uses a specific key,
# that association is configured here by the key index.
MODEL_KEY_MAP: dict[str, int] = {
    "router": 0,
    "kernel": 1,
    "researcher": 1,
    "creator": 1,
    "vision": 2,
    "reward": 2,
}


# --- BYOK (Bring Your Own Key) ---
# Per-agent overrides: if an agent role has a BYOK entry, it uses that
# base_url + api_key + model instead of the defaults.
# Structure: { "role": { "base_url": "...", "api_key": "...", "model": "..." } }
BYOK_OVERRIDES: dict[str, dict[str, str]] = {}

BYOK_FILE = Path(r"D:\automation\aura\.cache\byok.json")


def _load_byok() -> None:
    """Load saved BYOK overrides from disk."""
    if BYOK_FILE.exists():
        try:
            data = json.loads(BYOK_FILE.read_text(encoding="utf-8"))
            BYOK_OVERRIDES.update(data)
        except Exception:
            pass


def _save_byok() -> None:
    """Persist BYOK overrides to disk."""
    BYOK_FILE.parent.mkdir(parents=True, exist_ok=True)
    BYOK_FILE.write_text(json.dumps(BYOK_OVERRIDES, indent=2), encoding="utf-8")


def set_byok(role: str, base_url: str, api_key: str, model: str) -> None:
    """Set a BYOK override for an agent role."""
    BYOK_OVERRIDES[role] = {
        "base_url": base_url.rstrip("/"),
        "api_key": api_key,
        "model": model,
    }
    _save_byok()


def remove_byok(role: str) -> bool:
    """Remove a BYOK override, reverting to default."""
    if role in BYOK_OVERRIDES:
        del BYOK_OVERRIDES[role]
        _save_byok()
        return True
    return False


def get_byok(role: str) -> dict[str, str] | None:
    """Get the BYOK override for a role, if any."""
    return BYOK_OVERRIDES.get(role)


def list_byok() -> dict[str, dict[str, str]]:
    """Return all BYOK overrides (with keys masked)."""
    result = {}
    for role, cfg in BYOK_OVERRIDES.items():
        key = cfg.get("api_key", "")
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        result[role] = {
            "base_url": cfg["base_url"],
            "api_key_masked": masked,
            "model": cfg["model"],
        }
    return result


class Settings(BaseModel):
    nvidia_api_keys: list[str]
    nvidia_base_url: str = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class HardwareProfile:
    cpu_model: str = "Intel i5-10300H"
    cpu_cores: int = 8
    gpu_model: str = "NVIDIA GTX 1650"
    gpu_vram_mb: int = 4096
    ram_gb: int = 16


HARDWARE = HardwareProfile()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings with OpenRouter details."""
    return Settings(
        nvidia_api_keys=["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"],
        nvidia_base_url="https://openrouter.ai/api/v1"
    )


def get_api_key(agent_role: str = "kernel") -> str:
    """Get the appropriate API key for a given agent role."""
    # BYOK override takes priority
    byok = get_byok(agent_role)
    if byok:
        return byok["api_key"]

    settings = get_settings()
    key_index = MODEL_KEY_MAP.get(agent_role, 0)
    # Clamp to available keys
    key_index = min(key_index, len(settings.nvidia_api_keys) - 1)
    return settings.nvidia_api_keys[key_index]


# Load saved BYOK overrides on import
_load_byok()
