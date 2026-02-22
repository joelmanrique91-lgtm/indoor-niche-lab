from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import admin, api, web

STATIC_ROOT = Path("app/static")
(STATIC_ROOT / "img" / "generated").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Indoor Niche Lab")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/health")
def health():
    return {"ok": True}
