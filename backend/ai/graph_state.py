from typing import TypedDict, Optional, List


class RAGState(TypedDict, total=False):
    question: str
    user_id: int
    chat_history: str
    source_filter: Optional[dict]

    search_query: str          # rewritten/broadened query used for retrieval
    retry_count: int
    needs_retry: bool

    docs_with_scores: list
    relevant_docs: list
    context: str
    source_labels: List[str]

    answer: str
    sources: List[str]
    confidence: Optional[str]
    verified: bool
