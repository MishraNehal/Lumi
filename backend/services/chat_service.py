from backend.database.vectorstore import vector_store
from backend.ai.rag_chain import rag_answer


def ask_question(question: str) -> dict:
    return rag_answer(question)