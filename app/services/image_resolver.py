from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = ROOT / "app" / "static" / "section-images"
PUBLIC_PREFIX = "/static/section-images"

HOME_IMAGES: dict[str, str] = {
    "hero": f"{PUBLIC_PREFIX}/home/home.hero.v1.svg",
    "beneficios-1": f"{PUBLIC_PREFIX}/home/home.beneficios-1.v1.svg",
    "beneficios-2": f"{PUBLIC_PREFIX}/home/home.beneficios-2.v1.svg",
    "beneficios-3": f"{PUBLIC_PREFIX}/home/home.beneficios-3.v1.svg",
    "como-funciona": f"{PUBLIC_PREFIX}/home/home.como-funciona.v1.svg",
    "testimonios": f"{PUBLIC_PREFIX}/home/home.testimonios.v1.svg",
    "faq": f"{PUBLIC_PREFIX}/home/home.faq.v1.svg",
}

STAGE_CARD_PLACEHOLDER = f"{PUBLIC_PREFIX}/stages/stages.card.placeholder.v1.svg"
STAGE_BANNER_PLACEHOLDER = f"{PUBLIC_PREFIX}/stages/stages.banner.placeholder.v1.svg"
PRODUCT_CARD_PLACEHOLDER = f"{PUBLIC_PREFIX}/products/products.card.placeholder.v1.svg"
KIT_CARD_PLACEHOLDER = f"{PUBLIC_PREFIX}/kits/kits.card.placeholder.v1.svg"


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
        path = STATIC_ROOT / folder / filename
        if path.exists():
            return f"{PUBLIC_PREFIX}/{folder}/{filename}"

    return fallback


def home_image(key: str) -> str:
    return HOME_IMAGES.get(key, HOME_IMAGES["hero"])


def stage_card_image(slug: str | None) -> str:
    return _resolve_by_prefix("stages", "stages.card", slug, STAGE_CARD_PLACEHOLDER)


def stage_banner_image(slug: str | None) -> str:
    return _resolve_by_prefix("stages", "stages.banner", slug, STAGE_BANNER_PLACEHOLDER)


def product_card_image(slug: str | None) -> str:
    return _resolve_by_prefix("products", "products.card", slug, PRODUCT_CARD_PLACEHOLDER)


def kit_card_image(slug: str | None) -> str:
    return _resolve_by_prefix("kits", "kits.card", slug, KIT_CARD_PLACEHOLDER)
