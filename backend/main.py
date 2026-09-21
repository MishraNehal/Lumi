from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chat
from backend.routers import ingest_document
from backend.routers import ingest_ocr
from backend.routers import ingest_youtube
from backend.routers import ingest_web
from backend.routers import auth
from backend.routers import conversations
from backend.routers import sources
from backend.database.db import init_db


app = FastAPI(
    title="Lumi",
    description="AI Personal Knowledge Assistant",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(sources.router)
app.include_router(ingest_document.router)
app.include_router(ingest_ocr.router)
app.include_router(ingest_youtube.router)
app.include_router(ingest_web.router)
app.include_router(chat.router)


@app.get("/health")
def health_check():
    return {"status": "Lumi backend is running"}