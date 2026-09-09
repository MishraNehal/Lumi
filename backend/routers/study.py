import json
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.database.vectorstore import get_vector_store
from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.ai.llm import hf_llm
from backend.ai.prompts import QUIZ_GENERATION_PROMPT

router = APIRouter(prefix="/study")


class QuizRequest(BaseModel):
    source_filter: dict | None = None  # e.g. {"filename": "java_notes.pdf"}
    num_questions: int = 5


@router.post("/quiz")
def generate_quiz(request: QuizRequest, current_user: User = Depends(get_current_user)):
    store = get_vector_store(current_user.id)
    if store.is_empty():
        raise HTTPException(status_code=400, detail="No study material ingested yet.")

    # Pull a representative sample of chunks from the chosen source (or whole KB)
    raw = store.db.get(include=["documents", "metadatas"])
    texts, metas = raw.get("documents") or [], raw.get("metadatas") or []

    filtered = []
    for text, meta in zip(texts, metas):
        if request.source_filter and not all(meta.get(k) == v for k, v in request.source_filter.items()):
            continue
        filtered.append(text)

    if not filtered:
        raise HTTPException(status_code=400, detail="No content found for the selected source.")

    context = "\n\n".join(filtered[:12])  # cap context size
    num_q = max(1, min(request.num_questions, 10))

    prompt = QUIZ_GENERATION_PROMPT.format(context=context, num_questions=num_q)
    try:
        raw_response = hf_llm.generate(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

    # Extract JSON (LLM may wrap it in prose/backticks despite instructions)
    match = re.search(r"\[.*\]", raw_response, re.DOTALL)
    if not match:
        raise HTTPException(status_code=500, detail="Could not parse quiz output. Try again.")
    try:
        questions = json.loads(match.group(0))
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Quiz output was malformed JSON. Try again.")

    valid = [
        q for q in questions
        if isinstance(q, dict) and "question" in q and "options" in q and "correct_index" in q
    ]
    if not valid:
        raise HTTPException(status_code=500, detail="No valid questions generated.")

    return {"questions": valid}
