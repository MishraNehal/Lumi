# from fastapi import APIRouter
# from schemas.chat import ChatRequest, ChatResponse
# from services.chat_service import ask_question

# router = APIRouter()


# @router.post("/chat", response_model=ChatResponse)
# def chat(request: ChatRequest):
#     result = ask_question(request.question)
#     return ChatResponse(**result)

from fastapi import APIRouter, HTTPException
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ask_question

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Ask Lumi a question. Returns answer + source references."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = ask_question(request.question.strip())
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}",
        )