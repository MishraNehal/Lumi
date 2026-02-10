from langchain_community.vectorstores import FAISS
from ai.embeddings import get_embedding_model

class VectorStore:
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.db = None

    def add_documents(self, documents):
        if self.db is None:
            self.db = FAISS.from_documents(documents, self.embedding_model)
        else:
            self.db.add_documents(documents)

    def similarity_search(self, query: str, k: int = 4):
        if self.db is None:
            return []
        return self.db.similarity_search(query, k=k)

    def as_retriever(self, **kwargs):
        if self.db is None:
            return None
        return self.db.as_retriever(**kwargs)

vector_store = VectorStore()
