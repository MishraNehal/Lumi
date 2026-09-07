from langchain_chroma import Chroma
from backend.ai.embeddings import get_embedding_model

CHROMA_PATH = "backend/data/chroma"

_embedding_model = get_embedding_model()
_store_cache: dict[int, "VectorStore"] = {}


class VectorStore:
    """One Chroma collection per user — fully isolated."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = Chroma(
            collection_name=f"user_{user_id}",
            embedding_function=_embedding_model,
            persist_directory=CHROMA_PATH,
        )

    def add_documents(self, documents):
        if not documents:
            return
        self.db.add_documents(documents)

    def similarity_search(self, query: str, k: int = 4):
        return self.db.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 8):
        """
        Returns list of (Document, score) tuples.
        Chroma uses cosine distance by default — lower = more relevant.
        """
        return self.db.similarity_search_with_score(query, k=k)

    def is_empty(self) -> bool:
        return self.get_doc_count() == 0

    def get_doc_count(self) -> int:
        try:
            return self.db._collection.count()
        except Exception:
            return 0


def get_vector_store(user_id: int) -> VectorStore:
    """Cached per-user VectorStore instance."""
    if user_id not in _store_cache:
        _store_cache[user_id] = VectorStore(user_id)
    return _store_cache[user_id]
