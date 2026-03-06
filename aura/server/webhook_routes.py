"""Webhook receiver endpoints — receive external webhooks and fire triggers."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

webhook_router = APIRouter()


@webhook_router.post("/webhooks/{webhook_id}")
async def receive_webhook(webhook_id: str, request: Request):
    """Receive an external webhook and fire the associated trigger."""
    from aura.brain.triggers import fire_webhook_trigger

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    secret = request.headers.get("x-webhook-secret", "")
    fired = fire_webhook_trigger(webhook_id, payload, secret)

    if fired:
        return {"status": "fired", "webhook_id": webhook_id}
    return {"status": "not_found", "webhook_id": webhook_id}


class TriggerCreateRequest(BaseModel):
    type: str
    config_json: str = "{}"
    workflow_name: str = ""


@webhook_router.get("/triggers")
async def api_list_triggers():
    """List all triggers."""
    from aura.brain.triggers import list_triggers
    return list_triggers()


@webhook_router.post("/triggers")
async def api_create_trigger(req: TriggerCreateRequest):
    """Create a new trigger."""
    from aura.brain.triggers import create_trigger
    trigger_id = create_trigger(req.type, req.config_json, req.workflow_name)
    return {"id": trigger_id, "type": req.type, "workflow_name": req.workflow_name}


@webhook_router.delete("/triggers/{trigger_id}")
async def api_delete_trigger(trigger_id: str):
    """Delete a trigger."""
    from aura.brain.triggers import delete_trigger
    deleted = delete_trigger(trigger_id)
    return {"deleted": deleted, "id": trigger_id}
