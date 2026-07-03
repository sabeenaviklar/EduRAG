# EduRAG — RAG for Educational Systems

> 🎓 Ask questions about your study materials. Get accurate, cited answers powered by AI.

---

## 📁 Project Structure

```
RAG/
├── backend/                        ← FastAPI REST API Server
│   ├── main.py                     ← App entry point, route registration, CORS
│   ├── api/
│   │   └── routes/
│   │       ├── health.py           ← GET  /api/health
│   │       ├── ingest.py           ← POST /api/ingest  |  DELETE /api/ingest/clear
│   │       ├── query.py            ← POST /api/query
│   │       └── documents.py        ← GET  /api/documents  |  DELETE /api/documents/{name}
│   ├── core/
│   │   ├── config.py               ← Central config (paths, models, parameters)
│   │   ├── ingest.py               ← Load → Split → Embed → Store logic
│   │   └── rag_pipeline.py         ← Retrieve → Generate logic (singleton)
│   └── models/
│       └── schemas.py              ← Pydantic request/response schemas
│
├── frontend/                       ← Streamlit Web UI
│   ├── app.py                      ← Main UI (Chat + KB Manager tabs)
│   └── utils/
│       └── api_client.py           ← HTTP client wrapping all backend calls
│
├── data/                           ← Put your PDFs/TXTs/DOCXs here
│   └── sample_educational_content.txt
├── vectorstore/                    ← ChromaDB index (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | FastAPI + Uvicorn | Fast async REST API, auto Swagger docs |
| **RAG Framework** | LangChain | Orchestrates retrieve + generate pipeline |
| **Vector DB** | ChromaDB | Local, persistent, fast similarity search |
| **Embeddings** | HuggingFace MiniLM | Free, runs locally, no API key needed |
| **LLM** | Groq (Llama-3.1-8b) | Free API, very fast inference |
| **Frontend** | Streamlit | Chat UI in pure Python |
| **HTTP Client** | httpx | Frontend → Backend API calls |
| **Validation** | Pydantic v2 | Request/response schema validation |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Backend + KB status check |
| `POST` | `/api/ingest` | Upload files → ingest into vector DB |
| `POST` | `/api/ingest/reload` | Reload pipeline from existing vector store |
| `DELETE` | `/api/ingest/clear` | Wipe all documents and vectors |
| `POST` | `/api/query` | Ask a question → get cited answer |
| `GET` | `/api/documents` | List all indexed documents |
| `DELETE` | `/api/documents/{name}` | Remove a specific document |

> 📖 **Auto-generated API docs:** http://localhost:8000/docs (Swagger UI)

---



---

## 🧠 How It Works

```
Student Question
      │
      ▼ (Streamlit calls POST /api/query)
FastAPI Backend
      │
      ├─ 1. EMBED QUERY   → HuggingFace MiniLM → 384-dim vector
      │
      ├─ 2. RETRIEVE      → ChromaDB similarity search → top-K chunks
      │
      └─ 3. GENERATE      → Groq Llama-3 + retrieved context → answer
                                         │
                              Streamlit displays answer + source citations
```
