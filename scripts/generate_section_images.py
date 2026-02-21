#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from openai import OpenAI

FALLBACK_PROMPTS = {
    "hero": "indoor gourmet mushrooms kit in a modern apartment, clean grow tent, soft light, premium brand aesthetic, wide composition, no text",
    "beneficios": "minimal still life of mushroom grow kit components on clean table, premium product photo, soft shadows, no text",
    "proceso": "sequence-like composition: inoculation, colonization, fruiting, harvest, four stages implied by objects, clean lab vibe, no text",
    "productos": "ecommerce-style product lineup of 3 kits, neutral background, premium lighting, no text",
    "seguridad": "sterile workspace with gloves, alcohol spray, laminar box vibe (home-safe), minimal, no text",
    "testimonios": "warm home kitchen scene with plated gourmet mushrooms, subtle community vibe, no text",
    "faq": "clean abstract help/support scene: icon-like objects, minimal, no text",
    "cta": "shipping box + kit ready to start, premium, hopeful mood, no text",
}

BASE_STYLE = (
    "Photorealistic premium brand image for gourmet indoor mushroom cultivation website. "
    "Clean home-lab environment, neutral palette with subtle olive-green accents, soft diffused lighting, "
    "no visible text/logos/watermarks, realistic anatomy and objects, commercial-grade composition with negative space."
)

SECTION_RE = re.compile(r"<section\b[^>]*>.*?</section>", re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*([\"'])(.*?)\2", re.DOTALL)
HEADING_RE = re.compile(r"<(h1|h2|h3)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
P_RE = re.compile(r"<(p|li)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class SectionInfo:
    slug: str
    selector: str
    title: str
    description: str
    section_type: str


def parse_attrs(tag_open: str) -> dict[str, str]:
    return {k.lower(): html.unescape(v.strip()) for k, _, v in ATTR_RE.findall(tag_open)}


def strip_tags(raw: str) -> str:
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return WHITESPACE_RE.sub(" ", text).strip()


def slugify(value: str) -> str:
    value = strip_tags(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "section"


def classify_section(title: str, description: str, slug: str) -> str:
    haystack = f"{title} {description} {slug}".lower()
    if any(w in haystack for w in ["hero", "portada"]) or slug == "hero":
        return "hero"
    if any(w in haystack for w in ["paso", "proceso", "funciona"]):
        return "proceso"
    if any(w in haystack for w in ["beneficio", "valor"]):
        return "beneficios"
    if any(w in haystack for w in ["producto", "kit"]):
        return "productos"
    if any(w in haystack for w in ["faq", "preguntas", "soporte"]):
        return "faq"
    if any(w in haystack for w in ["seguridad", "esteril", "steril"]):
        return "seguridad"
    if any(w in haystack for w in ["testimonio", "comunidad", "alumno"]):
        return "testimonios"
    if any(w in haystack for w in ["cta", "empeza", "empezá", "compr", "elegir"]):
        return "cta"
    return "beneficios"


def target_size_for(section_type: str) -> tuple[int, int]:
    if section_type == "hero":
        return (1600, 900)
    if section_type in {"faq", "seguridad"}:
        return (768, 768)
    return (1200, 800)


def openai_size_for(target: tuple[int, int]) -> str:
    if target[0] == target[1]:
        return "1024x1024"
    return "1536x1024"


def detect_sections(home_html: str) -> list[SectionInfo]:
    sections: list[SectionInfo] = []
    for idx, match in enumerate(SECTION_RE.finditer(home_html), start=1):
        block = match.group(0)
        open_tag = block.split(">", 1)[0]
        attrs = parse_attrs(open_tag)

        heading_match = HEADING_RE.search(block)
        title = strip_tags(heading_match.group(2)) if heading_match else f"Section {idx}"

        snippets = [strip_tags(snippet) for _, snippet in P_RE.findall(block)]
        snippets = [s for s in snippets if s]
        description = " ".join(snippets[:2])[:240]

        class_value = attrs.get("class", "")
        inferred_id = "hero" if "hero" in class_value.split() else ""
        section_id = attrs.get("id") or attrs.get("data-section") or inferred_id or slugify(title)
        selector = f"section#{section_id}" if attrs.get("id") or inferred_id else f"section:nth-of-type({idx})"
        section_type = classify_section(title, description, section_id)

        sections.append(
            SectionInfo(
                slug=slugify(section_id),
                selector=selector,
                title=title,
                description=description,
                section_type=section_type,
            )
        )
    return sections


def build_prompt(section: SectionInfo) -> str:
    fallback = FALLBACK_PROMPTS[section.section_type]
    return (
        f"{BASE_STYLE} Section title: {section.title}. "
        f"Section summary: {section.description or 'No description extracted.'}. "
        f"Creative direction: {fallback}"
    )


def generate_png(client: OpenAI, prompt: str, size: str) -> bytes:
    res = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
    b64 = res.data[0].b64_json
    if not b64:
        raise RuntimeError("OpenAI image response did not include base64 data.")
    return base64.b64decode(b64)




def resize_png(png_bytes: bytes, target: tuple[int, int]) -> bytes:
    from io import BytesIO

    from PIL import Image, ImageOps

    with Image.open(BytesIO(png_bytes)) as img:
        fitted = ImageOps.fit(img.convert("RGB"), target, method=Image.Resampling.LANCZOS)
        buffer = BytesIO()
        fitted.save(buffer, format="PNG")
        return buffer.getvalue()

def ensure_loading_attrs(img_tag: str) -> str:
    updated = img_tag
    if " loading=" not in updated:
        updated = updated.replace("<img", '<img loading="lazy"', 1)
    if " decoding=" not in updated:
        updated = updated.replace("<img", '<img decoding="async"', 1)
    return updated


def update_first_img(block: str, image_src: str) -> tuple[str, bool]:
    img_match = re.search(r"<img\b[^>]*>", block, re.IGNORECASE)
    if not img_match:
        return block, False
    tag = img_match.group(0)
    if "src=" in tag:
        tag = re.sub(r"src=(['\"]).*?\\1", f'src="{image_src}"', tag, count=1)
    else:
        tag = tag[:-1] + f' src="{image_src}">'
    tag = ensure_loading_attrs(tag)
    return block[: img_match.start()] + tag + block[img_match.end() :], True


def inject_safe_image(block: str, slug: str, image_src: str) -> str:
    marker_start = f"<!-- section-image:auto:{slug}:start -->"
    marker_end = f"<!-- section-image:auto:{slug}:end -->"
    safe_html = (
        f"{marker_start}<div class=\"section-visual-wrap\"><img class=\"section-visual\" "
        f"src=\"{image_src}\" alt=\"Ilustración de sección\" loading=\"lazy\" decoding=\"async\"></div>{marker_end}"
    )
    if marker_start in block and marker_end in block:
        return re.sub(
            re.escape(marker_start) + r".*?" + re.escape(marker_end),
            safe_html,
            block,
            flags=re.DOTALL,
        )
    return block.replace("</section>", safe_html + "</section>")


def integrate_template(template_path: Path, images_by_slug: dict[str, str]) -> list[str]:
    source = template_path.read_text(encoding="utf-8")
    changes: list[str] = []

    def _replace(match: re.Match[str]) -> str:
        block = match.group(0)
        open_tag = block.split(">", 1)[0]
        attrs = parse_attrs(open_tag)
        section_id = attrs.get("id") or attrs.get("data-section") or ""
        slug = slugify(section_id) if section_id else ""
        image_src = images_by_slug.get(slug)
        if not image_src:
            return block

        updated, did_update = update_first_img(block, image_src)
        if did_update:
            changes.append(f"updated <img> in {slug}")
            return updated

        changes.append(f"inserted safe <img> in {slug}")
        return inject_safe_image(block, slug, image_src)

    updated_source = SECTION_RE.sub(_replace, source)
    if updated_source != source:
        template_path.write_text(updated_source, encoding="utf-8")
    return changes


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate coherent section images and wire them into the homepage.")
    parser.add_argument("--url", required=True, help="Public URL to inspect homepage HTML.")
    parser.add_argument("--out", default="app/static/section-images", help="Output folder for generated PNG files.")
    parser.add_argument("--v", type=int, default=1, help="Version suffix for deterministic file names.")
    parser.add_argument("--home-template", default="app/templates/home.html", help="Local homepage template path to update.")
    parser.add_argument("--sections-json", default="outputs/section_images/sections.json")
    parser.add_argument("--manifest-json", default="outputs/section_images/manifest.json")
    parser.add_argument("--scan-only", action="store_true", help="Only inspect sections and write JSON outputs.")
    args = parser.parse_args()

    load_dotenv()

    homepage_html: str
    try:
        response = httpx.get(args.url, follow_redirects=True, timeout=30)
        response.raise_for_status()
        homepage_html = response.text
    except Exception as exc:
        template_fallback = Path(args.home_template)
        if not template_fallback.exists():
            raise SystemExit(f"Could not fetch URL ({exc}) and no local template fallback found.") from exc
        homepage_html = template_fallback.read_text(encoding="utf-8")
        print(f"Warning: could not fetch {args.url}. Using local template fallback: {template_fallback}")

    sections = detect_sections(homepage_html)

    section_payload = [
        {
            "slug": s.slug,
            "selector": s.selector,
            "title": s.title,
            "description": s.description,
            "section_type": s.section_type,
        }
        for s in sections
    ]
    write_json(Path(args.sections_json), section_payload)

    if not sections:
        raise SystemExit("No sections were detected on the provided homepage URL.")

    image_out = Path(args.out)
    image_out.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "source_url": args.url,
        "version": args.v,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": [],
        "integration_changes": [],
    }

    if args.scan_only:
        for section in sections:
            manifest["sections"].append(
                {
                    "section": section.slug,
                    "prompt": build_prompt(section),
                    "file": None,
                    "size": f"{target_size_for(section.section_type)[0]}x{target_size_for(section.section_type)[1]}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "scan-only",
                }
            )
        write_json(Path(args.manifest_json), manifest)
        print(f"Section audit complete ({len(sections)} sections).")
        return

    import os

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing. Add it to .env before generating images.")

    client = OpenAI(api_key=api_key)
    images_by_slug: dict[str, str] = {}

    for section in sections:
        prompt = build_prompt(section)
        target = target_size_for(section.section_type)
        size = openai_size_for(target)
        output_file = image_out / f"{section.slug}__v{args.v}.png"
        png = generate_png(client, prompt, size)
        output_file.write_bytes(resize_png(png, target))
        images_by_slug[section.slug] = f"/static/section-images/{output_file.name}"
        manifest["sections"].append(
            {
                "section": section.slug,
                "prompt": prompt,
                "file": str(output_file),
                "size": f"{target[0]}x{target[1]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "generated",
            }
        )

    integration_changes = integrate_template(Path(args.home_template), images_by_slug)
    manifest["integration_changes"] = integration_changes
    write_json(Path(args.manifest_json), manifest)

    print(f"Generated {len(images_by_slug)} section images in {image_out}.")
    print(f"Updated template: {args.home_template}")


if __name__ == "__main__":
    main()
