"""
backend/api/routes/ingest.py
─────────────────────────────
POST /api/ingest          — upload files + build the vector database
POST /api/ingest/reload   — reload the pipeline after external ingest

WHY A SEPARATE INGEST API?
  Separation of concerns: the Streamlit UI doesn't run Python directly.
  Instead it sends files to THIS endpoint, which handles all heavy work
  (loading, chunking, embedding) server-side. The UI just shows progress.
"""

import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List

from backend.models.schemas import IngestResponse, ClearKBResponse
from backend.core.ingest import run_full_ingest
from backend.core.rag_pipeline import rag_pipeline
from backend.core.config import DATA_DIR, VECTORSTORE_DIR

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest Documents",
    description=(
        "Upload one or more educational documents (PDF, TXT, DOCX). "
        "The backend will chunk them, embed them, and store them in ChromaDB. "
        "The RAG pipeline is automatically reloaded after ingestion."
    ),
)
async def ingest_documents(files: List[UploadFile] = File(...)):
    """
    Flow:
      1. Validate file types
      2. Save uploaded files to DATA_DIR
      3. Run the ingestion pipeline (load → split → embed → store)
      4. Reload the RAG pipeline to use the new knowledge base
    """
    # ── Validate extensions ──────────────────────────────────────────────────
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: '{f.filename}'. "
                       f"Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

    # ── Save files to disk ───────────────────────────────────────────────────
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    saved_files = []

    for upload in files:
        dest = DATA_DIR / upload.filename
        content = await upload.read()
        dest.write_bytes(content)
        saved_files.append(upload.filename)

    # ── Run ingestion pipeline ───────────────────────────────────────────────
    try:
        stats = run_full_ingest(DATA_DIR, VECTORSTORE_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    if stats.get("error"):
        raise HTTPException(status_code=400, detail=stats["error"])

    # ── Reload the RAG pipeline ──────────────────────────────────────────────
    try:
        rag_pipeline.reload(VECTORSTORE_DIR)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion succeeded but pipeline reload failed: {str(e)}",
        )

    return IngestResponse(
        success=True,
        message=f"Successfully ingested {len(saved_files)} file(s).",
        files_processed=stats["files_processed"],
        total_chunks_created=stats["total_chunks_created"],
        total_chunks_in_db=stats["total_chunks_in_db"],
    )


@router.post(
    "/ingest/reload",
    response_model=IngestResponse,
    summary="Reload Knowledge Base",
    description="Reload the RAG pipeline from an existing vector store (no file upload needed).",
)
def reload_pipeline():
    """
    Useful when documents were added externally (e.g., via ingest.py CLI)
    and the pipeline just needs to be refreshed.
    """
    success = rag_pipeline.reload(VECTORSTORE_DIR)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="No vector store found. Please ingest documents first.",
        )
    stats = rag_pipeline.get_stats()
    return IngestResponse(
        success=True,
        message="Knowledge base reloaded successfully.",
        files_processed=0,
        total_chunks_created=0,
        total_chunks_in_db=stats["total_chunks"],
    )


@router.delete(
    "/ingest/clear",
    response_model=ClearKBResponse,
    summary="Clear Knowledge Base",
    description="Deletes all documents and the vector store. Cannot be undone.",
)
def clear_knowledge_base():
    """Wipes all ingested data — both the raw files and the vector index."""
    # Clear ChromaDB
    if VECTORSTORE_DIR.exists():
        shutil.rmtree(VECTORSTORE_DIR)

    # Clear data folder
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Reset pipeline state
    rag_pipeline.ready = False
    rag_pipeline.vectorstore = None
    rag_pipeline.qa_chain = None

    return ClearKBResponse(
        success=True,
        message="Knowledge base cleared. All documents and vectors have been deleted.",
    )
