from database.vectorstore import VectorStore

vs = VectorStore()

vs.add_texts([
    "Lumi is an AI personal knowledge assistant",
    "FastAPI is used to build backend APIs",
    "LangChain helps build RAG pipelines"
])

results = vs.similarity_search("What is Lumi?")

for doc in results:
    print(doc.page_content)
