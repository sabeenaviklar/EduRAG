"""
backend/core/config.py
─────────────────────
Central configuration for the entire backend.
All paths, model names, and tunable parameters live here.
Change one value here and it automatically propagates everywhere.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Project Paths ────────────────────────────────────────────────────────────
# ROOT_DIR = RAG/  (two levels up from this file: backend/core/config.py)
ROOT_DIR: Path = Path(__file__).resolve().parent.parent.parent

DATA_DIR: Path = ROOT_DIR / "data"
VECTORSTORE_DIR: Path = ROOT_DIR / "vectorstore" / "chroma_db"

# ── Embedding Model ──────────────────────────────────────────────────────────
# Runs entirely locally — no API key required.
# Downloads ~80 MB on first run; subsequent runs use the local cache.
EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

# ── ChromaDB ─────────────────────────────────────────────────────────────────
COLLECTION_NAME: str = "educational_docs"

# ── LLM (Groq) ───────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.1-8b-instant"
LLM_TEMPERATURE: float = 0.3
LLM_MAX_TOKENS: int = 1024

# ── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200

# ── Retrieval ────────────────────────────────────────────────────────────────
K_RETRIEVED_DOCS: int = 4

# ── API ──────────────────────────────────────────────────────────────────────
BACKEND_HOST: str = "0.0.0.0"
BACKEND_PORT: int = 8000
FRONTEND_PORT: int = 8501

# Allowed CORS origins (Streamlit dev server)
CORS_ORIGINS: list[str] = [
    f"http://localhost:{FRONTEND_PORT}",
    "http://127.0.0.1:8501",
]
