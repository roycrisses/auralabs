"""Task scheduler — delayed and recurring task execution.

Supports:
- One-shot delayed tasks: "remind me in 30 minutes"
- Recurring cron-like tasks: "every day at 9am"
- Command execution at scheduled time

Uses a background thread to avoid blocking the main event loop.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(r"D:\automation\aura\.cache\scheduler.db")

_scheduler_thread: threading.Thread | None = None
_scheduler_running = False


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_scheduler_db() -> None:
    """Create the scheduled_tasks table."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id          TEXT PRIMARY KEY,
            task_type   TEXT NOT NULL,
            description TEXT NOT NULL,
            run_at      TEXT NOT NULL,
            repeat_seconds INTEGER DEFAULT 0,
            command     TEXT DEFAULT '',
            status      TEXT DEFAULT 'pending',
            created_at  TEXT NOT NULL,
            last_run    TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()


# --- Task CRUD ---

def schedule_delay(description: str, delay_seconds: int, command: str = "") -> str:
    """Schedule a one-shot task to run after a delay.

    Args:
        description: What the task does (shown in notification).
        delay_seconds: Seconds from now to execute.
        command: Optional shell command to run when triggered.

    Returns:
        Task ID.
    """
    task_id = uuid.uuid4().hex[:10]
    run_at = (datetime.now() + timedelta(seconds=delay_seconds)).isoformat()
    now = datetime.now().isoformat()

    conn = _get_conn()
    conn.execute(
        "INSERT INTO scheduled_tasks (id, task_type, description, run_at, command, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, "delay", description, run_at, command, now),
    )
    conn.commit()
    conn.close()
    return task_id


def schedule_recurring(description: str, interval_seconds: int, command: str = "") -> str:
    """Schedule a recurring task.

    Args:
        description: What the task does.
        interval_seconds: Seconds between each execution.
        command: Optional shell command to run each time.

    Returns:
        Task ID.
    """
    task_id = uuid.uuid4().hex[:10]
    run_at = (datetime.now() + timedelta(seconds=interval_seconds)).isoformat()
    now = datetime.now().isoformat()

    conn = _get_conn()
    conn.execute(
        "INSERT INTO scheduled_tasks (id, task_type, description, run_at, repeat_seconds, command, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task_id, "recurring", description, run_at, interval_seconds, command, now),
    )
    conn.commit()
    conn.close()
    return task_id


def list_scheduled_tasks(include_done: bool = False) -> list[dict]:
    """List all scheduled tasks."""
    conn = _get_conn()
    if include_done:
        rows = conn.execute("SELECT * FROM scheduled_tasks ORDER BY run_at").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scheduled_tasks WHERE status IN ('pending', 'recurring') ORDER BY run_at"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def cancel_task(task_id: str) -> bool:
    """Cancel a scheduled task."""
    conn = _get_conn()
    cursor = conn.execute(
        "UPDATE scheduled_tasks SET status = 'cancelled' WHERE id = ?", (task_id,)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def _get_due_tasks() -> list[dict]:
    """Get tasks that are past their run_at time and still pending."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    rows = conn.execute(
        "SELECT * FROM scheduled_tasks WHERE status IN ('pending', 'recurring') AND run_at <= ?",
        (now,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _mark_done(task_id: str) -> None:
    conn = _get_conn()
    conn.execute(
        "UPDATE scheduled_tasks SET status = 'done', last_run = ? WHERE id = ?",
        (datetime.now().isoformat(), task_id),
    )
    conn.commit()
    conn.close()


def _reschedule(task_id: str, interval: int) -> None:
    next_run = (datetime.now() + timedelta(seconds=interval)).isoformat()
    conn = _get_conn()
    conn.execute(
        "UPDATE scheduled_tasks SET run_at = ?, last_run = ? WHERE id = ?",
        (next_run, datetime.now().isoformat(), task_id),
    )
    conn.commit()
    conn.close()


# --- Execution callbacks ---

_on_task_due: list = []  # list of callables: fn(task_dict) -> None


def on_task_triggered(callback) -> None:
    """Register a callback for when a scheduled task fires."""
    _on_task_due.append(callback)


def _execute_task(task: dict) -> None:
    """Run the task's action and notify callbacks."""
    # If there's a command, run it
    if task.get("command"):
        import subprocess
        import sys
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
        try:
            subprocess.Popen(
                task["command"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except Exception:
            pass

    # Notify all callbacks (e.g. send_notification)
    for cb in _on_task_due:
        try:
            cb(task)
        except Exception:
            pass


# --- Background scheduler loop ---

def _scheduler_loop() -> None:
    """Background thread that checks for due tasks every 5 seconds."""
    global _scheduler_running
    while _scheduler_running:
        try:
            due = _get_due_tasks()
            for task in due:
                _execute_task(task)
                if task["task_type"] == "recurring" and task["repeat_seconds"] > 0:
                    _reschedule(task["id"], task["repeat_seconds"])
                else:
                    _mark_done(task["id"])
        except Exception:
            pass
        time.sleep(5)


def start_scheduler() -> None:
    """Start the background scheduler thread."""
    global _scheduler_thread, _scheduler_running
    if _scheduler_running:
        return

    init_scheduler_db()
    _scheduler_running = True
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True, name="aura-scheduler")
    _scheduler_thread.start()


def stop_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler_running
    _scheduler_running = False


# Register default callback: send a Windows notification when a task fires
def _default_notify(task: dict) -> None:
    try:
        from aura.body.notify import send_notification
        send_notification("Aura Reminder", task.get("description", "Scheduled task triggered"))
    except Exception:
        pass

on_task_triggered(_default_notify)


# Trigger integration callback: fire schedule-type triggers
def _trigger_integration_callback(task: dict) -> None:
    """Check if a scheduled task is linked to a trigger and fire it."""
    try:
        from aura.brain.triggers import _fire_trigger
        description = task.get("description", "")
        if description.startswith("trigger:"):
            trigger_id = description.split(":", 1)[1].strip()
            _fire_trigger(trigger_id, "", {"scheduled": "true"})
    except Exception:
        pass


on_task_triggered(_trigger_integration_callback)
