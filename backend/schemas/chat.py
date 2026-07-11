from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[str] = None  # "high" | "medium" | "low" | None