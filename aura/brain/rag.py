"""RAG engine — index local documents with embeddings and retrieve relevant chunks.

Uses ChromaDB for vector storage with persistent storage at .cache/knowledge/.
Embedding: sentence-transformers all-MiniLM-L6-v2 (local) or NIM embedding endpoint.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(r"D:\automation\aura\.cache\knowledge")
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
COLLECTION_NAME = "aura_knowledge"

_chroma_client = None
_collection = None
_embed_fn = None


def _get_chroma():
    """Lazy-initialize ChromaDB client and collection."""
    global _chroma_client, _collection
    if _chroma_client is None:
        import chromadb
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(KNOWLEDGE_DIR))
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _get_embed_fn():
    """Get embedding function. Uses sentence-transformers locally."""
    global _embed_fn
    if _embed_fn is None:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            _embed_fn = model.encode
        except ImportError:
            logger.warning("sentence-transformers not installed, using ChromaDB default embeddings")
            _embed_fn = None
    return _embed_fn


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def _read_file_content(path: str) -> str:
    """Read file content based on extension."""
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(p))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            return f"Error: PyPDF2 not installed for PDF reading"

    # Text-based formats
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading {path}: {e}"


def _file_id(path: str) -> str:
    """Generate a stable ID for a file path."""
    return hashlib.md5(os.path.abspath(path).encode()).hexdigest()


def index_file(path: str) -> dict:
    """Index a file into the knowledge base.

    Returns dict with: path, chunks_added, status.
    """
    collection = _get_chroma()
    embed_fn = _get_embed_fn()

    abs_path = os.path.abspath(path)
    content = _read_file_content(abs_path)
    if content.startswith("Error"):
        return {"path": abs_path, "chunks_added": 0, "status": content}

    chunks = _chunk_text(content)
    if not chunks:
        return {"path": abs_path, "chunks_added": 0, "status": "No content to index"}

    fid = _file_id(abs_path)

    # Remove existing chunks for this file (re-index)
    try:
        existing = collection.get(where={"source": abs_path})
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    ids = [f"{fid}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": abs_path, "chunk_index": i, "filename": Path(abs_path).name} for i in range(len(chunks))]

    if embed_fn is not None:
        embeddings = embed_fn(chunks).tolist()
        collection.add(ids=ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)
    else:
        collection.add(ids=ids, documents=chunks, metadatas=metadatas)

    return {"path": abs_path, "chunks_added": len(chunks), "status": "indexed"}


def index_directory(path: str, extensions: str = ".md,.txt,.py,.js,.ts,.json,.yaml,.csv,.pdf") -> list[dict]:
    """Index all matching files in a directory."""
    ext_list = [e.strip() for e in extensions.split(",")]
    results = []
    for p in Path(path).rglob("*"):
        if p.is_file() and p.suffix.lower() in ext_list:
            result = index_file(str(p))
            results.append(result)
    return results


def search(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base for relevant chunks.

    Returns list of {content, source, score, chunk_index}.
    """
    collection = _get_chroma()
    embed_fn = _get_embed_fn()

    kwargs: dict[str, Any] = {"query_texts": [query], "n_results": min(top_k, collection.count() or 1)}
    if embed_fn is not None:
        query_embedding = embed_fn([query]).tolist()
        kwargs = {"query_embeddings": query_embedding, "n_results": min(top_k, collection.count() or 1)}

    if collection.count() == 0:
        return []

    results = collection.query(**kwargs)

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append({
            "content": doc,
            "source": meta.get("source", "unknown"),
            "filename": meta.get("filename", "unknown"),
            "chunk_index": meta.get("chunk_index", 0),
            "score": round(1 - dist, 4),  # Convert distance to similarity
        })

    return chunks


def list_indexed() -> list[dict]:
    """Return list of indexed documents with chunk counts."""
    collection = _get_chroma()
    if collection.count() == 0:
        return []

    all_data = collection.get(include=["metadatas"])
    docs: dict[str, int] = {}
    for meta in all_data.get("metadatas", []):
        source = meta.get("source", "unknown")
        docs[source] = docs.get(source, 0) + 1

    return [{"path": path, "chunks": count} for path, count in sorted(docs.items())]


def remove_document(path: str) -> bool:
    """Remove a document's chunks from the index."""
    collection = _get_chroma()
    abs_path = os.path.abspath(path)
    try:
        existing = collection.get(where={"source": abs_path})
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
            return True
    except Exception:
        pass
    return False
