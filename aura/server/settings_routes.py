"""Settings API — read and update Aura configuration."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from aura.body.confirm import CONFIRMATION_ENABLED, TOOL_RISK
from aura.config import KEYS_FILE, MODEL_REGISTRY

settings_router = APIRouter(prefix="/settings")


class SettingsResponse(BaseModel):
    models: dict[str, str]
    confirmation_enabled: bool
    tool_risk_levels: dict[str, str]
    allowed_roots: list[str]
    byok: dict[str, dict[str, str]]


class UpdateModelsRequest(BaseModel):
    models: dict[str, str]


class UpdateConfirmationRequest(BaseModel):
    enabled: bool


class ByokRequest(BaseModel):
    role: str
    base_url: str
    api_key: str
    model: str


@settings_router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current Aura settings."""
    from aura.body.filesystem import ALLOWED_ROOTS
    from aura.config import list_byok

    return SettingsResponse(
        models=MODEL_REGISTRY,
        confirmation_enabled=CONFIRMATION_ENABLED,
        tool_risk_levels=TOOL_RISK,
        allowed_roots=[str(r) for r in ALLOWED_ROOTS],
        byok=list_byok(),
    )


@settings_router.put("/models")
async def update_models(req: UpdateModelsRequest):
    """Update the model registry."""
    for role, model in req.models.items():
        if role in MODEL_REGISTRY:
            MODEL_REGISTRY[role] = model
    return {"status": "ok", "models": MODEL_REGISTRY}


@settings_router.put("/confirmation")
async def update_confirmation(req: UpdateConfirmationRequest):
    """Enable or disable tool confirmation prompts."""
    import aura.body.confirm as confirm_mod
    confirm_mod.CONFIRMATION_ENABLED = req.enabled
    return {"status": "ok", "confirmation_enabled": req.enabled}


@settings_router.put("/tool-risk/{tool_name}")
async def update_tool_risk(tool_name: str, level: str = "prompt"):
    """Update the risk level for a specific tool."""
    if level not in ("safe", "prompt", "blocked"):
        return {"error": f"Invalid level: {level}. Must be safe, prompt, or blocked."}
    TOOL_RISK[tool_name] = level
    return {"status": "ok", "tool": tool_name, "level": level}


# --- BYOK (Bring Your Own Key) ---

@settings_router.put("/byok")
async def set_byok_endpoint(req: ByokRequest):
    """Set a BYOK override for an agent role.

    The agent will use the provided base_url, api_key, and model
    instead of the default NVIDIA NIM configuration.
    """
    from aura.config import list_byok, set_byok

    if not req.role:
        return {"error": "role is required"}
    if not req.base_url:
        return {"error": "base_url is required"}
    if not req.api_key:
        return {"error": "api_key is required"}
    if not req.model:
        return {"error": "model is required"}

    set_byok(req.role, req.base_url, req.api_key, req.model)
    return {"status": "ok", "byok": list_byok()}


@settings_router.delete("/byok/{role}")
async def remove_byok_endpoint(role: str):
    """Remove a BYOK override for an agent role, reverting to default."""
    from aura.config import list_byok, remove_byok

    removed = remove_byok(role)
    return {
        "status": "removed" if removed else "not_found",
        "role": role,
        "byok": list_byok(),
    }


@settings_router.get("/byok")
async def list_byok_endpoint():
    """List all BYOK overrides (API keys are masked)."""
    from aura.config import list_byok
    return list_byok()
