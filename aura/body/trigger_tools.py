"""Trigger management tools — create, list, enable/disable triggers."""

from __future__ import annotations

from aura.body.registry import register_tool


@register_tool("create_trigger")
def create_trigger_tool(type: str, config_json: str, workflow_name: str = "") -> str:
    """Create a new event trigger.

    Types:
    - file_watcher: Watch for file changes. Config: {"path": "...", "patterns": ["*.py"], "events": ["created", "modified"]}
    - webhook: Receive HTTP webhooks. Config: {"webhook_id": "my-hook", "secret": "optional-secret"}
    - schedule: Time-based trigger. Config: {"cron": "0 9 * * *"} or {"daily_at": "09:00"}

    Args:
        type: Trigger type (file_watcher, webhook, schedule).
        config_json: JSON string with trigger configuration.
        workflow_name: Name of the workflow to run when triggered.
    """
    from aura.brain.triggers import create_trigger

    trigger_id = create_trigger(type, config_json, workflow_name)
    return f"Created {type} trigger: {trigger_id}"


@register_tool("list_triggers")
def list_triggers_tool() -> str:
    """List all event triggers and their status."""
    from aura.brain.triggers import list_triggers

    triggers = list_triggers()
    if not triggers:
        return "No triggers configured."
    lines = [f"Triggers ({len(triggers)}):"]
    for t in triggers:
        status = "enabled" if t.get("enabled") else "disabled"
        fired = t.get("last_fired", "never") or "never"
        lines.append(f"  [{t['id']}] {t['type']} ({status}) — workflow: {t.get('workflow_name', '(none)')}, last fired: {fired}")
    return "\n".join(lines)


@register_tool("enable_trigger")
def enable_trigger_tool(trigger_id: str) -> str:
    """Enable a trigger by ID."""
    from aura.brain.triggers import enable_trigger

    ok = enable_trigger(trigger_id)
    return f"Enabled trigger {trigger_id}." if ok else f"Trigger {trigger_id} not found."


@register_tool("disable_trigger")
def disable_trigger_tool(trigger_id: str) -> str:
    """Disable a trigger by ID."""
    from aura.brain.triggers import disable_trigger

    ok = disable_trigger(trigger_id)
    return f"Disabled trigger {trigger_id}." if ok else f"Trigger {trigger_id} not found."


@register_tool("delete_trigger")
def delete_trigger_tool(trigger_id: str) -> str:
    """Delete a trigger by ID."""
    from aura.brain.triggers import delete_trigger

    ok = delete_trigger(trigger_id)
    return f"Deleted trigger {trigger_id}." if ok else f"Trigger {trigger_id} not found."
