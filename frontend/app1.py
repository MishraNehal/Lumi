import streamlit as st
import requests
import json

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Lumi", page_icon="🔮", layout="wide", initial_sidebar_state="expanded")

for key, default in {
    "token": None, "email": None, "conversation_id": None, "messages": [],
    "page": "💬 Chat", "show_archived": False, "theme": "dark",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════ THEME / CSS ══════════════════════════════
def inject_css(theme: str):
    if theme == "dark":
        bg, bg2, card, text, subtext, border = "#0f1117", "#161923", "#1c1f2b", "#f1f2f6", "#9aa0ac", "#2a2e3d"
    else:
        bg, bg2, card, text, subtext, border = "#f7f8fb", "#ffffff", "#ffffff", "#1a1d29", "#6b7280", "#e5e7eb"

    st.markdown(f"""
    <style>
        :root {{
            --grad: linear-gradient(135deg, #7c5cff 0%, #ff5cc4 100%);
        }}
        .stApp {{ background: {bg}; color: {text}; }}
        section[data-testid="stSidebar"] {{ background: {bg2}; border-right: 1px solid {border}; }}

        h1, h2, h3 {{ color: {text}; }}
        .lumi-title {{
            font-size: 1.6rem; font-weight: 800;
            background: var(--grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }}
        .lumi-subtitle {{ color: {subtext}; font-size: 0.85rem; margin-bottom: 1rem; }}

        div[data-testid="stChatMessage"] {{
            background: {card}; border: 1px solid {border}; border-radius: 14px;
            padding: 0.6rem 0.9rem; margin-bottom: 0.5rem;
        }}

        .stButton>button {{
            border-radius: 10px; border: 1px solid {border}; background: {card}; color: {text};
        }}
        .stButton>button:hover {{ border-color: #7c5cff; color: #7c5cff; }}

        div[data-testid="stChatInput"] textarea {{
            background: {card} !important; border-radius: 14px !important; border: 1px solid {border} !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {card}; border: 1px solid {border} !important; border-radius: 14px !important;
        }}

        .source-badge {{
            display: inline-block; padding: 2px 10px; border-radius: 999px;
            background: var(--grad); color: white; font-size: 0.72rem; font-weight: 600;
        }}

        [data-testid="stMetricValue"] {{ color: #7c5cff; }}
    </style>
    """, unsafe_allow_html=True)


inject_css(st.session_state.theme)


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
    st.markdown('<div class="lumi-title">🔮 Lumi</div>', unsafe_allow_html=True)
    st.markdown('<div class="lumi-subtitle">Your AI Personal Knowledge Assistant</div>', unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Login", "Sign up"])
    for tab, endpoint in [(tab_login, "/auth/login"), (tab_signup, "/auth/signup")]:
        with tab:
            with st.container(border=True):
                email = st.text_input("Email", key=endpoint + "_email")
                password = st.text_input("Password", type="password", key=endpoint + "_pw")
                if st.button("Continue", key=endpoint + "_btn", use_container_width=True):
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
    top = st.columns([4, 1])
    top[0].markdown('<div class="lumi-title">🔮 Lumi</div>', unsafe_allow_html=True)
    if top[1].button("🌗", help="Toggle theme"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

    st.caption(st.session_state.email)

    st.session_state.page = st.radio(
        "Navigate", ["💬 Chat", "📚 Study Mode", "📊 Eval Dashboard"],
        label_visibility="collapsed",
    )
    st.divider()

    if st.session_state.page == "💬 Chat":
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

        search_q = st.text_input("🔍 Search chats", label_visibility="collapsed", placeholder="Search chats...")
        st.session_state.show_archived = st.checkbox("Show archived", value=st.session_state.show_archived)

        params = {}
        if search_q:
            params["search"] = search_q
        if st.session_state.show_archived:
            params["archived"] = True

        convs = api_get("/conversations", params=params).json()

        for c in convs:
            with st.container(border=True):
                cols = st.columns([5, 1, 1, 1])
                title = ("⭐ " if c["is_favorite"] else "") + (c["title"] or "Untitled")
                is_active = st.session_state.conversation_id == c["id"]
                if cols[0].button(("👉 " if is_active else "") + title, key=f"open_{c['id']}", use_container_width=True):
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

# ══════════════════════════════ PAGE: CHAT ══════════════════════════════
if st.session_state.page == "💬 Chat":
    col_chat, col_sources = st.columns([3, 1])

    with col_chat:
        st.markdown('<div class="lumi-title">🔮 Lumi</div>', unsafe_allow_html=True)

        src_list = api_get("/sources").json()
        src_options = {"All sources": None}
        for s in src_list:
            src_options[f"{s['source_type']}: {s['filename']}"] = {"filename": s["filename"]}
        chosen_label = st.selectbox("Ask this source", list(src_options.keys()), label_visibility="collapsed")
        active_filter = src_options[chosen_label]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("sources"):
                    badges = " ".join(f'<span class="source-badge">{s}</span>' for s in msg["sources"])
                    st.markdown(badges, unsafe_allow_html=True)
                if msg.get("verified") is False:
                    st.caption("⚠️ Faithfulness check flagged this answer for review.")

        question = st.chat_input("Ask something...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question, "sources": []})
            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
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
                        badges = " ".join(f'<span class="source-badge">{s}</span>' for s in sources)
                        st.markdown(badges, unsafe_allow_html=True)
                    if not verified:
                        st.caption("⚠️ Faithfulness check flagged this answer for review.")

                    st.session_state.conversation_id = conv_id
                    st.session_state.messages.append({
                        "role": "assistant", "content": full_answer, "sources": sources, "verified": verified,
                    })
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    with col_sources:
        st.markdown("#### 📥 Add Sources")
        tab_doc, tab_web, tab_yt = st.tabs(["📄 Doc", "🌐 Web", "🎥 YouTube"])

        with tab_doc:
            with st.container(border=True):
                files = st.file_uploader("Upload", accept_multiple_files=True, label_visibility="collapsed")
                if st.button("Ingest document(s)", use_container_width=True) and files:
                    with st.spinner("Ingesting..."):
                        payload = [("files", (f.name, f.getvalue())) for f in files]
                        r = api_post("/ingest/document", files=payload)
                    st.success(r.json().get("message")) if r.status_code == 200 else st.error(r.text)

        with tab_web:
            with st.container(border=True):
                url = st.text_input("Website URL", label_visibility="collapsed", placeholder="https://...")
                if st.button("Ingest web page", use_container_width=True) and url:
                    with st.spinner("Scraping..."):
                        r = api_post("/ingest/web", params={"url": url})
                    st.success(r.json().get("message")) if r.status_code == 200 else st.error(r.text)

        with tab_yt:
            with st.container(border=True):
                yt_url = st.text_input("YouTube URL", label_visibility="collapsed", placeholder="https://youtube.com/...")
                if st.button("Ingest video", use_container_width=True) and yt_url:
                    with st.spinner("Fetching transcript..."):
                        r = api_post("/ingest/youtube", params={"url": yt_url})
                    st.success(r.json().get("message")) if r.status_code == 200 else st.error(r.text)

        st.markdown("#### 📚 Your Sources")
        if not src_list:
            st.caption("Nothing ingested yet.")
        for s in src_list:
            with st.container(border=True):
                icon = {"document": "📄", "web": "🌐", "youtube": "🎥", "ocr": "🖨️"}.get(s["source_type"], "📁")
                st.markdown(f"{icon} **{s['filename']}**")

# ══════════════════════════════ PAGE: STUDY MODE ══════════════════════════════
elif st.session_state.page == "📚 Study Mode":
    st.markdown('<div class="lumi-title">📚 Study Mode</div>', unsafe_allow_html=True)

    src_list = api_get("/sources").json()
    src_options = {"All sources": None}
    for s in src_list:
        src_options[f"{s['source_type']}: {s['filename']}"] = {"filename": s["filename"]}

    with st.container(border=True):
        chosen_label = st.selectbox("Generate quiz from", list(src_options.keys()))
        num_q = st.slider("Number of questions", 3, 10, 5)
        if st.button("🎯 Generate Quiz", use_container_width=True):
            with st.spinner("Generating quiz from your material..."):
                r = api_post("/study/quiz", json={"source_filter": src_options[chosen_label], "num_questions": num_q})
            if r.status_code == 200:
                st.session_state.quiz = r.json()["questions"]
            else:
                st.error(r.json().get("detail", "Failed to generate quiz."))

    if st.session_state.get("quiz"):
        for i, q in enumerate(st.session_state.quiz):
            with st.container(border=True):
                st.markdown(f"**Q{i + 1}. {q['question']}**")
                choice = st.radio("Options", q["options"], key=f"quiz_{i}", label_visibility="collapsed")
                if st.button("Check", key=f"check_{i}"):
                    correct = q["options"][q["correct_index"]]
                    if choice == correct:
                        st.success(f"✅ Correct! {q.get('explanation', '')}")
                    else:
                        st.error(f"❌ Correct answer: {correct}. {q.get('explanation', '')}")

# ══════════════════════════════ PAGE: EVAL DASHBOARD ══════════════════════════════
elif st.session_state.page == "📊 Eval Dashboard":
    st.markdown('<div class="lumi-title">📊 RAG Evaluation Dashboard</div>', unsafe_allow_html=True)

    stats = api_get("/eval/stats").json()
    if stats.get("total_queries", 0) == 0:
        st.info("No queries logged yet — ask something in Chat first.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1, st.container(border=True):
            st.metric("Total Queries", stats["total_queries"])
        with c2, st.container(border=True):
            st.metric("Avg Latency (ms)", stats.get("avg_latency_ms") or "—")
        with c3, st.container(border=True):
            st.metric("Unverified Answers", stats.get("unverified_count", 0))

        with st.container(border=True):
            st.markdown("**Confidence breakdown**")
            st.bar_chart(stats.get("confidence_breakdown", {}))

        with st.container(border=True):
            st.markdown("**Recent queries**")
            logs = api_get("/eval/logs").json()
            st.dataframe(logs, use_container_width=True)