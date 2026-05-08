# from fastapi import APIRouter
# from services.web_service import ingest_web

# router = APIRouter(prefix="/ingest/web")


# @router.post("")
# def ingest_web_route(url: str):
#     ingest_web(url)
#     return {"message": "Web page ingested successfully"}

from fastapi import APIRouter, HTTPException
from backend.services.web_service import ingest_web

router = APIRouter(prefix="/ingest/web")


@router.post("")
def ingest_web_route(url: str):
    """Ingest a web page into the knowledge base."""
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL is required.")

    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Must start with http:// or https://",
        )

    try:
        result = ingest_web(url.strip())
        return {
            "message": "Web page ingested successfully.",
            "chunks": result.get("chunks", 0),
            "url": url,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape web page: {str(e)}. The site may be blocking requests.",
        )