from fastapi import APIRouter
from services.web_service import ingest_web

router = APIRouter(prefix="/ingest/web")


@router.post("")
def ingest_web_route(url: str):
    ingest_web(url)
    return {"message": "Web page ingested successfully"}
