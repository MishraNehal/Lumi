# from fastapi import APIRouter, HTTPException
# from services.youtube_service import ingest_youtube

# router = APIRouter(prefix="/ingest/youtube")


# @router.post("")
# def ingest_youtube_route(url: str, current_user: User = Depends(get_current_user)):
#     success = ingest_youtube(url)

#     if not success:
#         raise HTTPException(
#             status_code=400,
#             detail="No subtitles available for this YouTube video"
#         )

#     return {"message": "YouTube video ingested successfully"}


from fastapi import APIRouter, HTTPException
from backend.services.youtube_service import ingest_youtube
from fastapi import Depends
from backend.auth.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/ingest/youtube")


@router.post("")
def ingest_youtube_route(url: str, current_user: User = Depends(get_current_user)):
    """Ingest a YouTube video transcript into the knowledge base."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="YouTube URL is required.")

    try:
        result = ingest_youtube(url.strip(), current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to ingest YouTube video."),
        )

    return {
        "message": result["message"],
        "chunks": result.get("chunks", 0),
        "video_id": result.get("video_id", ""),
        "transcript_length": result.get("transcript_length", 0),
    }