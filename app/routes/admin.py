from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import init_db
from app.repositories import (
    create_stage,
    create_step,
    get_stage,
    list_stages,
    list_steps_by_stage,
)
from app.services.ai_content import generate_stage_tutorial

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")

def _stage_illustration(name: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in name)
    slug = "-".join(normalized.split())
    mapping = {
        "preparacion-del-sustrato": "/static/assets/illustrations/substrate_prep.svg",
        "inoculacion-e-incubacion": "/static/assets/illustrations/incubation.svg",
    }
    return mapping.get(slug, "/static/assets/illustrations/stage_default.svg")


def _seed_demo_data() -> None:
    from scripts.seed_demo import seed_demo_data

    seed_demo_data()


@router.get("")
def dashboard(request: Request, message: str = ""):
    return templates.TemplateResponse(
        "admin/dashboard.html", {"request": request, "message": message, "stages": list_stages(), "stage_illustration": _stage_illustration}
    )


@router.get("/editor")
def editor(request: Request, stage_id: int | None = None):
    selected_stage = get_stage(stage_id) if stage_id else None
    steps = list_steps_by_stage(stage_id) if stage_id else []
    return templates.TemplateResponse(
        "admin/editor.html",
        {"request": request, "stages": list_stages(), "selected_stage": selected_stage, "steps": steps},
    )


@router.post("/init-db")
def init_db_action():
    init_db()
    return RedirectResponse(url="/admin?message=Base+de+datos+inicializada", status_code=303)


@router.post("/seed-demo")
def seed_demo_action():
    init_db()
    _seed_demo_data()
    return RedirectResponse(url="/admin?message=Datos+demo+cargados", status_code=303)


@router.post("/generate/{stage_id}")
def generate_action(stage_id: int):
    stage = get_stage(stage_id)
    if not stage:
        return RedirectResponse(url="/admin?message=Etapa+no+encontrada", status_code=303)

    try:
        tutorial = generate_stage_tutorial(stage.name)
    except Exception as exc:
        msg = str(exc).replace(" ", "+")
        return RedirectResponse(url=f"/admin?message={msg}", status_code=303)

    from app.repositories import replace_steps

    payload = []
    for step in tutorial.steps:
        content = (
            f"Objetivo: {step.objective}\n\n"
            + "Instrucciones:\n"
            + "\n".join([f"- {item}" for item in step.instructions])
            + "\n\nErrores comunes:\n"
            + "\n".join([f"- {item}" for item in step.common_mistakes])
            + "\n\nChecklist:\n"
            + "\n".join([f"- {item}" for item in step.checklist])
        )
        payload.append(
            {
                "title": step.title,
                "content": content,
                "tools": step.materials,
                "estimated_cost_usd": step.estimated_cost_usd,
            }
        )
    replace_steps(stage_id, payload)
    return RedirectResponse(url="/admin?message=Contenido+IA+generado", status_code=303)


@router.post("/editor/stage")
def create_or_update_stage(
    stage_id: int | None = Form(default=None), name: str = Form(...), order_index: int = Form(...)
):
    from app.repositories import update_stage

    if stage_id:
        update_stage(stage_id, name, order_index)
    else:
        create_stage(name, order_index)
    return RedirectResponse(url="/admin/editor", status_code=303)


@router.post("/editor/step")
def add_step(
    stage_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    tools_csv: str = Form(default=""),
    estimated_cost_usd: float = Form(default=0),
):
    tools = [item.strip() for item in tools_csv.split(",") if item.strip()]
    create_step(stage_id, title, content, tools, estimated_cost_usd)
    return RedirectResponse(url=f"/admin/editor?stage_id={stage_id}", status_code=303)
