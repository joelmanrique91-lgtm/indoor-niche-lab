from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates

from app.repositories import get_stage_by_slug, list_products, list_stages

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/stages")
def stages(request: Request):
    return templates.TemplateResponse(
        "stage_list.html",
        {"request": request, "stages": list_stages()},
    )


@router.get("/stages/{slug}")
def stage_detail(slug: str, request: Request):
    stage = get_stage_by_slug(slug)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    return templates.TemplateResponse(
        "stage_detail.html",
        {"request": request, "stage": stage},
    )


@router.get("/products")
def products(request: Request):
    return templates.TemplateResponse(
        "product_list.html",
        {"request": request, "products": list_products()},
    )
