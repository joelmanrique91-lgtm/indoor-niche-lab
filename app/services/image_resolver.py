from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC_SECTION_ROOT = ROOT / "app" / "static" / "section-images"
STATIC_GENERATED_ROOT = ROOT / "app" / "static" / "img" / "generated"
SECTION_PUBLIC_PREFIX = "/static/section-images"
GENERATED_PUBLIC_PREFIX = "/static/img/generated"

HOME_IMAGES_LEGACY: dict[str, str] = {
    "hero": f"{SECTION_PUBLIC_PREFIX}/home/home.hero.v1.svg",
    "beneficios-1": f"{SECTION_PUBLIC_PREFIX}/home/home.beneficios-1.v1.svg",
    "beneficios-2": f"{SECTION_PUBLIC_PREFIX}/home/home.beneficios-2.v1.svg",
    "beneficios-3": f"{SECTION_PUBLIC_PREFIX}/home/home.beneficios-3.v1.svg",
    "como-funciona": f"{SECTION_PUBLIC_PREFIX}/home/home.como-funciona.v1.svg",
    "como-funciona-1": f"{SECTION_PUBLIC_PREFIX}/home/home.como-funciona.v1.svg",
    "como-funciona-2": f"{SECTION_PUBLIC_PREFIX}/home/home.como-funciona.v1.svg",
    "como-funciona-3": f"{SECTION_PUBLIC_PREFIX}/home/home.como-funciona.v1.svg",
    "testimonios": f"{SECTION_PUBLIC_PREFIX}/home/home.testimonios.v1.svg",
    "testimonios-1": f"{SECTION_PUBLIC_PREFIX}/home/home.testimonios.v1.svg",
    "testimonios-2": f"{SECTION_PUBLIC_PREFIX}/home/home.testimonios.v1.svg",
    "testimonios-3": f"{SECTION_PUBLIC_PREFIX}/home/home.testimonios.v1.svg",
    "faq": f"{SECTION_PUBLIC_PREFIX}/home/home.faq.v1.svg",
}

STAGE_CARD_PLACEHOLDER = f"{SECTION_PUBLIC_PREFIX}/stages/stages.card.placeholder.v1.svg"
STAGE_BANNER_PLACEHOLDER = f"{SECTION_PUBLIC_PREFIX}/stages/stages.banner.placeholder.v1.svg"
PRODUCT_CARD_PLACEHOLDER = f"{SECTION_PUBLIC_PREFIX}/products/products.card.placeholder.v1.svg"
KIT_CARD_PLACEHOLDER = f"{SECTION_PUBLIC_PREFIX}/kits/kits.card.placeholder.v1.svg"


def slugify(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def _resolve_by_prefix(folder: str, prefix: str, slug: str | None, fallback: str) -> str:
    normalized_slug = slugify(slug)
    if not normalized_slug:
        return fallback

    exts = ("webp", "png", "svg")
    for ext in exts:
        filename = f"{prefix}.{normalized_slug}.v1.{ext}"
        path = STATIC_SECTION_ROOT / folder / filename
        if path.exists():
            return f"{SECTION_PUBLIC_PREFIX}/{folder}/{filename}"

    return fallback


def _home_generated(slot: str, preferred: str = "md") -> str | None:
    size_order = [preferred] + [size for size in ("sm", "lg", "md") if size != preferred]
    slot_root = STATIC_GENERATED_ROOT / "home" / f"home.{slot}"
    for size in size_order:
        candidate = slot_root / f"{size}.webp"
        if candidate.exists():
            return f"{GENERATED_PUBLIC_PREFIX}/home/home.{slot}/{size}.webp"
    return None


def home_image(key: str) -> str:
    generated = _home_generated(key)
    if generated:
        return generated
    return HOME_IMAGES_LEGACY.get(key, HOME_IMAGES_LEGACY["hero"])


def stage_card_image(slug: str | None) -> str:
    return _resolve_by_prefix("stages", "stages.card", slug, STAGE_CARD_PLACEHOLDER)


def stage_banner_image(slug: str | None) -> str:
    return _resolve_by_prefix("stages", "stages.banner", slug, STAGE_BANNER_PLACEHOLDER)


def product_card_image(slug: str | None) -> str:
    return _resolve_by_prefix("products", "products.card", slug, PRODUCT_CARD_PLACEHOLDER)


def kit_card_image(slug: str | None) -> str:
    return _resolve_by_prefix("kits", "kits.card", slug, KIT_CARD_PLACEHOLDER)
