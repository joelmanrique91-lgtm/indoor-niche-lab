from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.repositories import get_stage, list_kits, list_products, list_stages, list_steps_by_stage

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/stages")
def stages(request: Request):
    return templates.TemplateResponse("stage_list.html", {"request": request, "stages": list_stages()})


@router.get("/stages/{stage_id}")
def stage_detail(stage_id: int, request: Request):
    stage = get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    steps = list_steps_by_stage(stage_id)
    return templates.TemplateResponse(
        "stage_detail.html", {"request": request, "stage": stage, "steps": steps}
    )


@router.get("/products")
def products(request: Request):
    return templates.TemplateResponse("product_list.html", {"request": request, "products": list_products()})


@router.get("/kits")
def kits(request: Request):
    return templates.TemplateResponse("kit_list.html", {"request": request, "kits": list_kits()})
