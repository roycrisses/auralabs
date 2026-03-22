"""Long-term memory — persistent facts, preferences, and user profile.

Stores facts in SQLite with categories and full-text search.
Auto-extracts key facts from conversations on session end.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(r"D:\automation\aura\.cache\memory.db")

_initialized = False


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_long_memory() -> None:
    """Create the facts table if it doesn't exist."""
    global _initialized
    if _initialized:
        return
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS facts (
            id              TEXT PRIMARY KEY,
            category        TEXT NOT NULL DEFAULT 'fact',
            content         TEXT NOT NULL,
            source_session  TEXT DEFAULT '',
            confidence      REAL DEFAULT 1.0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
    """)
    conn.commit()
    conn.close()
    _initialized = True


def save_fact(
    category: str,
    content: str,
    source_session: str = "",
    confidence: float = 1.0,
) -> str:
    """Store a fact. Returns fact ID.

    Categories: preference, fact, instruction, person, project
    """
    init_long_memory()
    fact_id = uuid.uuid4().hex[:10]
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO facts (id, category, content, source_session, confidence, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fact_id, category, content, source_session, confidence, now, now),
    )
    conn.commit()
    conn.close()
    return fact_id


def search_facts(query: str, top_k: int = 5) -> list[dict]:
    """Search facts using keyword matching (LIKE).

    Returns list of matching facts sorted by relevance.
    """
    init_long_memory()
    conn = _get_conn()
    # Simple keyword search using LIKE on content
    keywords = query.lower().split()
    if not keywords:
        return []

    # Build a WHERE clause that matches any keyword
    conditions = " OR ".join(["LOWER(content) LIKE ?" for _ in keywords])
    params = [f"%{kw}%" for kw in keywords]

    rows = conn.execute(
        f"SELECT * FROM facts WHERE {conditions} ORDER BY updated_at DESC LIMIT ?",
        params + [top_k],
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_facts(category: str | None = None) -> list[dict]:
    """List all facts, optionally filtered by category."""
    init_long_memory()
    conn = _get_conn()
    if category:
        rows = conn.execute(
            "SELECT * FROM facts WHERE category = ? ORDER BY updated_at DESC", (category,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM facts ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_fact(fact_id: str) -> bool:
    """Delete a fact by ID."""
    init_long_memory()
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM facts WHERE id = ?", (fact_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def get_relevant_context(user_message: str, top_k: int = 3) -> str:
    """Search facts matching the user's message and return as context string.

    Called before each agent invocation to inject relevant long-term context.
    """
    init_long_memory()
    facts = search_facts(user_message, top_k=top_k)
    if not facts:
        return ""

    lines = ["[Long-term memory context]"]
    for f in facts:
        lines.append(f"- [{f['category']}] {f['content']}")
    return "\n".join(lines)


def extract_facts_from_messages(messages: list[dict], session_id: str = "") -> list[str]:
    """Extract key facts from conversation messages using simple heuristics.

    Looks for patterns like "I prefer...", "remember that...", "my name is...", etc.
    Called on session end or after N messages.
    """
    import re

    patterns = [
        (r"(?:i prefer|i like|i want|my preference is)\s+(.+)", "preference"),
        (r"(?:remember that|note that|keep in mind)\s+(.+)", "instruction"),
        (r"(?:my name is|i am|i'm)\s+(\w[\w\s]{1,30})", "person"),
        (r"(?:i'm working on|my project is|the project)\s+(.+)", "project"),
    ]

    extracted = []
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "").lower()
        for pattern, category in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                fact_content = match.strip().rstrip(".")
                if len(fact_content) > 5:  # Skip very short matches
                    fact_id = save_fact(category, fact_content, source_session=session_id)
                    extracted.append(f"{category}: {fact_content}")

    return extracted


# Initialize on import
init_long_memory()
