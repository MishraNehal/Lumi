import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

# ----------------------------------
# Page Config
# ----------------------------------
st.set_page_config(
    page_title="Lumi",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Lumi – AI Personal Knowledge Assistant")
st.caption("Chat with your web pages, documents, and YouTube videos")

# ----------------------------------
# SESSION STATE (CHAT HISTORY)
# ----------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------------
# SIDEBAR — INGESTION
# ----------------------------------
st.sidebar.header("📥 Ingest Knowledge")

# ---- Web Ingestion ----
web_url = st.sidebar.text_input("🌐 Web URL")
if st.sidebar.button("Ingest Web"):
    if web_url.strip():
        res = requests.post(
            f"{BACKEND_URL}/ingest/web",
            params={"url": web_url}
        )
        if res.status_code == 200:
            st.sidebar.success(res.json().get("message", "Web ingested"))
        else:
            st.sidebar.error("Failed to ingest web")

# ---- YouTube Ingestion ----
yt_url = st.sidebar.text_input("🎥 YouTube URL")
if st.sidebar.button("Ingest YouTube"):
    if yt_url.strip():
        res = requests.post(
            f"{BACKEND_URL}/ingest/youtube",
            params={"url": yt_url}
        )
        if res.status_code == 200:
            st.sidebar.success(res.json().get("message", "YouTube ingested"))
        else:
            st.sidebar.error("Failed to ingest YouTube")

# ---- Document Ingestion ----
uploaded_file = st.sidebar.file_uploader(
    "📄 Upload Document",
    type=["txt", "pdf", "docx"]
)

if uploaded_file and st.sidebar.button("Ingest Document"):
    files = {
        "file": (uploaded_file.name, uploaded_file.getvalue())
    }
    res = requests.post(
        f"{BACKEND_URL}/ingest/document",
        files=files
    )
    if res.status_code == 200:
        st.sidebar.success("Document ingested")
    else:
        st.sidebar.error("Failed to ingest document")

# ---- Clear Chat ----
if st.sidebar.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# ----------------------------------
# RENDER CHAT HISTORY
# ----------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show sources only for assistant messages
        if message["role"] == "assistant":
            sources = message.get("sources", [])
            if sources:
                st.markdown("**Sources used:**")
                for src in sources:
                    st.markdown(f"- {src}")

# ----------------------------------
# CHAT INPUT
# ----------------------------------
prompt = st.chat_input("Ask Lumi...")

if prompt:
    # ---- Show user message ----
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # ---- Call backend ----
    res = requests.post(
        f"{BACKEND_URL}/chat",
        json={"question": prompt}
    )

    if res.status_code == 200:
        data = res.json()

        answer = data.get("answer", "No answer returned")
        sources = data.get("sources", [])

        # ---- Save assistant message ----
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

        with st.chat_message("assistant"):
            st.markdown(answer)
            if sources:
                st.markdown("**Sources used:**")
                for src in sources:
                    st.markdown(f"- {src}")
            else:
                st.markdown("_No sources available_")

    else:
        with st.chat_message("assistant"):
            st.error("Failed to get response from Lumi backend")
