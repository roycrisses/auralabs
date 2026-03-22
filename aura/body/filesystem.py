"""Sandboxed file operations — read, write, list with path restrictions."""

from __future__ import annotations

from pathlib import Path

from aura.body.registry import register_tool

ALLOWED_ROOTS: list[Path] = [
    Path(r"D:\automation"),
    Path.home() / "Documents",
    Path.home() / "Desktop",
]


def _is_allowed(path: Path) -> bool:
    """Check if path falls within allowed roots."""
    resolved = path.resolve()
    return any(
        resolved == root or root in resolved.parents
        for root in ALLOWED_ROOTS
    )


@register_tool("read_file")
def read_file(path: str) -> str:
    """Read file contents. Rejects paths outside allowed roots."""
    p = Path(path)
    if not _is_allowed(p):
        raise PermissionError(f"Access denied: {path} is outside allowed directories")
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


@register_tool("write_file")
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    p = Path(path)
    if not _is_allowed(p):
        raise PermissionError(f"Access denied: {path} is outside allowed directories")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {path}"


@register_tool("list_directory")
def list_directory(path: str = ".") -> str:
    """List directory contents with type indicators."""
    p = Path(path)
    if not _is_allowed(p):
        raise PermissionError(f"Access denied: {path} is outside allowed directories")
    if not p.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    entries = []
    for item in sorted(p.iterdir()):
        prefix = "[DIR] " if item.is_dir() else "[FILE]"
        size = ""
        if item.is_file():
            sz = item.stat().st_size
            size = f" ({sz:,} bytes)"
        entries.append(f"{prefix} {item.name}{size}")
    return "\n".join(entries) if entries else "(empty directory)"
