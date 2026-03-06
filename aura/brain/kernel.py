"""Kernel agent — OS tasks, code execution, file operations."""

from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool

from aura.brain.context import trim_messages
from aura.brain.llm import get_llm
from aura.brain.tools import bind_agent_tools
from aura.models import AgentState, ToolCall

KERNEL_SYSTEM_PROMPT = """\
You are the Kernel agent for Aura, a desktop automation system running on Windows 11 (i5-10300H, GTX 1650, 16GB RAM).
You specialize in: code execution, scripting, file operations, system commands, debugging, and process management.

You have access to these tools:
- run_command: Execute a shell command and return stdout/stderr
- read_file: Read the contents of a file
- write_file: Write content to a file
- list_directory: List files in a directory
- screenshot: Capture a screenshot of the screen
- analyze_screenshot: Take a screenshot and analyze it with a vision model (useful for seeing what's happening)
- get_screen_size: Get the current screen resolution
- mouse_move: Move the mouse to specific x,y coordinates
- mouse_click: Click at a specific location or current position
- mouse_drag: Drag the mouse to a location
- mouse_scroll: Scroll the mouse wheel
- keyboard_type: Type text into the focused window
- keyboard_hotkey: Press a key combination (e.g. 'ctrl,c')
- open_application: Launch a Windows application by name (notepad, calculator, terminal, etc.) or path
- open_url: Open a URL in the default browser
- get_system_info: Get detailed OS, CPU, RAM info
- get_disk_info: Get disk partition usage
- get_network_info: Get network interface addresses and stats
- list_processes: List running processes sorted by CPU or memory
- send_notification: Send a Windows toast notification
- set_reminder: Set a timed reminder (triggers a notification)
- schedule_command: Schedule a shell command to run after a delay
- schedule_recurring_task: Schedule a recurring task
- list_reminders: List pending reminders and scheduled tasks
- cancel_reminder: Cancel a scheduled task by ID
- index_document: Index a file into the knowledge base for later retrieval
- delegate_to_agent: Delegate a sub-task to another agent (researcher or creator)
- remember_fact: Save a fact or preference to long-term memory
- recall_facts: Search long-term memory for relevant facts

When asked to interact with the desktop or apps, follow this loop:
1. Capture/Analyze screenshot to see state.
2. Calculate mouse coordinates or keyboard actions.
3. Perform action.
4. Verify by capturing/analyzing another screenshot.

Always explain what you're doing before using a tool. Be concise and helpful."""


# Tool definitions for LangChain bind_tools
@tool
def run_command(command: str, timeout: int = 30) -> str:
    """Execute a shell command and return stdout/stderr."""
    ...

@tool
def read_file(path: str) -> str:
    """Read the contents of a file at the given path."""
    ...

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file at the given path."""
    ...

@tool
def list_directory(path: str = ".") -> str:
    """List files and directories at the given path."""
    ...

@tool
def screenshot(region: str | None = None) -> str:
    """Capture a screenshot. Optional region as 'x,y,width,height'."""
    ...

@tool
def open_application(name: str, args: str = "") -> str:
    """Open a Windows application by name or path."""
    ...

@tool
def open_url(url: str) -> str:
    """Open a URL in the default web browser."""
    ...

@tool
def get_system_info() -> str:
    """Return detailed OS, CPU, and RAM information."""
    ...

@tool
def get_disk_info() -> str:
    """Return disk partition usage information."""
    ...

@tool
def get_network_info() -> str:
    """Return network interface addresses and connection stats."""
    ...

@tool
def list_processes(sort_by: str = "memory", limit: int = 15) -> str:
    """List running processes sorted by CPU or memory usage."""
    ...

@tool
def send_notification(title: str, message: str, duration: int = 5) -> str:
    """Send a Windows toast notification."""
    ...

@tool
def set_reminder(description: str, delay_minutes: int) -> str:
    """Set a timed reminder that triggers a notification."""
    ...

@tool
def schedule_command(description: str, command: str, delay_minutes: int) -> str:
    """Schedule a shell command to run after a delay in minutes."""
    ...

@tool
def schedule_recurring_task(description: str, interval_minutes: int, command: str = "") -> str:
    """Schedule a recurring task at a given interval in minutes."""
    ...

@tool
def list_reminders() -> str:
    """List all pending scheduled tasks and reminders."""
    ...

@tool
def cancel_reminder(task_id: str) -> str:
    """Cancel a scheduled task or reminder by ID."""
    ...

@tool
def index_document(path: str) -> str:
    """Index a file into the knowledge base for later retrieval."""
    ...

@tool
def delegate_to_agent(target_agent: str, task: str) -> str:
    """Delegate a sub-task to another agent (researcher or creator)."""
    ...

@tool
def remember_fact(content: str, category: str = "fact") -> str:
    """Save a fact or preference to long-term memory."""
    ...

@tool
def recall_facts(query: str, top_k: int = 5) -> str:
    """Search long-term memory for relevant facts and preferences."""
    ...


def _get_kernel_tools():
    from aura.body.desktop import (
        get_screen_size, mouse_move, mouse_click, mouse_drag, mouse_scroll,
        keyboard_type, keyboard_hotkey
    )
    from aura.body.vision import analyze_screenshot

    return [
        run_command, read_file, write_file, list_directory, screenshot,
        analyze_screenshot, get_screen_size,
        mouse_move, mouse_click, mouse_drag, mouse_scroll,
        keyboard_type, keyboard_hotkey,
        open_application, open_url,
        get_system_info, get_disk_info, get_network_info, list_processes,
        send_notification,
        set_reminder, schedule_command, schedule_recurring_task, list_reminders, cancel_reminder,
        index_document, delegate_to_agent, remember_fact, recall_facts,
    ]


KERNEL_TOOLS = _get_kernel_tools()


async def kernel_node(state: AgentState) -> dict:
    """LangGraph node: invoke the Kernel agent."""
    llm = get_llm("kernel", temperature=0.2, max_tokens=4096)
    llm_with_tools = bind_agent_tools(llm, KERNEL_TOOLS)

    messages = [SystemMessage(content=KERNEL_SYSTEM_PROMPT)] + state["messages"]
    messages = trim_messages(messages, agent_role="kernel")
    response = await llm_with_tools.ainvoke(messages)

    # Extract tool calls if present
    tool_calls = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            tool_calls.append(
                ToolCall(
                    tool_name=tc["name"],
                    call_id=tc.get("id", tc["name"]),
                    arguments=tc.get("args", {}),
                )
            )

    thinking = response.content if response.content else ""

    return {
        "messages": [response],
        "tool_calls": tool_calls,
        "thinking_log": [f"[Kernel] {thinking[:200]}"] if thinking else [],
    }
