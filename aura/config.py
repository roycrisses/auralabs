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
    "router": "meta/llama-3.1-8b-instruct",
    "kernel": "meta/llama-3.1-70b-instruct",
    "researcher": "meta/llama-3.1-70b-instruct",
    "creator": "meta/llama-3.1-70b-instruct",
    "vision": "nvidia/llama-3.2-nvlm-1.1-72b-instruct",
    "reward": "nvidia/llama-3.1-nemotron-70b-reward",
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
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"


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
    """Load settings from the keys file. Supports both JSON and code-snippet formats."""
    if not KEYS_FILE.exists():
        raise FileNotFoundError(
            f"API keys file not found: {KEYS_FILE}\n"
            'Create it with your NVIDIA NIM API key(s).'
        )

    # Try secure (encrypted) loading first, fallback to plaintext
    try:
        from aura.security import load_keys_secure
        text = load_keys_secure()
    except Exception:
        text = KEYS_FILE.read_text(encoding="utf-8")

    # Try JSON format first (backwards compatible)
    try:
        raw = json.loads(text)
        key = raw.get("nvidia_nim_api_key", "")
        base = raw.get("nvidia_nim_base_url", "https://integrate.api.nvidia.com/v1")
        return Settings(nvidia_api_keys=[key], nvidia_base_url=base)
    except (json.JSONDecodeError, KeyError):
        pass

    # Parse API keys from code snippets (nvapi-xxx patterns)
    keys = list(dict.fromkeys(re.findall(r'nvapi-[A-Za-z0-9_\-]+', text)))
    if not keys:
        raise ValueError(f"No API keys (nvapi-...) found in {KEYS_FILE}")

    return Settings(nvidia_api_keys=keys)


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
