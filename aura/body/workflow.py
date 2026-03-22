"""Workflow tools — registered tools for the AI to manage and run workflows."""

from __future__ import annotations

import json

from aura.body.registry import register_tool
from aura.brain.workflows import (
    list_workflows,
    load_workflow,
    run_workflow,
    save_workflow,
)


@register_tool("list_workflows")
def list_workflows_tool() -> str:
    """List all available workflow definitions."""
    workflows = list_workflows()
    if not workflows:
        return "No workflows found. Create one with save_workflow."
    lines = []
    for w in workflows:
        lines.append(f"  {w['file']}: {w['name']} ({w['steps']} steps)")
    return "\n".join(lines)


@register_tool("run_workflow")
def run_workflow_tool(name: str, variables: str = "{}") -> str:
    """Run a saved workflow by name.

    Args:
        name: Workflow filename (without extension).
        variables: JSON string of variables to inject, e.g. '{"city": "Tokyo"}'.
    """
    try:
        vars_dict = json.loads(variables)
    except json.JSONDecodeError:
        vars_dict = {}

    results = run_workflow(name, variables=vars_dict)

    lines = [f"Workflow '{name}' — {len(results)} steps executed:"]
    for r in results:
        status = "OK" if r["success"] else "FAIL"
        if r["type"] == "tool":
            lines.append(f"  Step {r['step']}: [{status}] {r.get('tool', '?')} -> {r.get('output', '')[:100]}")
        elif r["type"] == "prompt":
            lines.append(f"  Step {r['step']}: [PROMPT] {r.get('prompt', '')[:100]}")
    return "\n".join(lines)


@register_tool("save_workflow")
def save_workflow_tool(name: str, definition: str) -> str:
    """Save a workflow definition.

    Args:
        name: Workflow name (becomes the filename).
        definition: JSON string defining the workflow with 'name' and 'steps' keys.
                    Steps can have 'tool' + 'args' or 'prompt' keys.
    """
    try:
        defn = json.loads(definition)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    if "steps" not in defn:
        return "Workflow must have a 'steps' key"

    path = save_workflow(name, defn)
    return f"Workflow saved: {path}"
