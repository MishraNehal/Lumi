from ai.prompts import RAG_PROMPT
from ai.llm import hf_llm
from ai.memory import SimpleChatMemory
from database.vectorstore import vector_store


memory = SimpleChatMemory()


def clean_youtube_text(text: str) -> str:
    """
    Remove common spoken fillers from YouTube transcripts
    to improve embedding similarity.
    """
    fillers = [
        "subscribe", "like", "share", "guys",
        "welcome", "channel", "hello", "today we will"
    ]
    lowered = text.lower()
    for f in fillers:
        lowered = lowered.replace(f, "")
    return lowered


def rag_answer(question: str) -> dict:
    """
    Full RAG pipeline with:
    - Higher k retrieval
    - Source diversity (YouTube + Web + Doc)
    - Deduplication
    - Strict grounding
    """

    # -------------------------------
    # 1️⃣ Primary Retrieval (k=6)
    # -------------------------------
    retriever = vector_store.as_retriever(
        search_kwargs={"k": 6}
    )

    docs = retriever.invoke(question)

    if not docs:
        return {
            "answer": "I don't know based on the provided data.",
            "sources": []
        }

    # -------------------------------
    # 2️⃣ Ensure YouTube participation
    # -------------------------------
    has_youtube = any(
        d.metadata.get("source") == "youtube" for d in docs
    )

    if not has_youtube:
        youtube_fallback = vector_store.similarity_search(
            question + " explained in video",
            k=2
        )
        for d in youtube_fallback:
            if d.metadata.get("source") == "youtube":
                docs.append(d)

    # -------------------------------
    # 3️⃣ Deduplicate & clean context
    # -------------------------------
    seen = set()
    clean_chunks = []
    sources = set()

    for doc in docs:
        content = doc.page_content.strip()
        source = doc.metadata.get("source", "unknown")

        if source == "youtube":
            content = clean_youtube_text(content)

        if content and content not in seen:
            seen.add(content)
            clean_chunks.append(content)
            sources.add(source)

    if not clean_chunks:
        return {
            "answer": "I don't know based on the provided data.",
            "sources": []
        }

    context = "\n\n".join(clean_chunks)

    # -------------------------------
    # 4️⃣ Memory (last turn only)
    # -------------------------------
    chat_history = memory.get_last_turn()

    # -------------------------------
    # 5️⃣ Prompt construction
    # -------------------------------
    prompt = RAG_PROMPT.format(
        context=context,
        chat_history=chat_history,
        question=question
    )

    # -------------------------------
    # 6️⃣ LLM call
    # -------------------------------
    answer = hf_llm.generate(prompt)

    # -------------------------------
    # 7️⃣ Save memory
    # -------------------------------
    memory.add(question, answer)

    return {
        "answer": answer,
        "sources": list(sources)
    }
