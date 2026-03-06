"""API routes — REST and WebSocket endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from aura.body.hardware import get_system_stats
from aura.body.registry import list_tools
from aura.brain.memory import (
    auto_title,
    create_session,
    delete_session,
    get_message_count,
    get_messages,
    list_sessions,
    messages_to_langchain,
    save_message,
)

router = APIRouter()

# Lazy graph compilation (compiled once on first request)
_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        from aura.brain.graph import build_graph
        _compiled_graph = build_graph()
    return _compiled_graph


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    attachments: list[str] = []


class ChatResponse(BaseModel):
    response: str
    agent: str
    session_id: str
    thinking_log: list[str]
@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message and get a synchronous response."""
    graph = _get_graph()

    # Resolve or create session
    session_id = req.session_id or create_session()

    # Prepend attachment context if files are attached
    message = req.message
    if req.attachments:
        from aura.server.upload import get_attachment_context
        attachment_ctx = get_attachment_context(req.attachments)
        if attachment_ctx:
            message = f"{attachment_ctx}\n\n{message}"
    save_message(session_id, "user", message)
    if get_message_count(session_id) == 1:
        auto_title(session_id, req.message)

    # Load history for context
    history = messages_to_langchain(get_messages(session_id, limit=50))

    initial_state = {
        "messages": history,
        "current_agent": "",
        "tool_calls": [],
        "tool_results": [],
        "thinking_log": [],
        "iteration": 0,
        "delegation_depth": 0,
    }

    # Use ainvoke for async graph
    result = await graph.ainvoke(initial_state)

    # Extract the last AI message
    response_text = ""
    agent_name = result.get("current_agent", "unknown")
    for msg in reversed(result["messages"]):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            response_text = msg.content
            break

    if not response_text:
        response_text = "(No response generated)"

    save_message(session_id, "assistant", response_text, agent=agent_name)

    return ChatResponse(
        response=response_text,
        agent=agent_name,
        session_id=session_id,
        thinking_log=result.get("thinking_log", []),
    )


@router.websocket("/chat/stream")
async def chat_stream(ws: WebSocket):
    """WebSocket endpoint for streaming chat with thinking events and tokens."""
    from aura.brain.run import run_graph
    await ws.accept()

    # Per-connection session
    session_id: str | None = None

    try:
        while True:
            data = await ws.receive_text()
            payload = json.loads(data)
            message = payload.get("content", payload.get("message", ""))

            if not message:
                await ws.send_json({"type": "error", "content": "Empty message"})
                continue

            # Resolve session
            if payload.get("session_id"):
                session_id = payload["session_id"]
            if not session_id:
                session_id = create_session()
                await ws.send_json({"type": "session", "session_id": session_id})

            save_message(session_id, "user", message)
            if get_message_count(session_id) == 1:
                auto_title(session_id, message)

            # Load history
            history = messages_to_langchain(get_messages(session_id, limit=50))
            
            try:
                current_agent = "router"
                full_response = ""

                # Delegate to the specialized run_graph utility
                async for event in run_graph(message, history, session_id):
                    # Forward events to the websocket
                    await ws.send_json(event)
                    
                    # Accumulate response for memory
                    if event["type"] == "token":
                        full_response += event["content"]
                    elif event["type"] == "route":
                        current_agent = event["agent"]
                    elif event["type"] == "thinking" and "agent" in event:
                        current_agent = event["agent"]

                # Save assistant response to memory once done
                if full_response:
                    save_message(session_id, "assistant", full_response, agent=current_agent)

                await ws.send_json({"type": "done", "session_id": session_id})

            except Exception as e:
                import traceback
                traceback.print_exc()
                await ws.send_json({
                    "type": "error",
                    "content": f"{type(e).__name__}: {e}",
                })

    except WebSocketDisconnect:
        pass


# --- Session endpoints ---

@router.get("/sessions")
async def sessions_list(limit: int = 20):
    """List recent conversation sessions."""
    return list_sessions(limit)


@router.get("/sessions/{session_id}/messages")
async def session_messages(session_id: str, limit: int = 100):
    """Get messages for a session."""
    return get_messages(session_id, limit)


@router.delete("/sessions/{session_id}")
async def session_delete(session_id: str):
    """Delete a session and its messages."""
    delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


@router.get("/sessions/{session_id}/export")
async def session_export(session_id: str, fmt: str = "md"):
    """Export a session as markdown or JSON."""
    from fastapi.responses import PlainTextResponse

    msgs = get_messages(session_id, limit=500)
    if not msgs:
        return PlainTextResponse("(no messages)", media_type="text/plain")

    if fmt == "json":
        import json as json_mod
        return PlainTextResponse(
            json_mod.dumps(msgs, indent=2, ensure_ascii=False),
            media_type="application/json",
        )

    # Markdown
    lines = [f"# Aura Session {session_id}\n"]
    for m in msgs:
        role = m["role"].capitalize()
        agent = f" ({m['agent']})" if m.get("agent") else ""
        lines.append(f"### {role}{agent}\n{m['content']}\n")
    return PlainTextResponse("\n".join(lines), media_type="text/markdown")


# --- Branching endpoints ---

class BranchRequest(BaseModel):
    at_message: int | None = None
    title: str = ""


@router.post("/sessions/{session_id}/branch")
async def session_branch(session_id: str, req: BranchRequest):
    """Fork a session at a given point."""
    from aura.brain.memory import fork_session
    new_id = fork_session(session_id, at_message_index=req.at_message, title=req.title)
    return {"session_id": new_id, "parent_session_id": session_id}


@router.get("/sessions/{session_id}/branches")
async def session_branches(session_id: str):
    """List branches of a session."""
    from aura.brain.memory import get_branches
    return get_branches(session_id)


# --- Utility endpoints ---

@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0", "tools": list_tools()}


@router.get("/hardware")
async def hardware():
    """Return current hardware stats."""
    return get_system_stats()


@router.get("/agents")
async def agents():
    """List available agents."""
    from aura.config import MODEL_REGISTRY
    return {
        name: {"model": model, "status": "ready"}
        for name, model in MODEL_REGISTRY.items()
    }


# --- MCP management endpoints ---

class MCPServerRequest(BaseModel):
    name: str
    command: str
    args: list[str] = []
    env: dict[str, str] = {}


@router.get("/mcp/servers")
async def mcp_list_servers():
    """List configured MCP servers and their tools."""
    from aura.mcp.config import load_mcp_config
    from aura.mcp.client import list_connected
    configs = load_mcp_config()
    connected = list_connected()
    result = []
    for cfg in configs:
        name = cfg["name"]
        result.append({
            **cfg,
            "connected": name in connected,
            "tools": connected.get(name, []),
        })
    return result


@router.post("/mcp/servers")
async def mcp_add_server(req: MCPServerRequest):
    """Add and connect to a new MCP server."""
    from aura.mcp.config import add_server
    from aura.mcp.client import connect_server
    entry = add_server(req.name, req.command, req.args, req.env)
    tools = connect_server(req.name, req.command, req.args, req.env)
    return {"server": entry, "tools": tools}


@router.delete("/mcp/servers/{name}")
async def mcp_remove_server(name: str):
    """Remove an MCP server configuration."""
    from aura.mcp.config import remove_server
    from aura.mcp.client import disconnect_server
    disconnect_server(name)
    removed = remove_server(name)
    return {"removed": removed, "name": name}


class FactRequest(BaseModel):
    content: str
    category: str = "fact"


@router.get("/memory/facts")
async def memory_list_facts(category: str | None = None):
    """List all stored facts."""
    from aura.brain.long_memory import list_facts
    return list_facts(category)


@router.post("/memory/facts")
async def memory_save_fact(req: FactRequest):
    """Save a fact to long-term memory."""
    from aura.brain.long_memory import save_fact
    fact_id = save_fact(req.category, req.content)
    return {"id": fact_id, "category": req.category, "content": req.content}


@router.delete("/memory/facts/{fact_id}")
async def memory_delete_fact(fact_id: str):
    """Delete a fact from long-term memory."""
    from aura.brain.long_memory import delete_fact
    deleted = delete_fact(fact_id)
    return {"deleted": deleted, "id": fact_id}


@router.get("/memory/search")
async def memory_search(query: str, top_k: int = 5):
    """Search long-term memory."""
    from aura.brain.long_memory import search_facts
    return search_facts(query, top_k)


@router.post("/mcp/servers/{name}/reconnect")
async def mcp_reconnect_server(name: str):
    """Reconnect to an MCP server."""
    from aura.mcp.config import get_server
    from aura.mcp.client import disconnect_server, connect_server
    cfg = get_server(name)
    if not cfg:
        return {"error": f"Server '{name}' not found"}
    disconnect_server(name)
    tools = connect_server(name, cfg["command"], cfg.get("args", []), cfg.get("env", {}))
    return {"name": name, "tools": tools}
