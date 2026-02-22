from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.repositories import get_stage, list_kits, list_products, list_stages, list_steps_by_stage
from app.services.image_resolver import (
    home_image,
    kit_card_image,
    product_card_image,
    slugify,
    stage_banner_image,
    stage_card_image,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _home_images() -> dict[str, str]:
    return {
        "home.hero": home_image("hero"),
        "home.beneficios-1": home_image("beneficios-1"),
        "home.beneficios-2": home_image("beneficios-2"),
        "home.beneficios-3": home_image("beneficios-3"),
        "home.como-funciona": home_image("como-funciona"),
        "home.testimonios": home_image("testimonios"),
        "home.faq": home_image("faq"),
    }


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "img": _home_images()})


@router.get("/stages")
def stages(request: Request):
    stage_rows = []
    for stage in list_stages():
        stage_rows.append(
            {
                "id": stage.id,
                "name": stage.name,
                "order_index": stage.order_index,
                "slug": slugify(stage.name),
                "image_url": stage_card_image(stage.name),
            }
        )
    return templates.TemplateResponse("stage_list.html", {"request": request, "stages": stage_rows})


@router.get("/stages/{stage_id}")
def stage_detail(stage_id: int, request: Request):
    stage = get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    steps = list_steps_by_stage(stage_id)
    banner_url = stage_banner_image(stage.name)
    return templates.TemplateResponse(
        "stage_detail.html",
        {"request": request, "stage": stage, "steps": steps, "banner_url": banner_url},
    )


@router.get("/products")
def products(request: Request):
    product_rows = []
    for product in list_products():
        product_rows.append(
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "affiliate_url": product.affiliate_url,
                "internal_product": product.internal_product,
                "slug": slugify(product.name),
                "image_url": product_card_image(product.name),
            }
        )
    return templates.TemplateResponse("product_list.html", {"request": request, "products": product_rows})


@router.get("/kits")
def kits(request: Request):
    kit_rows = []
    for kit in list_kits():
        kit_rows.append(
            {
                "id": kit.id,
                "name": kit.name,
                "description": kit.description,
                "price": kit.price,
                "components_json": kit.components_json,
                "slug": slugify(kit.name),
                "image_url": kit_card_image(kit.name),
            }
        )
    return templates.TemplateResponse("kit_list.html", {"request": request, "kits": kit_rows})
