from backend.ai.rag_chain import rag_answer


def ask_question(question: str, user_id: int, chat_history: str = "No previous conversation.",
                  source_filter: dict | None = None) -> dict:
    return rag_answer(question, user_id, chat_history, source_filter)
