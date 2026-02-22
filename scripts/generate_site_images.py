#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
HOME_TEMPLATE = ROOT / "app/templates/home.html"
OUTPUT_ROOT = ROOT / "app/static/img/generated/home"
MANIFEST_PATH = ROOT / "data/generated_images_manifest.json"

MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")


@dataclass(frozen=True)
class SlotSpec:
    slot: str
    alt: str
    prompt: str
    source_template: str = "app/templates/home.html"


HOME_SLOTS: list[SlotSpec] = [
    SlotSpec("home.hero", "Persona cosechando hongos gourmet frescos en una cocina de hogar", "Fotografía realista, cocina hogareña, persona cosechando hongos gourmet sobre tabla de madera, luz natural cálida, estética limpia, sin marcas, sin texto."),
    SlotSpec("home.beneficios-1", "Kit de cultivo indoor listo para comenzar sobre mesa de trabajo", "Fotografía realista de kit de cultivo de hongos gourmet sobre mesa, elementos ordenados, luz natural, estilo e-commerce premium, sin logos."),
    SlotSpec("home.beneficios-2", "Cosecha abundante de hongos gourmet recién cortados", "Fotografía realista de bandeja con hongos ostra/shiitake recién cosechados en cocina, enfoque nítido, luz cálida."),
    SlotSpec("home.beneficios-3", "Persona recibiendo asesoría de soporte para cultivo por mensaje", "Fotografía realista de manos usando celular con guía/tutorial, ambiente de cocina, sensación de acompañamiento, sin texto en pantalla."),
    SlotSpec("home.como-funciona-1", "Entrega de kit de cultivo listo para abrir en el hogar", "Fotografía realista de paquete o box de kit llegando a casa, manos recibiendo, puerta o mesa de entrada, luz natural."),
    SlotSpec("home.como-funciona-2", "Seguimiento de checklist de cultivo en una guía impresa", "Fotografía realista de checklist o guía impresa junto al kit, manos señalando pasos, mesa limpia, luz natural."),
    SlotSpec("home.como-funciona-3", "Resultado final de hongos gourmet cosechados en cocina", "Fotografía realista de hongos gourmet listos para cocinar en sartén o plato, estética casera premium, luz cálida."),
    SlotSpec("home.testimonios-1", "Foto de Andrea cliente de Indoor Niche Lab", "Fotografía realista testimonial en cocina hogareña: manos cocinando hongos gourmet con kit en uso al fondo, luz natural cálida, sin primer plano de rostro, sin deformaciones."),
    SlotSpec("home.testimonios-2", "Foto de Martín cliente de Indoor Niche Lab", "Fotografía realista testimonial en cocina hogareña: persona de espaldas preparando kit de cultivo sobre mesada, composición limpia, luz natural, sin primer plano de rostro."),
    SlotSpec("home.testimonios-3", "Foto de Lucía cliente de Indoor Niche Lab", "Fotografía realista testimonial en cocina hogareña: plato final con hongos gourmet y manos sirviendo, estética cálida, coherente con dirección de arte del sitio."),
    SlotSpec("home.faq", "Mesa limpia de soporte y preguntas frecuentes", "Fotografía realista de mesa de cocina limpia con kit y una libreta o agenda, sensación de orden y claridad, luz natural."),
]

SIZES = {"sm": (640, 426), "md": (1024, 683), "lg": (1536, 1024)}


def _slot_dir(slot: str) -> Path:
    return OUTPUT_ROOT / slot


def _output_files(slot: str) -> dict[str, Path]:
    base = _slot_dir(slot)
    return {k: base / f"{k}.webp" for k in SIZES}


def _is_complete(slot: str) -> bool:
    return all(path.exists() for path in _output_files(slot).values())


def _generate_real_png(client, prompt: str) -> bytes:
    result = client.images.generate(model=MODEL, prompt=prompt, size="1536x1024", quality="high")
    b64 = result.data[0].b64_json
    if not b64:
        raise RuntimeError("OpenAI no devolvió b64_json")
    return base64.b64decode(b64)


def _generate_mock_png(slot: str, prompt: str) -> bytes:
    w, h = 1536, 1024
    image = Image.new("RGB", (w, h), color=(228, 216, 194))
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 60, w - 60, h - 60), outline=(120, 95, 65), width=5)
    draw.text((100, 120), f"MOCK {slot}", fill=(88, 64, 40))
    draw.text((100, 190), prompt[:180], fill=(88, 64, 40))
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _save_webp_variants(png_bytes: bytes, slot: str) -> dict[str, str]:
    out = _output_files(slot)
    out[next(iter(out))].parent.mkdir(parents=True, exist_ok=True)
    with Image.open(BytesIO(png_bytes)) as image:
        source = image.convert("RGB")
        public: dict[str, str] = {}
        for size_name, dims in SIZES.items():
            variant = source.resize(dims, Image.Resampling.LANCZOS)
            variant.save(out[size_name], format="WEBP", quality=82, method=6)
            public[size_name] = str(out[size_name].relative_to(ROOT))
        return public


def _load_manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _write_manifest(rows: list[dict]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def _upsert_manifest(manifest: list[dict], row: dict) -> None:
    for idx, existing in enumerate(manifest):
        if existing.get("slot") == row.get("slot"):
            manifest[idx] = row
            return
    manifest.append(row)


def generate_home(mock: bool, force: bool) -> None:
    manifest = _load_manifest()
    client = None
    if not mock:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    for spec in HOME_SLOTS:
        files = _output_files(spec.slot)
        if _is_complete(spec.slot) and not force:
            row = {
                "slot": spec.slot,
                "prompt": spec.prompt,
                "alt": spec.alt,
                "model": "mock" if mock else MODEL,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_template": spec.source_template,
                "output_files": {k: str(v.relative_to(ROOT)) for k, v in files.items()},
                "status": "skipped-existing",
            }
            _upsert_manifest(manifest, row)
            continue

        png = _generate_mock_png(spec.slot, spec.prompt) if mock else _generate_real_png(client, spec.prompt)
        saved = _save_webp_variants(png, spec.slot)
        row = {
            "slot": spec.slot,
            "prompt": spec.prompt,
            "alt": spec.alt,
            "model": "mock" if mock else MODEL,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_template": spec.source_template,
            "output_files": saved,
            "status": "generated",
        }
        _upsert_manifest(manifest, row)

    manifest.sort(key=lambda x: x.get("slot", ""))
    _write_manifest(manifest)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generador IA de imágenes por slots para Home.")
    parser.add_argument("--only", choices=["home"], default="home")
    parser.add_argument("--mock", action="store_true", help="Genera placeholders locales sin API key")
    parser.add_argument("--real", action="store_true", help="Genera imágenes reales con OpenAI")
    parser.add_argument("--force", action="store_true", help="Regenera aunque existan archivos")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mock and args.real:
        raise SystemExit("Elegí solo un modo: --mock o --real")

    use_mock = args.mock or not args.real
    if not use_mock and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Falta OPENAI_API_KEY. Usá --mock o configurá la variable para --real")

    if args.only == "home":
        if not HOME_TEMPLATE.exists():
            raise SystemExit("No se encontró app/templates/home.html")
        generate_home(mock=use_mock, force=args.force)

    print("Generación completada")


if __name__ == "__main__":
    main()
