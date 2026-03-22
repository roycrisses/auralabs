"""Creator agent — content generation, writing, creative tasks."""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from aura.brain.context import trim_messages
from aura.brain.llm import get_llm
from aura.brain.tools import bind_agent_tools
from aura.models import AgentState, ToolCall

CREATOR_SYSTEM_PROMPT = """\
You are the Creator agent for Aura, a desktop automation system.
You specialize in: content generation, creative writing, blog posts, emails, document drafting, and UI design.

You have access to these tools:
- write_file: Save generated content to a file
- clipboard_write: Copy content to the clipboard
- web_search: Search the web for inspiration or reference material
- send_notification: Notify the user when a long task is complete
- delegate_to_agent: Delegate a sub-task to another agent (kernel or researcher)
- recall_facts: Search long-term memory for relevant facts and preferences

You may also have access to MCP (Model Context Protocol) tools from external servers.
These tools are prefixed with 'mcp_' and work like any other tool.

Be creative, articulate, and produce high-quality output. Format with markdown when appropriate."""


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file at the given path."""
    ...

@tool
def clipboard_write(text: str) -> str:
    """Copy text to the system clipboard."""
    ...

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for reference material or inspiration."""
    ...

@tool
def send_notification(title: str, message: str, duration: int = 5) -> str:
    """Send a Windows toast notification to alert the user."""
    ...

@tool
def delegate_to_agent(target_agent: str, task: str) -> str:
    """Delegate a sub-task to another agent (kernel or researcher)."""
    ...

@tool
def recall_facts(query: str, top_k: int = 5) -> str:
    """Search long-term memory for relevant facts and preferences."""
    ...


CREATOR_TOOLS = [write_file, clipboard_write, web_search, send_notification, delegate_to_agent, recall_facts]


async def creator_node(state: AgentState) -> dict:
    """LangGraph node: invoke the Creator agent."""
    llm = get_llm("creator", temperature=0.7, max_tokens=8192)
    llm_with_tools = bind_agent_tools(llm, CREATOR_TOOLS)

    messages = [SystemMessage(content=CREATOR_SYSTEM_PROMPT)] + state["messages"]
    messages = trim_messages(messages, agent_role="creator")
    # Wrap in async call
    response = await llm_with_tools.ainvoke(messages)

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
        "thinking_log": [f"[Creator] {thinking[:200]}"] if thinking else [],
    }
