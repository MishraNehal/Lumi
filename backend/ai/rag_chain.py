from backend.ai.prompts import RAG_PROMPT, NO_CONTEXT_RESPONSE, OFF_TOPIC_RESPONSE
from backend.ai.llm import hf_llm
from backend.database.vectorstore import get_vector_store


# ── Score threshold — FAISS L2 distance ──
# Below this = relevant, above this = reject and don't call LLM
RELEVANCE_THRESHOLD = 1.5

# ── Off-topic / greeting detection ──
GREETINGS = {"hi", "hello", "hey", "good morning", "good evening",
             "sup", "what's up", "hii", "helo", "namaste"}

OFF_TOPIC_PATTERNS = [
    "tell me a joke", "what is your name", "who made you",
    "what is 2+2", "capital of", "weather today", "stock price",
    "who is the president", "what day is it", "translate this",
    "write a poem", "write code", "what is love",
]


def is_greeting(question: str) -> bool:
    q = question.lower().strip().rstrip("?!.")
    return q in GREETINGS


def is_off_topic(question: str) -> bool:
    q = question.lower()
    return any(pattern in q for pattern in OFF_TOPIC_PATTERNS)


def get_source_label(doc) -> str:
    """Human-readable source label from document metadata."""
    source_type = doc.metadata.get("source", "unknown")
    if source_type == "youtube":
        url = doc.metadata.get("url", "")
        video_id = doc.metadata.get("video_id", "")
        return url if url else f"YouTube ({video_id})"
    elif source_type == "web":
        return doc.metadata.get("url", "Web page")
    elif source_type in ["document", "ocr"]:
        filename = doc.metadata.get("filename", "")
        return filename if filename else f"Document ({doc.metadata.get('file_type', 'file')})"
    return source_type


def clean_youtube_text(text: str) -> str:
    """Remove spoken filler words from YouTube transcripts."""
    fillers = [
        "subscribe", "like this video", "hit the bell",
        "smash that", "welcome back", "don't forget to",
        "in this video", "today we will", "guys",
    ]
    for filler in fillers:
        text = text.replace(filler, "").replace(filler.capitalize(), "")
    return text.strip()


def rag_answer(question: str, user_id: int, chat_history: str = "No previous conversation.") -> dict:
    """
    Full RAG pipeline with score-based rejection:

    1.  Greeting / off-topic guard
    2.  Empty KB guard
    3.  Retrieve top-k chunks WITH scores (FAISS L2)
    4.  Reject if best score > RELEVANCE_THRESHOLD (no LLM call)
    5.  Filter only relevant chunks
    6.  Source diversity (include YouTube if available)
    7.  Deduplicate chunks
    8.  Build context + conversation history
    9.  LLM call
    10. Post-process + save to memory
    """

    question = question.strip()

    # ── 1. Greeting ──
    if is_greeting(question):
        return {
            "answer": (
                "Hello! 👋 I'm **Lumi**, your AI study assistant.\n\n"
                "I can answer questions based on the study material you've uploaded — "
                "PDFs, YouTube lectures, websites, notes, and more.\n\n"
                "Upload something from the sidebar and ask me anything about it!"
            ),
            "sources": [],
            "confidence": None,
        }

    # ── 2. Off-topic ──
    if is_off_topic(question):
        return {
            "answer": OFF_TOPIC_RESPONSE,
            "sources": [],
            "confidence": None,
        }

    # ── 3. Empty KB ──
    if get_vector_store(user_id).is_empty():
        return {
            "answer": (
                "📭 **No study material loaded yet.**\n\n"
                "Please add content first:\n"
                "- 📄 Upload a PDF, DOCX, PPTX, or TXT from the sidebar\n"
                "- 🎥 Paste a YouTube lecture URL\n"
                "- 🌐 Add a website or article link\n\n"
                "Then ask me anything about it!"
            ),
            "sources": [],
            "confidence": None,
        }

    # ── 4. Retrieve with scores ──
    try:
        docs_with_scores = get_vector_store(user_id).similarity_search_with_score(question, k=8)
    except Exception as e:
        return {
            "answer": f"⚠️ Retrieval error: {str(e)}. Please try again.",
            "sources": [],
            "confidence": None,
        }

    if not docs_with_scores:
        return {
            "answer": NO_CONTEXT_RESPONSE,
            "sources": [],
            "confidence": None,
        }

    # ── 5. Score-based rejection ──
    # FAISS L2: lower = better. If even the best chunk is too far away, reject.
    best_score = min(score for _, score in docs_with_scores)

    if best_score > RELEVANCE_THRESHOLD:
        return {
            "answer": (
                "❌ I couldn't find relevant information about this in your uploaded material.\n\n"
                "Please make sure you've uploaded content related to your question, "
                "or try rephrasing it."
            ),
            "sources": [],
            "confidence": "low",
        }

    # ── 6. Filter only relevant chunks (below threshold) ──
    relevant_docs = [
        doc for doc, score in docs_with_scores
        if score < RELEVANCE_THRESHOLD
    ]

    # ── 7. Compute confidence from avg score of top-3 ──
    top_scores = sorted([score for _, score in docs_with_scores])[:3]
    avg_score = sum(top_scores) / len(top_scores)

    if avg_score < 0.5:
        confidence = "high"
    elif avg_score < 1.0:
        confidence = "medium"
    else:
        confidence = "low"

    # ── 8. Source diversity: include YouTube if missed ──
    has_youtube = any(d.metadata.get("source") == "youtube" for d in relevant_docs)
    if not has_youtube:
        try:
            yt_docs = get_vector_store(user_id).similarity_search(question, k=2)
            for d in yt_docs:
                if d.metadata.get("source") == "youtube":
                    relevant_docs.append(d)
        except Exception:
            pass

    # ── 9. Deduplicate + clean ──
    seen_content = set()
    source_labels = set()
    clean_chunks = []

    for doc in relevant_docs:
        content = doc.page_content.strip()
        if doc.metadata.get("source") == "youtube":
            content = clean_youtube_text(content)
        if content and content not in seen_content and len(content) > 30:
            seen_content.add(content)
            clean_chunks.append(content)
            source_labels.add(get_source_label(doc))

    if not clean_chunks:
        return {
            "answer": NO_CONTEXT_RESPONSE,
            "sources": [],
            "confidence": "low",
        }

    # ── 10. Build context ──
    context = "\n\n---\n\n".join(clean_chunks)

    # ── 12. Prompt ──
    prompt = RAG_PROMPT.format(
        context=context,
        chat_history=chat_history,
        question=question,
    )

    # ── 13. LLM call ──
    try:
        answer = hf_llm.generate(prompt)
    except Exception as e:
        return {
            "answer": f"⚠️ LLM error: {str(e)}. Check your GROQ_API_KEY in .env file.",
            "sources": list(source_labels),
            "confidence": None,
        }

    # ── 14. Reject garbage answers ──
    if not answer or len(answer.strip()) < 10:
        return {
            "answer": NO_CONTEXT_RESPONSE,
            "sources": [],
            "confidence": "low",
        }

    return {
        "answer": answer,
        "sources": list(source_labels),
        "confidence": confidence,
    }
