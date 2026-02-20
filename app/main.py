from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes.admin import router as admin_router
from app.routes.api import router as api_router
from app.routes.web import router as web_router

app = FastAPI(title=settings.app_title)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web_router)
app.include_router(api_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
