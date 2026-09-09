from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None
    source_filter: Optional[dict] = None  # e.g. {"filename": "notes.pdf"} or {"source": "youtube"}


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[str] = None
    conversation_id: int
