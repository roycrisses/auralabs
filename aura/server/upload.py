"""File upload handling — accept file uploads and store in .cache/uploads/."""

from __future__ import annotations

import shutil
import python_multipart  # noqa: F401
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

UPLOAD_DIR = Path(r"D:\automation\aura\.cache\uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_DOC_TYPES = {".pdf", ".txt", ".md", ".csv", ".json", ".yaml", ".yml"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES

upload_router = APIRouter()


@upload_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file. Returns the saved file path.

    Supports images (png, jpg, gif, webp) and documents (pdf, txt, md, csv).
    Max size: 10MB.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Validate file extension
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            400, f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_TYPES))}"
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large ({len(content)} bytes). Max: {MAX_FILE_SIZE} bytes.")

    # Save with unique name
    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    save_path = UPLOAD_DIR / unique_name
    save_path.write_bytes(content)

    file_type = "image" if ext in ALLOWED_IMAGE_TYPES else "document"

    return {
        "path": str(save_path),
        "filename": file.filename,
        "type": file_type,
        "size": len(content),
    }


def get_attachment_context(attachments: list[str]) -> str:
    """Generate context text for message attachments.

    For images: suggests using analyze_image tool.
    For documents: suggests reading the file.
    """
    if not attachments:
        return ""

    parts = []
    for path in attachments:
        p = Path(path)
        ext = p.suffix.lower()
        if ext in ALLOWED_IMAGE_TYPES:
            parts.append(f"[Attached image: {p.name} at {path} — use screenshot/vision tools to analyze]")
        elif ext in ALLOWED_DOC_TYPES:
            parts.append(f"[Attached document: {p.name} at {path} — use read_file to read contents]")
        else:
            parts.append(f"[Attached file: {p.name} at {path}]")

    return "\n".join(parts)
