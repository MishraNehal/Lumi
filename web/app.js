const API_URL = "http://127.0.0.1:8000";
const state = { token: localStorage.getItem("lumi_token"), email: localStorage.getItem("lumi_email"), authMode: "login", conversationId: null, messages: [] };
const $ = (id) => document.getElementById(id);

function setVisible(id, visible) { $(id).classList.toggle("hidden", !visible); }
function headers(extra = {}) { return { ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}), ...extra }; }
async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, { ...options, headers: headers(options.headers || {}) });
  let data = {};
  try { data = await response.json(); } catch {}
  if (!response.ok) throw new Error(data.detail || "Request failed.");
  return data;
}
function showToast(message, error = false) { $("toast").textContent = message; $("toast").style.color = error ? "var(--danger)" : "#6ee7b7"; }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char])); }
function renderMarkdown(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

function setAuthMode(mode) {
  state.authMode = mode;
  document.querySelectorAll("[data-auth-mode]").forEach((button) => button.classList.toggle("active", button.dataset.authMode === mode));
  $("auth-submit").textContent = mode === "login" ? "Log in" : "Create account";
  $("auth-password").autocomplete = mode === "login" ? "current-password" : "new-password";
  $("auth-error").textContent = "";
}

async function submitAuth(event) {
  event.preventDefault();
  $("auth-error").textContent = "";
  try {
    const data = await api(`/auth/${state.authMode === "login" ? "login" : "signup"}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: $("auth-email").value.trim(), password: $("auth-password").value }),
    });
    state.token = data.access_token;
    state.email = $("auth-email").value.trim();
    localStorage.setItem("lumi_token", state.token);
    localStorage.setItem("lumi_email", state.email);
    await showApp();
  } catch (error) { $("auth-error").textContent = error.message; }
}

async function showApp() {
  setVisible("auth-view", false); setVisible("app-view", true); $("user-email").textContent = state.email || "";
  await Promise.all([loadConversations(), loadSources()]);
}
function logout() { localStorage.clear(); state.token = null; state.email = null; setVisible("app-view", false); setVisible("auth-view", true); }

async function loadConversations() {
  const search = $("conversation-search").value.trim();
  const conversations = await api(`/conversations${search ? `?search=${encodeURIComponent(search)}` : ""}`);
  $("conversation-list").innerHTML = conversations.map((conversation) => `
    <div class="conversation ${conversation.id === state.conversationId ? "active" : ""}">
      <button class="conversation-title ghost" data-open="${conversation.id}">${conversation.is_favorite ? "★ " : ""}${escapeHtml(conversation.title || "Untitled")}</button>
      <button class="conversation-action" data-favorite="${conversation.id}" title="Favorite">★</button>
      <button class="conversation-action" data-delete-conversation="${conversation.id}" title="Delete">×</button>
    </div>`).join("") || '<p class="muted">No chats yet.</p>';
}
async function loadSources() {
  const sources = await api("/sources");
  $("source-filter").innerHTML = '<option value="">All sources</option>' + sources.map((source) => `<option value="${escapeHtml(source.filename)}">${escapeHtml(source.source_type)}: ${escapeHtml(source.filename)}</option>`).join("");
  $("source-list").innerHTML = sources.map((source) => `<div class="source-item"><span>${source.source_type === "youtube" ? "🎥" : source.source_type === "web" ? "🌐" : "📄"}</span><span class="source-name" title="${escapeHtml(source.filename)}">${escapeHtml(source.filename)}</span><button class="source-delete" data-delete-source="${encodeURIComponent(source.filename)}">×</button></div>`).join("") || '<p class="muted">Nothing ingested yet.</p>';
}
async function openConversation(id) {
  state.conversationId = Number(id); state.messages = await api(`/conversations/${id}/messages`); renderMessages(); await loadConversations();
}
function renderMessages() {
  const list = $("message-list");
  if (!state.messages.length) { list.innerHTML = '<div class="empty-state"><div class="empty-icon">✦</div><h3>Start a conversation</h3><p>Upload a source, then ask Lumi anything about it.</p></div>'; return; }
  list.innerHTML = state.messages.map((message) => `<article class="message ${message.role}"><div class="message-label">${message.role === "user" ? "YOU" : "LUMI"}</div><p>${message.role === "assistant" ? renderMarkdown(message.content) : escapeHtml(message.content).replace(/\n/g, "<br>")}</p>${message.sources?.length ? `<div class="message-meta">Sources: ${escapeHtml(message.sources.join(", "))}</div>` : ""}${message.verified === false ? '<div class="message-meta">⚠️ This answer needs review.</div>' : ""}</article>`).join("");
  list.scrollTop = list.scrollHeight;
}

async function sendQuestion(event) {
  event.preventDefault();
  const question = $("question").value.trim(); if (!question) return;
  $("question").value = ""; state.messages.push({ role: "user", content: question, sources: [] }); renderMessages();
  const assistant = { role: "assistant", content: "", sources: [], verified: true }; state.messages.push(assistant); renderMessages();
  const response = await fetch(`${API_URL}/chat/stream`, { method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify({ question, conversation_id: state.conversationId, source_filter: $("source-filter").value ? { filename: $("source-filter").value } : null }) });
  if (!response.ok || !response.body) { assistant.content = "Unable to reach Lumi."; renderMessages(); return; }
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  while (true) {
    const { value, done } = await reader.read(); if (done) break; buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n"); buffer = events.pop();
    for (const eventText of events) {
      const line = eventText.split("\n").find((entry) => entry.startsWith("data: ")); if (!line) continue;
      const eventData = JSON.parse(line.slice(6));
      if (eventData.token) assistant.content += eventData.token;
      if (eventData.done) { state.conversationId = eventData.conversation_id || state.conversationId; assistant.sources = eventData.sources || []; assistant.verified = eventData.verified; }
      renderMessages();
    }
  }
  await loadConversations();
}

async function ingestDocuments() {
  const files = $("document-files").files; if (!files.length) return showToast("Choose at least one file.", true);
  const form = new FormData(); [...files].forEach((file) => form.append("files", file));
  try { const result = await api("/ingest/document", { method: "POST", body: form }); showToast(result.message); $("document-files").value = ""; await loadSources(); } catch (error) { showToast(error.message, true); }
}
async function ingestUrl(type, inputId) {
  const url = $(inputId).value.trim(); if (!url) return showToast("Enter a URL first.", true);
  try { const result = await api(`/ingest/${type}?url=${encodeURIComponent(url)}`, { method: "POST" }); showToast(`${result.message} (${result.chunks} chunks)`); $(inputId).value = ""; await loadSources(); } catch (error) { showToast(error.message, true); }
}

document.querySelectorAll("[data-auth-mode]").forEach((button) => button.addEventListener("click", () => setAuthMode(button.dataset.authMode)));
$("auth-form").addEventListener("submit", submitAuth); $("logout").addEventListener("click", logout);
$("new-chat").addEventListener("click", () => { state.conversationId = null; state.messages = []; renderMessages(); loadConversations(); });
$("chat-form").addEventListener("submit", sendQuestion); $("upload-documents").addEventListener("click", ingestDocuments);
$("ingest-web").addEventListener("click", () => ingestUrl("web", "web-url")); $("ingest-youtube").addEventListener("click", () => ingestUrl("youtube", "youtube-url"));
$("conversation-search").addEventListener("input", () => loadConversations().catch((error) => showToast(error.message, true)));
$("conversation-list").addEventListener("click", async (event) => {
  const open = event.target.closest("[data-open]"); const favorite = event.target.closest("[data-favorite]"); const remove = event.target.closest("[data-delete-conversation]");
  try {
    if (open) await openConversation(open.dataset.open);
    if (favorite) { await api(`/conversations/${favorite.dataset.favorite}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ is_favorite: true }) }); await loadConversations(); }
    if (remove) { await api(`/conversations/${remove.dataset.deleteConversation}`, { method: "DELETE" }); if (state.conversationId === Number(remove.dataset.deleteConversation)) { state.conversationId = null; state.messages = []; renderMessages(); } await loadConversations(); }
  } catch (error) { showToast(error.message, true); }
});
$("source-list").addEventListener("click", async (event) => { const button = event.target.closest("[data-delete-source]"); if (!button) return; try { await api(`/sources/${button.dataset.deleteSource}`, { method: "DELETE" }); await loadSources(); } catch (error) { showToast(error.message, true); } });

if (state.token) showApp().catch(() => logout());
