from langgraph.graph import StateGraph, START, END
from backend.ai.graph_state import RAGState
from backend.ai.prompts import (
    RAG_PROMPT, NO_CONTEXT_RESPONSE, OFF_TOPIC_RESPONSE,
    QUERY_REWRITE_PROMPT, BROADEN_QUERY_PROMPT, FAITHFULNESS_PROMPT,
)
from backend.ai.llm import hf_llm
from backend.database.vectorstore import get_vector_store
from backend.ai.reranker import rerank
from backend.ai.rag_helpers import (
    is_greeting, is_off_topic, get_source_label,
    clean_youtube_text, RERANK_REJECT_THRESHOLD,
)

FAITHFULNESS_CAVEAT = (
    "\n\n⚠️ *Note: parts of this answer may not be fully supported by your sources — please verify.*"
)


# ── Entry router ──
def route_intent(state: RAGState) -> str:
    q = state["question"]
    if is_greeting(q):
        return "greeting"
    if is_off_topic(q):
        return "off_topic"
    return "check_kb"


def greeting_node(state: RAGState) -> RAGState:
    return {
        "answer": (
            "Hello! 👋 I'm **Lumi**, your AI study assistant.\n\n"
            "I can answer questions based on the study material you've uploaded — "
            "PDFs, YouTube lectures, websites, notes, and more.\n\n"
            "Upload something from the sidebar and ask me anything about it!"
        ),
        "sources": [], "confidence": None,
    }


def off_topic_node(state: RAGState) -> RAGState:
    return {"answer": OFF_TOPIC_RESPONSE, "sources": [], "confidence": None}


def check_kb_node(state: RAGState) -> RAGState:
    return state


def route_kb(state: RAGState) -> str:
    return "empty" if get_vector_store(state["user_id"]).is_empty() else "rewrite_query"


def empty_node(state: RAGState) -> RAGState:
    return {
        "answer": (
            "📭 **No study material loaded yet.**\n\n"
            "Please add content first:\n"
            "- 📄 Upload a PDF, DOCX, PPTX, or TXT from the sidebar\n"
            "- 🎥 Paste a YouTube lecture URL\n"
            "- 🌐 Add a website or article link\n\n"
            "Then ask me anything about it!"
        ),
        "sources": [], "confidence": None,
    }


# ── Query rewriting: turn follow-ups into standalone search queries ──
def rewrite_query_node(state: RAGState) -> RAGState:
    history = state.get("chat_history", "No previous conversation.")
    if not history or history == "No previous conversation.":
        return {"search_query": state["question"]}
    try:
        prompt = QUERY_REWRITE_PROMPT.format(chat_history=history, question=state["question"])
        rewritten = hf_llm.generate(prompt).strip().strip('"')
        if not rewritten or len(rewritten) < 3:
            rewritten = state["question"]
    except Exception:
        rewritten = state["question"]
    return {"search_query": rewritten}


def retrieve_node(state: RAGState) -> RAGState:
    query = state.get("search_query") or state["question"]
    try:
        candidates = get_vector_store(state["user_id"]).hybrid_search(
            query, k=12, source_filter=state.get("source_filter"),
        )
    except Exception as e:
        return {"answer": f"⚠️ Retrieval error: {str(e)}. Please try again.",
                "sources": [], "confidence": None}

    if not candidates:
        return {"answer": NO_CONTEXT_RESPONSE, "sources": [], "confidence": None}

    reranked = rerank(query, candidates, top_n=8)
    return {"docs_with_scores": reranked}


def route_retrieved(state: RAGState) -> str:
    return "done" if "answer" in state else "score_gate"


def score_gate_node(state: RAGState) -> RAGState:
    docs_with_scores = state["docs_with_scores"]
    best_score = max(score for _, score in docs_with_scores)

    if best_score < RERANK_REJECT_THRESHOLD:
        if state.get("retry_count", 0) < 1:
            return {"needs_retry": True}
        return {
            "answer": (
                "❌ I couldn't find relevant information about this in your uploaded material.\n\n"
                "Please make sure you've uploaded content related to your question, "
                "or try rephrasing it."
            ),
            "sources": [], "confidence": "low",
        }

    relevant_docs = [doc for doc, score in docs_with_scores if score >= RERANK_REJECT_THRESHOLD]
    top_scores = sorted([score for _, score in docs_with_scores], reverse=True)[:3]
    avg_score = sum(top_scores) / len(top_scores)
    confidence = "high" if avg_score > 2.0 else "medium" if avg_score > 0.0 else "low"

    return {"relevant_docs": relevant_docs, "confidence": confidence, "needs_retry": False}


def route_score(state: RAGState) -> str:
    if state.get("needs_retry"):
        return "broaden"
    return "rejected" if "answer" in state else "build_context"


# ── Retrieval retry/self-correction: broaden the query once and retry ──
def broaden_node(state: RAGState) -> RAGState:
    try:
        prompt = BROADEN_QUERY_PROMPT.format(question=state.get("search_query") or state["question"])
        broadened = hf_llm.generate(prompt).strip().strip('"')
        if not broadened or len(broadened) < 3:
            broadened = state["question"]
    except Exception:
        broadened = state["question"]
    return {"search_query": broadened, "retry_count": state.get("retry_count", 0) + 1, "needs_retry": False}


def build_context_node(state: RAGState) -> RAGState:
    relevant_docs = state["relevant_docs"]
    user_id = state["user_id"]
    query = state.get("search_query") or state["question"]

    has_youtube = any(d.metadata.get("source") == "youtube" for d in relevant_docs)
    if not has_youtube:
        try:
            for d in get_vector_store(user_id).hybrid_search(query, k=2):
                if d.metadata.get("source") == "youtube":
                    relevant_docs.append(d)
        except Exception:
            pass

    seen_content, source_labels, clean_chunks = set(), set(), []
    for doc in relevant_docs:
        content = doc.page_content.strip()
        if doc.metadata.get("source") == "youtube":
            content = clean_youtube_text(content)
        if content and content not in seen_content and len(content) > 30:
            seen_content.add(content)
            clean_chunks.append(content)
            source_labels.add(get_source_label(doc))

    if not clean_chunks:
        return {"answer": NO_CONTEXT_RESPONSE, "sources": [], "confidence": "low"}

    return {
        "context": "\n\n---\n\n".join(clean_chunks),
        "source_labels": list(source_labels),
    }


def route_context(state: RAGState) -> str:
    return "no_context" if "answer" in state else "generate"


def generate_node(state: RAGState) -> RAGState:
    prompt = RAG_PROMPT.format(
        context=state["context"],
        chat_history=state.get("chat_history", "No previous conversation."),
        question=state["question"],
    )
    try:
        answer = hf_llm.generate(prompt)
    except Exception as e:
        return {
            "answer": f"⚠️ LLM error: {str(e)}. Check your GROQ_API_KEY in .env file.",
            "sources": state["source_labels"], "confidence": None,
        }

    if not answer or len(answer.strip()) < 10:
        return {"answer": NO_CONTEXT_RESPONSE, "sources": [], "confidence": "low"}

    return {"answer": answer, "sources": state["source_labels"]}


# ── Faithfulness / citation verification ──
def check_faithfulness(context: str, answer: str) -> tuple[bool, str]:
    """Returns (is_verified, possibly-annotated answer)."""
    if not context or not answer or len(answer.strip()) < 10:
        return True, answer
    try:
        prompt = FAITHFULNESS_PROMPT.format(context=context, answer=answer)
        verdict = hf_llm.generate(prompt).strip().upper()
    except Exception:
        return True, answer
    if verdict.startswith("UNSUPPORTED"):
        return False, answer + FAITHFULNESS_CAVEAT
    return True, answer


def verify_node(state: RAGState) -> RAGState:
    answer = state.get("answer", "")
    if not answer or state.get("confidence") == "low" and not state.get("context"):
        return {"verified": True}
    verified, final_answer = check_faithfulness(state.get("context", ""), answer)
    return {"answer": final_answer, "verified": verified}


# ── Build the graph ──
_graph = StateGraph(RAGState)

_graph.add_node("check_kb", check_kb_node)
_graph.add_node("greeting", greeting_node)
_graph.add_node("off_topic", off_topic_node)
_graph.add_node("empty", empty_node)
_graph.add_node("rewrite_query", rewrite_query_node)
_graph.add_node("retrieve", retrieve_node)
_graph.add_node("score_gate", score_gate_node)
_graph.add_node("broaden", broaden_node)
_graph.add_node("build_context", build_context_node)
_graph.add_node("generate", generate_node)
_graph.add_node("verify", verify_node)

_graph.add_conditional_edges(START, route_intent, {
    "greeting": "greeting", "off_topic": "off_topic", "check_kb": "check_kb",
})
_graph.add_conditional_edges("check_kb", route_kb, {"empty": "empty", "rewrite_query": "rewrite_query"})
_graph.add_edge("rewrite_query", "retrieve")
_graph.add_conditional_edges("retrieve", route_retrieved, {
    "score_gate": "score_gate", "done": END,
})
_graph.add_conditional_edges("score_gate", route_score, {
    "broaden": "broaden", "rejected": END, "build_context": "build_context",
})
_graph.add_edge("broaden", "retrieve")
_graph.add_conditional_edges("build_context", route_context, {
    "no_context": END, "generate": "generate",
})

_graph.add_edge("greeting", END)
_graph.add_edge("off_topic", END)
_graph.add_edge("empty", END)
_graph.add_edge("generate", "verify")
_graph.add_edge("verify", END)


def prepare_state(
    question: str, user_id: int,
    chat_history: str = "No previous conversation.",
    source_filter: dict | None = None,
) -> RAGState:
    """
    Mirrors the graph's routing/rewrite/retrieve/retry/gate logic but stops
    before the LLM call — used by the streaming endpoint (which does its own
    generation + calls check_faithfulness() itself after the stream).
    """
    state: RAGState = {
        "question": question.strip(), "user_id": user_id,
        "chat_history": chat_history, "source_filter": source_filter,
    }

    route = route_intent(state)
    if route == "greeting":
        return {**state, **greeting_node(state)}
    if route == "off_topic":
        return {**state, **off_topic_node(state)}

    if route_kb(state) == "empty":
        return {**state, **empty_node(state)}

    state = {**state, **rewrite_query_node(state)}
    state = {**state, **retrieve_node(state)}
    if "answer" in state:
        return state

    state = {**state, **score_gate_node(state)}
    if state.get("needs_retry"):
        state = {**state, **broaden_node(state)}
        state = {**state, **retrieve_node(state)}
        if "answer" in state:
            return state
        state = {**state, **score_gate_node(state)}
    if "answer" in state:
        return state

    state = {**state, **build_context_node(state)}
    return state


rag_graph = _graph.compile()


def run_rag_graph(
    question: str, user_id: int,
    chat_history: str = "No previous conversation.",
    source_filter: dict | None = None,
) -> dict:
    result = rag_graph.invoke({
        "question": question.strip(),
        "user_id": user_id,
        "chat_history": chat_history,
        "source_filter": source_filter,
    })
    return {
        "answer": result.get("answer", NO_CONTEXT_RESPONSE),
        "sources": result.get("sources", []),
        "confidence": result.get("confidence"),
        "verified": result.get("verified", True),
    }
