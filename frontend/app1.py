import streamlit as st
import requests
import json

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Lumi", page_icon="🔮", layout="wide")

for key, default in {
    "token": None, "email": None, "conversation_id": None, "messages": [],
    "show_archived": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_post(path, json=None, files=None, params=None):
    return requests.post(f"{BACKEND_URL}{path}", json=json, files=files,
                          params=params, headers=auth_headers())


def api_get(path, params=None):
    return requests.get(f"{BACKEND_URL}{path}", params=params, headers=auth_headers())


def api_patch(path, json=None):
    return requests.patch(f"{BACKEND_URL}{path}", json=json, headers=auth_headers())


def api_delete(path):
    return requests.delete(f"{BACKEND_URL}{path}", headers=auth_headers())


def api_stream(path, json_body):
    return requests.post(f"{BACKEND_URL}{path}", json=json_body,
                          headers=auth_headers(), stream=True)


# ══════════════════════════════ LOGIN GATE ══════════════════════════════
if not st.session_state.token:
    st.title("🔮 Lumi")
    tab_login, tab_signup = st.tabs(["Login", "Sign up"])
    for tab, endpoint in [(tab_login, "/auth/login"), (tab_signup, "/auth/signup")]:
        with tab:
            email = st.text_input("Email", key=endpoint + "_email")
            password = st.text_input("Password", type="password", key=endpoint + "_pw")
            if st.button("Continue", key=endpoint + "_btn"):
                r = requests.post(f"{BACKEND_URL}{endpoint}", json={"email": email, "password": password})
                if r.status_code == 200:
                    st.session_state.token = r.json()["access_token"]
                    st.session_state.email = email
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Failed."))
    st.stop()

# ══════════════════════════════ SIDEBAR ══════════════════════════════
with st.sidebar:
    st.markdown(f"**{st.session_state.email}**")

    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    search_q = st.text_input("🔍 Search chats", label_visibility="collapsed", placeholder="Search chats...")
    st.session_state.show_archived = st.checkbox("Show archived", value=st.session_state.show_archived)

    params = {}
    if search_q:
        params["search"] = search_q
    if st.session_state.show_archived:
        params["archived"] = True

    convs = api_get("/conversations", params=params).json()

    for c in convs:
        cols = st.columns([5, 1, 1, 1])
        title = ("⭐ " if c["is_favorite"] else "") + (c["title"] or "Untitled")
        if cols[0].button(title, key=f"open_{c['id']}", use_container_width=True):
            st.session_state.conversation_id = c["id"]
            st.session_state.messages = api_get(f"/conversations/{c['id']}/messages").json()
            st.rerun()
        if cols[1].button("⭐", key=f"fav_{c['id']}", help="Favorite"):
            api_patch(f"/conversations/{c['id']}", json={"is_favorite": not c["is_favorite"]})
            st.rerun()
        if cols[2].button("🗄", key=f"arc_{c['id']}", help="Archive/Unarchive"):
            api_patch(f"/conversations/{c['id']}", json={"is_archived": not c["is_archived"]})
            st.rerun()
        if cols[3].button("🗑", key=f"del_{c['id']}", help="Delete"):
            api_delete(f"/conversations/{c['id']}")
            if st.session_state.conversation_id == c["id"]:
                st.session_state.conversation_id = None
                st.session_state.messages = []
            st.rerun()

        with st.expander("✏️ Rename"):
            new_title = st.text_input("New title", value=c["title"], key=f"rename_input_{c['id']}",
                                       label_visibility="collapsed")
            if st.button("Save", key=f"rename_save_{c['id']}"):
                api_patch(f"/conversations/{c['id']}", json={"title": new_title})
                st.rerun()

    st.divider()
    if st.button("Logout", use_container_width=True):
        st.session_state.token = None
        st.session_state.messages = []
        st.rerun()

# ══════════════════════════════ MAIN LAYOUT ══════════════════════════════
col_chat, col_sources = st.columns([3, 1])

with col_chat:
    st.markdown("### 🔮 Lumi")

    src_list = api_get("/sources").json()
    src_options = {"All sources": None}
    for s in src_list:
        src_options[f"{s['source_type']}: {s['filename']}"] = {"filename": s["filename"]}
    chosen_label = st.selectbox("Ask this source", list(src_options.keys()), label_visibility="collapsed")
    active_filter = src_options[chosen_label]

    for msg in st.session_state.messages:
        with col_chat.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                st.caption("Sources: " + ", ".join(msg["sources"]))
            if msg.get("verified") is False:
                st.caption("⚠️ Faithfulness check flagged this answer for review.")

with col_sources:
    st.markdown("#### 📥 Add Sources")
    tab_doc, tab_web, tab_yt = st.tabs(["📄 Doc", "🌐 Web", "🎥 YouTube"])

    with tab_doc:
        files = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")
        if st.button("Ingest document(s)", use_container_width=True) and files:
            with st.spinner("Ingesting..."):
                payload = [("files", (f.name, f.getvalue())) for f in files]
                r = api_post("/ingest/document", files=payload)
            if r.status_code == 200:
                data = r.json()
                st.success(data.get("message", "Done."))
                for res in data.get("results", []):
                    if res["status"] == "success":
                        st.caption(f"✅ {res['filename']} — {res['chunks']} chunks created")
                    else:
                        st.caption(f"❌ {res['filename']} — {res['message']}")
            else:
                st.error(r.text)

    with tab_web:
        url = st.text_input("Website URL", label_visibility="collapsed", placeholder="https://...")
        if st.button("Ingest web page", use_container_width=True) and url:
            with st.spinner("Scraping..."):
                r = api_post("/ingest/web", params={"url": url})
            if r.status_code == 200:
                data = r.json()
                st.success(data.get("message", "Done."))
                st.caption(f"📦 {data.get('chunks', 0)} chunks created")
            else:
                st.error(r.text)

    with tab_yt:
        yt_url = st.text_input("YouTube URL", label_visibility="collapsed", placeholder="https://youtube.com/...")
        if st.button("Ingest video", use_container_width=True) and yt_url:
            with st.spinner("Fetching transcript..."):
                r = api_post("/ingest/youtube", params={"url": yt_url})
            if r.status_code == 200:
                data = r.json()
                st.success(data.get("message", "Done."))
                st.caption(f"📦 {data.get('chunks', 0)} timestamped chunks created")
            else:
                st.error(r.text)

    st.markdown("#### 📚 Your Sources")
    if not src_list:
        st.caption("Nothing ingested yet.")
    for s in src_list:
        icon = {"document": "📄", "web": "🌐", "youtube": "🎥", "ocr": "🖨️"}.get(s["source_type"], "📁")
        row = st.columns([4, 1])
        row[0].write(f"{icon} {s['filename']}")
        if row[1].button("🗑", key=f"delsrc_{s['filename']}"):
            r = api_delete(f"/sources/{s['filename']}")
            if r.status_code == 200:
                st.rerun()
            else:
                st.error("Failed to delete.")

# ══════════════════════════════ CHAT INPUT — kept at root level so it stays pinned to bottom ══════════════════════════════
question = st.chat_input("Ask something...")
if question:
    st.session_state.messages.append({"role": "user", "content": question, "sources": []})
    col_chat.chat_message("user").write(question)

    with col_chat.chat_message("assistant"):
        status_placeholder = st.empty()
        placeholder = st.empty()
        full_answer = ""
        sources = []
        conv_id = st.session_state.conversation_id
        verified = True

        try:
            r = api_stream("/chat/stream", {
                "question": question,
                "conversation_id": st.session_state.conversation_id,
                "source_filter": active_filter,
            })
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                payload = json.loads(line[len("data: "):])

                if payload.get("status"):
                    status_placeholder.caption(f"🔄 {payload['status']}...")
                    continue

                if payload.get("done"):
                    sources = payload.get("sources", [])
                    conv_id = payload.get("conversation_id", conv_id)
                    verified = payload.get("verified", True)
                    break

                full_answer += payload.get("token", "")
                placeholder.markdown(full_answer + "▌")

            status_placeholder.empty()
            placeholder.markdown(full_answer)
            if sources:
                st.caption("Sources: " + ", ".join(sources))
            if not verified:
                st.caption("⚠️ Faithfulness check flagged this answer for review.")

            st.session_state.conversation_id = conv_id
            st.session_state.messages.append({
                "role": "assistant", "content": full_answer, "sources": sources, "verified": verified,
            })
        except Exception as e:
            st.error(f"Something went wrong: {e}")