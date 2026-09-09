from backend.ai.graph import run_rag_graph


def rag_answer(question: str, user_id: int, chat_history: str = "No previous conversation.",
                source_filter: dict | None = None) -> dict:
    return run_rag_graph(question, user_id, chat_history, source_filter)
