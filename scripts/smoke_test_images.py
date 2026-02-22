from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

MANIFEST_PATH = ROOT / "data/generated_images_manifest.json"

HOME_SLOTS = [
    "home.hero",
    "home.beneficios-1",
    "home.beneficios-2",
    "home.beneficios-3",
    "home.como-funciona-1",
    "home.como-funciona-2",
    "home.como-funciona-3",
    "home.testimonios-1",
    "home.testimonios-2",
    "home.testimonios-3",
    "home.faq",
]


def _public_to_file(public_url: str) -> Path:
    if not public_url.startswith("/static/"):
        raise ValueError(f"Ruta no estática: {public_url}")
    return ROOT / "app" / "static" / public_url.removeprefix("/static/")


def _load_manifest_items() -> list[dict]:
    if not MANIFEST_PATH.exists():
        raise SystemExit("Manifest de imágenes no encontrado. Ejecutá generate_site_images.py primero.")

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if isinstance(data, list):
        items = []
        for row in data:
            slot_key = str(row.get("slot", ""))
            if "." not in slot_key:
                continue
            section, slot = slot_key.split(".", 1)
            output_files = row.get("output_files", {})
            if not isinstance(output_files, dict):
                continue
            for size, path in output_files.items():
                items.append({"section": section, "slot": slot, "size": size, "path": path})
        return items

    if not isinstance(data, dict):
        raise SystemExit("Manifest inválido: formato no reconocido")

    items = data.get("items", [])
    if not isinstance(items, list):
        raise SystemExit("Manifest inválido: 'items' debe ser una lista")
    return items


def _check_manifest_and_fallback(items: list[dict]) -> None:
    from app.services.image_resolver import home_image

    slot_keys = {f"{item.get('section')}.{item.get('slot')}" for item in items if item.get("section") and item.get("slot")}
    missing = [slot for slot in HOME_SLOTS if slot not in slot_keys]
    if missing:
        raise SystemExit(f"Faltan slots en manifest: {', '.join(missing)}")

    for full_slot in HOME_SLOTS:
        resolver_key = full_slot.removeprefix("home.")
        resolved = home_image(resolver_key)
        resolved_path = _public_to_file(resolved)
        if not resolved_path.exists():
            raise SystemExit(f"Resolver devolvió ruta inexistente para {full_slot}: {resolved}")


def _check_home_render_and_images() -> None:
    from app.main import app

    client = TestClient(app)
    response = client.get("/")
    if response.status_code != 200:
        raise SystemExit(f"Home no renderiza OK: {response.status_code}")

    html = response.text
    expected_snippets = [
        "/static/img/generated/home/como-funciona-1",
        "/static/img/generated/home/como-funciona-2",
        "/static/img/generated/home/como-funciona-3",
        "/static/img/generated/home/testimonios-1",
        "/static/img/generated/home/testimonios-2",
        "/static/img/generated/home/testimonios-3",
    ]
    if not all(snippet in html for snippet in expected_snippets):
        raise SystemExit("El home renderizado no contiene referencias a los nuevos slots granulares.")

    for src in re.findall(r'src="([^"]+)"', html):
        if not src.startswith("/static/"):
            continue
        file_path = _public_to_file(src)
        if not file_path.exists():
            raise SystemExit(f"Imagen referenciada no existe: {src} -> {file_path}")


def _check_stage_product_coverage() -> None:
    from app.repositories import list_kits, list_products, list_stages
    from app.services.image_resolver import entity_slot, resolve_static_path, PLACEHOLDER_STATIC_PATH

    missing: list[str] = []

    for stage in list_stages():
        slot = entity_slot("stage", stage.id, stage.name)
        resolved_md = resolve_static_path("stages", slot, "md")
        resolved_lg = resolve_static_path("stages", slot, "lg")
        if resolved_md == PLACEHOLDER_STATIC_PATH:
            missing.append(f"section=stages slot={slot} size=md entity=stage:{stage.id}")
        if resolved_lg == PLACEHOLDER_STATIC_PATH:
            missing.append(f"section=stages slot={slot} size=lg entity=stage:{stage.id}")

    for product in list_products():
        slot = entity_slot("product", product.id, product.name)
        resolved = resolve_static_path("products", slot, "md")
        if resolved == PLACEHOLDER_STATIC_PATH:
            missing.append(f"section=products slot={slot} size=md entity=product:{product.id}")

    for kit in list_kits():
        slot = entity_slot("kit", kit.id, kit.name)
        result_slot = entity_slot("kit-result", kit.id, kit.name)
        resolved_kit = resolve_static_path("kits", slot, "md")
        resolved_result = resolve_static_path("kits", result_slot, "md")
        if resolved_kit == PLACEHOLDER_STATIC_PATH:
            missing.append(f"section=kits slot={slot} size=md entity=kit:{kit.id}")
        if resolved_result == PLACEHOLDER_STATIC_PATH:
            missing.append(f"section=kits slot={result_slot} size=md entity=kit-result:{kit.id}")

    if missing:
        lines = "\n - ".join(missing)
        raise SystemExit(f"Cobertura de imágenes incompleta; faltan assets esperados:\n - {lines}")


def main() -> None:
    items = _load_manifest_items()
    _check_manifest_and_fallback(items)
    _check_home_render_and_images()
    _check_stage_product_coverage()
    print("OK")


if __name__ == "__main__":
    main()
