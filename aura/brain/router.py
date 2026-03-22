"""Router agent — classifies user intent and delegates to a sub-agent."""

from __future__ import annotations

import re

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


# --- Fast keyword pre-router (skips LLM entirely for obvious cases) ---
_KERNEL_PATTERNS = re.compile(
    r"\b(open|launch|run|execute|start|close|kill|stop|restart|"
    r"delete|rename|move|copy|create folder|create file|mkdir|"
    r"process|task manager|cmd|terminal|powershell|pip install|"
    r"install|uninstall|shutdown|reboot|battery|disk|cpu|ram|"
    r"memory|screenshot|clipboard|volume|brightness|wifi|bluetooth|"
    r"system info|hardware|list files|list dir|schedule|cron|automate|"
    r"set reminder|alarm|timer|registry|env var|path)\b",
    re.IGNORECASE,
)

_RESEARCHER_PATTERNS = re.compile(
    r"\b(search|google|look up|find out|what is|who is|explain|"
    r"tell me about|how does|why does|when did|where is|"
    r"fetch|browse|web|internet|latest|news|weather|wiki|"
    r"summarize this url|read this page|research|define|meaning of)\b",
    re.IGNORECASE,
)

_CREATOR_PATTERNS = re.compile(
    r"\b(write|draft|compose|create (a |an )?(blog|post|article|email|letter|"
    r"essay|story|poem|script|report|proposal|readme|document)|"
    r"generate content|rewrite|paraphrase|translate|proofread|edit text|"
    r"design|ui|mockup|wireframe)\b",
    re.IGNORECASE,
)


def _fast_route(text: str) -> str | None:
    """Attempt keyword-based routing. Returns agent name or None if ambiguous."""
    scores = {
        "kernel": len(_KERNEL_PATTERNS.findall(text)),
        "researcher": len(_RESEARCHER_PATTERNS.findall(text)),
        "creator": len(_CREATOR_PATTERNS.findall(text)),
    }
    top = max(scores, key=scores.get)  # type: ignore[arg-type]
    # Only use fast route if there's a clear winner (score >= 1 and no tie)
    if scores[top] >= 1:
        others = [v for k, v in scores.items() if k != top]
        if all(scores[top] > o for o in others):
            return top
    return None


async def route_node(state: AgentState) -> dict:
    """LangGraph node: invoke the router to pick a sub-agent."""
    # Extract the last user message
    user_messages = [m for m in state["messages"] if hasattr(m, "type") and m.type == "human"]
    if not user_messages:
        user_messages = [m for m in state["messages"] if (isinstance(m, dict) and m.get("role") == "user")]
    last_msg = user_messages[-1] if user_messages else state["messages"][-1]
    last_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # 1. Try fast keyword routing first (0ms, no LLM call)
    fast_result = _fast_route(last_content)
    if fast_result:
        return {
            "current_agent": fast_result,
            "thinking_log": [f"[Router] -> {fast_result} (fast route)"],
            "messages": [],
        }

    # 2. Fallback to LLM router for ambiguous requests
    llm = get_llm("router", temperature=0.1, max_tokens=128)
    structured_llm = llm.with_structured_output(RouterDecision)

    system_prompt = ROUTER_SYSTEM_PROMPT
    try:
        from aura.brain.long_memory import get_relevant_context
        context = await get_relevant_context(last_content, top_k=2)
        if context:
            system_prompt += f"\n\nUser context from long-term memory:\n{context}"
    except Exception:
        pass

    messages = [
        SystemMessage(content=system_prompt),
        last_msg if hasattr(last_msg, "content") else HumanMessage(content=str(last_msg)),
    ]

    decision: RouterDecision = await structured_llm.ainvoke(messages)

    return {
        "current_agent": decision.target_agent,
        "thinking_log": [f"[Router] -> {decision.target_agent}: {decision.reasoning}"],
        "messages": [],
    }
