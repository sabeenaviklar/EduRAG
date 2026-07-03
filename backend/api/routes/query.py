"""
backend/api/routes/query.py
────────────────────────────
POST /api/query   — ask a question, get a grounded answer

This is the most important endpoint in the project.
It triggers the full 3-step RAG pipeline:
  1. Embed the question → vector
  2. Search ChromaDB → top-K relevant chunks
  3. Groq Llama-3 generates the final answer (grounded in chunks)
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import QueryRequest, QueryResponse, SourceDocument
from backend.core.rag_pipeline import rag_pipeline

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a Question",
    description=(
        "Send a student question to the RAG pipeline. "
        "The system retrieves the most relevant document chunks from "
        "ChromaDB and generates a grounded answer using Groq Llama-3."
    ),
)
def query_knowledge_base(body: QueryRequest):
    """
    Request body:
      - question: str  (required, 3-2000 chars)
      - k:        int  (optional, 1-10, default 4)

    Response:
      - answer:           The LLM's response (grounded in your documents)
      - sources:          List of source documents used
      - chunks_retrieved: How many chunks were retrieved
    """
    if not rag_pipeline.ready:
        raise HTTPException(
            status_code=503,
            detail=(
                "Knowledge base is not loaded. "
                "Please ingest documents first via POST /api/ingest."
            ),
        )

    try:
        result = rag_pipeline.query(
            question=body.question,
            k=body.k,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during query processing: {str(e)}",
        )

    # Convert raw source dicts → Pydantic SourceDocument models
    sources = [
        SourceDocument(
            file=src["file"],
            page=src["page"],
            snippet=src["snippet"],
        )
        for src in result["sources"]
    ]

    return QueryResponse(
        success=True,
        question=body.question,
        answer=result["answer"],
        sources=sources,
        chunks_retrieved=result["chunks_retrieved"],
    )
