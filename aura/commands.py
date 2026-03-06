"""Slash commands — special commands prefixed with / for CLI and WebSocket.

Returns (handled: bool, output: str | None).
If handled is True, the command was processed and output should be displayed.
If handled is False, the input should be passed to the AI agent as usual.
"""

from __future__ import annotations

from aura.body.audit import get_recent_logs
from aura.body.registry import list_tools
from aura.brain.memory import (
    create_session,
    get_messages,
    list_sessions,
    delete_session,
)


def handle_command(text: str, session_id: str) -> tuple[bool, str | None, str]:
    """Process a slash command.

    Returns:
        (handled, output, session_id)
        - handled: True if the command was recognized
        - output: text to display (or None)
        - session_id: potentially updated session ID (for /new)
    """
    parts = text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        return True, _help_text(), session_id

    if cmd == "/clear":
        return True, "[Cleared thinking log and tool events]", session_id

    if cmd == "/tools":
        tools = list_tools()
        lines = [f"Registered tools ({len(tools)}):"]
        for t in sorted(tools):
            lines.append(f"  - {t}")
        return True, "\n".join(lines), session_id

    if cmd == "/agents":
        from aura.config import MODEL_REGISTRY
        lines = ["Available agents:"]
        for name, model in MODEL_REGISTRY.items():
            lines.append(f"  {name}: {model}")
        return True, "\n".join(lines), session_id

    if cmd == "/history":
        msgs = get_messages(session_id, limit=30)
        if not msgs:
            return True, "(no messages in this session)", session_id
        lines = []
        for m in msgs:
            role = m["role"].upper()
            agent = f" [{m['agent']}]" if m.get("agent") else ""
            content = m["content"][:120]
            lines.append(f"  {role}{agent}: {content}")
        return True, "\n".join(lines), session_id

    if cmd == "/sessions":
        sessions = list_sessions(limit=10)
        if not sessions:
            return True, "(no sessions)", session_id
        lines = ["Recent sessions:"]
        for s in sessions:
            marker = " <--" if s["id"] == session_id else ""
            lines.append(f"  {s['id']}  {s.get('title', '(untitled)')}  {s['updated_at']}{marker}")
        return True, "\n".join(lines), session_id

    if cmd == "/new":
        new_id = create_session(title=arg)
        return True, f"[New session: {new_id}]", new_id

    if cmd == "/load":
        if not arg:
            return True, "Usage: /load <session_id>", session_id
        msgs = get_messages(arg, limit=1)
        if msgs:
            return True, f"[Loaded session: {arg}]", arg
        return True, f"Session not found: {arg}", session_id

    if cmd == "/delete":
        if not arg:
            return True, "Usage: /delete <session_id>", session_id
        delete_session(arg)
        return True, f"[Deleted session: {arg}]", session_id

    if cmd == "/audit":
        logs = get_recent_logs(limit=15)
        if not logs:
            return True, "(no audit entries)", session_id
        lines = ["Recent tool executions:"]
        for entry in logs:
            status = "OK" if entry.get("success") else "FAIL"
            lines.append(f"  [{entry['timestamp'][:19]}] {entry['tool']} -> {status}")
        return True, "\n".join(lines), session_id

    if cmd == "/export":
        return True, _export_session(session_id, fmt=arg or "md"), session_id

    if cmd == "/triggers":
        from aura.brain.triggers import list_triggers
        triggers = list_triggers()
        if not triggers:
            return True, "No triggers configured. Use create_trigger tool to add one.", session_id
        lines = [f"Triggers ({len(triggers)}):"]
        for t in triggers:
            status = "enabled" if t.get("enabled") else "disabled"
            lines.append(f"  [{t['id']}] {t['type']} ({status}) — {t.get('workflow_name', '(none)')}")
        return True, "\n".join(lines), session_id

    if cmd == "/mcp":
        return True, _mcp_command(arg), session_id

    if cmd == "/knowledge":
        return True, _knowledge_command(), session_id

    if cmd == "/remember":
        if not arg:
            return True, "Usage: /remember <text>", session_id
        from aura.brain.long_memory import save_fact
        fact_id = save_fact("instruction", arg, source_session=session_id)
        return True, f"Remembered: {arg} (id: {fact_id})", session_id

    if cmd == "/forget":
        if not arg:
            return True, "Usage: /forget <fact_id>", session_id
        from aura.brain.long_memory import delete_fact
        deleted = delete_fact(arg)
        return True, f"Deleted fact {arg}." if deleted else f"Fact {arg} not found.", session_id

    if cmd == "/branch":
        return True, _branch_command(arg, session_id), session_id

    if cmd == "/branches":
        from aura.brain.memory import get_branches
        branches = get_branches(session_id)
        if not branches:
            return True, "No branches for this session.", session_id
        lines = [f"Branches of session {session_id}:"]
        for b in branches:
            lines.append(f"  {b['id']}  {b.get('title', '(untitled)')}  (branched at msg {b.get('branch_point', '?')})")
        return True, "\n".join(lines), session_id

    if cmd == "/facts":
        from aura.brain.long_memory import list_facts
        facts = list_facts()
        if not facts:
            return True, "No stored facts. Use /remember <text> to add one.", session_id
        lines = [f"Stored facts ({len(facts)}):"]
        for f in facts:
            lines.append(f"  [{f['id']}] ({f['category']}) {f['content']}")
        return True, "\n".join(lines), session_id

    # Unknown command
    if text.startswith("/"):
        return True, f"Unknown command: {cmd}. Type /help for available commands.", session_id

    return False, None, session_id


def _help_text() -> str:
    return """Available commands:
  /help             Show this help message
  /clear            Clear thinking log and tool events
  /tools            List all registered tools
  /agents           List available AI agents and their models
  /history          Show conversation history for this session
  /sessions         List recent conversation sessions
  /new [title]      Start a new conversation session
  /load <id>        Load a previous session by ID
  /delete <id>      Delete a session
  /audit            Show recent tool execution audit log
  /export [md|json] Export current session (default: markdown)
  /mcp              List connected MCP servers and tools
  /mcp add <name> <command>  Add an MCP server
  /mcp remove <name>         Remove an MCP server
  /branch [title]   Fork current session at current point
  /branch at <n>    Fork at specific message index
  /branches         List branches of current session
  /knowledge        List indexed documents and stats
  /remember <text>  Save a fact to long-term memory
  /forget <id>      Delete a stored fact
  /facts            List all stored facts
  /triggers         List active triggers"""


def _branch_command(arg: str, session_id: str) -> str:
    """Handle /branch command."""
    from aura.brain.memory import fork_session

    parts = arg.strip().split(maxsplit=2)
    if parts and parts[0] == "at":
        if len(parts) < 2:
            return "Usage: /branch at <msg_index> [title]"
        try:
            idx = int(parts[1])
        except ValueError:
            return "Message index must be a number."
        title = parts[2] if len(parts) > 2 else ""
        new_id = fork_session(session_id, at_message_index=idx, title=title)
    else:
        title = arg.strip()
        new_id = fork_session(session_id, title=title)

    return f"Branched session: {new_id}. Use /load {new_id} to switch to it."


def _knowledge_command() -> str:
    """Handle /knowledge command."""
    from aura.brain.rag import list_indexed
    docs = list_indexed()
    if not docs:
        return "No documents indexed. Use the index_document tool to add files."
    total_chunks = sum(d["chunks"] for d in docs)
    lines = [f"Knowledge base: {len(docs)} documents, {total_chunks} chunks"]
    for d in docs:
        lines.append(f"  {d['path']} ({d['chunks']} chunks)")
    return "\n".join(lines)


def _mcp_command(arg: str) -> str:
    """Handle /mcp subcommands."""
    parts = arg.strip().split(maxsplit=2)
    subcmd = parts[0] if parts else ""

    if subcmd == "add":
        if len(parts) < 3:
            return "Usage: /mcp add <name> <command>"
        name, command = parts[1], parts[2]
        try:
            from aura.mcp.config import add_server
            from aura.mcp.client import connect_server
            add_server(name, command)
            tools = connect_server(name, command)
            return f"Added MCP server '{name}'. Registered {len(tools)} tools: {', '.join(tools) if tools else '(none)'}"
        except ValueError as e:
            return str(e)

    if subcmd == "remove":
        if len(parts) < 2:
            return "Usage: /mcp remove <name>"
        name = parts[1]
        from aura.mcp.config import remove_server
        from aura.mcp.client import disconnect_server
        disconnect_server(name)
        removed = remove_server(name)
        return f"Removed MCP server '{name}'." if removed else f"MCP server '{name}' not found."

    # Default: list connected servers
    from aura.mcp.client import list_connected
    connected = list_connected()
    if not connected:
        return "No MCP servers connected. Use /mcp add <name> <command> to add one."
    lines = ["Connected MCP servers:"]
    for name, tools in connected.items():
        lines.append(f"  {name}: {len(tools)} tools")
        for t in tools:
            lines.append(f"    - {t}")
    return "\n".join(lines)


def _export_session(session_id: str, fmt: str = "md") -> str:
    """Export session messages as markdown or JSON."""
    import json as json_mod
    msgs = get_messages(session_id, limit=500)
    if not msgs:
        return "(no messages to export)"

    if fmt == "json":
        return json_mod.dumps(msgs, indent=2, ensure_ascii=False)

    # Markdown format
    lines = [f"# Aura Session {session_id}\n"]
    for m in msgs:
        role = m["role"].capitalize()
        agent = f" ({m['agent']})" if m.get("agent") else ""
        lines.append(f"### {role}{agent}\n{m['content']}\n")
    return "\n".join(lines)
