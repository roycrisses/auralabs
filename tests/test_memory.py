"""Tests for conversation memory."""

import os
import tempfile
from unittest.mock import patch

from aura.brain.memory import (
    create_session,
    save_message,
    get_messages,
    get_message_count,
    list_sessions,
    delete_session,
    auto_title,
    messages_to_langchain,
)


def test_create_and_list_session():
    sid = create_session("test session")
    sessions = list_sessions()
    ids = [s["id"] for s in sessions]
    assert sid in ids


def test_save_and_get_messages():
    sid = create_session("msg test")
    save_message(sid, "user", "hello")
    save_message(sid, "assistant", "hi there", agent="researcher")

    msgs = get_messages(sid)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["agent"] == "researcher"


def test_message_count():
    sid = create_session()
    assert get_message_count(sid) == 0
    save_message(sid, "user", "test")
    assert get_message_count(sid) == 1


def test_delete_session():
    sid = create_session("to delete")
    save_message(sid, "user", "bye")
    delete_session(sid)
    assert get_messages(sid) == []


def test_auto_title():
    sid = create_session()
    auto_title(sid, "What is the weather in Tokyo today?")
    sessions = list_sessions()
    session = next(s for s in sessions if s["id"] == sid)
    assert "weather" in session["title"].lower()


def test_messages_to_langchain():
    sid = create_session()
    save_message(sid, "user", "hello")
    save_message(sid, "assistant", "world")
    msgs = get_messages(sid)
    lc_msgs = messages_to_langchain(msgs)
    assert len(lc_msgs) == 2
    assert lc_msgs[0].content == "hello"
    assert lc_msgs[1].content == "world"
