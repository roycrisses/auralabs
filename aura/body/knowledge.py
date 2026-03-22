"""Knowledge base tools — search, index, and manage personal document knowledge."""

from __future__ import annotations

from aura.body.registry import register_tool


@register_tool("search_knowledge")
def search_knowledge(query: str, top_k: int = 5) -> str:
    """Search indexed documents in the knowledge base for relevant information.

    Args:
        query: The search query.
        top_k: Maximum number of results to return.

    Returns:
        Relevant document chunks with source information.
    """
    from aura.brain.rag import search

    results = search(query, top_k=top_k)
    if not results:
        return "No results found in knowledge base. Try indexing documents first with index_document."

    lines = []
    for r in results:
        lines.append(f"[{r['filename']}] (score: {r['score']})")
        lines.append(r["content"])
        lines.append(f"  Source: {r['source']}")
        lines.append("")
    return "\n".join(lines)


@register_tool("index_document")
def index_document(path: str) -> str:
    """Index a file into the knowledge base for later retrieval.

    Supports: .txt, .md, .py, .js, .ts, .json, .yaml, .csv, .pdf

    Args:
        path: File path to index.

    Returns:
        Indexing result with chunk count.
    """
    from aura.brain.rag import index_file

    result = index_file(path)
    return f"Indexed {result['path']}: {result['chunks_added']} chunks ({result['status']})"


@register_tool("index_directory")
def index_directory_tool(path: str, extensions: str = ".md,.txt,.py") -> str:
    """Index all matching files in a directory into the knowledge base.

    Args:
        path: Directory path to scan.
        extensions: Comma-separated list of file extensions to include.

    Returns:
        Summary of indexed files.
    """
    from aura.brain.rag import index_directory

    results = index_directory(path, extensions)
    total_chunks = sum(r["chunks_added"] for r in results)
    return f"Indexed {len(results)} files, {total_chunks} total chunks."


@register_tool("list_indexed_documents")
def list_indexed_documents() -> str:
    """List all documents currently indexed in the knowledge base."""
    from aura.brain.rag import list_indexed

    docs = list_indexed()
    if not docs:
        return "No documents indexed. Use index_document to add files."
    lines = [f"Indexed documents ({len(docs)}):"]
    for d in docs:
        lines.append(f"  {d['path']} ({d['chunks']} chunks)")
    return "\n".join(lines)


@register_tool("remove_from_knowledge")
def remove_from_knowledge(path: str) -> str:
    """Remove a document from the knowledge base index.

    Args:
        path: File path to remove.
    """
    from aura.brain.rag import remove_document

    removed = remove_document(path)
    return f"Removed '{path}' from knowledge base." if removed else f"'{path}' not found in knowledge base."
