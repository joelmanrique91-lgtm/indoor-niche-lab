from __future__ import annotations

import re
import unicodedata
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC_GENERATED_ROOT = ROOT / "app" / "static" / "img" / "generated"
PLACEHOLDER_STATIC_PATH = "img/placeholder.svg"


def slugify(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def entity_slot(prefix: str, entity_id: int | None, label: str | None) -> str:
    slug = slugify(label)
    safe_id = entity_id if entity_id is not None else "x"
    if slug:
        return f"{prefix}-{slug}-{safe_id}"
    return f"{prefix}-{safe_id}"


def resolve_static_path(section: str, slot: str, size: str = "md") -> str:
    candidate = STATIC_GENERATED_ROOT / section / slot / f"{size}.webp"
    if candidate.exists() and candidate.stat().st_size > 0:
        return f"img/generated/{section}/{slot}/{size}.webp"
    if os.environ.get("IMAGE_RESOLVER_DEBUG_PLACEHOLDER") == "1":
        print(
            "[image_resolver] placeholder fallback "
            f"section={section} slot={slot} size={size} "
            f"expected_disk_path={candidate} exists={candidate.exists()}"
        )
    return PLACEHOLDER_STATIC_PATH


def resolve(section: str, slot: str, size: str = "md") -> str:
    return f"/static/{resolve_static_path(section, slot, size)}"


def home_image(slot: str, size: str = "md") -> str:
    return resolve("home", slot, size)
