from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import admin, api, web

app = FastAPI(title=settings.app_title)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(api.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"ok": True}
