"""
frontend/app.py  ←  Run with:  streamlit run frontend/app.py
──────────────────────────────────────────────────────────────
Streamlit UI for EduRAG.

This file ONLY handles UI logic.
ALL data operations go through the FastAPI backend via api_client.py.

Pages / Sections:
  - Sidebar: backend status, KB stats, document upload, settings
  - Main: chat interface with citation support + document manager tab
"""

import sys
from pathlib import Path

import streamlit as st

# Ensure the project root is on the path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from frontend.utils import api_client

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="EduRAG — AI Educational Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Premium Dark Theme
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { font-family: 'Inter', sans-serif; box-sizing: border-box; }

.stApp {
    background: linear-gradient(135deg, #080c14 0%, #0f172a 50%, #080c14 100%);
    color: #e2e8f0;
}

/* ── HEADER ── */
.hero {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 20px;
    padding: 28px 36px;
    margin-bottom: 24px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #63b3ed, #9f7aea, #68d391, #63b3ed);
    background-size: 200% 100%;
    animation: shimmer 3s linear infinite;
}
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.hero h1 {
    font-size: 2.2rem; font-weight: 800; margin: 0;
    background: linear-gradient(135deg, #63b3ed 0%, #9f7aea 50%, #68d391 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero p { color: #94a3b8; margin: 8px 0 0; font-size: 0.95rem; }

/* ── STATUS BADGES ── */
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    margin: 4px 4px 4px 0;
}
.badge-green  { background: rgba(72,187,120,0.15); border:1px solid rgba(72,187,120,0.4); color:#68d391; }
.badge-red    { background: rgba(252,129,129,0.15); border:1px solid rgba(252,129,129,0.4); color:#fc8181; }
.badge-yellow { background: rgba(246,173,85,0.15);  border:1px solid rgba(246,173,85,0.4);  color:#f6ad55; }
.badge-blue   { background: rgba(99,179,237,0.15);  border:1px solid rgba(99,179,237,0.4);  color:#63b3ed; }

/* ── STAT CARDS ── */
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.stat-card {
    background: rgba(30,41,59,0.8); border: 1px solid rgba(99,179,237,0.1);
    border-radius: 12px; padding: 14px; text-align: center;
}
.stat-value { font-size: 1.6rem; font-weight: 700; color: #63b3ed; line-height:1; }
.stat-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing:.06em; margin-top:4px; }

/* ── SOURCE CHIP ── */
.src-chip {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(99,179,237,0.08); border: 1px solid rgba(99,179,237,0.25);
    border-radius: 20px; padding: 3px 11px; font-size: 0.77rem; color: #63b3ed;
    margin: 3px 3px 0 0;
}

/* ── CHAT ── */
.stChatMessage {
    background: rgba(15,23,42,0.9) !important;
    border: 1px solid rgba(99,179,237,0.07) !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] { background: rgba(30,41,59,0.5); border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; color: #64748b; font-weight: 500; }
.stTabs [aria-selected="true"] { background: rgba(99,179,237,0.15) !important; color: #63b3ed !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff; border: none; border-radius: 9px; font-weight: 600;
    transition: all .2s ease; width: 100%;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(99,179,237,0.25); }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080c14 0%, #0f172a 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.08) !important;
}

/* ── DOC TABLE ── */
.doc-row {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(30,41,59,0.6); border: 1px solid rgba(99,179,237,0.08);
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.doc-name { font-weight: 500; color: #e2e8f0; font-size: .9rem; }
.doc-meta { font-size: .75rem; color: #64748b; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

defaults = {
    "chat_history": [],       # [{role, content, sources, chunks}]
    "health": None,           # last health check result
    "kb_ready": False,        # is the backend knowledge base ready?
    "total_chunks": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def refresh_health():
    h = api_client.check_health()
    st.session_state.health = h
    st.session_state.kb_ready = h.get("vectorstore_ready", False)
    st.session_state.total_chunks = h.get("total_chunks", 0)
    return h


def fmt_bytes(n: int) -> str:
    if n < 1024: return f"{n} B"
    if n < 1048576: return f"{n/1024:.1f} KB"
    return f"{n/1048576:.1f} MB"


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎓 EduRAG")
    st.caption("AI-Powered Educational Tutor")
    st.divider()

    # ── Backend Status ──────────────────────────────────────────────────────
    st.markdown("#### 🔌 Backend Status")

    if st.button("🔄 Refresh Status", key="refresh_health"):
        refresh_health()

    h = st.session_state.health
    if h is None:
        h = refresh_health()

    if h.get("success") is False:
        st.markdown(
            '<span class="badge badge-red">● Offline</span>',
            unsafe_allow_html=True,
        )
        st.warning(h.get("error", "Backend unreachable"))
    else:
        kb_status = "● Ready" if h.get("vectorstore_ready") else "● No KB"
        kb_cls = "badge-green" if h.get("vectorstore_ready") else "badge-yellow"
        st.markdown(
            f'<span class="badge badge-green">● Backend Online</span>'
            f'<span class="badge {kb_cls}">{kb_status}</span>',
            unsafe_allow_html=True,
        )

    # ── KB Stats ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="stat-grid">
          <div class="stat-card">
            <div class="stat-value">{st.session_state.total_chunks}</div>
            <div class="stat-label">Chunks</div>
          </div>
          <div class="stat-card">
            <div class="stat-value" style="font-size:1rem; color:{'#68d391' if st.session_state.kb_ready else '#f6ad55'}">
              {'Ready' if st.session_state.kb_ready else 'Empty'}
            </div>
            <div class="stat-label">KB Status</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Existing KB ─────────────────────────────────────────────────────
    if st.button("⚡ Load Existing KB", key="load_kb"):
        with st.spinner("Reloading pipeline..."):
            r = api_client.reload_pipeline()
        if r.get("success"):
            refresh_health()
            st.success("✅ Knowledge base loaded!")
        else:
            st.error(r.get("error", "Failed to reload."))

    st.divider()

    # ── Upload & Ingest ──────────────────────────────────────────────────────
    st.markdown("#### 📁 Upload Documents")
    st.caption("PDF · TXT · DOCX")

    uploaded = st.file_uploader(
        "Choose files",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        key="uploader",
        label_visibility="collapsed",
    )

    if uploaded and st.button("⚙️ Ingest Documents", key="ingest_btn"):
        mime_map = {"pdf": "application/pdf", "txt": "text/plain", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        file_tuples = [(f.name, f.read(), mime_map.get(f.name.split(".")[-1], "application/octet-stream")) for f in uploaded]

        with st.spinner(f"Ingesting {len(file_tuples)} file(s)... (this may take a minute)"):
            r = api_client.ingest_files(file_tuples)

        if r.get("success"):
            refresh_health()
            st.success(
                f"✅ Done! {r['files_processed']} file(s) · "
                f"{r['total_chunks_created']} chunks created · "
                f"{r['total_chunks_in_db']} total in DB"
            )
        else:
            st.error(r.get("error", "Ingestion failed."))

    st.divider()

    # ── Settings ─────────────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Settings")
    k_val = st.slider("Sources to retrieve (k)", 1, 8, 4, key="k_slider")
    show_sources = st.toggle("Show citations", value=True, key="show_src")
    show_snippets = st.toggle("Show text snippets", value=False, key="show_snip")

    st.divider()

    # ── Clear KB ─────────────────────────────────────────────────────────────
    st.markdown("#### ⚠️ Danger Zone")
    if st.button("🗑️ Clear All Data", key="clear_all"):
        r = api_client.clear_knowledge_base()
        if r.get("success"):
            refresh_health()
            st.session_state.chat_history = []
            st.success("Knowledge base cleared.")
        else:
            st.error(r.get("error"))

    if st.button("💬 Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>🎓 EduRAG</h1>
    <p>Retrieval-Augmented Generation for Educational Systems &nbsp;·&nbsp;
       Ask questions about your study materials and get accurate, cited answers.</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_chat, tab_docs = st.tabs(["💬 Chat", "📚 Knowledge Base"])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ═══════════════════════════════════════════════════════════════════════════

with tab_chat:
    # Backend offline warning
    if st.session_state.health and st.session_state.health.get("success") is False:
        st.error(
            "⚠️ **Backend is offline.** Start it with:\n\n"
            "```\nuvicorn backend.main:app --reload --port 8000\n```",
            icon="🔌",
        )
    elif not st.session_state.kb_ready:
        st.info(
            "👋 **No knowledge base loaded yet.** \n\n"
            "Upload your study materials (PDF / TXT / DOCX) in the sidebar and click **Ingest Documents**.",
            icon="📚",
        )
    else:
        # ── Example Questions ─────────────────────────────────────────────
        if not st.session_state.chat_history:
            st.markdown("##### 💡 Try asking:")
            examples = [
                "What is Newton's Third Law?",
                "Explain photosynthesis step by step.",
                "What caused World War I?",
                "What is the Pythagorean theorem?",
                "Explain supply and demand.",
                "Summarize the key concepts in the document.",
            ]
            cols = st.columns(3)
            for i, ex in enumerate(examples):
                with cols[i % 3]:
                    if st.button(f"💬 {ex}", key=f"ex_{i}"):
                        st.session_state.chat_history.append(
                            {"role": "user", "content": ex, "sources": [], "chunks": 0}
                        )
                        st.rerun()

    # ── Chat History ──────────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        avatar = "🎓" if msg["role"] == "assistant" else "🧑‍🎓"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

            if msg["role"] == "assistant" and msg.get("sources") and show_sources:
                with st.expander(f"📚 Sources ({len(msg['sources'])} retrieved)", expanded=False):
                    for src in msg["sources"]:
                        pg = f" · p.{src['page']+1}" if src.get("page") is not None else ""
                        st.markdown(
                            f'<span class="src-chip">📄 {src["file"]}{pg}</span>',
                            unsafe_allow_html=True,
                        )
                        if show_snippets:
                            st.caption(f'"{src["snippet"]}"')

    # ── Input ─────────────────────────────────────────────────────────────
    if question := st.chat_input(
        "Ask a question about your study materials...",
        key="chat_input",
        disabled=not st.session_state.kb_ready,
    ):
        st.session_state.chat_history.append(
            {"role": "user", "content": question, "sources": [], "chunks": 0}
        )

        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("🔍 Searching knowledge base..."):
                result = api_client.query_knowledge_base(question, k=k_val)

            if not result.get("success"):
                err = result.get("error", "Unknown error.")
                st.error(err)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": f"❌ {err}", "sources": [], "chunks": 0}
                )
            else:
                st.markdown(result["answer"])

                if result.get("sources") and show_sources:
                    with st.expander(
                        f"📚 Sources ({result['chunks_retrieved']} chunks retrieved)",
                        expanded=True,
                    ):
                        for src in result["sources"]:
                            pg = f" · p.{src['page']+1}" if src.get("page") is not None else ""
                            st.markdown(
                                f'<span class="src-chip">📄 {src["file"]}{pg}</span>',
                                unsafe_allow_html=True,
                            )
                            if show_snippets:
                                st.caption(f'"{src["snippet"]}"')

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                    "chunks": result.get("chunks_retrieved", 0),
                })


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — KNOWLEDGE BASE MANAGER
# ═══════════════════════════════════════════════════════════════════════════

with tab_docs:
    st.markdown("### 📚 Knowledge Base Documents")

    col_refresh, col_space = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh List", key="refresh_docs"):
            st.rerun()

    docs_resp = api_client.list_documents()

    if docs_resp.get("success") is False:
        st.error(docs_resp.get("error", "Could not fetch document list."))
    else:
        total_files = docs_resp.get("total_files", 0)
        total_chunks = docs_resp.get("total_chunks", 0)
        docs = docs_resp.get("documents", [])

        # Summary
        c1, c2, c3 = st.columns(3)
        c1.metric("📄 Documents", total_files)
        c2.metric("🧩 Total Chunks", total_chunks)
        c3.metric("📦 Avg Chunks/Doc", round(total_chunks / total_files, 1) if total_files else 0)

        st.divider()

        if not docs:
            st.info("No documents found. Upload files using the sidebar.")
        else:
            for doc in docs:
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f'<div class="doc-row">'
                        f'<div>'
                        f'<div class="doc-name">📄 {doc["filename"]}</div>'
                        f'<div class="doc-meta">{doc["file_type"]} · {fmt_bytes(doc["size_bytes"])}</div>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with col_del:
                    st.write("")  # vertical spacing
                    if st.button("🗑️", key=f"del_{doc['filename']}", help=f"Delete {doc['filename']}"):
                        r = api_client.delete_document(doc["filename"])
                        if r.get("success"):
                            st.success(r["message"])
                            st.rerun()
                        else:
                            st.error(r.get("error"))

        st.divider()
        st.markdown(
            "**Note:** After deleting files, click **Load Existing KB** in the sidebar "
            "and re-ingest to rebuild the vector store."
        )
