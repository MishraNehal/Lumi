import re
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from backend.ai.embeddings import get_embedding_model

CHROMA_PATH = "backend/data/chroma"

_embedding_model = get_embedding_model()
_store_cache: dict[int, "VectorStore"] = {}


def _tokenize(text: str) -> list:
    return re.findall(r"\w+", text.lower())


class VectorStore:
    """One Chroma collection per user — fully isolated. Adds BM25 keyword
    search on top of vector search, fused via Reciprocal Rank Fusion."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = Chroma(
            collection_name=f"user_{user_id}",
            embedding_function=_embedding_model,
            persist_directory=CHROMA_PATH,
        )
        self._bm25 = None
        self._bm25_corpus: list[tuple[str, dict]] = []

    def add_documents(self, documents):
        if not documents:
            return
        self.db.add_documents(documents)
        self._bm25 = None  # invalidate BM25 cache, rebuilt lazily on next search

    def _build_bm25(self):
        raw = self.db.get(include=["documents", "metadatas"])
        texts = raw.get("documents") or []
        metas = raw.get("metadatas") or []
        if not texts:
            self._bm25 = None
            self._bm25_corpus = []
            return
        self._bm25 = BM25Okapi([_tokenize(t) for t in texts])
        self._bm25_corpus = list(zip(texts, metas))

    def similarity_search(self, query: str, k: int = 4, source_filter: dict | None = None):
        return self.db.similarity_search(query, k=k, filter=source_filter)

    def similarity_search_with_score(self, query: str, k: int = 8, source_filter: dict | None = None):
        return self.db.similarity_search_with_score(query, k=k, filter=source_filter)

    def bm25_search(self, query: str, k: int = 8, source_filter: dict | None = None):
        if self._bm25 is None:
            self._build_bm25()
        if not self._bm25:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(zip(scores, self._bm25_corpus), key=lambda x: -x[0])
        results = []
        for score, (text, meta) in ranked:
            if score <= 0:
                break
            if source_filter and not all(meta.get(k_) == v for k_, v in source_filter.items()):
                continue
            results.append(Document(page_content=text, metadata=meta or {}))
            if len(results) >= k:
                break
        return results

    def hybrid_search(self, query: str, k: int = 10, source_filter: dict | None = None) -> list:
        """
        Combine dense vector search + sparse BM25 keyword search using
        Reciprocal Rank Fusion. Returns a deduplicated list of Documents.
        """
        vector_results = self.similarity_search_with_score(query, k=k, source_filter=source_filter)
        vector_docs_sorted = [d for d, _ in sorted(vector_results, key=lambda x: x[1])]
        bm25_docs = self.bm25_search(query, k=k, source_filter=source_filter)

        scores: dict[str, float] = {}
        docs_by_key: dict[str, Document] = {}
        RRF_K = 60

        def key(doc: Document) -> str:
            return doc.page_content[:150]

        for rank, doc in enumerate(vector_docs_sorted):
            dk = key(doc)
            docs_by_key[dk] = doc
            scores[dk] = scores.get(dk, 0.0) + 1.0 / (RRF_K + rank + 1)

        for rank, doc in enumerate(bm25_docs):
            dk = key(doc)
            docs_by_key[dk] = doc
            scores[dk] = scores.get(dk, 0.0) + 1.0 / (RRF_K + rank + 1)

        fused = sorted(scores.items(), key=lambda x: -x[1])
        return [docs_by_key[dk] for dk, _ in fused[:k]]

    def list_sources(self) -> list:
        """Distinct ingested sources for this user, for the 'Ask this source' filter."""
        raw = self.db.get(include=["metadatas"])
        seen = {}
        for meta in raw.get("metadatas") or []:
            filename = meta.get("filename") or meta.get("url") or "unknown"
            if filename not in seen:
                seen[filename] = {
                    "filename": filename,
                    "source_type": meta.get("source", "unknown"),
                    "url": meta.get("url"),
                }
        return list(seen.values())

    def is_empty(self) -> bool:
        return self.get_doc_count() == 0

    def get_doc_count(self) -> int:
        try:
            return self.db._collection.count()
        except Exception:
            return 0


def get_vector_store(user_id: int) -> VectorStore:
    if user_id not in _store_cache:
        _store_cache[user_id] = VectorStore(user_id)
    return _store_cache[user_id]
