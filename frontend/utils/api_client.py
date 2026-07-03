"""
frontend/utils/api_client.py
──────────────────────────────
HTTP client that wraps all calls to the FastAPI backend.

WHY A DEDICATED API CLIENT?
  - Single place to change the backend URL
  - Consistent error handling and timeouts
  - Streamlit app code stays clean (no raw httpx calls scattered around)

All methods return a dict with at least {"success": bool, ...}.
On network errors, they return {"success": False, "error": "..."}.
"""

import httpx
from typing import Optional

# Backend base URL — change this if you deploy to a server
BACKEND_URL = "http://localhost:8000"

# Timeouts: connect quickly, but allow longer time for heavy operations
_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0)


def _get(endpoint: str, **kwargs) -> dict:
    """Generic GET helper."""
    try:
        resp = httpx.get(f"{BACKEND_URL}{endpoint}", timeout=_DEFAULT_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to backend. Is it running?"}
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        return {"success": False, "error": detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _post(endpoint: str, **kwargs) -> dict:
    """Generic POST helper."""
    try:
        resp = httpx.post(f"{BACKEND_URL}{endpoint}", timeout=_DEFAULT_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to backend. Is it running?"}
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        return {"success": False, "error": detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _delete(endpoint: str, **kwargs) -> dict:
    """Generic DELETE helper."""
    try:
        resp = httpx.delete(f"{BACKEND_URL}{endpoint}", timeout=_DEFAULT_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to backend. Is it running?"}
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", str(e))
        return {"success": False, "error": detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Public API Methods ────────────────────────────────────────────────────────

def check_health() -> dict:
    """
    GET /api/health
    Returns backend status + KB stats.
    """
    return _get("/api/health")


def ingest_files(file_tuples: list[tuple]) -> dict:
    """
    POST /api/ingest
    Uploads files to the backend for ingestion.

    Args:
        file_tuples: list of (filename, file_bytes, mime_type)
    """
    files = [
        ("files", (name, data, mime))
        for name, data, mime in file_tuples
    ]
    return _post("/api/ingest", files=files)


def reload_pipeline() -> dict:
    """
    POST /api/ingest/reload
    Reloads the RAG pipeline from an existing vector store.
    """
    return _post("/api/ingest/reload")


def clear_knowledge_base() -> dict:
    """
    DELETE /api/ingest/clear
    Wipes all documents and the vector store.
    """
    return _delete("/api/ingest/clear")


def query_knowledge_base(question: str, k: int = 4) -> dict:
    """
    POST /api/query
    Sends a question through the RAG pipeline.

    Returns:
        {
            "success": bool,
            "answer":  str,
            "sources": [{"file": str, "page": int|None, "snippet": str}],
            "chunks_retrieved": int,
        }
    """
    return _post("/api/query", json={"question": question, "k": k})


def list_documents() -> dict:
    """
    GET /api/documents
    Returns a list of all documents in the knowledge base.
    """
    return _get("/api/documents")


def delete_document(filename: str) -> dict:
    """
    DELETE /api/documents/{filename}
    Removes a specific document from the data folder.
    """
    return _delete(f"/api/documents/{filename}")
