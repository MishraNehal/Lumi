# import streamlit as st
# import requests

# BACKEND_URL = "http://127.0.0.1:8000"

# # ----------------------------------
# # Page Config
# # ----------------------------------
# st.set_page_config(
#     page_title="Lumi",
#     page_icon="🧠",
#     layout="centered"
# )

# st.title("🧠 Lumi – AI Personal Knowledge Assistant")
# st.caption("Chat with your web pages, documents, and YouTube videos")

# # ----------------------------------
# # SESSION STATE (CHAT HISTORY)
# # ----------------------------------
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # ----------------------------------
# # SIDEBAR — INGESTION
# # ----------------------------------
# st.sidebar.header("📥 Ingest Knowledge")

# # ---- Web Ingestion ----
# web_url = st.sidebar.text_input("🌐 Web URL")
# if st.sidebar.button("Ingest Web"):
#     if web_url.strip():
#         res = requests.post(
#             f"{BACKEND_URL}/ingest/web",
#             params={"url": web_url}
#         )
#         if res.status_code == 200:
#             st.sidebar.success(res.json().get("message", "Web ingested"))
#         else:
#             st.sidebar.error("Failed to ingest web")

# # ---- YouTube Ingestion ----
# yt_url = st.sidebar.text_input("🎥 YouTube URL")
# if st.sidebar.button("Ingest YouTube"):
#     if yt_url.strip():
#         res = requests.post(
#             f"{BACKEND_URL}/ingest/youtube",
#             params={"url": yt_url}
#         )
#         if res.status_code == 200:
#             st.sidebar.success(res.json().get("message", "YouTube ingested"))
#         else:
#             st.sidebar.error("Failed to ingest YouTube")

# # ---- Document Ingestion ----
# uploaded_file = st.sidebar.file_uploader(
#     "📄 Upload Document",
#     type=["txt", "pdf", "docx"]
# )

# if uploaded_file and st.sidebar.button("Ingest Document"):
#     files = {
#         "file": (uploaded_file.name, uploaded_file.getvalue())
#     }
#     res = requests.post(
#         f"{BACKEND_URL}/ingest/document",
#         files=files
#     )
#     if res.status_code == 200:
#         st.sidebar.success("Document ingested")
#     else:
#         st.sidebar.error("Failed to ingest document")

# # ---- Clear Chat ----
# if st.sidebar.button("🧹 Clear Chat"):
#     st.session_state.messages = []
#     st.rerun()

# # ----------------------------------
# # RENDER CHAT HISTORY
# # ----------------------------------
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

#         # Show sources only for assistant messages
#         if message["role"] == "assistant":
#             sources = message.get("sources", [])
#             if sources:
#                 st.markdown("**Sources used:**")
#                 for src in sources:
#                     st.markdown(f"- {src}")

# # ----------------------------------
# # CHAT INPUT
# # ----------------------------------
# prompt = st.chat_input("Ask Lumi...")

# if prompt:
#     # ---- Show user message ----
#     st.session_state.messages.append({
#         "role": "user",
#         "content": prompt
#     })

#     with st.chat_message("user"):
#         st.markdown(prompt)

#     # ---- Call backend ----
#     res = requests.post(
#         f"{BACKEND_URL}/chat",
#         json={"question": prompt}
#     )

#     if res.status_code == 200:
#         data = res.json()

#         answer = data.get("answer", "No answer returned")
#         sources = data.get("sources", [])

#         # ---- Save assistant message ----
#         st.session_state.messages.append({
#             "role": "assistant",
#             "content": answer,
#             "sources": sources
#         })

#         with st.chat_message("assistant"):
#             st.markdown(answer)
#             if sources:
#                 st.markdown("**Sources used:**")
#                 for src in sources:
#                     st.markdown(f"- {src}")
#             else:
#                 st.markdown("_No sources available_")

#     else:
#         with st.chat_message("assistant"):
#             st.error("Failed to get response from Lumi backend")

import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Lumi — AI Knowledge Assistant",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# DARK THEME CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root variables ── */
:root {
    --bg-primary:    #0a0a0f;
    --bg-secondary:  #111118;
    --bg-card:       #16161f;
    --bg-hover:      #1e1e2a;
    --accent:        #7c3aed;
    --accent-light:  #9d5cff;
    --accent-glow:   rgba(124, 58, 237, 0.3);
    --accent2:       #06b6d4;
    --text-primary:  #f0eeff;
    --text-secondary:#a89fcf;
    --text-muted:    #6b6484;
    --border:        rgba(124,58,237,0.2);
    --border-subtle: rgba(255,255,255,0.06);
    --success:       #10b981;
    --error:         #ef4444;
    --warning:       #f59e0b;
}

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* ── Hide default streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* DO NOT hide header */
header {
    background: transparent !important;
}

/* Optional: style the toggle button */
button[kind="header"] {
    color: white !important;
}

/* ── Main container ── */
.block-container {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1100px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent), #5b21b6) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 0 12px var(--accent-glow) !important;
    width: 100% !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent-light) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-light) !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    margin-bottom: 0.75rem !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    border-left: 3px solid var(--accent) !important;
}
[data-testid="stChatMessage"][data-testid*="assistant"] {
    border-left: 3px solid var(--accent2) !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── Divider ── */
hr {
    border-color: var(--border-subtle) !important;
    margin: 0.75rem 0 !important;
}

/* ── Expander ── */
details {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
}

/* ── Alerts ── */
.stAlert {
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

/* ── Code font ── */
code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    background: rgba(124,58,237,0.12) !important;
    padding: 1px 5px !important;
    border-radius: 4px !important;
    color: var(--accent-light) !important;
}

/* ── Source badge ── */
.source-badge {
    display: inline-block;
    background: rgba(124,58,237,0.15);
    border: 1px solid rgba(124,58,237,0.4);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
    color: var(--accent-light);
    margin: 2px 3px;
    font-family: 'JetBrains Mono', monospace;
    max-width: 260px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;
}
.source-badge.youtube { border-color: rgba(239,68,68,0.5); color: #f87171; background: rgba(239,68,68,0.1); }
.source-badge.web     { border-color: rgba(6,182,212,0.5); color: #22d3ee; background: rgba(6,182,212,0.1); }
.source-badge.ocr     { border-color: rgba(245,158,11,0.5); color: #fbbf24; background: rgba(245,158,11,0.1); }

/* ── Doc list item ── */
.doc-item {
    background: var(--bg-hover);
    border-radius: 8px;
    padding: 0.4rem 0.7rem;
    margin: 0.25rem 0;
    font-size: 0.8rem;
    color: var(--text-secondary);
    border-left: 3px solid var(--accent);
    font-family: 'JetBrains Mono', monospace;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.doc-item.youtube { border-left-color: #ef4444; }
.doc-item.web     { border-left-color: #06b6d4; }

/* ── Chunk counter pill ── */
.chunk-pill {
    display: inline-block;
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.4);
    color: #34d399;
    border-radius: 20px;
    padding: 1px 8px;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
    margin-left: 6px;
}

/* ── Typing cursor animation ── */
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
}
.typing-cursor::after {
    content: '▋';
    animation: blink 0.8s infinite;
    color: var(--accent-light);
    margin-left: 2px;
}

/* ── Status dot ── */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.status-dot.online  { background: var(--success); box-shadow: 0 0 6px var(--success); }
.status-dot.offline { background: var(--error);   box-shadow: 0 0 6px var(--error); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingested_sources" not in st.session_state:
    st.session_state.ingested_sources = []  # list of dicts: {name, type, chunks}
if "backend_ok" not in st.session_state:
    st.session_state.backend_ok = False

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def check_backend() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def get_source_type(name: str) -> str:
    if "youtube" in name.lower() or "youtu.be" in name.lower():
        return "youtube"
    if name.startswith("http"):
        return "web"
    return "doc"

def source_icon(stype: str) -> str:
    return {"youtube": "🎥", "web": "🌐", "doc": "📄", "ocr": "🔍"}.get(stype, "📎")

def render_source_badges(sources: list[str]):
    if not sources:
        return
    badges_html = ""
    for s in sources:
        stype = get_source_type(s)
        label = s if len(s) <= 40 else s[:37] + "…"
        icon = source_icon(stype)
        badges_html += f'<span class="source-badge {stype}">{icon} {label}</span>'
    st.markdown(f'<div style="margin-top:0.5rem">{badges_html}</div>', unsafe_allow_html=True)

def typing_effect(placeholder, full_text: str, delay: float = 0.012):
    """Stream text word-by-word into a placeholder."""
    words = full_text.split(" ")
    displayed = ""
    for i, word in enumerate(words):
        displayed += ("" if i == 0 else " ") + word
        placeholder.markdown(
            f'<div class="typing-cursor">{displayed}</div>',
            unsafe_allow_html=True,
        )
        time.sleep(delay)
    # Final render without cursor
    placeholder.markdown(displayed)


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    # Logo / title
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 1.2rem">
        <div style="font-size:2.2rem">🔮</div>
        <div style="font-size:1.3rem; font-weight:700; color:#f0eeff; letter-spacing:2px">LUMI</div>
        <div style="font-size:0.72rem; color:#6b6484; letter-spacing:1px; margin-top:2px">AI KNOWLEDGE ASSISTANT</div>
    </div>
    """, unsafe_allow_html=True)

    # Backend status
    st.session_state.backend_ok = check_backend()
    dot_cls = "online" if st.session_state.backend_ok else "offline"
    status_text = "Backend connected" if st.session_state.backend_ok else "Backend offline"
    st.markdown(
        f'<div style="font-size:0.78rem; color:#a89fcf; margin-bottom:1rem">'
        f'<span class="status-dot {dot_cls}"></span>{status_text}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── DOCUMENT UPLOAD ──
    st.markdown('<p style="font-size:0.78rem;color:#6b6484;letter-spacing:1px;margin-bottom:0.4rem">📄 DOCUMENTS</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "txt", "docx", "pptx", "xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files and st.button("⚡ Ingest Documents"):
        if not st.session_state.backend_ok:
            st.error("Backend is offline.")
        else:
            files_payload = [
                ("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files
            ]
            with st.spinner(f"Processing {len(uploaded_files)} file(s)…"):
                try:
                    res = requests.post(f"{BACKEND_URL}/ingest/document", files=files_payload, timeout=120)
                    if res.status_code == 200:
                        data = res.json()
                        for r in data.get("results", []):
                            if r["status"] == "success":
                                st.session_state.ingested_sources.append({
                                    "name": r["filename"],
                                    "type": "doc",
                                    "chunks": r["chunks"],
                                })
                        st.success(data.get("message", "Done!"))
                        if data.get("total_chunks", 0):
                            st.markdown(
                                f'<span class="chunk-pill">✦ {data["total_chunks"]} chunks stored</span>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Upload failed')}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    st.markdown("---")

    # ── YOUTUBE INGESTION ──
    st.markdown('<p style="font-size:0.78rem;color:#6b6484;letter-spacing:1px;margin-bottom:0.4rem">🎥 YOUTUBE</p>', unsafe_allow_html=True)
    yt_urls_input = st.text_area(
        "YouTube URLs (one per line)",
        placeholder="https://youtube.com/watch?v=...\nhttps://youtu.be/...",
        height=90,
        label_visibility="collapsed",
    )
    if st.button("⚡ Ingest YouTube"):
        if not st.session_state.backend_ok:
            st.error("Backend is offline.")
        elif not yt_urls_input.strip():
            st.warning("Enter at least one YouTube URL.")
        else:
            yt_urls = [u.strip() for u in yt_urls_input.strip().splitlines() if u.strip()]
            for yt_url in yt_urls:
                with st.spinner(f"Fetching transcript…"):
                    try:
                        res = requests.post(
                            f"{BACKEND_URL}/ingest/youtube",
                            params={"url": yt_url},
                            timeout=90,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            chunks = data.get("chunks", 0)
                            vid_id = data.get("video_id", "video")
                            st.session_state.ingested_sources.append({
                                "name": yt_url,
                                "type": "youtube",
                                "chunks": chunks,
                            })
                            st.success(f"✅ {vid_id}")
                            st.markdown(
                                f'<span class="chunk-pill">✦ {chunks} chunks</span>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error(res.json().get("detail", "Failed"))
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")

    # ── WEB INGESTION ──
    st.markdown('<p style="font-size:0.78rem;color:#6b6484;letter-spacing:1px;margin-bottom:0.4rem">🌐 WEB PAGES</p>', unsafe_allow_html=True)
    web_urls_input = st.text_area(
        "Web URLs (one per line)",
        placeholder="https://example.com\nhttps://docs.something.io/page",
        height=90,
        label_visibility="collapsed",
    )
    if st.button("⚡ Ingest Web Pages"):
        if not st.session_state.backend_ok:
            st.error("Backend is offline.")
        elif not web_urls_input.strip():
            st.warning("Enter at least one URL.")
        else:
            web_urls = [u.strip() for u in web_urls_input.strip().splitlines() if u.strip()]
            for web_url in web_urls:
                with st.spinner(f"Scraping {web_url[:40]}…"):
                    try:
                        res = requests.post(
                            f"{BACKEND_URL}/ingest/web",
                            params={"url": web_url},
                            timeout=30,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            chunks = data.get("chunks", 0)
                            st.session_state.ingested_sources.append({
                                "name": web_url,
                                "type": "web",
                                "chunks": chunks,
                            })
                            st.success(f"✅ Scraped")
                            st.markdown(
                                f'<span class="chunk-pill">✦ {chunks} chunks</span>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.error(res.json().get("detail", "Failed"))
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")

    # ── KNOWLEDGE BASE STATUS ──
    if st.session_state.ingested_sources:
        total_chunks = sum(s.get("chunks", 0) for s in st.session_state.ingested_sources)
        st.markdown(
            f'<p style="font-size:0.78rem;color:#6b6484;letter-spacing:1px;margin-bottom:0.4rem">'
            f'📚 KNOWLEDGE BASE '
            f'<span class="chunk-pill">✦ {total_chunks} total chunks</span></p>',
            unsafe_allow_html=True,
        )
        for src in st.session_state.ingested_sources[-10:]:  # show last 10
            stype = src.get("type", "doc")
            icon = source_icon(stype)
            name = src["name"]
            display = (name[:32] + "…") if len(name) > 35 else name
            chunks = src.get("chunks", 0)
            st.markdown(
                f'<div class="doc-item {stype}">{icon} {display}'
                f'{"" if not chunks else f"<span class=chunk-pill>{chunks}</span>"}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")
        if st.button("🗑️ Clear Knowledge Base"):
            st.session_state.ingested_sources = []
            st.rerun()

    st.markdown("---")

    # ── CLEAR CHAT ──
    if st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()


# ─────────────────────────────────────────
# MAIN CHAT AREA
# ─────────────────────────────────────────
# Header
st.markdown("""
<div style="margin-bottom:1.5rem">
    <h1 style="font-size:1.8rem; font-weight:700; color:#f0eeff; margin:0; letter-spacing:1px">
        🔮 Lumi
        <span style="font-size:1rem; font-weight:300; color:#6b6484; margin-left:8px">
            AI Knowledge Assistant
        </span>
    </h1>
    <p style="color:#6b6484; font-size:0.85rem; margin:4px 0 0">
        Chat with your documents, YouTube videos, and web pages
    </p>
</div>
""", unsafe_allow_html=True)

# Welcome message when no chat
if not st.session_state.messages:
    st.markdown("""
    <div style="
        text-align:center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(6,182,212,0.05));
        border: 1px solid rgba(124,58,237,0.15);
        border-radius: 16px;
        margin: 2rem 0;
    ">
        <div style="font-size:3rem; margin-bottom:1rem">🔮</div>
        <h2 style="font-size:1.3rem; color:#f0eeff; font-weight:600; margin-bottom:0.5rem">
            Start by adding your knowledge
        </h2>
        <p style="color:#6b6484; font-size:0.88rem; max-width:400px; margin:0 auto">
            Upload PDFs, paste YouTube links, or add website URLs in the sidebar.
            Then ask anything about your content.
        </p>
        <div style="margin-top:1.5rem; display:flex; gap:1rem; justify-content:center; flex-wrap:wrap">
            <span style="background:rgba(124,58,237,0.15);border:1px solid rgba(124,58,237,0.3);
                         border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#9d5cff">
                📄 PDF / DOCX / PPTX
            </span>
            <span style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                         border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#f87171">
                🎥 YouTube Videos
            </span>
            <span style="background:rgba(6,182,212,0.1);border:1px solid rgba(6,182,212,0.3);
                         border-radius:20px;padding:4px 14px;font-size:0.78rem;color:#22d3ee">
                🌐 Web Pages
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Render chat history ──
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            sources = message.get("sources", [])
            if sources:
                render_source_badges(sources)

# ── Chat input ──
prompt = st.chat_input("Ask Lumi anything about your knowledge base…")

if prompt:
    if not st.session_state.backend_ok:
        st.error("⚠️ Backend is offline. Start it with: `uvicorn backend.main:app --reload`")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend and stream response
    with st.chat_message("assistant"):
        answer_placeholder = st.empty()
        answer_placeholder.markdown(
            '<div class="typing-cursor" style="color:#6b6484">Thinking…</div>',
            unsafe_allow_html=True,
        )

        try:
            res = requests.post(
                f"{BACKEND_URL}/chat",
                json={"question": prompt},
                timeout=60,
            )

            if res.status_code == 200:
                data = res.json()
                answer = data.get("answer", "No answer returned.")
                sources = data.get("sources", [])

                # Typing animation
                typing_effect(answer_placeholder, answer, delay=0.008)

                # Source badges
                if sources:
                    render_source_badges(sources)

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })

            else:
                error_msg = res.json().get("detail", "Unknown error from backend.")
                answer_placeholder.error(f"⚠️ {error_msg}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {error_msg}",
                    "sources": [],
                })

        except requests.exceptions.Timeout:
            answer_placeholder.error("⏱️ Request timed out. The LLM is taking too long. Try again.")
        except requests.exceptions.ConnectionError:
            answer_placeholder.error("🔌 Cannot connect to backend. Make sure it's running.")
        except Exception as e:
            answer_placeholder.error(f"❌ Unexpected error: {str(e)}")