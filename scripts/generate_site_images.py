#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageDraw

BASE_STYLE_PROMPT = (
    "Fotografía realista de producto o escena relacionada con el contenido de la sección, "
    "iluminación natural, enfoque nítido, fondo neutro, estilo de catálogo profesional, "
    "alta resolución, coherencia visual entre todas las imágenes del sitio."
)
DEFAULT_OUTPUT_DIR = Path("app/static/img/generated")
DEFAULT_MANIFEST_PATH = Path("data/generated_images_manifest.json")
DEFAULT_MAP_PATH = Path("data/generated_images_map.json")
URL_PREFIX = "/static/img/generated"

SOURCE_IMAGE_PATTERN = re.compile(
    r"(?:https://images\.unsplash\.com/[^'\"\s)]+|/static/img/generated/[^'\"\s)]+)"
)
IMG_BLOCK_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE | re.DOTALL)
SECTION_PATTERN = re.compile(r"<(section|article|main|div)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>")
JINJA_PATTERN = re.compile(r"\{[{%].*?[}%]\}", re.DOTALL)


@dataclass
class ImageTask:
    template_path: Path
    original_url: str
    context_text: str
    alt_text: str
    section_slug: str
    image_index: int


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def clean_text(raw: str) -> str:
    no_jinja = JINJA_PATTERN.sub(" ", raw)
    no_tags = TAG_PATTERN.sub(" ", no_jinja)
    compact = re.sub(r"\s+", " ", no_tags)
    return compact.strip()


def section_for_offset(source: str, offset: int) -> str:
    for match in SECTION_PATTERN.finditer(source):
        if match.start() <= offset <= match.end():
            return match.group(0)
    start = max(0, offset - 1000)
    end = min(len(source), offset + 400)
    return source[start:end]


def alt_for_offset(source: str, offset: int) -> str:
    start = max(0, offset - 250)
    end = min(len(source), offset + 350)
    snippet = source[start:end]
    img_match = IMG_BLOCK_PATTERN.search(snippet)
    if not img_match:
        return ""
    alt_match = re.search(r'alt=[\"\']([^\"\']+)[\"\']', img_match.group(0), re.IGNORECASE)
    return alt_match.group(1).strip() if alt_match else ""


def build_prompt(context_text: str, alt_text: str) -> str:
    normalized_context = textwrap.shorten(context_text, width=320, placeholder="...")
    guidance = f"Contexto de la sección: {normalized_context}."
    alt_hint = f" Descripción esperada: {alt_text}." if alt_text else ""
    return f"{BASE_STYLE_PROMPT} {guidance}{alt_hint}"


def extract_tasks(template_path: Path) -> list[ImageTask]:
    raw = template_path.read_text(encoding="utf-8")
    tasks: list[ImageTask] = []
    for idx, match in enumerate(SOURCE_IMAGE_PATTERN.finditer(raw), start=1):
        section_html = section_for_offset(raw, match.start())
        context_text = clean_text(section_html)
        alt_text = alt_for_offset(raw, match.start())
        slug_seed = alt_text or context_text[:80] or template_path.stem
        tasks.append(
            ImageTask(
                template_path=template_path,
                original_url=match.group(0),
                context_text=context_text,
                alt_text=alt_text,
                section_slug=slugify(slug_seed),
                image_index=idx,
            )
        )
    return tasks


def generate_with_openai(client: OpenAI, prompt: str, size: str, quality: str) -> bytes:
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        quality=quality,
    )
    image_b64 = result.data[0].b64_json
    if not image_b64:
        raise RuntimeError("La API no devolvió imagen en base64.")
    return base64.b64decode(image_b64)


def generate_mock_image(prompt: str, size: tuple[int, int]) -> bytes:
    img = Image.new("RGB", size, color=(244, 244, 240))
    draw = ImageDraw.Draw(img)
    preview = textwrap.fill(prompt[:160], width=34)
    draw.text((40, 40), preview, fill=(64, 64, 64))
    from io import BytesIO

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def clear_generated_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for file_path in output_dir.glob("*"):
        if file_path.name == ".gitkeep":
            continue
        if file_path.is_file():
            file_path.unlink()


def save_responsive_webp(png_bytes: bytes, output_base: Path) -> str:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    from io import BytesIO

    with Image.open(BytesIO(png_bytes)) as image:
        image = image.convert("RGB")
        sizes = {"sm": 640, "md": 1024, "lg": 1536}
        for suffix, width in sizes.items():
            resized = image.copy()
            resized.thumbnail((width, width), Image.Resampling.LANCZOS)
            resized.save(output_base.with_name(f"{output_base.name}-{suffix}.webp"), format="WEBP", quality=82, method=6)
    return f"{URL_PREFIX}/{output_base.name}-lg.webp"


def replace_urls_in_template(template_path: Path, replacements: list[str]) -> None:
    raw = template_path.read_text(encoding="utf-8")
    index = 0

    def _replace(_: re.Match[str]) -> str:
        nonlocal index
        value = replacements[index]
        index += 1
        return value

    updated = SOURCE_IMAGE_PATTERN.sub(_replace, raw)
    template_path.write_text(updated, encoding="utf-8")


def process_templates(root: Path, use_mock: bool, size: str, quality: str) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    templates = sorted(root.glob("*.html"))
    if not templates:
        raise RuntimeError("No se encontraron templates HTML en app/templates.")

    dims = tuple(int(v) for v in size.split("x"))
    client = None if use_mock else OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    manifest: dict[str, dict[str, str]] = {}
    generated_map: dict[str, list[dict[str, str]]] = {}

    clear_generated_dir(DEFAULT_OUTPUT_DIR)

    for template in templates:
        tasks = extract_tasks(template)
        if not tasks:
            continue

        generated_urls: list[str] = []
        template_key = str(template)
        manifest[template_key] = {}
        generated_map[template_key] = []

        for task in tasks:
            prompt = build_prompt(task.context_text, task.alt_text)
            file_stem = f"{task.template_path.stem}-{task.image_index:02d}-{task.section_slug}"
            output_base = DEFAULT_OUTPUT_DIR / file_stem

            png_bytes = generate_mock_image(prompt, dims) if use_mock else generate_with_openai(client, prompt, size, quality)
            new_src = save_responsive_webp(png_bytes, output_base)
            generated_urls.append(new_src)
            manifest[template_key][task.original_url] = new_src
            generated_map[template_key].append(
                {
                    "target": new_src,
                    "alt": task.alt_text,
                    "prompt": prompt,
                }
            )

        replace_urls_in_template(template, generated_urls)

    return manifest, generated_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de generación y reemplazo automático de imágenes del sitio.")
    parser.add_argument("--templates-dir", default="app/templates", help="Directorio con templates HTML.")
    parser.add_argument("--size", default="1536x1024", help="Resolución fija de generación IA (ancho x alto).")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"], help="Calidad fija del modelo de imágenes.")
    parser.add_argument("--mock", action="store_true", help="No llama API externa; genera imágenes de prueba locales.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Ruta para guardar trazabilidad de reemplazos.")
    parser.add_argument("--map", default=str(DEFAULT_MAP_PATH), help="Ruta para guardar prompts y rutas finales.")
    args = parser.parse_args()

    if not args.mock and not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Falta OPENAI_API_KEY. Usa --mock para pruebas locales sin API.")

    manifest, generated_map = process_templates(Path(args.templates_dir), args.mock, args.size, args.quality)

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    map_path = Path(args.map)
    map_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text(json.dumps(generated_map, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Pipeline completado. Templates actualizados: {len(manifest)}")
    print(f"Output dir: {DEFAULT_OUTPUT_DIR}")
    print(f"Manifest: {manifest_path}")
    print(f"Map: {map_path}")


if __name__ == "__main__":
    main()
