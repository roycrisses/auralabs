"""LangGraph orchestration — the central nervous system of Aura.

Graph flow:
    user -> route -> (kernel | researcher | creator) -> tool_exec? -> agent -> ... -> respond -> END

Supports multi-turn tool loops: an agent can call tools multiple times (search -> fetch -> summarize)
before producing a final response. Capped at MAX_TOOL_ITERATIONS to prevent infinite loops.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from aura.body.registry import execute_tool
from aura.brain.creator import creator_node
from aura.brain.kernel import kernel_node
from aura.brain.researcher import researcher_node
from aura.brain.router import route_node
from aura.models import AgentState, ToolCall, ToolResult

# Note: AgentState now includes delegation_depth for cross-agent delegation tracking

MAX_TOOL_ITERATIONS = 6


async def tool_exec_node(state: AgentState) -> dict:
    """Execute pending tool calls via the body registry."""
    results: list[ToolResult] = []
    for tc in state.get("tool_calls", []):
        # registry.execute_tool handles both sync and async tools
        result = await execute_tool(tc)
        results.append(result)

    # Build tool messages for the LLM to process
    from langchain_core.messages import ToolMessage

    tool_messages = []
    for tc, result in zip(state.get("tool_calls", []), results):
        content = str(result.output) if result.success else f"Error: {result.error}"
        tool_messages.append(
            ToolMessage(content=content, tool_call_id=tc.call_id or tc.tool_name)
        )

    thinking = []
    for r in results:
        status = "OK" if r.success else f"FAIL: {r.error}"
        thinking.append(f"[Tool] {r.tool_name} -> {status}")

    return {
        "messages": tool_messages,
        "tool_results": results,
        "tool_calls": [],  # clear pending calls
        "thinking_log": thinking,
        "iteration": state.get("iteration", 0) + 1,
    }


async def respond_node(state: AgentState) -> dict:
    """Final pass — terminal node before END."""
    return {"messages": [], "iteration": state.get("iteration", 0) + 1}


# --- Routing logic ---

def route_to_agent(state: AgentState) -> str:
    """Conditional edge: route to the selected agent."""
    return state.get("current_agent", "researcher")


def check_tool_calls(state: AgentState) -> str:
    """Conditional edge: if tool calls pending and under iteration cap, go to tool_exec."""
    if state.get("tool_calls") and state.get("iteration", 0) < MAX_TOOL_ITERATIONS:
        return "tool_exec"
    return "respond"


def after_tool_exec(state: AgentState) -> str:
    """After tool execution, route back to the current agent for interpretation.

    If we've hit the iteration cap, go straight to respond to avoid infinite loops.
    """
    if state.get("iteration", 0) >= MAX_TOOL_ITERATIONS:
        return "respond"
    return state.get("current_agent", "respond")


def build_graph() -> StateGraph:
    """Construct and compile the Aura orchestration graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("kernel", kernel_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("creator", creator_node)
    graph.add_node("tool_exec", tool_exec_node)
    graph.add_node("respond", respond_node)

    # Entry point
    graph.set_entry_point("route")

    # Router -> agent (conditional)
    graph.add_conditional_edges(
        "route",
        route_to_agent,
        {"kernel": "kernel", "researcher": "researcher", "creator": "creator"},
    )

    # Each agent -> check for tool calls
    for agent in ("kernel", "researcher", "creator"):
        graph.add_conditional_edges(
            agent,
            check_tool_calls,
            {"tool_exec": "tool_exec", "respond": "respond"},
        )

    # Tool execution -> back to agent for interpretation OR respond if capped
    graph.add_conditional_edges(
        "tool_exec",
        after_tool_exec,
        {
            "kernel": "kernel",
            "researcher": "researcher",
            "creator": "creator",
            "respond": "respond",
        },
    )

    # Respond -> END
    graph.add_edge("respond", END)

    return graph.compile()
