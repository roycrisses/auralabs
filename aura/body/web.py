"""Web tools — search the internet and fetch page content."""

from __future__ import annotations

import httpx
from duckduckgo_search import DDGS

from aura.body.registry import register_tool


@register_tool("web_search")
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo and return top results.

    Args:
        query: The search query string.
        max_results: Number of results to return (1-10).
    """
    max_results = max(1, min(10, max_results))

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    if not results:
        return f"No results found for: {query}"

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        href = r.get("href", "")
        body = r.get("body", "")
        lines.append(f"{i}. {title}\n   {href}\n   {body}")

    return "\n\n".join(lines)


@register_tool("web_fetch")
def web_fetch(url: str, max_chars: int = 8000) -> str:
    """Fetch a web page and return its text content (HTML stripped).

    Args:
        url: The URL to fetch.
        max_chars: Maximum characters to return.
    """
    max_chars = max(500, min(50000, max_chars))

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Aura/0.1"
    }

    with httpx.Client(follow_redirects=True, timeout=15) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")

    if "text/html" in content_type:
        text = _extract_text_from_html(resp.text)
    else:
        text = resp.text

    if len(text) > max_chars:
        text = text[:max_chars] + f"\n\n... (truncated at {max_chars} chars)"

    return text


def _extract_text_from_html(html: str) -> str:
    """Minimal HTML-to-text extraction without heavy dependencies."""
    import re

    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Convert common block tags to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr|blockquote)>", "\n", text, flags=re.IGNORECASE)

    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode common HTML entities
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )

    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
