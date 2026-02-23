from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image

from app.db import get_conn, init_db
from app.templating import templates
from app.repositories import (
    create_stage,
    create_step,
    get_stage,
    list_stages,
    list_steps_by_stage,
)
from app.services.ai_content import generate_stage_tutorial

router = APIRouter(prefix="/admin", tags=["admin"])


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


def _save_upload(upload: UploadFile | None, section: str, slot: str) -> str | None:
    if not upload or not upload.filename:
        return None
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        return None

    folder = Path("app/static/img/generated") / section / slot
    folder.mkdir(parents=True, exist_ok=True)

    raw = upload.file.read()
    if not raw:
        return None

    original_path = folder / f"original{suffix}"
    original_path.write_bytes(raw)

    image = Image.open(original_path).convert("RGB")
    image.resize((1120, 480)).save(folder / "lg.jpg", format="JPEG", quality=88, optimize=True)
    image.resize((560, 220)).save(folder / "md.jpg", format="JPEG", quality=86, optimize=True)
    image.resize((560, 220)).save(folder / "md.webp", format="WEBP", quality=82, method=6)
    image.resize((280, 140)).save(folder / "sm.jpg", format="JPEG", quality=82, optimize=True)
    image.resize((280, 140)).save(folder / "sm.webp", format="WEBP", quality=80, method=6)

    return f"img/generated/{section}/{slot}/md.jpg"


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
    stage_id: int | None = Form(default=None),
    name: str = Form(...),
    order_index: int = Form(...),
    image_card_1: str = Form(default=""),
    image_card_2: str = Form(default=""),
    image_hero: str = Form(default=""),
):
    from app.repositories import update_stage

    img1 = image_card_1.strip() or None
    img2 = image_card_2.strip() or None
    hero = image_hero.strip() or None
    if stage_id:
        update_stage(stage_id, name, order_index, img1, img2, hero)
    else:
        create_stage(name, order_index, img1, img2, hero)
    return RedirectResponse(url="/admin/editor", status_code=303)


@router.post("/editor/step")
def add_step(
    stage_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    tools_csv: str = Form(default=""),
    estimated_cost_usd: float = Form(default=0),
    image: str = Form(default=""),
    image_file: UploadFile | None = File(default=None),
):
    tools = [item.strip() for item in tools_csv.split(",") if item.strip()]
    stored_image = image.strip() or None
    if image_file and image_file.filename:
        saved = _save_upload(image_file, "stages", f"step-{uuid4().hex[:8]}")
        if saved:
            stored_image = saved
    create_step(stage_id, title, content, tools, estimated_cost_usd, stored_image)
    return RedirectResponse(url=f"/admin/editor?stage_id={stage_id}", status_code=303)


@router.post("/uploads/product/{product_id}")
def upload_product_image(product_id: int, image_file: UploadFile = File(...)):
    path = _save_upload(image_file, "products", f"product-{product_id}")
    if not path:
        return RedirectResponse(url="/admin?message=Formato+de+imagen+inválido", status_code=303)
    with get_conn() as conn:
        conn.execute("UPDATE products SET image = ? WHERE id = ?", (path, product_id))
    return RedirectResponse(url="/admin?message=Imagen+de+producto+actualizada", status_code=303)


@router.post("/uploads/kit/{kit_id}")
def upload_kit_images(
    kit_id: int,
    image_main: UploadFile | None = File(default=None),
    image_result: UploadFile | None = File(default=None),
):
    main_path = _save_upload(image_main, "kits", f"kit-{kit_id}") if image_main else None
    result_path = _save_upload(image_result, "kits", f"kit-result-{kit_id}") if image_result else None
    with get_conn() as conn:
        if main_path:
            conn.execute("UPDATE kits SET image_card = ? WHERE id = ?", (main_path, kit_id))
        if result_path:
            conn.execute("UPDATE kits SET image_result = ? WHERE id = ?", (result_path, kit_id))
    return RedirectResponse(url="/admin?message=Imágenes+de+kit+actualizadas", status_code=303)
