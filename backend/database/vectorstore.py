# from langchain_community.vectorstores import FAISS
# from ai.embeddings import get_embedding_model

# class VectorStore:
#     def __init__(self):
#         self.embedding_model = get_embedding_model()
#         self.db = None

#     def add_documents(self, documents):
#         if self.db is None:
#             self.db = FAISS.from_documents(documents, self.embedding_model)
#         else:
#             self.db.add_documents(documents)

#     def similarity_search(self, query: str, k: int = 4):
#         if self.db is None:
#             return []
#         return self.db.similarity_search(query, k=k)

#     def as_retriever(self, **kwargs):
#         if self.db is None:
#             return None
#         return self.db.as_retriever(**kwargs)

# vector_store = VectorStore()


import os
import shutil
from langchain_community.vectorstores import FAISS
from backend.ai.embeddings import get_embedding_model

FAISS_PATH = "backend/data/faiss_index"


class VectorStore:
    def __init__(self):
        self.embedding_model = get_embedding_model()
        self.db = None
        self._load_from_disk()

    def _load_from_disk(self):
        index_file = os.path.join(FAISS_PATH, "index.faiss")
        if os.path.exists(index_file):
            try:
                self.db = FAISS.load_local(
                    FAISS_PATH,
                    self.embedding_model,
                    allow_dangerous_deserialization=True,
                )
                print(f"✅ FAISS index loaded from {FAISS_PATH}")
            except Exception as e:
                print(f"⚠️ Could not load FAISS index: {e}. Starting fresh.")
                self.db = None
        else:
            print("ℹ️ No existing FAISS index found. Will create on first ingestion.")

    def _save_to_disk(self):
        """Windows-safe FAISS save — deletes folder first to avoid WinError 183."""
        try:
            # Save to a temp folder first
            temp_path = FAISS_PATH + "_temp"

            # Clean up any leftover temp folder
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)

            # Save to temp
            os.makedirs(temp_path, exist_ok=True)
            self.db.save_local(temp_path)

            # Now swap: delete old, rename temp to real
            if os.path.exists(FAISS_PATH):
                shutil.rmtree(FAISS_PATH)
            os.rename(temp_path, FAISS_PATH)

            print(f"✅ FAISS index saved to {FAISS_PATH}")
        except Exception as e:
            print(f"⚠️ Could not save FAISS index: {e}")

    def add_documents(self, documents):
        """Add documents and persist. Safe for multiple calls."""
        if not documents:
            return
        if self.db is None:
            self.db = FAISS.from_documents(documents, self.embedding_model)
        else:
            self.db.add_documents(documents)
        self._save_to_disk()

    def add_texts(self, texts: list, metadatas: list = None):
        """Add raw texts and persist."""
        if not texts:
            return
        if self.db is None:
            self.db = FAISS.from_texts(texts, self.embedding_model, metadatas=metadatas)
        else:
            self.db.add_texts(texts, metadatas=metadatas)
        self._save_to_disk()

    def similarity_search(self, query: str, k: int = 4):
        if self.db is None:
            return []
        return self.db.similarity_search(query, k=k)

    def as_retriever(self, **kwargs):
        if self.db is None:
            return None
        return self.db.as_retriever(**kwargs)

    def is_empty(self) -> bool:
        return self.db is None

    def get_doc_count(self) -> int:
        if self.db is None:
            return 0
        try:
            return self.db.index.ntotal
        except Exception:
            return 0


# Single shared instance
vector_store = VectorStore()