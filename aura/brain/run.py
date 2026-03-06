from __future__ import annotations

import json
from typing import AsyncGenerator

from aura.brain.graph import build_graph
from aura.models import AgentState


_compiled_graph = None

async def run_graph(message: str, history: list, session_id: str) -> AsyncGenerator[dict, None]:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    graph = _compiled_graph

    state: AgentState = {
        "messages": history,
        "current_agent": "",
        "tool_calls": [],
        "tool_results": [],
        "thinking_log": [],
        "iteration": 0,
        "delegation_depth": 0,
    }
    # Yield immediate feedback
    yield {"type": "thinking", "content": "Analyzing request...", "agent": "aura"}
    
    # We use astream_events to capture granular updates
    # Note: ensure LangChain components are using streaming=True where needed
    async for event in graph.astream_events(state, version="v2"):
        kind = event["event"]

        # 1. Thinking / Updates
        if kind == "on_chain_stream":
            data = event["data"].get("chunk")
            if isinstance(data, dict):
                # Node provided some updates (e.g. thinking_log)
                if "thinking_log" in data and data["thinking_log"]:
                    agent = data.get("current_agent", "aura")
                    for item in data["thinking_log"]:
                        yield {"type": "thinking", "content": item, "agent": agent}
                
                if "current_agent" in data and data["current_agent"]:
                    yield {"type": "route", "agent": data["current_agent"]}

        # 2. Tool Calls (Detected from chat model output)
        elif kind == "on_chat_model_end":
            output = event["data"].get("output")
            if output and hasattr(output, "tool_calls") and output.tool_calls:
                for tc in output.tool_calls:
                    yield {
                        "type": "tool_call",
                        "tool": tc["name"],
                        "args": tc["args"]
                    }

        # 3. Tool Execution Ends
        elif kind == "on_tool_end":
            name = event.get("name")
            output = event["data"].get("output")
            yield {
                "type": "tool_result",
                "tool": name,
                "success": True, # Assume success if no error field
                "output": str(output)
            }

        # 4. Response Tokens
        elif kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content"):
                yield {"type": "token", "content": chunk.content}
