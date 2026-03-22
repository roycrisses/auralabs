"""Workflow engine — user-defined multi-step automations.

Workflows are YAML/JSON files stored in .cache/workflows/ that define
sequential steps. Each step can be a tool call or an AI prompt.

Example workflow (morning.yaml):
    name: Morning Routine
    steps:
      - tool: web_search
        args: {query: "weather today"}
      - prompt: "Summarize this weather info briefly"
      - tool: send_notification
        args: {title: "Morning Brief", message: "{{last_result}}"}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # optional, fallback to JSON

from aura.body.registry import execute_tool
from aura.models import ToolCall, ToolResult

WORKFLOWS_DIR = Path(r"D:\automation\aura\.cache\workflows")


def _load_yaml_or_json(path: Path) -> dict:
    """Load a workflow definition from YAML or JSON."""
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        try:
            return yaml.safe_load(text)
        except Exception:
            pass
    return json.loads(text)


def list_workflows() -> list[dict]:
    """List available workflow definitions."""
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for f in sorted(WORKFLOWS_DIR.iterdir()):
        if f.suffix in (".yaml", ".yml", ".json"):
            try:
                data = _load_yaml_or_json(f)
                results.append({
                    "file": f.name,
                    "name": data.get("name", f.stem),
                    "steps": len(data.get("steps", [])),
                })
            except Exception:
                results.append({"file": f.name, "name": f.stem, "steps": 0, "error": "parse error"})
    return results


def load_workflow(name: str) -> dict:
    """Load a workflow by filename (with or without extension)."""
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

    # Try exact match first
    for ext in ("", ".yaml", ".yml", ".json"):
        path = WORKFLOWS_DIR / f"{name}{ext}"
        if path.exists():
            return _load_yaml_or_json(path)

    raise FileNotFoundError(f"Workflow not found: {name}")


def save_workflow(name: str, definition: dict) -> str:
    """Save a workflow definition to a JSON file."""
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    path = WORKFLOWS_DIR / f"{name}.json"
    path.write_text(json.dumps(definition, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def run_workflow(name: str, variables: dict[str, str] | None = None) -> list[dict]:
    """Execute a workflow step by step.

    Args:
        name: Workflow file name.
        variables: Optional variables to substitute into args ({{var}}).

    Returns:
        List of step results.
    """
    wf = load_workflow(name)
    steps = wf.get("steps", [])
    variables = variables or {}
    results = []
    last_result = ""

    for i, step in enumerate(steps):
        step_result = {"step": i + 1, "type": "unknown", "success": False}

        if "tool" in step:
            # Tool call step
            tool_name = step["tool"]
            args = step.get("args", {})

            # Substitute variables
            args = _substitute(args, {**variables, "last_result": last_result})

            tc = ToolCall(tool_name=tool_name, arguments=args)
            result = execute_tool(tc)

            step_result["type"] = "tool"
            step_result["tool"] = tool_name
            step_result["success"] = result.success
            step_result["output"] = str(result.output)[:500] if result.output else ""
            step_result["error"] = result.error

            last_result = str(result.output) if result.success else str(result.error)

        elif "prompt" in step:
            # AI prompt step — just store it; the caller can pipe it to an agent
            prompt = _substitute_str(step["prompt"], {**variables, "last_result": last_result})
            step_result["type"] = "prompt"
            step_result["prompt"] = prompt
            step_result["success"] = True
            last_result = prompt

        results.append(step_result)

        # Stop on failure unless continue_on_error is set
        if not step_result["success"] and not step.get("continue_on_error", False):
            break

    return results


def _substitute(args: dict, variables: dict) -> dict:
    """Replace {{var}} placeholders in argument values."""
    result = {}
    for k, v in args.items():
        if isinstance(v, str):
            result[k] = _substitute_str(v, variables)
        else:
            result[k] = v
    return result


def _substitute_str(text: str, variables: dict) -> str:
    """Replace {{var}} in a string."""
    for key, val in variables.items():
        text = text.replace(f"{{{{{key}}}}}", str(val))
    return text
