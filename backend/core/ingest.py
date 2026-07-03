"""
backend/core/ingest.py
──────────────────────
Document ingestion pipeline.

Pipeline:  Load  →  Split  →  Embed  →  Store in ChromaDB

This module is called by the /api/ingest endpoint when the user
uploads new documents via the Streamlit UI.
"""

import shutil
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
    Docx2txtLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from backend.core.config import (
    EMBEDDING_MODEL_NAME,
    COLLECTION_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def _get_embeddings() -> HuggingFaceEmbeddings:
    """Returns the HuggingFace embedding model (cached after first load)."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def load_documents(data_dir: Path) -> list:
    """
    Loads all supported documents from data_dir.

    Supported formats:
        .pdf  → PyPDFLoader (page-by-page)
        .txt  → TextLoader
        .docx → Docx2txtLoader

    Returns a flat list of LangChain Document objects.
    Each Document: { page_content: str, metadata: { source, page, ... } }
    """
    documents = []

    loaders = [
        ("**/*.pdf",  PyPDFLoader,     {}),
        ("**/*.txt",  TextLoader,      {"loader_kwargs": {"encoding": "utf-8"}}),
        ("**/*.docx", Docx2txtLoader,  {}),
    ]

    for glob, loader_cls, extra_kwargs in loaders:
        loader = DirectoryLoader(
            str(data_dir),
            glob=glob,
            loader_cls=loader_cls,
            show_progress=False,
            use_multithreading=True,
            **extra_kwargs,
        )
        documents.extend(loader.load())

    return documents


def split_documents(documents: list) -> list:
    """
    Splits long documents into overlapping chunks.

    RecursiveCharacterTextSplitter splits on:
      ["\n\n", "\n", " ", ""]  → tries to keep paragraphs intact.

    chunk_size=1000 chars, overlap=200 chars:
      - Big enough to carry useful context
      - Small enough for precise vector search
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )
    return splitter.split_documents(documents)


def build_vectorstore(chunks: list, vectorstore_dir: Path) -> Chroma:
    """
    Embeds all chunks and saves them to ChromaDB.

    Steps:
      1. Wipe old vectorstore (to avoid duplicates on re-ingest)
      2. Call HuggingFace MiniLM on every chunk → 384-dim vectors
      3. Persist (vectors + raw text + metadata) to disk via ChromaDB
    """
    if vectorstore_dir.exists():
        shutil.rmtree(vectorstore_dir)
    vectorstore_dir.mkdir(parents=True, exist_ok=True)

    embeddings = _get_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(vectorstore_dir),
    )
    return vectorstore


def get_vectorstore(vectorstore_dir: Path) -> Chroma | None:
    """
    Loads an existing vectorstore from disk.
    Returns None if the vectorstore does not exist yet.
    """
    if not vectorstore_dir.exists():
        return None

    embeddings = _get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(vectorstore_dir),
    )


def run_full_ingest(data_dir: Path, vectorstore_dir: Path) -> dict:
    """
    Orchestrates the complete ingestion pipeline.

    Returns a stats dict consumed by the /api/ingest response.
    """
    documents = load_documents(data_dir)
    if not documents:
        return {
            "files_processed": 0,
            "total_chunks_created": 0,
            "total_chunks_in_db": 0,
            "error": "No documents found in data directory.",
        }

    chunks = split_documents(documents)
    vectorstore = build_vectorstore(chunks, vectorstore_dir)

    # Count unique source files
    sources = {doc.metadata.get("source", "") for doc in chunks}

    return {
        "files_processed": len(sources),
        "total_chunks_created": len(chunks),
        "total_chunks_in_db": vectorstore._collection.count(),
        "error": None,
    }
