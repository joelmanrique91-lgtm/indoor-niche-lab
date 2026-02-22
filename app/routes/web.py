from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

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
        "home.como-funciona-1": home_image("como-funciona-1"),
        "home.como-funciona-2": home_image("como-funciona-2"),
        "home.como-funciona-3": home_image("como-funciona-3"),
        "home.testimonios-1": home_image("testimonios-1"),
        "home.testimonios-2": home_image("testimonios-2"),
        "home.testimonios-3": home_image("testimonios-3"),
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


@router.get("/debug/static-check")
def debug_static_check(request: Request):
    generated_root = Path("app/static/img/generated")
    files = []
    total_bytes = 0
    if generated_root.exists():
        for path in sorted(generated_root.rglob("*")):
            if not path.is_file():
                continue
            size = path.stat().st_size
            rel = path.relative_to(Path("app/static")).as_posix()
            files.append({
                "relative": rel,
                "size": size,
                "url": request.url_for("static", path=rel),
            })
            total_bytes += size

    html_parts = [
        "<html><body>",
        "<h1>Debug static check</h1>",
        f"<p>Total archivos: {len(files)}</p>",
        f"<p>Total bytes: {total_bytes}</p>",
        "<ul>",
    ]
    for item in files:
        url = str(item["url"])
        html_parts.append(
            f"<li><a href='{url}' target='_blank'>{item['relative']}</a> ({item['size']} bytes)<br>"
            f"<img src='{url}' alt='{item['relative']}' width='260' loading='lazy'></li><br>"
        )
    html_parts.extend(["</ul>", "</body></html>"])
    return HTMLResponse("".join(html_parts))
