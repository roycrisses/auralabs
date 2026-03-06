"""Agent delegation tool — route sub-tasks to other agents."""

from __future__ import annotations

from aura.body.registry import register_tool


@register_tool("delegate_to_agent")
def delegate_to_agent(target_agent: str, task: str) -> str:
    """Delegate a sub-task to another agent and return its response.

    Use this when a task requires expertise from another agent:
    - kernel: OS tasks, code execution, file operations
    - researcher: web search, information gathering, Q&A
    - creator: content generation, writing, creative tasks

    Args:
        target_agent: One of 'kernel', 'researcher', or 'creator'.
        task: The task description to delegate.

    Returns:
        The target agent's response.
    """
    valid_agents = ("kernel", "researcher", "creator")
    if target_agent not in valid_agents:
        return f"Error: target_agent must be one of {valid_agents}, got '{target_agent}'"

    from langchain_core.messages import HumanMessage, SystemMessage

    # Import the agent node functions
    from aura.brain.kernel import kernel_node
    from aura.brain.researcher import researcher_node
    from aura.brain.creator import creator_node

    agent_nodes = {
        "kernel": kernel_node,
        "researcher": researcher_node,
        "creator": creator_node,
    }

    # Build a minimal agent state for the sub-invocation
    state = {
        "messages": [HumanMessage(content=task)],
        "current_agent": target_agent,
        "tool_calls": [],
        "tool_results": [],
        "thinking_log": [],
        "iteration": 0,
        "delegation_depth": 0,
    }

    # Check delegation depth to prevent infinite chains
    # The calling context should set this, but default to 0
    current_depth = state.get("delegation_depth", 0)
    if current_depth >= 2:
        return f"Error: Maximum delegation depth (2) reached. Cannot delegate further."

    state["delegation_depth"] = current_depth + 1

    try:
        node_fn = agent_nodes[target_agent]
        result = node_fn(state)

        # Extract the response text from the agent's output
        for msg in reversed(result.get("messages", [])):
            if hasattr(msg, "content") and msg.content:
                # If the agent wants to use tools, we can't execute them in delegation
                # Just return the text content
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # Agent wants tools — execute them inline
                    return _execute_delegated_tools(state, target_agent, node_fn, result)
                return msg.content

        return "(No response from delegated agent)"

    except Exception as e:
        return f"Delegation error: {type(e).__name__}: {e}"


def _execute_delegated_tools(state: dict, agent_name: str, node_fn, initial_result: dict) -> str:
    """Execute tool calls from a delegated agent invocation (max 3 iterations)."""
    from aura.body.registry import execute_tool
    from aura.models import ToolCall, ToolResult
    from langchain_core.messages import ToolMessage

    current_messages = list(state["messages"])
    current_messages.extend(initial_result.get("messages", []))

    tool_calls = initial_result.get("tool_calls", [])
    max_iterations = 3

    for _iteration in range(max_iterations):
        if not tool_calls:
            break

        # Execute tool calls
        for tc in tool_calls:
            result = execute_tool(tc)
            content = str(result.output) if result.success else f"Error: {result.error}"
            current_messages.append(
                ToolMessage(content=content, tool_call_id=tc.call_id or tc.tool_name)
            )

        # Re-invoke the agent with updated messages
        new_state = {
            **state,
            "messages": current_messages,
            "tool_calls": [],
            "iteration": _iteration + 1,
        }
        result = node_fn(new_state)
        current_messages.extend(result.get("messages", []))
        tool_calls = result.get("tool_calls", [])

    # Extract final response
    for msg in reversed(current_messages):
        if hasattr(msg, "type") and msg.type == "ai" and hasattr(msg, "content") and msg.content:
            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                return msg.content

    # If last message has content, return it even if it also has tool calls
    for msg in reversed(current_messages):
        if hasattr(msg, "content") and msg.content and hasattr(msg, "type") and msg.type == "ai":
            return msg.content

    return "(Delegated agent did not produce a final response)"
