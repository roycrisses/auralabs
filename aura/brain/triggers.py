"""Event trigger engine — file watcher, webhook listener, and schedule triggers.

Triggers fire workflows or commands when events occur:
- File changes (create, modify, delete) via watchdog
- Incoming webhooks (HTTP POST)
- Scheduled events (cron-like via existing scheduler)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = Path(r"D:\automation\aura\.cache\triggers.db")

_watchers: dict[str, Any] = {}  # trigger_id -> Observer instance
_trigger_running = False
_initialized = False


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_triggers_db() -> None:
    """Create the triggers table."""
    global _initialized
    if _initialized:
        return
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS triggers (
            id              TEXT PRIMARY KEY,
            type            TEXT NOT NULL,
            config_json     TEXT NOT NULL DEFAULT '{}',
            workflow_name   TEXT NOT NULL DEFAULT '',
            enabled         INTEGER DEFAULT 1,
            created_at      TEXT NOT NULL,
            last_fired      TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()
    _initialized = True


# --- Trigger CRUD ---

def create_trigger(
    trigger_type: str,
    config_json: str,
    workflow_name: str = "",
) -> str:
    """Create a new trigger. Returns trigger ID.

    Types: file_watcher, webhook, schedule
    """
    init_triggers_db()
    trigger_id = uuid.uuid4().hex[:10]
    now = datetime.now().isoformat()

    conn = _get_conn()
    conn.execute(
        "INSERT INTO triggers (id, type, config_json, workflow_name, enabled, created_at) "
        "VALUES (?, ?, ?, ?, 1, ?)",
        (trigger_id, trigger_type, config_json, workflow_name, now),
    )
    conn.commit()
    conn.close()

    # Start the trigger if it's a file watcher
    if trigger_type == "file_watcher":
        _start_file_watcher(trigger_id, json.loads(config_json), workflow_name)

    return trigger_id


def list_triggers() -> list[dict]:
    """List all triggers."""
    init_triggers_db()
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM triggers ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_trigger(trigger_id: str) -> dict | None:
    """Get a trigger by ID."""
    init_triggers_db()
    conn = _get_conn()
    row = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def enable_trigger(trigger_id: str) -> bool:
    """Enable a trigger."""
    init_triggers_db()
    conn = _get_conn()
    cursor = conn.execute("UPDATE triggers SET enabled = 1 WHERE id = ?", (trigger_id,))
    conn.commit()
    conn.close()

    trigger = get_trigger(trigger_id)
    if trigger and trigger["type"] == "file_watcher":
        _start_file_watcher(trigger_id, json.loads(trigger["config_json"]), trigger["workflow_name"])

    return cursor.rowcount > 0


def disable_trigger(trigger_id: str) -> bool:
    """Disable a trigger."""
    init_triggers_db()
    conn = _get_conn()
    cursor = conn.execute("UPDATE triggers SET enabled = 0 WHERE id = ?", (trigger_id,))
    conn.commit()
    conn.close()

    _stop_file_watcher(trigger_id)
    return cursor.rowcount > 0


def delete_trigger(trigger_id: str) -> bool:
    """Delete a trigger."""
    init_triggers_db()
    _stop_file_watcher(trigger_id)
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM triggers WHERE id = ?", (trigger_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def _mark_fired(trigger_id: str) -> None:
    """Update last_fired timestamp."""
    conn = _get_conn()
    conn.execute(
        "UPDATE triggers SET last_fired = ? WHERE id = ?",
        (datetime.now().isoformat(), trigger_id),
    )
    conn.commit()
    conn.close()


# --- File Watcher ---

def _start_file_watcher(trigger_id: str, config: dict, workflow_name: str) -> None:
    """Start a watchdog observer for a file watcher trigger."""
    if trigger_id in _watchers:
        return

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler, FileSystemEvent
    except ImportError:
        logger.warning("watchdog not installed — file watcher triggers disabled")
        return

    watch_path = config.get("path", ".")
    patterns = config.get("patterns", ["*"])
    events = config.get("events", ["created", "modified"])

    class _Handler(FileSystemEventHandler):
        def _matches(self, event: FileSystemEvent) -> bool:
            if event.is_directory:
                return False
            event_type = event.event_type  # created, modified, deleted, moved
            if event_type not in events:
                return False
            # Check filename patterns
            file_name = Path(event.src_path).name
            for pattern in patterns:
                if pattern == "*" or file_name.endswith(pattern.lstrip("*")):
                    return True
            return False

        def on_any_event(self, event: FileSystemEvent) -> None:
            if not self._matches(event):
                return
            _mark_fired(trigger_id)
            _fire_trigger(trigger_id, workflow_name, {
                "file_path": str(event.src_path),
                "event_type": event.event_type,
            })

    try:
        observer = Observer()
        observer.schedule(_Handler(), str(watch_path), recursive=True)
        observer.daemon = True
        observer.start()
        _watchers[trigger_id] = observer
        logger.info("File watcher started for trigger %s on %s", trigger_id, watch_path)
    except Exception as e:
        logger.error("Failed to start file watcher: %s", e)


def _stop_file_watcher(trigger_id: str) -> None:
    """Stop a file watcher observer."""
    observer = _watchers.pop(trigger_id, None)
    if observer:
        observer.stop()


# --- Trigger Firing ---

def _fire_trigger(trigger_id: str, workflow_name: str, variables: dict) -> None:
    """Fire a trigger — run the associated workflow or send notification."""
    logger.info("Trigger %s fired: %s", trigger_id, variables)

    if workflow_name:
        try:
            from aura.body.workflow import run_workflow
            run_workflow(workflow_name, variables)
        except Exception as e:
            logger.error("Failed to run workflow '%s': %s", workflow_name, e)

    # Always send a notification
    try:
        from aura.body.notify import send_notification
        event_desc = ", ".join(f"{k}={v}" for k, v in variables.items())
        send_notification("Aura Trigger", f"Trigger {trigger_id}: {event_desc}")
    except Exception:
        pass


# --- Webhook handling ---

def fire_webhook_trigger(webhook_id: str, payload: dict, secret: str = "") -> bool:
    """Fire a webhook trigger if it exists and is enabled.

    Returns True if fired successfully.
    """
    init_triggers_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM triggers WHERE type = 'webhook' AND enabled = 1"
    ).fetchall()
    conn.close()

    for row in rows:
        trigger = dict(row)
        config = json.loads(trigger["config_json"])
        if config.get("webhook_id") == webhook_id:
            # Validate secret if configured
            expected_secret = config.get("secret", "")
            if expected_secret and expected_secret != secret:
                return False
            _mark_fired(trigger["id"])
            _fire_trigger(trigger["id"], trigger["workflow_name"], {"webhook_data": json.dumps(payload)})
            return True
    return False


# --- Lifecycle ---

def start_triggers() -> None:
    """Start all enabled file watcher triggers."""
    global _trigger_running
    init_triggers_db()
    _trigger_running = True

    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM triggers WHERE type = 'file_watcher' AND enabled = 1"
    ).fetchall()
    conn.close()

    for row in rows:
        trigger = dict(row)
        config = json.loads(trigger["config_json"])
        _start_file_watcher(trigger["id"], config, trigger["workflow_name"])


def stop_triggers() -> None:
    """Stop all file watchers."""
    global _trigger_running
    _trigger_running = False
    for trigger_id in list(_watchers.keys()):
        _stop_file_watcher(trigger_id)
