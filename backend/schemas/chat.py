from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None  # None = start a new conversation


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[str] = None
    conversation_id: int
