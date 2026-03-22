"""Vision tools — screenshot analysis using a vision-capable LLM."""

from __future__ import annotations

import base64
from pathlib import Path

from aura.body.registry import register_tool


@register_tool("analyze_screenshot")
def analyze_screenshot(prompt: str = "Describe what you see on the screen.", region: str | None = None) -> str:
    """Take a screenshot and analyze it with a vision model.

    Args:
        prompt: What to look for or describe in the screenshot.
        region: Optional "x,y,width,height" for partial capture.
    """
    from aura.body.desktop import screenshot

    # Take the screenshot and get the file path
    result = screenshot(region=region)
    # result is like "Screenshot saved: D:\...\screenshot_xxx.png"
    path_str = result.replace("Screenshot saved: ", "").strip()
    path = Path(path_str)

    if not path.exists():
        return f"Screenshot file not found: {path_str}"

    return _analyze_image(path, prompt)


@register_tool("analyze_image")
def analyze_image(image_path: str, prompt: str = "Describe this image in detail.") -> str:
    """Analyze an image file with a vision model.

    Args:
        image_path: Path to the image file (png, jpg, etc.).
        prompt: What to analyze or describe.
    """
    path = Path(image_path)
    if not path.exists():
        return f"Image not found: {image_path}"

    return _analyze_image(path, prompt)


def _analyze_image(image_path: Path, prompt: str) -> str:
    """Send an image to a vision model for analysis."""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    from aura.config import MODEL_REGISTRY, get_api_key, get_settings

    settings = get_settings()

    # Encode image as base64
    image_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")

    # Determine media type
    suffix = image_path.suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
    media_type = media_types.get(suffix, "image/png")

    # Use the registered vision model
    llm = ChatOpenAI(
        base_url=settings.nvidia_base_url,
        api_key=get_api_key("vision"),
        model=MODEL_REGISTRY.get("vision", "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"),
        max_tokens=1024,
        temperature=0.3,
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{image_data}"},
            },
        ]
    )

    try:
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"Vision analysis failed: {type(e).__name__}: {e}"
