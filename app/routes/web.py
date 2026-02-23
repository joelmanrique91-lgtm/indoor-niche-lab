from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.templating import templates

from app.repositories import get_product, get_stage, list_kits, list_products, list_stages, list_steps_by_stage
from app.services.image_resolver import (
    entity_slot,
    build_picture_sources,
    kit_card_image,
    kit_result_image,
    product_image,
    resolve_static_path,
    resolution_debug,
    stage_hero_image,
    stage_list_images,
    step_image_cards,
)

router = APIRouter()


def _static_url(request: Request, path: str) -> str:
    return str(request.app.url_path_for("static", path=path))


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
                "images": stage_list_images(stage),
                "image_variants": {k: build_picture_sources(v) for k, v in stage_list_images(stage).items()},
            }
        )
    return templates.TemplateResponse("stage_list.html", {"request": request, "stages": stage_rows, "hero_path": resolve_static_path("stages", "hero", "md")})


@router.get("/stages/{stage_id}")
def stage_detail(stage_id: int, request: Request):
    stage = get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    steps = list_steps_by_stage(stage_id)
    step_rows = []
    for step in steps:
        cards = step_image_cards(step, stage=stage)
        step_rows.append(
            {
                "id": step.id,
                "title": step.title,
                "content": step.content,
                "tools_json": step.tools_json,
                "estimated_cost_usd": step.estimated_cost_usd,
                "image_cards": cards,
                "image_variants": {"card_1": build_picture_sources(cards["card_1"]), "card_2": build_picture_sources(cards["card_2"])},
            }
        )
    return templates.TemplateResponse(
        "stage_detail.html",
        {
            "request": request,
            "stage": stage,
            "steps": step_rows,
            "stage_image_path": stage_hero_image(stage),
            "stage_image_variants": build_picture_sources(stage_hero_image(stage)),
        },
    )


@router.get("/products")
def products(request: Request):
    product_rows = []
    for product in list_products():
        image_path = product_image(product)
        product_rows.append(
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "affiliate_url": product.affiliate_url,
                "internal_product": product.internal_product,
                "image_path": image_path,
                "image_variants": build_picture_sources(image_path),
            }
        )
    hero_path = resolve_static_path("products", "hero", "md")
    return templates.TemplateResponse(
        "product_list.html",
        {"request": request, "products": product_rows, "hero_path": hero_path, "hero_variants": build_picture_sources(hero_path)},
    )


@router.get("/products/{product_id}")
def product_detail(product_id: int, request: Request):
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    image_path = product_image(product)
    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "product": product, "image_path": image_path, "image_variants": build_picture_sources(image_path)},
    )


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
                "image_path": kit_card_image(kit),
                "result_image_path": kit_result_image(kit),
                "image_variants": build_picture_sources(kit_card_image(kit)),
                "result_image_variants": build_picture_sources(kit_result_image(kit)),
            }
        )
    hero_path = resolve_static_path("kits", "hero", "md")
    return templates.TemplateResponse("kit_list.html", {"request": request, "kits": kit_rows, "hero_path": hero_path, "hero_variants": build_picture_sources(hero_path)})


@router.get("/debug/image-bindings")
def debug_image_bindings(request: Request, stage_id: int | None = None, kit_id: int | None = None):
    rows: list[dict[str, object]] = []

    if stage_id is not None:
        stage = get_stage(stage_id)
        if not stage:
            raise HTTPException(status_code=404, detail="Etapa no encontrada")
        stage_slot = entity_slot("stage", stage.id, stage.name)
        rows.append({"entity": f"stage:{stage.id}", "kind": "hero", **resolution_debug("stages", stage_slot, stage.image_hero)})
        rows.append({"entity": f"stage:{stage.id}", "kind": "card-1", **resolution_debug("stages", f"{stage_slot}-card-1", stage.image_card_1)})
        rows.append({"entity": f"stage:{stage.id}", "kind": "card-2", **resolution_debug("stages", f"{stage_slot}-card-2", stage.image_card_2)})

        for step in list_steps_by_stage(stage_id):
            step_slot = entity_slot("step", step.id, step.title)
            debug_row = resolution_debug("stages", step_slot, step.image)
            rows.append({"entity": f"step:{step.id}", "kind": "step", **debug_row})

    if kit_id is not None:
        kit = next((item for item in list_kits() if item.id == kit_id), None)
        if not kit:
            raise HTTPException(status_code=404, detail="Kit no encontrado")
        kit_slot = entity_slot("kit", kit.id, kit.name)
        result_slot = entity_slot("kit-result", kit.id, kit.name)
        rows.append({"entity": f"kit:{kit.id}", "kind": "main", **resolution_debug("kits", kit_slot, kit.image_card)})
        rows.append({"entity": f"kit:{kit.id}", "kind": "result", **resolution_debug("kits", result_slot, kit.image_result)})

    if stage_id is None and kit_id is None:
        return {"hint": "Pasá stage_id y/o kit_id en query params", "rows": rows}

    for row in rows:
        row["public_url"] = _static_url(request, row["selected_path"])

    return {"stage_id": stage_id, "kit_id": kit_id, "rows": rows}


@router.get("/debug/static-check")
def debug_static_check(request: Request):
    generated_root = Path("app/static/img/generated")
    sections = ["home", "stages", "products", "kits"]
    files = []
    total_bytes = 0
    section_counts = {section: 0 for section in sections}
    section_bytes = {section: 0 for section in sections}
    if generated_root.exists():
        for path in sorted(generated_root.rglob("*")):
            if not path.is_file():
                continue
            size = path.stat().st_size
            rel = path.relative_to(Path("app/static")).as_posix()
            parts = rel.split("/")
            if len(parts) >= 3 and parts[0] == "img" and parts[1] == "generated" and parts[2] in section_counts:
                section = parts[2]
                section_counts[section] += 1
                section_bytes[section] += size
            files.append({
                "relative": rel,
                "size": size,
                "url": request.app.url_path_for("static", path=rel),
            })
            total_bytes += size

    expected_examples: list[dict[str, str]] = []
    stages_rows = list_stages()
    product_rows = list_products()
    kit_rows = list_kits()

    if stages_rows:
        stage = stages_rows[0]
        stage_slot = entity_slot("stage", stage.id, stage.name)
        expected_examples.extend(
            [
                {"label": f"stage:{stage.id} md", "path": f"img/generated/stages/{stage_slot}/md.webp"},
                {"label": f"stage:{stage.id} lg", "path": f"img/generated/stages/{stage_slot}/lg.webp"},
            ]
        )
    if product_rows:
        product = product_rows[0]
        product_slot = entity_slot("product", product.id, product.name)
        expected_examples.append({"label": f"product:{product.id} md", "path": f"img/generated/products/{product_slot}/md.webp"})
    if kit_rows:
        kit = kit_rows[0]
        kit_slot = entity_slot("kit", kit.id, kit.name)
        kit_result_slot = entity_slot("kit-result", kit.id, kit.name)
        expected_examples.extend(
            [
                {"label": f"kit:{kit.id} md", "path": f"img/generated/kits/{kit_slot}/md.webp"},
                {"label": f"kit-result:{kit.id} md", "path": f"img/generated/kits/{kit_result_slot}/md.webp"},
            ]
        )

    missing_sections = [section for section in sections if section_counts.get(section, 0) == 0]

    html_parts = [
        "<html><body>",
        "<h1>Debug static check</h1>",
        f"<p>Total archivos: {len(files)}</p>",
        f"<p>Total bytes: {total_bytes}</p>",
        "<h2>Conteo por sección</h2>",
        "<ul>",
    ]
    for section in sections:
        html_parts.append(f"<li><strong>{section}</strong>: {section_counts[section]} archivos, {section_bytes[section]} bytes</li>")

    html_parts.append("</ul>")
    if missing_sections:
        html_parts.append(f"<p style='color:#b91c1c;'><strong>ALERTA:</strong> secciones sin archivos: {', '.join(missing_sections)}</p>")

    html_parts.extend([
        "<h2>Expected examples (DB-derived)</h2>",
        "<ul>",
    ])
    if expected_examples:
        for item in expected_examples:
            rel_path = item["path"]
            abs_path = Path("app/static") / rel_path
            exists = abs_path.exists() and abs_path.stat().st_size > 0
            status = "EXISTS" if exists else "MISSING"
            color = "#166534" if exists else "#b91c1c"
            url = str(request.app.url_path_for("static", path=rel_path))
            html_parts.append(
                f"<li><strong>{item['label']}</strong>: <code>{rel_path}</code> "
                f"<span style='color:{color};font-weight:bold;'>{status}</span> "
                f"<a href='{url}' target='_blank'>open</a></li>"
            )
    else:
        html_parts.append("<li>Sin entidades en DB para construir ejemplos esperados.</li>")

    html_parts.extend([
        "</ul>",
        "<h2>Archivos detectados</h2>",
        "<ul>",
    ])

    for item in files:
        url = str(item["url"])
        html_parts.append(
            f"<li><a href='{url}' target='_blank'>{item['relative']}</a> ({item['size']} bytes)<br>"
            f"<img src='{url}' alt='{item['relative']}' width='260' loading='lazy'></li><br>"
        )
    html_parts.extend(["</ul>", "</body></html>"])
    return HTMLResponse("".join(html_parts))
