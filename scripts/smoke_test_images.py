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


def _load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        raise SystemExit("Manifest de imágenes no encontrado. Ejecutá generate_site_images.py primero.")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Manifest inválido: se esperaba una lista de slots")
    return data


def _check_manifest_and_fallback(entries: list[dict]) -> None:
    from app.services.image_resolver import home_image

    by_slot = {entry.get("slot"): entry for entry in entries}
    missing = [slot for slot in HOME_SLOTS if slot not in by_slot]
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


def main() -> None:
    entries = _load_manifest()
    _check_manifest_and_fallback(entries)
    _check_home_render_and_images()
    print("OK")


if __name__ == "__main__":
    main()
