from fastapi import APIRouter, HTTPException
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ask_question
from backend.ai.rag_chain import clear_memory

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


@router.post("/chat/clear")
def clear_chat():
    """Clear conversation memory on the backend."""
    clear_memory()
    return {"message": "Conversation memory cleared."}