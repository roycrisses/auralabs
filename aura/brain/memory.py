"""Conversation memory — SQLite-backed chat history with session support."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

DB_PATH = Path(r"D:\automation\aura\.cache\memory.db")


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          TEXT PRIMARY KEY,
            title       TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL REFERENCES sessions(id),
            role        TEXT NOT NULL,
            content     TEXT NOT NULL,
            agent       TEXT DEFAULT '',
            tool_name   TEXT DEFAULT '',
            tool_args   TEXT DEFAULT '{}',
            timestamp   TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, id);
    """)
    conn.commit()

    # Migration: add branching columns if they don't exist
    try:
        conn.execute("SELECT parent_session_id FROM sessions LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE sessions ADD COLUMN parent_session_id TEXT DEFAULT ''")
        conn.execute("ALTER TABLE sessions ADD COLUMN branch_point INTEGER DEFAULT 0")
        conn.commit()

    conn.close()


# --- Session management ---

def create_session(title: str = "") -> str:
    """Create a new conversation session. Returns the session ID."""
    session_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, title, now, now),
    )
    conn.commit()
    conn.close()
    return session_id


def list_sessions(limit: int = 20) -> list[dict]:
    """List recent sessions, newest first."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session(session_id: str) -> dict | None:
    """Get a session by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_session_title(session_id: str, title: str) -> None:
    """Update a session's title."""
    conn = _get_conn()
    conn.execute(
        "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.now().isoformat(), session_id),
    )
    conn.commit()
    conn.close()


def delete_session(session_id: str) -> None:
    """Delete a session and all its messages."""
    conn = _get_conn()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


# --- Message storage ---

def save_message(
    session_id: str,
    role: str,
    content: str,
    agent: str = "",
    tool_name: str = "",
    tool_args: dict | None = None,
) -> None:
    """Save a message to the session."""
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, content, agent, tool_name, tool_args, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, role, content, agent, tool_name, json.dumps(tool_args or {}), now),
    )
    conn.execute(
        "UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id)
    )
    conn.commit()
    conn.close()


def get_messages(session_id: str, limit: int = 100) -> list[dict]:
    """Get messages for a session, oldest first."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content, agent, tool_name, tool_args, timestamp "
        "FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_message_count(session_id: str) -> int:
    """Get the number of messages in a session."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return row["cnt"]


# --- LangChain message conversion ---

def messages_to_langchain(messages: list[dict]) -> list:
    """Convert stored messages to LangChain message objects for context injection."""
    lc_messages = []
    for m in messages:
        role = m["role"]
        content = m["content"]
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
        elif role == "system":
            lc_messages.append(SystemMessage(content=content))
        elif role == "tool":
            lc_messages.append(ToolMessage(content=content, tool_call_id=m.get("tool_name", "")))
    return lc_messages


def auto_title(session_id: str, first_message: str) -> None:
    """Auto-generate a session title from the first user message."""
    title = first_message[:60].strip()
    if len(first_message) > 60:
        title += "..."
    update_session_title(session_id, title)


# --- Branching / Forking ---

def fork_session(session_id: str, at_message_index: int | None = None, title: str = "") -> str:
    """Fork a session at a given message index (or current point).

    Creates a new session and copies messages up to the branch point.

    Args:
        session_id: The session to fork from.
        at_message_index: Message index to branch at (None = copy all messages).
        title: Title for the new branch.

    Returns:
        New session ID.
    """
    new_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()

    conn = _get_conn()

    # Get messages from source session
    msgs = conn.execute(
        "SELECT role, content, agent, tool_name, tool_args, timestamp "
        "FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()

    # Determine branch point
    branch_point = at_message_index if at_message_index is not None else len(msgs)
    msgs_to_copy = msgs[:branch_point]

    if not title:
        title = f"Branch of {session_id}"

    # Create new session with parent reference
    conn.execute(
        "INSERT INTO sessions (id, title, created_at, updated_at, parent_session_id, branch_point) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (new_id, title, now, now, session_id, branch_point),
    )

    # Copy messages
    for m in msgs_to_copy:
        m_dict = dict(m)
        conn.execute(
            "INSERT INTO messages (session_id, role, content, agent, tool_name, tool_args, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id, m_dict["role"], m_dict["content"], m_dict["agent"],
             m_dict["tool_name"], m_dict["tool_args"], m_dict["timestamp"]),
        )

    conn.commit()
    conn.close()
    return new_id


def get_branches(session_id: str) -> list[dict]:
    """List all sessions branched from this session."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at, branch_point FROM sessions "
        "WHERE parent_session_id = ? ORDER BY created_at DESC",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_tree(session_id: str) -> dict:
    """Return the full branch tree: parent + children."""
    session = get_session(session_id)
    if not session:
        return {}

    parent_id = ""
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT parent_session_id FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        conn.close()
        parent_id = dict(row).get("parent_session_id", "") if row else ""
    except Exception:
        pass

    children = get_branches(session_id)
    return {
        "session": session,
        "parent_session_id": parent_id,
        "branches": children,
    }


# Initialize DB on import
init_db()
