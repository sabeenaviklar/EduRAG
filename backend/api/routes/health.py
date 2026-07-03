"""
backend/api/routes/health.py
─────────────────────────────
GET /api/health

Returns the health status of the backend service:
  - Is the vector store loaded?
  - How many chunks are indexed?
  - Which models are in use?

Used by the Streamlit frontend on startup to check if the backend is alive.
"""

from fastapi import APIRouter
from backend.models.schemas import HealthResponse
from backend.core.rag_pipeline import rag_pipeline
from backend.core.config import GROQ_MODEL, EMBEDDING_MODEL_NAME

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the backend and knowledge base are ready.",
)
def health_check():
    stats = rag_pipeline.get_stats()
    return HealthResponse(
        status="ok",
        vectorstore_ready=stats["ready"],
        total_chunks=stats["total_chunks"],
        model=GROQ_MODEL,
        embedding_model=EMBEDDING_MODEL_NAME,
    )
