from fastapi import FastAPI
from routers import chat
from routers import ingest_document
from routers import ingest_ocr
from routers import ingest_youtube
from routers import ingest_web




app = FastAPI(
    title="Lumi",
    description="AI Personal Knowledge Assistant",
    version="0.1.0"
)

app.include_router(ingest_document.router)
app.include_router(ingest_ocr.router)
app.include_router(ingest_youtube.router)
app.include_router(ingest_web.router)
app.include_router(chat.router)


@app.get("/health")
def health_check():
    return {"status": "Lumi backend is running"}
