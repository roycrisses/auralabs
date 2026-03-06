"""Researcher agent — information retrieval, explanations, Q&A."""

from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from aura.brain.context import trim_messages
from aura.brain.llm import get_llm
from aura.models import AgentState, ToolCall

RESEARCHER_SYSTEM_PROMPT = """\
You are the Researcher agent for Aura, a desktop automation system.
You specialize in: information retrieval, explanations, summarization, fact-checking, and Q&A.

You have access to these tools:
- web_search: Search the internet via DuckDuckGo (returns titles, URLs, snippets)
- web_fetch: Fetch the text content of a web page by URL
- read_file: Read a local document
- clipboard_read: Read the current clipboard contents
- search_knowledge: Search the personal knowledge base for indexed document content
- delegate_to_agent: Delegate a sub-task to another agent (kernel or creator)
- recall_facts: Search long-term memory for relevant facts and preferences

Strategy: Use web_search first to find relevant sources, then web_fetch to read specific pages for deeper information.
You may also have access to MCP (Model Context Protocol) tools from external servers.
These tools are prefixed with 'mcp_' and work like any other tool.

Provide thorough, well-structured answers. Cite your sources with URLs when using web results."""


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo. Returns titles, URLs, and snippets."""
    ...

@tool
def web_fetch(url: str, max_chars: int = 8000) -> str:
    """Fetch a web page and return its text content (HTML stripped)."""
    ...

@tool
def read_file(path: str) -> str:
    """Read the contents of a file at the given path."""
    ...

@tool
def clipboard_read() -> str:
    """Read the current clipboard contents."""
    ...

@tool
def search_knowledge(query: str, top_k: int = 5) -> str:
    """Search the personal knowledge base for indexed document content."""
    ...

@tool
def delegate_to_agent(target_agent: str, task: str) -> str:
    """Delegate a sub-task to another agent (kernel or creator)."""
    ...

@tool
def recall_facts(query: str, top_k: int = 5) -> str:
    """Search long-term memory for relevant facts and preferences."""
    ...


RESEARCHER_TOOLS = [web_search, web_fetch, read_file, clipboard_read, search_knowledge, delegate_to_agent, recall_facts]


def researcher_node(state: AgentState) -> dict:
    """LangGraph node: invoke the Researcher agent."""
    llm = get_llm("researcher", temperature=0.4, max_tokens=4096)
    llm_with_tools = llm.bind_tools(RESEARCHER_TOOLS)

    messages = [SystemMessage(content=RESEARCHER_SYSTEM_PROMPT)] + state["messages"]
    messages = trim_messages(messages, agent_role="researcher")
    response = llm_with_tools.invoke(messages)

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
        "thinking_log": [f"[Researcher] {thinking[:200]}"] if thinking else [],
    }
