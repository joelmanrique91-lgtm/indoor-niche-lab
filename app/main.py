from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings

app = FastAPI(title=settings.app_title)


def _resolve_templates_dir() -> Path | None:
    candidates = [Path("app/templates"), Path("templates")]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _resolve_static_dir() -> Path | None:
    candidates = [Path("app/static"), Path("static")]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


def _include_router_if_available(module_path: str, router_name: str = "router") -> None:
    if find_spec(module_path) is None:
        return
    module = import_module(module_path)
    router = getattr(module, router_name)
    app.include_router(router)


templates_dir = _resolve_templates_dir()
if templates_dir:
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

static_dir = _resolve_static_dir()
if static_dir:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

_include_router_if_available("app.routes.web")
_include_router_if_available("app.routes.api")
_include_router_if_available("app.routes.admin")


@app.get("/health")
def health():
    return {"ok": True}
