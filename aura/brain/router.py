"""Router agent — classifies user intent and delegates to a sub-agent."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from aura.brain.llm import get_llm
from aura.models import AgentState, RouterDecision

ROUTER_SYSTEM_PROMPT = """\
You are the Router for Aura, a desktop automation system.
Classify the user's request to exactly one agent:

- kernel: OS tasks, code execution, scripting, file operations, system commands, debugging, process management, launching apps, system info, disk/network stats, managing processes
- researcher: web search, fetching web pages, information gathering, explanations, summarization, fact-checking, Q&A, looking things up online
- creator: content generation, creative writing, document drafting, blog posts, emails, UI design

Respond with the target agent name and one sentence of reasoning."""


def route_node(state: AgentState) -> dict:
    """LangGraph node: invoke the router to pick a sub-agent."""
    llm = get_llm("router", temperature=0.1, max_tokens=256)
    structured_llm = llm.with_structured_output(RouterDecision)

    # Build message list — only pass the latest user message for routing
    user_messages = [m for m in state["messages"] if hasattr(m, "type") and m.type == "human"]
    if not user_messages:
        # Fallback: treat raw dicts
        user_messages = [m for m in state["messages"] if (isinstance(m, dict) and m.get("role") == "user")]

    last_msg = user_messages[-1] if user_messages else state["messages"][-1]

    # Inject relevant long-term context if available
    system_prompt = ROUTER_SYSTEM_PROMPT
    try:
        from aura.brain.long_memory import get_relevant_context
        last_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        context = get_relevant_context(last_content, top_k=2)
        if context:
            system_prompt += f"\n\nUser context from long-term memory:\n{context}"
    except Exception:
        pass

    messages = [
        SystemMessage(content=system_prompt),
        last_msg if hasattr(last_msg, "content") else HumanMessage(content=str(last_msg)),
    ]

    decision: RouterDecision = structured_llm.invoke(messages)

    return {
        "current_agent": decision.target_agent,
        "thinking_log": [f"[Router] -> {decision.target_agent}: {decision.reasoning}"],
        "messages": [],
    }
