from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import admin, api, web

app = FastAPI(title=settings.app_title)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers additive: web/admin/api endpoints coexist.
app.include_router(web.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}
