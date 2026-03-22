"""Long-term memory tools — remember and recall facts across sessions."""

from __future__ import annotations

from aura.body.registry import register_tool


@register_tool("remember_fact")
def remember_fact(content: str, category: str = "fact") -> str:
    """Save a fact or preference to long-term memory for future sessions.

    Args:
        content: The fact or preference to remember.
        category: One of: preference, fact, instruction, person, project.
    """
    from aura.brain.long_memory import save_fact

    valid = ("preference", "fact", "instruction", "person", "project")
    if category not in valid:
        category = "fact"
    fact_id = save_fact(category, content)
    return f"Remembered [{category}]: {content} (id: {fact_id})"


@register_tool("recall_facts")
def recall_facts(query: str, top_k: int = 5) -> str:
    """Search long-term memory for relevant facts and preferences.

    Args:
        query: Search query to find matching facts.
        top_k: Maximum number of results.
    """
    from aura.brain.long_memory import search_facts

    facts = search_facts(query, top_k=top_k)
    if not facts:
        return "No matching facts found in long-term memory."
    lines = ["Recalled facts:"]
    for f in facts:
        lines.append(f"  [{f['category']}] {f['content']} (id: {f['id']})")
    return "\n".join(lines)
