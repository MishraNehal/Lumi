from backend.utils.youtube_transcript import fetch_transcript_segments, extract_video_id
from langchain_core.documents import Document
from backend.database.vectorstore import get_vector_store

FILLERS = [
    "subscribe", "like this video", "hit the bell",
    "guys", "welcome back", "channel", "smash that",
    "today we will", "in this video", "don't forget to",
]

WINDOW_SECONDS = 45   # group transcript segments into ~45s chunks
MIN_CHUNK_CHARS = 30


def clean_text(text: str) -> str:
    for filler in FILLERS:
        text = text.replace(filler, "").replace(filler.capitalize(), "")
    return text.strip()


def _group_into_windows(segments: list) -> list:
    """Group timestamped segments into ~WINDOW_SECONDS chunks, each keeping its start timestamp."""
    if not segments:
        return []
    windows = []
    current_start = segments[0]["start"]
    current_texts = []

    for seg in segments:
        if seg["start"] - current_start > WINDOW_SECONDS and current_texts:
            windows.append({"start": current_start, "text": " ".join(current_texts)})
            current_start = seg["start"]
            current_texts = []
        current_texts.append(seg["text"])

    if current_texts:
        windows.append({"start": current_start, "text": " ".join(current_texts)})

    return windows


def ingest_youtube(url: str, user_id: int) -> dict:
    """Ingest a YouTube video with per-chunk timestamps for clickable citations."""
    url = str(url).strip()
    print(f"▶️  YouTube ingestion started: {url}")

    video_id = extract_video_id(url)
    if not video_id:
        return {"success": False, "message": "Invalid YouTube URL.", "chunks": 0}

    segments = fetch_transcript_segments(url)
    if not segments:
        return {
            "success": False,
            "message": "No captions/subtitles available for this video. Try a video with English captions.",
            "chunks": 0,
        }

    windows = _group_into_windows(segments)

    documents = []
    for w in windows:
        text = clean_text(w["text"])
        if len(text) < MIN_CHUNK_CHARS:
            continue
        start_seconds = int(w["start"])
        documents.append(Document(
            page_content=text,
            metadata={
                "source": "youtube",
                "url": url,
                "video_id": video_id,
                "filename": f"youtube_{video_id}",
                "timestamp": start_seconds,
                "timestamp_url": f"https://youtu.be/{video_id}?t={start_seconds}",
            },
        ))

    if not documents:
        return {"success": False, "message": "Transcript was too short to process.", "chunks": 0}

    get_vector_store(user_id).add_documents(documents)
    print(f"✅ YouTube ingestion complete: {len(documents)} timestamped chunks stored")

    return {
        "success": True,
        "message": "YouTube video ingested successfully.",
        "chunks": len(documents),
        "video_id": video_id,
    }
