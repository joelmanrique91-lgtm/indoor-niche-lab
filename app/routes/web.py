from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.repositories import get_stage, list_kits, list_products, list_stages, list_steps_by_stage
from app.services.image_resolver import entity_slot, resolve_static_path

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _home_images() -> dict[str, str]:
    return {
        "home.hero": resolve_static_path("home", "hero"),
        "home.beneficios-1": resolve_static_path("home", "beneficios-1"),
        "home.beneficios-2": resolve_static_path("home", "beneficios-2"),
        "home.beneficios-3": resolve_static_path("home", "beneficios-3"),
        "home.como-funciona-1": resolve_static_path("home", "como-funciona-1"),
        "home.como-funciona-2": resolve_static_path("home", "como-funciona-2"),
        "home.como-funciona-3": resolve_static_path("home", "como-funciona-3"),
        "home.testimonios-1": resolve_static_path("home", "testimonios-1"),
        "home.testimonios-2": resolve_static_path("home", "testimonios-2"),
        "home.testimonios-3": resolve_static_path("home", "testimonios-3"),
        "home.faq": resolve_static_path("home", "faq"),
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
                "slot": entity_slot("stage", stage.id, stage.name),
                "image_path": resolve_static_path("stages", entity_slot("stage", stage.id, stage.name), "md"),
            }
        )
    return templates.TemplateResponse("stage_list.html", {"request": request, "stages": stage_rows, "hero_path": resolve_static_path("stages", "hero", "md")})


@router.get("/stages/{stage_id}")
def stage_detail(stage_id: int, request: Request):
    stage = get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    steps = list_steps_by_stage(stage_id)
    stage_slot = entity_slot("stage", stage.id, stage.name)
    return templates.TemplateResponse(
        "stage_detail.html",
        {
            "request": request,
            "stage": stage,
            "steps": steps,
            "stage_image_path": resolve_static_path("stages", stage_slot, "lg"),
        },
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
                "slot": entity_slot("product", product.id, product.name),
                "image_path": resolve_static_path("products", entity_slot("product", product.id, product.name), "md"),
            }
        )
    return templates.TemplateResponse("product_list.html", {"request": request, "products": product_rows, "hero_path": resolve_static_path("products", "hero", "md")})


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
                "slot": entity_slot("kit", kit.id, kit.name),
                "image_path": resolve_static_path("kits", entity_slot("kit", kit.id, kit.name), "md"),
                "result_image_path": resolve_static_path("kits", entity_slot("kit-result", kit.id, kit.name), "md"),
            }
        )
    return templates.TemplateResponse("kit_list.html", {"request": request, "kits": kit_rows, "hero_path": resolve_static_path("kits", "hero", "md")})


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
