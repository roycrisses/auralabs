"""Aura shared data models — Pydantic schemas and LangGraph state."""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    agent: str | None = None
    thinking: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolCall(BaseModel):
    tool_name: str
    call_id: str = ""  # LLM-assigned tool call ID for ToolMessage pairing
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    output: Any = None
    error: str | None = None


class RouterDecision(BaseModel):
    """Structured output from the router agent."""
    target_agent: Literal["kernel", "researcher", "creator"]
    reasoning: str


class DelegationRequest(BaseModel):
    """Request to delegate a sub-task to another agent."""
    target_agent: Literal["kernel", "researcher", "creator"]
    task: str


class AgentState(TypedDict):
    """LangGraph mutable state schema."""
    messages: Annotated[list, operator.add]
    current_agent: str
    tool_calls: list[ToolCall]
    tool_results: list[ToolResult]
    thinking_log: Annotated[list[str], operator.add]
    iteration: int
    delegation_depth: int
