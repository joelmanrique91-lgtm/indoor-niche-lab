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
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.repositories import list_kits, list_products, list_stages
from app.services.image_resolver import entity_slot

OUTPUT_ROOT = ROOT / "app/static/img/generated"
MANIFEST_PATH = ROOT / "data/generated_images_manifest.json"

MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")


@dataclass(frozen=True)
class SlotSpec:
    section: str
    slot: str
    alt: str
    prompt: str
    source_template: str

    @property
    def slot_key(self) -> str:
        return f"{self.section}.{self.slot}"


HOME_SLOTS: list[SlotSpec] = [
    SlotSpec("home", "hero", "Persona cosechando hongos gourmet frescos en una cocina de hogar", "Fotografía realista, cocina hogareña, persona cosechando hongos gourmet sobre tabla de madera, luz natural cálida, estética limpia, sin marcas, sin texto.", "app/templates/home.html"),
    SlotSpec("home", "beneficios-1", "Kit de cultivo indoor listo para comenzar sobre mesa de trabajo", "Fotografía realista de kit de cultivo de hongos gourmet sobre mesa, elementos ordenados, luz natural, estilo e-commerce premium, sin logos.", "app/templates/home.html"),
    SlotSpec("home", "beneficios-2", "Cosecha abundante de hongos gourmet recién cortados", "Fotografía realista de bandeja con hongos ostra/shiitake recién cosechados en cocina, enfoque nítido, luz cálida.", "app/templates/home.html"),
    SlotSpec("home", "beneficios-3", "Persona recibiendo asesoría de soporte para cultivo por mensaje", "Fotografía realista de manos usando celular con guía/tutorial, ambiente de cocina, sensación de acompañamiento, sin texto en pantalla.", "app/templates/home.html"),
    SlotSpec("home", "como-funciona-1", "Entrega de kit de cultivo listo para abrir en el hogar", "Fotografía realista de paquete o box de kit llegando a casa, manos recibiendo, puerta o mesa de entrada, luz natural.", "app/templates/home.html"),
    SlotSpec("home", "como-funciona-2", "Seguimiento de checklist de cultivo en una guía impresa", "Fotografía realista de checklist o guía impresa junto al kit, manos señalando pasos, mesa limpia, luz natural.", "app/templates/home.html"),
    SlotSpec("home", "como-funciona-3", "Resultado final de hongos gourmet cosechados en cocina", "Fotografía realista de hongos gourmet listos para cocinar en sartén o plato, estética casera premium, luz cálida.", "app/templates/home.html"),
    SlotSpec("home", "testimonios-1", "Foto de Andrea cliente de Indoor Niche Lab", "Fotografía realista testimonial en cocina hogareña: manos cocinando hongos gourmet con kit en uso al fondo, luz natural cálida, sin primer plano de rostro, sin deformaciones.", "app/templates/home.html"),
    SlotSpec("home", "testimonios-2", "Foto de Martín cliente de Indoor Niche Lab", "Fotografía realista testimonial en cocina hogareña: persona de espaldas preparando kit de cultivo sobre mesada, composición limpia, luz natural, sin primer plano de rostro.", "app/templates/home.html"),
    SlotSpec("home", "testimonios-3", "Foto de Lucía cliente de Indoor Niche Lab", "Fotografía realista testimonial en cocina hogareña: plato final con hongos gourmet y manos sirviendo, estética cálida, coherente con dirección de arte del sitio.", "app/templates/home.html"),
    SlotSpec("home", "faq", "Mesa limpia de soporte y preguntas frecuentes", "Fotografía realista de mesa de cocina limpia con kit y una libreta o agenda, sensación de orden y claridad, luz natural.", "app/templates/home.html"),
]

SIZES = {"sm": (640, 426), "md": (1024, 683), "lg": (1536, 1024)}


def _dynamic_slots() -> list[SlotSpec]:
    slots: list[SlotSpec] = [
        SlotSpec("stages", "hero", "Portada de etapas de cultivo de hongos gourmet", "Fotografía realista de una secuencia de cultivo indoor de hongos gourmet, ambiente limpio, luz natural y estética editorial premium.", "app/templates/stage_list.html"),
        SlotSpec("kits", "hero", "Portada de kits de cultivo indoor", "Fotografía realista de kits de cultivo de hongos gourmet alineados sobre mesa de trabajo, iluminación cálida, estilo e-commerce premium.", "app/templates/kit_list.html"),
        SlotSpec("products", "hero", "Portada de productos para cultivo indoor", "Fotografía realista de productos e insumos de cultivo indoor organizados en composición de catálogo sobre fondo neutro.", "app/templates/product_list.html"),
    ]

    for stage in list_stages():
        slot = entity_slot("stage", stage.id, stage.name)
        slots.append(
            SlotSpec(
                "stages",
                slot,
                f"Imagen de la etapa {stage.name}",
                f"Fotografía realista de la etapa '{stage.name}' del cultivo de hongos gourmet, contexto doméstico controlado, luz natural y enfoque detallado.",
                "app/templates/stage_list.html",
            )
        )
        slots.append(
            SlotSpec(
                "stages",
                entity_slot("stage-detail", stage.id, stage.name),
                f"Detalle ampliado de la etapa {stage.name}",
                f"Fotografía realista en primer plano del proceso de la etapa '{stage.name}' para tutorial de cultivo de hongos gourmet, alta nitidez y composición didáctica.",
                "app/templates/stage_detail.html",
            )
        )

    for kit in list_kits():
        slot = entity_slot("kit", kit.id, kit.name)
        slots.append(
            SlotSpec(
                "kits",
                slot,
                f"Kit {kit.name} en entorno real",
                f"Fotografía realista del kit '{kit.name}' para cultivo indoor de hongos gourmet sobre superficie de cocina limpia, luz natural, estilo de catálogo.",
                "app/templates/kit_list.html",
            )
        )
        slots.append(
            SlotSpec(
                "kits",
                entity_slot("kit-result", kit.id, kit.name),
                f"Resultado de cosecha del kit {kit.name}",
                f"Fotografía realista de resultado final de cosecha obtenido con el kit '{kit.name}', hongos gourmet frescos en plato de cocina, sin texto.",
                "app/templates/kit_list.html",
            )
        )

    for product in list_products():
        slots.append(
            SlotSpec(
                "products",
                entity_slot("product", product.id, product.name),
                f"Producto {product.name}",
                f"Fotografía realista del producto '{product.name}' para cultivo indoor de hongos gourmet, toma tipo e-commerce con fondo neutro y luz de estudio suave.",
                "app/templates/product_list.html",
            )
        )

    return slots


def _selected_slots(only: str) -> list[SlotSpec]:
    all_slots = HOME_SLOTS + _dynamic_slots()
    if only == "all":
        return all_slots
    return [slot for slot in all_slots if slot.section == only]


def _slot_dir(section: str, slot: str) -> Path:
    return OUTPUT_ROOT / section / slot


def _output_files(section: str, slot: str) -> dict[str, Path]:
    base = _slot_dir(section, slot)
    return {k: base / f"{k}.webp" for k in SIZES}


def _is_complete(section: str, slot: str) -> bool:
    return all(path.exists() and path.stat().st_size > 0 for path in _output_files(section, slot).values())


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


def _save_webp_variants(png_bytes: bytes, section: str, slot: str) -> dict[str, str]:
    out = _output_files(section, slot)
    out[next(iter(out))].parent.mkdir(parents=True, exist_ok=True)
    with Image.open(BytesIO(png_bytes)) as image:
        source = image.convert("RGB")
        public: dict[str, str] = {}
        for size_name, dims in SIZES.items():
            variant = source.resize(dims, Image.Resampling.LANCZOS)
            variant.save(out[size_name], format="WEBP", quality=82, method=6)
            public[size_name] = str(out[size_name].relative_to(ROOT))
            print(f"[images] Archivo creado correctamente: {out[size_name]}")
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


def sanity_check_outputs(manifest: list[dict]) -> tuple[int, list[str]]:
    stale_slots: list[str] = []
    for row in manifest:
        slot = row.get("slot", "")
        output_files = row.get("output_files", {})
        if not isinstance(output_files, dict) or not output_files:
            continue
        missing = False
        for relative in output_files.values():
            output_path = ROOT / str(relative)
            if not output_path.exists() or output_path.stat().st_size <= 0:
                missing = True
                break
        if missing:
            stale_slots.append(slot)
    print(f"[images] sanity_check_outputs: stale={len(stale_slots)}")
    return len(stale_slots), stale_slots


def generate_slots(slots: list[SlotSpec], mock: bool, force: bool) -> tuple[dict[str, int], list[str]]:
    manifest = _load_manifest()
    _, stale_slots = sanity_check_outputs(manifest)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    counters = {"generated": 0, "skipped-existing": 0, "regenerated-stale": 0, "failed": 0}
    failures: list[str] = []

    client = None
    if not mock:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    stale_set = set(stale_slots)

    for spec in slots:
        files = _output_files(spec.section, spec.slot)
        slot_key = spec.slot_key
        output_dir = files["md"].parent
        prompt_preview = spec.prompt.replace("\n", " ")[:120]

        try:
            is_complete = _is_complete(spec.section, spec.slot)
            if is_complete and not force:
                status = "skipped-existing"
                counters[status] += 1
                print(f"[images] slot={slot_key} prompt='{prompt_preview}' out={output_dir} result={status}")
                row = {
                    "slot": slot_key,
                    "prompt": spec.prompt,
                    "alt": spec.alt,
                    "model": "mock" if mock else MODEL,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "source_template": spec.source_template,
                    "output_files": {k: str(v.relative_to(ROOT)) for k, v in files.items()},
                    "status": status,
                }
                _upsert_manifest(manifest, row)
                continue

            stale = slot_key in stale_set and not force
            if stale:
                print(f"[images] slot={slot_key} detectado como stale_missing. Regenerando...")

            print(f"[images] Generando imagen para sección: {slot_key}")
            print(f"[images] Guardando en: {output_dir}")
            png = _generate_mock_png(slot_key, spec.prompt) if mock else _generate_real_png(client, spec.prompt)
            saved = _save_webp_variants(png, spec.section, spec.slot)

            status = "regenerated-stale" if stale else "generated"
            counters[status] += 1
            print(f"[images] slot={slot_key} prompt='{prompt_preview}' out={output_dir} result={status}")
            row = {
                "slot": slot_key,
                "prompt": spec.prompt,
                "alt": spec.alt,
                "model": "mock" if mock else MODEL,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_template": spec.source_template,
                "output_files": saved,
                "status": status,
            }
            _upsert_manifest(manifest, row)
        except Exception as exc:
            counters["failed"] += 1
            failures.append(f"{slot_key}: {exc}")
            print(f"[images] slot={slot_key} prompt='{prompt_preview}' out={output_dir} result=failed error={exc}")

    manifest.sort(key=lambda x: x.get("slot", ""))
    _write_manifest(manifest)
    return counters, failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generador IA de imágenes por slots para el sitio.")
    parser.add_argument("--only", choices=["all", "home", "stages", "kits", "products"], default="all")
    parser.add_argument("--mock", action="store_true", help="Genera placeholders locales sin API key")
    parser.add_argument("--real", action="store_true", help="Genera imágenes reales con OpenAI")
    parser.add_argument("--force", action="store_true", help="Regenera aunque existan archivos")
    return parser.parse_args()


def _resolve_mode(args: argparse.Namespace) -> bool:
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    if args.mock and args.real:
        raise SystemExit("Elegí solo un modo: --mock o --real")
    if args.mock:
        print("[images] mode=MOCK (forced by --mock)")
        return True
    if args.real:
        if not has_key:
            raise SystemExit("Falta OPENAI_API_KEY. No se puede usar --real sin API key")
        print("[images] mode=REAL (forced by --real)")
        return False
    if has_key:
        print("[images] mode=REAL (OPENAI_API_KEY present)")
        return False
    print("[images] mode=MOCK (reason=OPENAI_API_KEY missing)")
    return True


def _count_generated_files() -> int:
    return sum(1 for path in OUTPUT_ROOT.rglob("*.webp") if path.is_file() and path.stat().st_size > 0)


def main() -> None:
    args = parse_args()
    use_mock = _resolve_mode(args)

    slots = _selected_slots(args.only)
    counters, failures = generate_slots(slots=slots, mock=use_mock, force=args.force)

    total_files = _count_generated_files()
    print(
        "[images] resumen "
        f"generated={counters.get('generated', 0)} "
        f"skipped-existing={counters.get('skipped-existing', 0)} "
        f"regenerated-stale={counters.get('regenerated-stale', 0)} "
        f"failed={counters.get('failed', 0)} "
        f"files_on_disk={total_files}"
    )
    if failures:
        print("[images] fallas detectadas:")
        for item in failures:
            print(f" - {item}")

    if not use_mock and total_files == 0:
        raise SystemExit("Ejecución REAL sin archivos generados: verifique OPENAI_API_KEY, cuotas y errores previos")

    if counters.get("failed", 0) > 0:
        raise SystemExit("Generación completada con fallas")

    print("Generación completada")


if __name__ == "__main__":
    main()
