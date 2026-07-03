"""
backend/core/rag_pipeline.py
─────────────────────────────
The core RAG (Retrieval-Augmented Generation) engine.

THE 3-STEP PIPELINE on every query:
  1. RETRIEVE  — embed the question, search ChromaDB, get top-K chunks
  2. AUGMENT   — inject retrieved chunks into the system prompt
  3. GENERATE  — Groq Llama-3 produces a grounded, cited answer

WHY THIS PREVENTS HALLUCINATIONS:
  The system prompt strictly instructs the LLM to use ONLY the
  retrieved context. If the answer isn't in the docs, it says so.
"""

from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from backend.core.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    K_RETRIEVED_DOCS,
)
from backend.core.ingest import get_vectorstore


# ── System Prompt ────────────────────────────────────────────────────────────
# This is the single most critical piece of the RAG system.
# It defines the LLM's persona, constraints, and output format.

_RAG_PROMPT = PromptTemplate(
    template="""You are EduRAG, an expert educational tutor AI.
Your goal is to help students understand concepts clearly, accurately, and concisely.

STRICT RULES — follow these without exception:
1. Base your answer SOLELY on the CONTEXT provided below.
2. If the context does not contain enough information, respond with:
   "I don't have enough information in the knowledge base to answer that. Please add more relevant study materials or ask your instructor."
3. Do NOT use outside knowledge or make up facts.
4. Structure your answer using bullet points or numbered steps when appropriate.
5. End with a "📚 Sources:" section listing the source file names.

────────────────────────────────────────────
CONTEXT (retrieved from knowledge base):
{context}
────────────────────────────────────────────

STUDENT QUESTION: {question}

YOUR ANSWER:""",
    input_variables=["context", "question"],
)


class RAGPipeline:
    """
    Singleton-style class that holds all loaded components.

    Loaded once at app startup (via lifespan in main.py) and
    reused for every query — avoids re-loading the 80MB embedding
    model on each request.
    """

    def __init__(self):
        self.vectorstore: Chroma | None = None
        self.llm: ChatGroq | None = None
        self.qa_chain: RetrievalQA | None = None
        self.ready: bool = False

    def load(self, vectorstore_dir: Path) -> bool:
        """
        Initializes all components from an existing vector store on disk.
        Returns True if successful, False if no vector store found.
        """
        self.vectorstore = get_vectorstore(vectorstore_dir)
        if self.vectorstore is None:
            return False

        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in the .env file.")

        self.llm = ChatGroq(
            model=GROQ_MODEL,
            groq_api_key=GROQ_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )

        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": K_RETRIEVED_DOCS},
        )

        # chain_type="stuff" → concatenate all retrieved chunks into one prompt.
        # For very large context needs, use "map_reduce" or "refine".
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": _RAG_PROMPT},
        )

        self.ready = True
        return True

    def reload(self, vectorstore_dir: Path) -> bool:
        """Reloads the pipeline after new documents have been ingested."""
        self.ready = False
        self.vectorstore = None
        self.qa_chain = None
        return self.load(vectorstore_dir)

    def query(self, question: str, k: int = K_RETRIEVED_DOCS) -> dict:
        """
        Runs the full RAG pipeline for a given question.

        Args:
            question: The student's question.
            k:        Number of chunks to retrieve (overrides default).

        Returns:
            {
                "answer":  str,
                "sources": list[dict],   # [{file, page, snippet}, ...]
                "chunks_retrieved": int,
            }
        """
        if not self.ready:
            raise RuntimeError("RAG pipeline is not ready. Ingest documents first.")

        # Dynamically update k if caller specified a different value
        self.qa_chain.retriever.search_kwargs["k"] = k

        result = self.qa_chain.invoke({"query": question})
        sources = self._parse_sources(result.get("source_documents", []))

        return {
            "answer": result.get("result", ""),
            "sources": sources,
            "chunks_retrieved": len(result.get("source_documents", [])),
        }

    def _parse_sources(self, source_docs: list) -> list[dict]:
        """Deduplicates and formats retrieved source documents."""
        seen, sources = set(), []
        for doc in source_docs:
            meta = doc.metadata
            src_file = meta.get("source", "Unknown")
            page = meta.get("page")
            key = f"{src_file}::{page}"
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file": Path(src_file).name,
                    "page": page,
                    "snippet": doc.page_content[:250] + "...",
                })
        return sources

    def get_stats(self) -> dict:
        """Returns knowledge base statistics."""
        if not self.vectorstore:
            return {"total_chunks": 0, "ready": False}
        return {
            "total_chunks": self.vectorstore._collection.count(),
            "ready": self.ready,
        }


# ── Module-level singleton used by all routes ────────────────────────────────
rag_pipeline = RAGPipeline()
