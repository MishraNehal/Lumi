GREETINGS = {"hi", "hello", "hey", "good morning", "good evening",
             "sup", "what's up", "hii", "helo", "namaste"}

OFF_TOPIC_PATTERNS = [
    "tell me a joke", "what is your name", "who made you",
    "what is 2+2", "capital of", "weather today", "stock price",
    "who is the president", "what day is it", "translate this",
    "write a poem", "write code", "what is love",
]

RELEVANCE_THRESHOLD = 1.5  # legacy, unused after hybrid+rerank switch
# MS MARCO cross-encoder scores are model logits, not probabilities. Negative
# scores can still represent the best available match for a user's material.
RERANK_REJECT_THRESHOLD = -8.0


def is_greeting(question: str) -> bool:
    q = question.lower().strip().rstrip("?!.")
    return q in GREETINGS


def is_off_topic(question: str) -> bool:
    q = question.lower()
    return any(pattern in q for pattern in OFF_TOPIC_PATTERNS)


def get_source_label(doc) -> str:
    """Human-readable, citation-aware source label from document metadata."""
    source_type = doc.metadata.get("source", "unknown")

    if source_type == "youtube":
        ts_url = doc.metadata.get("timestamp_url")
        timestamp = doc.metadata.get("timestamp")
        if ts_url is not None and timestamp is not None:
            mins, secs = divmod(int(timestamp), 60)
            return f"{ts_url} (at {mins}:{secs:02d})"
        return doc.metadata.get("url", "YouTube video")

    elif source_type == "web":
        return doc.metadata.get("url", "Web page")

    elif source_type in ["document", "ocr"]:
        filename = doc.metadata.get("filename", "Document")
        page = doc.metadata.get("page")
        if page is not None:
            return f"{filename} (page {int(page) + 1})"
        return filename

    return source_type


def clean_youtube_text(text: str) -> str:
    fillers = [
        "subscribe", "like this video", "hit the bell",
        "smash that", "welcome back", "don't forget to",
        "in this video", "today we will", "guys",
    ]
    for filler in fillers:
        text = text.replace(filler, "").replace(filler.capitalize(), "")
    return text.strip()
