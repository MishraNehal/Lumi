import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ask_question
from backend.database.db import get_db
from backend.database.models import Conversation, Message, User
from backend.auth.dependencies import get_current_user

router = APIRouter()

HISTORY_TURNS = 5  # last N exchanges used as context


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


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Get or create conversation, scoped to this user
    if request.conversation_id:
        conv = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        conv = Conversation(
            user_id=current_user.id,
            title=request.question.strip()[:50],
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    history_text = _build_history_text(db, conv.id)

    try:
        result = ask_question(request.question.strip(), current_user.id, history_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")

    # Persist both turns
    db.add(Message(conversation_id=conv.id, role="user", content=request.question.strip()))
    db.add(Message(
        conversation_id=conv.id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(result.get("sources", [])),
    ))
    db.commit()

    return ChatResponse(**result, conversation_id=conv.id)
