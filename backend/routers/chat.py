import json
import time
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ask_question
from backend.database.db import get_db, SessionLocal
from backend.database.models import Conversation, Message, User, QueryLog
from backend.auth.dependencies import get_current_user
from backend.ai.graph import prepare_state, check_faithfulness, FAITHFULNESS_CAVEAT
from backend.ai.llm import hf_llm
from backend.ai.prompts import RAG_PROMPT

router = APIRouter()

HISTORY_TURNS = 5


def _build_history_text(db: Session, conversation_id: int) -> str:
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(HISTORY_TURNS * 2)
        .all()
    )
    if not msgs:
        return "No previous conversation."
    msgs.reverse()
    lines = [f"{m.role.capitalize()}: {m.content}" for m in msgs]
    return "\n".join(lines)


def _get_or_create_conversation(request: ChatRequest, db: Session, current_user: User) -> Conversation:
    if request.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == request.conversation_id, Conversation.user_id == current_user.id)
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        return conv
    conv = Conversation(user_id=current_user.id, title=request.question.strip()[:50])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def _log_query(user_id: int, conversation_id: int, question: str, num_sources: int,
               confidence: str | None, verified: bool | None, latency_ms: float):
    s = SessionLocal()
    try:
        s.add(QueryLog(
            user_id=user_id, conversation_id=conversation_id, question=question,
            num_sources=num_sources, confidence=confidence, verified=verified,
            latency_ms=latency_ms,
        ))
        s.commit()
    finally:
        s.close()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start = time.perf_counter()
    conv = _get_or_create_conversation(request, db, current_user)
    history_text = _build_history_text(db, conv.id)

    try:
        result = ask_question(request.question.strip(), current_user.id, history_text, request.source_filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    latency_ms = (time.perf_counter() - start) * 1000

    db.add(Message(conversation_id=conv.id, role="user", content=request.question.strip()))
    db.add(Message(
        conversation_id=conv.id, role="assistant",
        content=result["answer"], sources=json.dumps(result.get("sources", [])),
        verified=result.get("verified"),
    ))
    db.commit()

    _log_query(current_user.id, conv.id, request.question.strip(),
               len(result.get("sources", [])), result.get("confidence"),
               result.get("verified"), latency_ms)

    return ChatResponse(**result, conversation_id=conv.id)


@router.post("/chat/stream")
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start = time.perf_counter()
    conv = _get_or_create_conversation(request, db, current_user)
    history_text = _build_history_text(db, conv.id)
    user_question = request.question.strip()
    conv_id = conv.id
    user_id = current_user.id

    def sse(event: dict) -> str:
        return f"data: {json.dumps(event)}\n\n"

    def event_generator():
        yield sse({"status": "Searching", "done": False})
        state = prepare_state(user_question, user_id, history_text, request.source_filter)

        full_answer = ""
        sources = []
        verified = True

        if "answer" in state:
            full_answer = state["answer"]
            sources = state.get("sources", [])
            yield sse({"token": full_answer, "done": False})
        else:
            yield sse({"status": "Generating", "done": False})
            prompt = RAG_PROMPT.format(
                context=state["context"], chat_history=history_text, question=user_question,
            )
            try:
                for token in hf_llm.generate_stream(prompt):
                    full_answer += token
                    yield sse({"token": token, "done": False})
            except Exception as e:
                full_answer = f"⚠️ LLM error: {str(e)}"
                yield sse({"token": full_answer, "done": False})

            sources = state.get("source_labels", [])

            yield sse({"status": "Verifying", "done": False})
            verified, _ = check_faithfulness(state.get("context", ""), full_answer)
            if not verified:
                full_answer += FAITHFULNESS_CAVEAT
                yield sse({"token": FAITHFULNESS_CAVEAT, "done": False})

        confidence = state.get("confidence")
        latency_ms = (time.perf_counter() - start) * 1000

        s = SessionLocal()
        try:
            s.add(Message(conversation_id=conv_id, role="user", content=user_question))
            s.add(Message(
                conversation_id=conv_id, role="assistant",
                content=full_answer, sources=json.dumps(sources), verified=verified,
            ))
            s.commit()
        finally:
            s.close()

        _log_query(user_id, conv_id, user_question, len(sources), confidence, verified, latency_ms)

        yield sse({
            "token": "", "done": True, "sources": sources,
            "conversation_id": conv_id, "verified": verified,
        })

    return StreamingResponse(event_generator(), media_type="text/event-stream")
