# from ai.prompts import RAG_PROMPT
# from ai.llm import hf_llm
# from ai.memory import SimpleChatMemory
# from database.vectorstore import vector_store


# memory = SimpleChatMemory()


# def clean_youtube_text(text: str) -> str:
#     """
#     Remove common spoken fillers from YouTube transcripts
#     to improve embedding similarity.
#     """
#     fillers = [
#         "subscribe", "like", "share", "guys",
#         "welcome", "channel", "hello", "today we will"
#     ]
#     lowered = text.lower()
#     for f in fillers:
#         lowered = lowered.replace(f, "")
#     return lowered


# def rag_answer(question: str) -> dict:
#     """
#     Full RAG pipeline with:
#     - Higher k retrieval
#     - Source diversity (YouTube + Web + Doc)
#     - Deduplication
#     - Strict grounding
#     """

#     # -------------------------------
#     # 1️⃣ Primary Retrieval (k=6)
#     # -------------------------------
#     retriever = vector_store.as_retriever(
#         search_kwargs={"k": 6}
#     )

#     docs = retriever.invoke(question)

#     if not docs:
#         return {
#             "answer": "I don't know based on the provided data.",
#             "sources": []
#         }

#     # -------------------------------
#     # 2️⃣ Ensure YouTube participation
#     # -------------------------------
#     has_youtube = any(
#         d.metadata.get("source") == "youtube" for d in docs
#     )

#     if not has_youtube:
#         youtube_fallback = vector_store.similarity_search(
#             question + " explained in video",
#             k=2
#         )
#         for d in youtube_fallback:
#             if d.metadata.get("source") == "youtube":
#                 docs.append(d)

#     # -------------------------------
#     # 3️⃣ Deduplicate & clean context
#     # -------------------------------
#     seen = set()
#     clean_chunks = []
#     sources = set()

#     for doc in docs:
#         content = doc.page_content.strip()
#         source = doc.metadata.get("source", "unknown")

#         if source == "youtube":
#             content = clean_youtube_text(content)

#         if content and content not in seen:
#             seen.add(content)
#             clean_chunks.append(content)
#             sources.add(source)

#     if not clean_chunks:
#         return {
#             "answer": "I don't know based on the provided data.",
#             "sources": []
#         }

#     context = "\n\n".join(clean_chunks)

#     # -------------------------------
#     # 4️⃣ Memory (last turn only)
#     # -------------------------------
#     chat_history = memory.get_last_turn()

#     # -------------------------------
#     # 5️⃣ Prompt construction
#     # -------------------------------
#     prompt = RAG_PROMPT.format(
#         context=context,
#         chat_history=chat_history,
#         question=question
#     )

#     # -------------------------------
#     # 6️⃣ LLM call
#     # -------------------------------
#     answer = hf_llm.generate(prompt)

#     # -------------------------------
#     # 7️⃣ Save memory
#     # -------------------------------
#     memory.add(question, answer)

#     return {
#         "answer": answer,
#         "sources": list(sources)
#     }



from backend.ai.prompts import RAG_PROMPT
from backend.ai.llm import hf_llm
from backend.ai.memory import SimpleChatMemory
from backend.database.vectorstore import vector_store


memory = SimpleChatMemory()


def clean_youtube_text(text: str) -> str:
    """Remove common spoken fillers from YouTube transcripts."""
    fillers = [
        "subscribe", "like", "share", "guys",
        "welcome", "channel", "hello", "today we will",
    ]
    lowered = text.lower()
    for f in fillers:
        lowered = lowered.replace(f, "")
    return lowered


def get_source_label(doc) -> str:
    """Build a human-readable source label from document metadata."""
    source_type = doc.metadata.get("source", "unknown")
    if source_type == "youtube":
        video_id = doc.metadata.get("video_id", "")
        url = doc.metadata.get("url", "")
        return url if url else f"YouTube ({video_id})"
    elif source_type == "web":
        return doc.metadata.get("url", "Web page")
    elif source_type == "document" or source_type == "ocr":
        filename = doc.metadata.get("filename", "")
        if filename:
            return filename
        return f"Document ({doc.metadata.get('file_type', 'file')})"
    return source_type


def rag_answer(question: str) -> dict:
    """
    Full RAG pipeline:
    1. Guard against empty vector store
    2. Retrieve top-k chunks (k=6)
    3. Ensure source diversity
    4. Deduplicate chunks
    5. Build prompt with memory
    6. Generate answer via LLM
    7. Return answer + sources
    """

    # Guard: no documents ingested yet
    if vector_store.is_empty():
        return {
            "answer": "No knowledge base loaded yet. Please ingest a document, YouTube video, or web page first using the sidebar.",
            "sources": [],
        }

    # 1. Primary retrieval
    retriever = vector_store.as_retriever(search_kwargs={"k": 6})
    if retriever is None:
        return {
            "answer": "Knowledge base is not ready. Please ingest some content first.",
            "sources": [],
        }

    try:
        docs = retriever.invoke(question)
    except Exception as e:
        return {
            "answer": f"Retrieval error: {str(e)}. Please try again.",
            "sources": [],
        }

    if not docs:
        return {
            "answer": "I could not find relevant information for your question in the knowledge base.",
            "sources": [],
        }

    # 2. Ensure YouTube participation (if any YouTube content exists)
    has_youtube = any(d.metadata.get("source") == "youtube" for d in docs)
    if not has_youtube:
        try:
            youtube_fallback = vector_store.similarity_search(
                question + " explained in video", k=2
            )
            for d in youtube_fallback:
                if d.metadata.get("source") == "youtube":
                    docs.append(d)
        except Exception:
            pass

    # 3. Deduplicate and clean
    seen = set()
    clean_chunks = []
    source_labels = set()

    for doc in docs:
        content = doc.page_content.strip()
        if doc.metadata.get("source") == "youtube":
            content = clean_youtube_text(content)
        if content and content not in seen:
            seen.add(content)
            clean_chunks.append(content)
            source_labels.add(get_source_label(doc))

    if not clean_chunks:
        return {
            "answer": "I don't know based on the provided data.",
            "sources": [],
        }

    context = "\n\n".join(clean_chunks)

    # 4. Memory (last turn only to prevent topic pollution)
    chat_history = memory.get_last_turn()

    # 5. Build prompt
    prompt = RAG_PROMPT.format(
        context=context,
        chat_history=chat_history,
        question=question,
    )

    # 6. LLM call
    try:
        answer = hf_llm.generate(prompt)
    except Exception as e:
        return {
            "answer": f"LLM error: {str(e)}. Please check your GROQ_API_KEY.",
            "sources": list(source_labels),
        }

    # 7. Save to memory
    memory.add(question, answer)

    return {
        "answer": answer,
        "sources": list(source_labels),
    }