from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FRONTEND_ORIGINS, LIBRARY_DIR, QR_DIR, STATIC_DIR, TTS_CACHE_DIR
from backend.database import Base, SessionLocal, engine
from backend.routers import api_admin, api_dj, api_mesas, pages, ws

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SingPe Karaoke")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/qr", StaticFiles(directory=str(QR_DIR)), name="qr")
app.mount("/static/tts_cache", StaticFiles(directory=str(TTS_CACHE_DIR)), name="tts_cache")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/media", StaticFiles(directory=str(LIBRARY_DIR)), name="media")

app.include_router(pages.router)
app.include_router(ws.router)
app.include_router(api_mesas.router)
app.include_router(api_dj.router)
app.include_router(api_admin.router)


@app.on_event("startup")
def seed_config():
    from backend import crud

    db = SessionLocal()
    try:
        crud.get_config(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True, "app": "SingPe Karaoke"}
