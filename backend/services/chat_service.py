from backend.ai.rag_chain import rag_answer


def ask_question(question: str, user_id: int, chat_history: str = "No previous conversation.") -> dict:
    return rag_answer(question, user_id, chat_history)
