from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import db
from .calls_api import router as calls_router
from .portal import router as portal_router

app = FastAPI(title="ClirntCabinet", description="Готовые сайты и автоматизация бизнеса без программистов")

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
app.include_router(portal_router)
app.include_router(calls_router)

db.init_db()


@app.get("/api/health")
@app.get("/health", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok"}
