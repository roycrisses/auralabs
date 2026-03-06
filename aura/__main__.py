"""Aura CLI entry point — run with `python -m aura`."""

from __future__ import annotations

import sys

# Import body modules to trigger tool registration
import aura.body.clipboard
import aura.body.desktop
import aura.body.filesystem
import aura.body.process
import aura.body.web
import aura.body.apps
import aura.body.sysinfo
import aura.body.notify
import aura.body.schedule
import aura.body.workflow
import aura.body.vision
import aura.body.voice
import aura.body.knowledge
import aura.body.delegate
import aura.body.memory_tools
import aura.body.trigger_tools

# Load user plugins
from aura.plugins import load_all_plugins as _load_plugins
_plugin_results = _load_plugins()

# Load configured MCP servers
from aura.plugins import load_mcp_servers as _load_mcp
_mcp_results = _load_mcp()


def run_cli():
    """Interactive CLI loop with rich terminal output."""
    from langchain_core.messages import HumanMessage
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text

    from aura.brain.graph import build_graph
    from aura.brain.memory import (
        auto_title,
        create_session,
        get_messages,
        messages_to_langchain,
        save_message,
    )
    from aura.body.confirm import format_confirmation_prompt
    from aura.body.registry import set_confirm_callback
    from aura.config import get_settings

    console = Console()

    # Set up CLI confirmation callback for dangerous tools
    def _cli_confirm(tool_name: str, arguments: dict) -> bool:
        prompt = format_confirmation_prompt(tool_name, arguments)
        try:
            answer = input(f"  \u26a0\ufe0f  {prompt}").strip().lower()
            return answer in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    set_confirm_callback(_cli_confirm)

    # Validate config on startup
    try:
        settings = get_settings()
        console.print(
            f"[bold cyan]Aura v0.1.0[/] connected to NIM: {settings.nvidia_base_url}"
        )
        console.print(f"[dim]API keys loaded: {len(settings.nvidia_api_keys)}[/]")
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to load config: {e}")
        console.print('Populate D:\\automation\\AI keys and tetails.txt with your API keys.')
        sys.exit(1)

    # Start background scheduler
    from aura.brain.scheduler import start_scheduler
    start_scheduler()

    # Start event triggers (file watchers, etc.)
    from aura.brain.triggers import start_triggers
    start_triggers()

    console.print("[dim]Compiling agent graph...[/]")
    graph = build_graph()

    # Start a new conversation session
    session_id = create_session()
    console.print(f"[dim]Session: {session_id}[/]")
    console.print("[bold green]Ready.[/] Type [bold]/help[/] for commands, [bold]quit[/] to exit.\n")

    while True:
        try:
            user_input = console.input("[bold white]You:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold cyan]Goodbye![/]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("[bold cyan]Goodbye![/]")
            break

        # Handle slash commands
        if user_input.startswith("/"):
            from aura.commands import handle_command
            handled, output, session_id = handle_command(user_input, session_id)
            if handled:
                if output:
                    console.print(f"\n{output}\n")
                continue

        # Save user message & auto-title on first message
        save_message(session_id, "user", user_input)
        if get_messages(session_id, limit=1):
            auto_title(session_id, user_input)

        # Load conversation history for context
        history = messages_to_langchain(get_messages(session_id, limit=50))

        # Build initial state with history
        state = {
            "messages": history[:-1] + [HumanMessage(content=user_input)],
            "current_agent": "",
            "tool_calls": [],
            "tool_results": [],
            "thinking_log": [],
            "iteration": 0,
        }

        try:
            # Stream execution — collect all messages and state from events
            all_messages = []
            current_agent = "?"

            for event in graph.stream(state, stream_mode="updates"):
                for node_name, update in event.items():
                    for thought in update.get("thinking_log", []):
                        console.print(f"  [dim italic]{thought}[/]")
                    for tc in update.get("tool_calls", []):
                        console.print(
                            f"  [yellow]\u2699 {tc.tool_name}[/]([dim]{tc.arguments}[/])"
                        )
                    for tr in update.get("tool_results", []):
                        color = "green" if tr.success else "red"
                        console.print(
                            f"  [{color}]\u2192 {tr.tool_name}:[/] {str(tr.output)[:200]}"
                        )
                    if update.get("current_agent"):
                        current_agent = update["current_agent"]
                    all_messages.extend(update.get("messages", []))

            # Extract the last AI message from the streamed events
            response_text = None
            for msg in reversed(all_messages):
                if hasattr(msg, "type") and msg.type == "ai" and msg.content:
                    response_text = msg.content
                    break

            if response_text:
                console.print()
                console.print(
                    Panel(
                        Markdown(response_text),
                        title=f"[bold cyan]Aura[/] [dim]({current_agent})[/]",
                        border_style="cyan",
                        padding=(1, 2),
                    )
                )
                console.print()
                save_message(session_id, "assistant", response_text, agent=current_agent)
            else:
                console.print("\n[dim]Aura: (no response)[/]\n")

        except Exception as e:
            console.print(f"\n[bold red]ERROR:[/] {type(e).__name__}: {e}\n")


def run_server():
    """Start the FastAPI server."""
    from aura.server.app import run_server as _run
    _run()


def run_tray():
    """Start Aura as a system tray application."""
    from aura.service.tray import run_tray as _run
    _run()


if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    elif "--mcp-server" in sys.argv:
        from aura.mcp.server import run_mcp_server
        run_mcp_server()
    elif "--tray" in sys.argv:
        run_tray()
    elif "--startup" in sys.argv:
        from aura.service.startup import add_to_startup
        print(add_to_startup())
    elif "--no-startup" in sys.argv:
        from aura.service.startup import remove_from_startup
        print(remove_from_startup())
    else:
        run_cli()
