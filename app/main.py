from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routes.admin import router as admin_router
from app.routes.api import router as api_router
from app.routes.web import router as web_router

app = FastAPI(title="Indoor Niche Lab")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(web_router)
app.include_router(api_router)
app.include_router(admin_router)
