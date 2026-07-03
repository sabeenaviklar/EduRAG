"""
backend/models/schemas.py
─────────────────────────
Pydantic models for all API request and response bodies.

WHY PYDANTIC?
    FastAPI uses Pydantic to:
      1. Automatically validate incoming JSON request bodies
      2. Serialize Python objects to JSON responses
      3. Auto-generate OpenAPI (Swagger) docs at /docs
"""

from typing import Optional
from pydantic import BaseModel, Field


# ────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    vectorstore_ready: bool = Field(..., example=True)
    total_chunks: int = Field(..., example=128)
    model: str = Field(..., example="llama-3.1-8b-instant")
    embedding_model: str = Field(..., example="sentence-transformers/all-MiniLM-L6-v2")


# ────────────────────────────────────────────────────────────────────────────
# INGEST
# ────────────────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    success: bool
    message: str
    files_processed: int
    total_chunks_created: int
    total_chunks_in_db: int


# ────────────────────────────────────────────────────────────────────────────
# QUERY
# ────────────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        example="What is Newton's Third Law of Motion?",
    )
    k: Optional[int] = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve",
    )


class SourceDocument(BaseModel):
    file: str = Field(..., example="physics_notes.pdf")
    page: Optional[int] = Field(None, example=3)
    snippet: str = Field(..., example="Newton's third law states that...")


class QueryResponse(BaseModel):
    success: bool
    question: str
    answer: str
    sources: list[SourceDocument]
    chunks_retrieved: int


# ────────────────────────────────────────────────────────────────────────────
# DOCUMENTS  (list what's in the knowledge base)
# ────────────────────────────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    filename: str
    size_bytes: int
    file_type: str


class DocumentListResponse(BaseModel):
    total_files: int
    total_chunks: int
    documents: list[DocumentInfo]


# ────────────────────────────────────────────────────────────────────────────
# CLEAR KNOWLEDGE BASE
# ────────────────────────────────────────────────────────────────────────────

class ClearKBResponse(BaseModel):
    success: bool
    message: str


# ────────────────────────────────────────────────────────────────────────────
# GENERIC ERROR
# ────────────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
