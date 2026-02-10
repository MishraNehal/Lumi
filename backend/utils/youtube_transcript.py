import subprocess
import json
import tempfile
import os


def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1]
    else:
        raise ValueError("Invalid YouTube URL")


def fetch_transcript_yt_dlp(url: str) -> str | None:
    """
    Uses yt-dlp to fetch auto or manual subtitles
    """

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

        try:
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
        except Exception:
            return None

        # Find subtitle file
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
                        if text:
                            texts.append(text)

                return " ".join(texts)

    return None
