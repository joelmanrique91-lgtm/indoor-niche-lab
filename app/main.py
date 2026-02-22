from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import admin, api, web

APP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = APP_ROOT.parent


def _resolve_static_root() -> Path | None:
    candidates = [APP_ROOT / "static", PROJECT_ROOT / "static"]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


STATIC_ROOT = _resolve_static_root()
if STATIC_ROOT:
    (STATIC_ROOT / "img" / "generated").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Indoor Niche Lab")
if STATIC_ROOT:
    app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="static")

app.include_router(web.router)
app.include_router(admin.router)
app.include_router(api.router)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/debug/static")
def debug_static():
    candidates = {
        "app_static": str((APP_ROOT / "static").resolve()),
        "project_static": str((PROJECT_ROOT / "static").resolve()),
    }
    checks = [
        "css/styles.css",
        "js/app.js",
        "assets/logo.svg",
        "assets/favicon.svg",
        "img/logo.svg",
    ]
    files = {}
    if STATIC_ROOT:
        for relative_path in checks:
            files[relative_path] = (STATIC_ROOT / relative_path).exists()
    return {
        "static_mounted": bool(STATIC_ROOT),
        "mounted_directory": str(STATIC_ROOT.resolve()) if STATIC_ROOT else None,
        "candidate_directories": candidates,
        "files": files,
    }
