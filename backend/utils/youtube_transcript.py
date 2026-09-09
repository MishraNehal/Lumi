# import subprocess
# import json
# import tempfile
# import os


# def extract_video_id(url: str) -> str:
#     if "v=" in url:
#         return url.split("v=")[1].split("&")[0]
#     elif "youtu.be/" in url:
#         return url.split("youtu.be/")[1]
#     else:
#         raise ValueError("Invalid YouTube URL")


# def fetch_transcript_yt_dlp(url: str) -> str | None:
#     """
#     Uses yt-dlp to fetch auto or manual subtitles
#     """

#     with tempfile.TemporaryDirectory() as tmpdir:
#         output_template = os.path.join(tmpdir, "%(id)s")

#         cmd = [
#             "yt-dlp",
#             "--skip-download",
#             "--write-auto-sub",
#             "--write-sub",
#             "--sub-lang", "en",
#             "--sub-format", "json3",
#             "-o", output_template,
#             url,
#         ]

#         try:
#             subprocess.run(
#                 cmd,
#                 stdout=subprocess.DEVNULL,
#                 stderr=subprocess.DEVNULL,
#                 check=True,
#             )
#         except Exception:
#             return None

#         # Find subtitle file
#         for file in os.listdir(tmpdir):
#             if file.endswith(".json3"):
#                 path = os.path.join(tmpdir, file)
#                 with open(path, "r", encoding="utf-8") as f:
#                     data = json.load(f)

#                 events = data.get("events", [])
#                 texts = []

#                 for event in events:
#                     for seg in event.get("segs", []):
#                         text = seg.get("utf8", "").strip()
#                         if text:
#                             texts.append(text)

#                 return " ".join(texts)

#     return None


import re
import subprocess
import json
import tempfile
import os

# Try importing youtube-transcript-api (primary method)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("⚠️ youtube-transcript-api not installed. Only yt-dlp fallback will be used.")


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from any common URL format."""
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/v/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _fetch_via_transcript_api(video_id: str) -> str | None:
    """
    Primary method: youtube-transcript-api.
    Fast, reliable, works on most videos with captions.
    """
    if not TRANSCRIPT_API_AVAILABLE:
        return None
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([item["text"] for item in transcript_list])
        if text.strip():
            print(f"✅ Transcript fetched via youtube-transcript-api ({len(text)} chars)")
            return text.strip()
    except Exception as e:
        print(f"⚠️ youtube-transcript-api failed: {e}")
    return None


def _fetch_via_yt_dlp(url: str) -> str | None:
    """
    Fallback method: yt-dlp subprocess.
    Handles videos where transcript-api is blocked.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(id)s")
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang", "en",
                "--sub-format", "json3",
                "-o", output_template,
                url,
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            if result.returncode != 0:
                print(f"⚠️ yt-dlp exited with code {result.returncode}")
                return None

            # Find and parse the subtitle file
            for file in os.listdir(tmpdir):
                if file.endswith(".json3"):
                    path = os.path.join(tmpdir, file)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    events = data.get("events", [])
                    texts = []
                    for event in events:
                        for seg in event.get("segs", []):
                            text = seg.get("utf8", "").strip()
                            if text and text != "\n":
                                texts.append(text)
                    result_text = " ".join(texts).strip()
                    if result_text:
                        print(f"✅ Transcript fetched via yt-dlp ({len(result_text)} chars)")
                        return result_text
    except subprocess.TimeoutExpired:
        print("⚠️ yt-dlp timed out after 60 seconds")
    except FileNotFoundError:
        print("⚠️ yt-dlp not found in PATH. Install it: pip install yt-dlp")
    except Exception as e:
        print(f"⚠️ yt-dlp fallback failed: {e}")
    return None


def _fetch_segments_via_transcript_api(video_id: str):
    """Returns list of {'start': float, 'text': str} or None."""
    if not TRANSCRIPT_API_AVAILABLE:
        return None
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        segments = [{"start": float(item["start"]), "text": item["text"]} for item in transcript_list]
        if segments:
            print(f"✅ Transcript segments fetched via youtube-transcript-api ({len(segments)} segments)")
            return segments
    except Exception as e:
        print(f"⚠️ youtube-transcript-api failed: {e}")
    return None


def _fetch_segments_via_yt_dlp(url: str):
    """Returns list of {'start': float, 'text': str} or None, using yt-dlp json3 subtitle events."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(id)s")
            cmd = [
                "yt-dlp", "--skip-download", "--write-auto-sub", "--write-sub",
                "--sub-lang", "en", "--sub-format", "json3", "-o", output_template, url,
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            if result.returncode != 0:
                return None
            for file in os.listdir(tmpdir):
                if file.endswith(".json3"):
                    with open(os.path.join(tmpdir, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    segments = []
                    for event in data.get("events", []):
                        start_ms = event.get("tStartMs", 0)
                        text = "".join(seg.get("utf8", "") for seg in event.get("segs", [])).strip()
                        if text and text != "\n":
                            segments.append({"start": start_ms / 1000.0, "text": text})
                    if segments:
                        print(f"✅ Transcript segments fetched via yt-dlp ({len(segments)} segments)")
                        return segments
    except Exception as e:
        print(f"⚠️ yt-dlp segment fallback failed: {e}")
    return None


def fetch_transcript_segments(url: str):
    """
    Returns list of {'start': float, 'text': str} timestamped segments, or None.
    Used to build citation-friendly, timestamp-aware chunks.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None

    segments = _fetch_segments_via_transcript_api(video_id)
    if segments:
        return segments

    print("🔄 Trying yt-dlp fallback for segments...")
    return _fetch_segments_via_yt_dlp(url)



    """
    Main entry point. Tries primary method first, then fallback.
    Returns transcript text or None if both methods fail.
    """
    video_id = extract_video_id(url)
    if not video_id:
        print(f"❌ Could not extract video ID from URL: {url}")
        return None

    print(f"▶️  Fetching transcript for video ID: {video_id}")

    # Method 1: youtube-transcript-api (fast)
    text = _fetch_via_transcript_api(video_id)
    if text:
        return text

    # Method 2: yt-dlp (fallback)
    print("🔄 Trying yt-dlp fallback...")
    text = _fetch_via_yt_dlp(url)
    if text:
        return text

    print(f"❌ Both methods failed for video: {url}")
    return None


# Keep old function name for backward compatibility
def fetch_transcript_yt_dlp(url: str) -> str | None:
    return fetch_transcript(url)