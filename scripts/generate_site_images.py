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

from app.repositories import list_kits, list_products, list_stages, list_steps_by_stage
from app.services.image_resolver import entity_slot, slugify

OUTPUT_ROOT = ROOT / "app" / "static" / "img" / "generated"
MANIFEST_PATH = ROOT / "data" / "generated_images_manifest.json"
STYLE_ID = "indoor-niche-lab.v1"
DEFAULT_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1")

SIZE_DIMS = {
    "sm": (640, 426),
    "md": (1024, 683),
    "lg": (1536, 1024),
}
STYLE_HEADER = (
    "Indoor Niche Lab brand style v1, editorial photorealism, soft natural light, moderate depth of field, "
    "neutral warm color temperature, clean controlled background, realistic textures, commercial composition, "
    "no visible text, no logos, no watermark."
)
NEGATIVE_PROMPT = (
    "no visible text, no logos, no watermark, no brand marks, no distorted anatomy, no surreal objects, "
    "no CGI/cartoon look, no noisy artifacts"
)


@dataclass(frozen=True)
class SlotSpec:
    slot_id: str
    section: str
    entity: dict[str, object]
    prompt: str
    alt: str
    sizes: tuple[str, ...]


@dataclass(frozen=True)
class GenerationOptions:
    mock: bool
    force: bool
    optimize_existing: bool


def _output_file(section: str, slot: str, size: str) -> Path:
    return OUTPUT_ROOT / section / slot / f"{size}.webp"


def _build_prompt(scene: str, composition: str, constraints: str) -> str:
    return f"{STYLE_HEADER} Scene content: {scene} Composition cues: {composition} Constraints: {constraints}"


def _home_slots() -> list[SlotSpec]:
    scenes = [
        ("hero", "Persona cosechando hongos gourmet en cocina doméstica ordenada."),
        ("beneficios-1", "Kit de cultivo completo sobre mesa limpia con componentes ordenados."),
        ("beneficios-2", "Cosecha fresca de hongos gourmet en bandeja sobre mesada."),
        ("beneficios-3", "Soporte de cultivo con móvil y guía junto al kit."),
        ("como-funciona-1", "Entrega de kit listo para abrir en hogar."),
        ("como-funciona-2", "Seguimiento de checklist de cultivo en mesa limpia."),
        ("como-funciona-3", "Resultado final listo para cocinar con hongos cosechados."),
        ("testimonios-1", "Escena testimonial cocinando hongos con kit al fondo."),
        ("testimonios-2", "Escena testimonial preparando kit sobre mesada."),
        ("testimonios-3", "Escena testimonial sirviendo plato con hongos gourmet."),
        ("faq", "Mesa ordenada de soporte de cultivo con libreta y kit."),
    ]
    rows: list[SlotSpec] = []
    for slot, scene in scenes:
        rows.append(
            SlotSpec(
                slot_id=f"home.{slot}",
                section="home",
                entity={"type": "page", "id": None, "slug": "home"},
                prompt=_build_prompt(scene, "medium shot, balanced framing, soft shadows.", "no text overlays, no logos, no brand labels."),
                alt=scene,
                sizes=("sm", "md", "lg"),
            )
        )
    return rows


def _dynamic_slots() -> list[SlotSpec]:
    slots: list[SlotSpec] = [
        SlotSpec(
            slot_id="stages.hero",
            section="stages",
            entity={"type": "page", "id": None, "slug": "stages"},
            prompt=_build_prompt(
                "Resumen visual de etapas del cultivo indoor de hongos gourmet en estación doméstica controlada.",
                "wide editorial shot with depth layers.",
                "no text, no logos.",
            ),
            alt="Portada de etapas de cultivo indoor.",
            sizes=("sm", "md", "lg"),
        ),
        SlotSpec(
            slot_id="kits.hero",
            section="kits",
            entity={"type": "page", "id": None, "slug": "kits"},
            prompt=_build_prompt(
                "Kits de cultivo alineados sobre mesa limpia con componentes visibles.",
                "catalog wide shot with controlled background.",
                "no text, no logos.",
            ),
            alt="Portada de kits de cultivo indoor.",
            sizes=("sm", "md", "lg"),
        ),
        SlotSpec(
            slot_id="products.hero",
            section="products",
            entity={"type": "page", "id": None, "slug": "products"},
            prompt=_build_prompt(
                "Surtido de productos de cultivo indoor ordenados como catálogo.",
                "wide product layout on neutral surface.",
                "no text, no logos.",
            ),
            alt="Portada de productos para cultivo indoor.",
            sizes=("sm", "md", "lg"),
        ),
    ]

    for stage in list_stages():
        stage_slot = entity_slot("stage", stage.id, stage.name)
        stage_entity = {"type": "stage", "id": stage.id, "slug": slugify(stage.name)}
        slots.append(
            SlotSpec(
                slot_id=f"stages.{stage_slot}",
                section="stages",
                entity=stage_entity,
                prompt=_build_prompt(
                    f"Etapa completa '{stage.name}' del cultivo indoor, mostrando herramientas y entorno controlado.",
                    "medium editorial angle, natural highlights.",
                    "no text, no logos.",
                ),
                alt=f"Etapa {stage.name} en entorno real.",
                sizes=("md", "lg"),
            )
        )
        for card in ("card-1", "card-2"):
            slots.append(
                SlotSpec(
                    slot_id=f"stages.{stage_slot}-{card}",
                    section="stages",
                    entity=stage_entity,
                    prompt=_build_prompt(
                        f"Vista {card} de la etapa '{stage.name}', variación complementaria de la fase.",
                        "close-medium shot with negative space.",
                        "no text, no logos.",
                    ),
                    alt=f"Tarjeta {card} de la etapa {stage.name}.",
                    sizes=("md",),
                )
            )

        for step in list_steps_by_stage(stage.id):
            step_slot = entity_slot("step", step.id, step.title)
            context = (step.content or "").strip().replace("\n", " ")[:220]
            tools = ", ".join(step.tools_json or [])
            for card in ("card-1", "card-2"):
                slots.append(
                    SlotSpec(
                        slot_id=f"stages.{step_slot}-{card}",
                        section="stages",
                        entity={"type": "step", "id": step.id, "slug": slugify(step.title)},
                        prompt=_build_prompt(
                            f"Paso '{step.title}' de la etapa '{stage.name}'. Context: {context}. Tools: {tools}.",
                            "process-focused close shot suitable for tutorial card.",
                            "no text, no logos, no watermarks.",
                        ),
                        alt=f"Paso {step.title}, imagen {card}.",
                        sizes=("md",),
                    )
                )

    for kit in list_kits():
        slot = entity_slot("kit", kit.id, kit.name)
        entity = {"type": "kit", "id": kit.id, "slug": slugify(kit.name)}
        slots.append(
            SlotSpec(
                slot_id=f"kits.{slot}",
                section="kits",
                entity=entity,
                prompt=_build_prompt(
                    f"Kit '{kit.name}' con componentes ordenados sobre mesa limpia.",
                    "product editorial shot.",
                    "no text, no logos.",
                ),
                alt=f"Kit {kit.name} en entorno real.",
                sizes=("md", "lg"),
            )
        )
        result_slot = entity_slot("kit-result", kit.id, kit.name)
        slots.append(
            SlotSpec(
                slot_id=f"kits.{result_slot}",
                section="kits",
                entity=entity,
                prompt=_build_prompt(
                    f"Resultado de cosecha asociado al kit '{kit.name}', hongos frescos y presentación limpia.",
                    "medium close-up with natural light.",
                    "no text, no logos.",
                ),
                alt=f"Resultado final del kit {kit.name}.",
                sizes=("md",),
            )
        )

    for product in list_products():
        slot = entity_slot("product", product.id, product.name)
        slots.append(
            SlotSpec(
                slot_id=f"products.{slot}",
                section="products",
                entity={"type": "product", "id": product.id, "slug": slugify(product.name)},
                prompt=_build_prompt(
                    f"Producto '{product.name}' de categoría '{product.category}' aislado en fondo neutro con iluminación suave.",
                    "catalog product shot, high texture realism.",
                    "no text, no logos.",
                ),
                alt=f"Producto {product.name} sobre fondo neutro.",
                sizes=("md",),
            )
        )

    return slots


def _all_slots() -> list[SlotSpec]:
    rows = _home_slots() + _dynamic_slots()
    rows.sort(key=lambda x: x.slot_id)
    return rows


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"manifest_version": 2, "style_id": STYLE_ID, "generated_at": "", "slots": []}
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("slots"), list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        # migrate legacy lightweight structure
        migrated = {"manifest_version": 2, "style_id": STYLE_ID, "generated_at": "", "slots": []}
        grouped: dict[str, dict] = {}
        for item in payload["items"]:
            section = item.get("section")
            slot = item.get("slot")
            if not section or not slot:
                continue
            slot_id = f"{section}.{slot}"
            row = grouped.setdefault(
                slot_id,
                {
                    "slot_id": slot_id,
                    "section": section,
                    "entity": {"type": "unknown", "id": None, "slug": None},
                    "prompt": "",
                    "negative_prompt": NEGATIVE_PROMPT,
                    "alt": "",
                    "style_id": STYLE_ID,
                    "model": DEFAULT_MODEL,
                    "created_at": "",
                    "updated_at": "",
                    "output_files": {},
                    "status": "missing",
                    "error_message": None,
                },
            )
            if item.get("size") and item.get("url"):
                row["output_files"][item["size"]] = item["url"]
        migrated["slots"] = sorted(grouped.values(), key=lambda x: x["slot_id"])
        return migrated
    raise SystemExit("Manifest inválido")


def _save_manifest(payload: dict) -> None:
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    payload["style_id"] = STYLE_ID
    payload["manifest_version"] = 2
    payload["slots"] = sorted(payload.get("slots", []), key=lambda x: x.get("slot_id", ""))
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _index_manifest(payload: dict) -> dict[str, dict]:
    return {row.get("slot_id", ""): row for row in payload.get("slots", []) if row.get("slot_id")}


def _is_complete(section: str, slot_name: str, sizes: tuple[str, ...]) -> bool:
    return all(_output_file(section, slot_name, size).exists() and _output_file(section, slot_name, size).stat().st_size > 0 for size in sizes)


def _generate_mock_png(slot_id: str, prompt: str) -> bytes:
    image = Image.new("RGB", (1536, 1024), color=(228, 216, 194))
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 60, 1476, 964), outline=(120, 95, 65), width=5)
    draw.text((100, 120), f"MOCK {slot_id}", fill=(88, 64, 40))
    draw.text((100, 190), prompt[:220], fill=(88, 64, 40))
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _generate_real_png(client, prompt: str) -> bytes:
    result = client.images.generate(model=DEFAULT_MODEL, prompt=prompt, size="1536x1024", quality="high")
    b64 = result.data[0].b64_json
    if not b64:
        raise RuntimeError("OpenAI no devolvió b64_json")
    return base64.b64decode(b64)


def _save_variants(png_bytes: bytes, section: str, slot_name: str, sizes: tuple[str, ...]) -> dict[str, str]:
    with Image.open(BytesIO(png_bytes)) as source_image:
        rgb = source_image.convert("RGB")
        output: dict[str, str] = {}
        for size in sizes:
            width, height = SIZE_DIMS[size]
            target = _output_file(section, slot_name, size)
            target.parent.mkdir(parents=True, exist_ok=True)
            variant = rgb.resize((width, height), Image.Resampling.LANCZOS)
            variant.save(target, format="WEBP", quality=82, method=6)
            output[size] = f"/static/{target.relative_to(ROOT / 'app' / 'static').as_posix()}"
        return output


def _optimize_existing(section: str, slot_name: str, sizes: tuple[str, ...]) -> dict[str, str]:
    output: dict[str, str] = {}
    for size in sizes:
        target = _output_file(section, slot_name, size)
        if not target.exists() or target.stat().st_size <= 0:
            continue
        with Image.open(target) as source:
            source.convert("RGB").save(target, format="WEBP", quality=80, method=6)
        output[size] = f"/static/{target.relative_to(ROOT / 'app' / 'static').as_posix()}"
    return output


def _resolve_mode(args: argparse.Namespace) -> bool:
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    if args.mock and args.real:
        raise SystemExit("Elegí solo un modo: --mock o --real")
    if args.real and not has_key:
        raise SystemExit("Falta OPENAI_API_KEY. No se puede usar --real sin API key")
    if args.mock:
        return True
    if args.real:
        return False
    return not has_key


def _filter_slots(all_slots: list[SlotSpec], only: str, only_slot: str | None) -> list[SlotSpec]:
    selected = all_slots
    if only != "all":
        selected = [slot for slot in selected if slot.section == only]
    if only_slot:
        selected = [slot for slot in selected if slot.slot_id == only_slot]
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generador idempotente de imágenes por slot")
    parser.add_argument("--only", choices=["all", "home", "stages", "kits", "products"], default="all")
    parser.add_argument("--only-slot", help="Genera solo el slot_id exacto (ej: stages.step-incubacion-10-card-1)")
    parser.add_argument("--mock", action="store_true", help="Usa placeholders locales")
    parser.add_argument("--real", action="store_true", help="Usa OpenAI")
    parser.add_argument("--force", action="store_true", help="Regenera aunque existan archivos")
    parser.add_argument("--optimize-existing", action="store_true", help="Recomprime WEBP existentes sin regenerar prompt")
    return parser.parse_args()


def generate(slots: list[SlotSpec], options: GenerationOptions) -> tuple[dict[str, int], list[str]]:
    payload = _load_manifest()
    manifest_map = _index_manifest(payload)
    counters = {"generated": 0, "skipped": 0, "optimized": 0, "failed": 0}
    failures: list[str] = []

    client = None
    if not options.mock:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    now = datetime.now(timezone.utc).isoformat()

    for slot in slots:
        section, slot_name = slot.slot_id.split(".", 1)
        existing = manifest_map.get(slot.slot_id, {})
        created_at = existing.get("created_at") or now
        try:
            complete = _is_complete(section, slot_name, slot.sizes)
            if complete and not options.force:
                if options.optimize_existing:
                    output_files = _optimize_existing(section, slot_name, slot.sizes)
                    status = "ok"
                    counters["optimized"] += 1
                else:
                    output_files = {
                        size: f"/static/{_output_file(section, slot_name, size).relative_to(ROOT / 'app' / 'static').as_posix()}"
                        for size in slot.sizes
                    }
                    status = "ok"
                    counters["skipped"] += 1
            else:
                png = _generate_mock_png(slot.slot_id, slot.prompt) if options.mock else _generate_real_png(client, slot.prompt)
                output_files = _save_variants(png, section, slot_name, slot.sizes)
                status = "ok"
                counters["generated"] += 1

            manifest_map[slot.slot_id] = {
                "slot_id": slot.slot_id,
                "section": slot.section,
                "entity": slot.entity,
                "prompt": slot.prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "alt": slot.alt,
                "style_id": STYLE_ID,
                "model": "mock" if options.mock else DEFAULT_MODEL,
                "created_at": created_at,
                "updated_at": now,
                "output_files": output_files,
                "status": status,
                "error_message": None,
            }
            print(f"[images] {slot.slot_id} -> {status}")
        except Exception as exc:
            counters["failed"] += 1
            failures.append(f"{slot.slot_id}: {exc}")
            previous_output = existing.get("output_files", {}) if isinstance(existing, dict) else {}
            manifest_map[slot.slot_id] = {
                "slot_id": slot.slot_id,
                "section": slot.section,
                "entity": slot.entity,
                "prompt": slot.prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "alt": slot.alt,
                "style_id": STYLE_ID,
                "model": "mock" if options.mock else DEFAULT_MODEL,
                "created_at": created_at,
                "updated_at": now,
                "output_files": previous_output,
                "status": "error",
                "error_message": str(exc),
            }
            print(f"[images] {slot.slot_id} -> error: {exc}")

    payload["slots"] = list(manifest_map.values())
    _save_manifest(payload)
    return counters, failures


def main() -> None:
    args = parse_args()
    mock = _resolve_mode(args)
    all_slots = _all_slots()
    selected = _filter_slots(all_slots, args.only, args.only_slot)
    if args.only_slot and not selected:
        raise SystemExit(f"No existe slot_id: {args.only_slot}")

    counters, failures = generate(
        slots=selected,
        options=GenerationOptions(mock=mock, force=args.force, optimize_existing=args.optimize_existing),
    )

    print(
        "[images] summary "
        f"generated={counters['generated']} skipped={counters['skipped']} "
        f"optimized={counters['optimized']} failed={counters['failed']}"
    )
    if failures:
        for failure in failures:
            print(f" - {failure}")
        raise SystemExit("Generación completada con fallas")
    print("Generación completada")


if __name__ == "__main__":
    main()
