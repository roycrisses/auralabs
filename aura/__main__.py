import logging
import os
import sys
from pathlib import Path

# Setup logging to file
if getattr(sys, 'frozen', False):
    # Running from bundled exe
    APP_DIR = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "AgentAura"
else:
    # Running from source
    APP_DIR = Path(__file__).parent.parent.resolve()

LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "aura.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE)),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("aura.startup")
logger.info("Aura starting up...")

import subprocess
import asyncio

# Global console window suppression for Windows
if sys.platform == "win32":
    # 1. Monkeypatch standard subprocess.Popen (used by most libraries)
    _orig_popen = subprocess.Popen
    def _patched_popen(*args, **kwargs):
        # Add CREATE_NO_WINDOW to suppress terminal flashes
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
        return _orig_popen(*args, **kwargs)
    subprocess.Popen = _patched_popen

    # 2. Monkeypatch asyncio subprocesses (used by MCP and others)
    _orig_exec = asyncio.create_subprocess_exec
    _orig_shell = asyncio.create_subprocess_shell

    async def _patched_exec(*args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
        return await _orig_exec(*args, **kwargs)

    async def _patched_shell(*args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
        return await _orig_shell(*args, **kwargs)

    asyncio.create_subprocess_exec = _patched_exec
    asyncio.create_subprocess_shell = _patched_shell

    # 3. Add flag to environment for scripts that might check it
    os.environ["AURA_CONSOLE_HIDDEN"] = "1"

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

    from aura.brain.graph import build_graph
    from aura.brain.memory import (
        auto_title,
        create_session,
        get_messages,
        messages_to_langchain,
        save_message,
        switch_session,
    )
    from aura.config import MODEL_REGISTRY

    console = Console()
    graph = build_graph()
    session_id = create_session()

    console.print(Panel("[bold cyan]Aura AI CLI[/]\n[italic]Your autonomous desktop companion[/]"))
    console.print(f"Session: [bold yellow]{session_id}[/]")
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
            "thought_trace": [],
            "delegation_depth": 0,
            "session_id": session_id
        }

        # Run the graph
        config = {"configurable": {"thread_id": session_id}}
        
        console.print("\n[bold blue]Aura thinking...[/]")
        
        try:
            for event in graph.stream(state, config, stream_mode="values"):
                if "messages" in event:
                    msg = event["messages"][-1]
                    # If it's the assistant's final response, print it
                    if hasattr(msg, "content") and msg.type == "ai" and not msg.tool_calls:
                        console.print(Panel(Markdown(msg.content), title="Aura", border_style="cyan"))
                        save_message(session_id, "assistant", msg.content)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")
            logger.error(f"Graph execution error: {e}", exc_info=True)


def run_gui():
    """Start the graphical interactive layer (Future work)."""
    print("GUI mode is not yet implemented. Please use --cli.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Aura — The Autonomous Desktop Agent")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--gui", action="store_true", help="Run in GUI mode")
    parser.add_argument("--mcp", action="store_true", help="List loaded MCP servers")
    parser.add_argument("--byok", nargs=4, metavar=("ROLE", "URL", "KEY", "MODEL"), 
                        help="Configure Bring Your Own Key override")
    
    args = parser.parse_args()

    if args.byok:
        from aura.config import set_byok
        role, url, key, model = args.byok
        set_byok(role, url, key, model)
        print(f"BYOK configured for {role}.")
        return

    if args.mcp:
        print("Loaded MCP Servers:")
        if not _mcp_results:
            print("  None.")
        for name, success in _mcp_results.items():
            status = "OK" if success else "FAILED"
            print(f"  {name}: {status}")
        return

    # Default to CLI if no mode is specified yet
    if args.gui:
        run_gui()
    else:
        run_cli()


if __name__ == "__main__":
    main()
