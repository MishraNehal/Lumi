import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.models import Conversation, Message, User
from backend.auth.dependencies import get_current_user

router = APIRouter(prefix="/conversations")


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None


def _get_owned_conversation(conversation_id: int, db: Session, current_user: User) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@router.get("")
def list_conversations(
    search: Optional[str] = None,
    archived: Optional[bool] = None,
    favorite: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    if archived is not None:
        q = q.filter(Conversation.is_archived == archived)
    else:
        q = q.filter(Conversation.is_archived == False)  # noqa: E712 — hide archived by default
    if favorite is not None:
        q = q.filter(Conversation.is_favorite == favorite)
    if search:
        q = q.filter(Conversation.title.ilike(f"%{search}%"))

    convs = q.order_by(Conversation.is_favorite.desc(), Conversation.created_at.desc()).all()
    return [
        {
            "id": c.id, "title": c.title, "created_at": c.created_at.isoformat(),
            "is_archived": c.is_archived, "is_favorite": c.is_favorite,
        }
        for c in convs
    ]


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _get_owned_conversation(conversation_id, db, current_user)
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.id.asc())
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "sources": json.loads(m.sources or "[]"), "verified": m.verified}
        for m in msgs
    ]


@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: int,
    body: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _get_owned_conversation(conversation_id, db, current_user)
    if body.title is not None:
        conv.title = body.title.strip()[:80] or conv.title
    if body.is_archived is not None:
        conv.is_archived = body.is_archived
    if body.is_favorite is not None:
        conv.is_favorite = body.is_favorite
    db.commit()
    db.refresh(conv)
    return {
        "id": conv.id, "title": conv.title,
        "is_archived": conv.is_archived, "is_favorite": conv.is_favorite,
    }


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = _get_owned_conversation(conversation_id, db, current_user)
    db.query(Message).filter(Message.conversation_id == conv.id).delete()
    db.delete(conv)
    db.commit()
    return {"deleted": True}
