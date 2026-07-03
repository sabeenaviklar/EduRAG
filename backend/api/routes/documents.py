"""
backend/api/routes/documents.py
────────────────────────────────
GET    /api/documents         — list all documents in the knowledge base
DELETE /api/documents/{name}  — remove a specific document file

Lets the Streamlit UI show what's currently in the knowledge base
and allows users to remove individual files.
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from backend.models.schemas import DocumentListResponse, DocumentInfo, ClearKBResponse
from backend.core.rag_pipeline import rag_pipeline
from backend.core.config import DATA_DIR

router = APIRouter()

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List Documents",
    description="Returns metadata for all documents currently in the knowledge base.",
)
def list_documents():
    """
    Scans the DATA_DIR for supported files and returns:
      - filename
      - file size in bytes
      - file type (extension)
      - total chunks indexed in ChromaDB
    """
    if not DATA_DIR.exists():
        return DocumentListResponse(
            total_files=0,
            total_chunks=0,
            documents=[],
        )

    doc_infos = []
    for f in DATA_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            doc_infos.append(
                DocumentInfo(
                    filename=f.name,
                    size_bytes=f.stat().st_size,
                    file_type=f.suffix.lower().lstrip(".").upper(),
                )
            )

    stats = rag_pipeline.get_stats()

    return DocumentListResponse(
        total_files=len(doc_infos),
        total_chunks=stats["total_chunks"],
        documents=sorted(doc_infos, key=lambda d: d.filename),
    )


@router.delete(
    "/documents/{filename}",
    response_model=ClearKBResponse,
    summary="Delete a Document",
    description=(
        "Deletes a specific document from the data folder. "
        "Note: you must re-ingest (POST /api/ingest/reload) to update the vector store."
    ),
)
def delete_document(filename: str):
    """
    Removes a single file from DATA_DIR.
    Does NOT automatically rebuild the vector store — call /api/ingest/reload after.
    """
    target = DATA_DIR / filename

    # Security: prevent path traversal attacks
    try:
        target.resolve().relative_to(DATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    target.unlink()
    return ClearKBResponse(
        success=True,
        message=f"'{filename}' deleted. Re-ingest to update the knowledge base.",
    )
