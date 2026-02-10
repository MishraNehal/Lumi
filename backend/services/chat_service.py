
from database.vectorstore import vector_store
from ai.rag_chain import rag_answer


def ask_question(question: str) -> str:
    return rag_answer(question)






