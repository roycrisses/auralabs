"""Context window management — token counting and message pruning.

Prevents long conversations from exceeding the LLM's context limit by
trimming older messages while preserving the system prompt and recent turns.
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage, SystemMessage

# Approximate tokens-per-character ratio for English text.
# Conservative estimate: 1 token ≈ 3.5 chars.
CHARS_PER_TOKEN = 3.5

# Default context budgets per agent role (in tokens).
# Leave headroom for the response.
CONTEXT_LIMITS: dict[str, int] = {
    "kernel": 28_000,     # 32k model, keep 4k for response
    "researcher": 28_000,
    "creator": 28_000,
    "router": 800,        # Router only needs the latest message
}


def estimate_tokens(text: str) -> int:
    """Estimate token count from character length."""
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def estimate_message_tokens(msg: BaseMessage) -> int:
    """Estimate tokens for a single LangChain message (content + overhead)."""
    content = msg.content if isinstance(msg.content, str) else str(msg.content)
    # ~4 tokens overhead per message for role tags, etc.
    return estimate_tokens(content) + 4


def trim_messages(
    messages: list[BaseMessage],
    max_tokens: int | None = None,
    agent_role: str = "researcher",
) -> list[BaseMessage]:
    """Trim a message list to fit within the token budget.

    Strategy:
    1. Always keep the system message (first) and the latest user message (last).
    2. Keep as many recent messages as possible within the budget.
    3. If the middle is too long, drop oldest non-system messages first.
    """
    if max_tokens is None:
        max_tokens = CONTEXT_LIMITS.get(agent_role, 28_000)

    if not messages:
        return messages

    # Separate system messages from the rest
    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    if not other_msgs:
        return messages

    # Calculate system message cost
    system_cost = sum(estimate_message_tokens(m) for m in system_msgs)
    remaining_budget = max_tokens - system_cost

    if remaining_budget <= 0:
        # System prompt alone exceeds budget — just keep it + last message
        return system_msgs + other_msgs[-1:]

    # Greedily include messages from the end (most recent first)
    kept: list[BaseMessage] = []
    used = 0

    for msg in reversed(other_msgs):
        cost = estimate_message_tokens(msg)
        if used + cost <= remaining_budget:
            kept.append(msg)
            used += cost
        else:
            break

    kept.reverse()
    return system_msgs + kept


def get_context_usage(messages: list[BaseMessage], agent_role: str = "researcher") -> dict:
    """Return context window usage stats."""
    total = sum(estimate_message_tokens(m) for m in messages)
    limit = CONTEXT_LIMITS.get(agent_role, 28_000)
    return {
        "estimated_tokens": total,
        "limit": limit,
        "usage_percent": round(total / limit * 100, 1) if limit > 0 else 0,
        "message_count": len(messages),
    }
