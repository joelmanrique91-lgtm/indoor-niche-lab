from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
from app.routes import admin, api, web

app = FastAPI(title=settings.app_title)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(api.router)
app.include_router(admin.router)


@app.on_event("startup")
def startup() -> None:
    """Inicializa la base de datos al arrancar la app."""
    init_db()


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
