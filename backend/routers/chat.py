from fastapi import APIRouter
from schemas.chat import ChatRequest, ChatResponse
from services.chat_service import ask_question

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = ask_question(request.question)
    return ChatResponse(**result)
