from pydantic import BaseModel, HttpUrl


class YouTubeIngestRequest(BaseModel):
    url: HttpUrl


class YouTubeIngestResponse(BaseModel):
    message: str
    chunks_added: int
