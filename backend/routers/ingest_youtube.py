from fastapi import APIRouter, HTTPException
from services.youtube_service import ingest_youtube

router = APIRouter(prefix="/ingest/youtube")


@router.post("")
def ingest_youtube_route(url: str):
    success = ingest_youtube(url)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="No subtitles available for this YouTube video"
        )

    return {"message": "YouTube video ingested successfully"}
