"""Scheduler tools — registered tools for the AI to create reminders and tasks."""

from __future__ import annotations

from aura.body.registry import register_tool
from aura.brain.scheduler import (
    cancel_task,
    list_scheduled_tasks,
    schedule_delay,
    schedule_recurring,
)


@register_tool("set_reminder")
def set_reminder(description: str, delay_minutes: int) -> str:
    """Set a reminder that will trigger a notification after a delay.

    Args:
        description: What to remind about.
        delay_minutes: Minutes from now (1-1440).
    """
    delay_minutes = max(1, min(1440, delay_minutes))
    task_id = schedule_delay(description, delay_seconds=delay_minutes * 60)
    return f"Reminder set (ID: {task_id}): '{description}' in {delay_minutes} minutes"


@register_tool("schedule_command")
def schedule_command(description: str, command: str, delay_minutes: int) -> str:
    """Schedule a shell command to run after a delay.

    Args:
        description: What this command does.
        command: The shell command to execute.
        delay_minutes: Minutes from now.
    """
    delay_minutes = max(1, min(1440, delay_minutes))
    task_id = schedule_delay(description, delay_seconds=delay_minutes * 60, command=command)
    return f"Scheduled (ID: {task_id}): '{command}' in {delay_minutes} minutes"


@register_tool("schedule_recurring_task")
def schedule_recurring_task(description: str, interval_minutes: int, command: str = "") -> str:
    """Schedule a recurring task.

    Args:
        description: What the task does.
        interval_minutes: Minutes between executions (5-10080).
        command: Optional shell command to run each time.
    """
    interval_minutes = max(5, min(10080, interval_minutes))
    task_id = schedule_recurring(description, interval_seconds=interval_minutes * 60, command=command)
    return f"Recurring task set (ID: {task_id}): every {interval_minutes} minutes"


@register_tool("list_reminders")
def list_reminders() -> str:
    """List all pending scheduled tasks and reminders."""
    tasks = list_scheduled_tasks()
    if not tasks:
        return "No scheduled tasks"
    lines = []
    for t in tasks:
        lines.append(f"  [{t['id']}] {t['task_type']} | {t['description']} | runs at: {t['run_at'][:19]}")
    return "\n".join(lines)


@register_tool("cancel_reminder")
def cancel_reminder(task_id: str) -> str:
    """Cancel a scheduled task or reminder by ID.

    Args:
        task_id: The task ID to cancel.
    """
    if cancel_task(task_id):
        return f"Cancelled task: {task_id}"
    return f"Task not found: {task_id}"
