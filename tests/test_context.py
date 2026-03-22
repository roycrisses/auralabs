"""Tests for context window management."""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from aura.brain.context import (
    estimate_tokens,
    estimate_message_tokens,
    trim_messages,
    get_context_usage,
)


def test_estimate_tokens():
    assert estimate_tokens("") == 1  # minimum 1
    assert estimate_tokens("hello world") > 0
    # ~11 chars / 3.5 = ~3 tokens
    assert estimate_tokens("hello world") == 3


def test_trim_keeps_system_and_recent():
    msgs = [
        SystemMessage(content="You are helpful."),
        HumanMessage(content="msg1"),
        AIMessage(content="resp1"),
        HumanMessage(content="msg2"),
        AIMessage(content="resp2"),
        HumanMessage(content="msg3"),
    ]

    # With a very small budget, should keep system + last message(s)
    trimmed = trim_messages(msgs, max_tokens=30)
    assert trimmed[0].content == "You are helpful."
    assert trimmed[-1].content == "msg3"
    assert len(trimmed) <= len(msgs)


def test_trim_no_op_when_fits():
    msgs = [
        SystemMessage(content="hi"),
        HumanMessage(content="hello"),
    ]
    trimmed = trim_messages(msgs, max_tokens=10000)
    assert len(trimmed) == 2


def test_get_context_usage():
    msgs = [HumanMessage(content="hello world")]
    usage = get_context_usage(msgs, agent_role="kernel")
    assert usage["estimated_tokens"] > 0
    assert usage["limit"] == 28000
    assert usage["message_count"] == 1
