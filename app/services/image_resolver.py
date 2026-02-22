from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = ROOT / "app" / "static"
STATIC_GENERATED_ROOT = STATIC_ROOT / "img" / "generated"

PLACEHOLDERS = {
    "default": "img/placeholder.svg",
    "stages_card_1": "section-images/stages/stage.card.1.v1.svg",
    "stages_card_2": "section-images/stages/stage.card.2.v1.svg",
    "stages_hero": "section-images/stages/stage.hero.v1.svg",
    "step_default": "section-images/steps/step.placeholder.v1.svg",
    "kits_card": "section-images/kits/kit.card.v1.svg",
    "kits_result": "section-images/kits/kit.result.v1.svg",
}


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


def _first_existing_static_path(candidates: list[str], fallback: str) -> str:
    for candidate in candidates:
        static_candidate = STATIC_ROOT / candidate
        if static_candidate.exists() and static_candidate.stat().st_size > 0:
            return candidate
    return fallback


def _generated_candidates(section: str, slot: str, sizes: tuple[str, ...] = ("md", "lg")) -> list[str]:
    candidates: list[str] = []
    for size in sizes:
        candidates.append(f"img/generated/{section}/{slot}/{size}.webp")
        candidates.append(f"img/generated/{section}/{slot}/{size}.png")
        candidates.append(f"img/generated/{section}/{slot}/{size}.jpg")
        candidates.append(f"img/generated/{section}/{slot}/{size}.jpeg")
    return candidates


def resolve_static_path(section: str, slot: str, size: str = "md") -> str:
    fallback = PLACEHOLDERS["default"]
    candidates = [
        f"img/generated/{section}/{slot}/{size}.webp",
        f"img/generated/{section}/{slot}/{size}.png",
        f"img/generated/{section}/{slot}/{size}.jpg",
        f"img/generated/{section}/{slot}/{size}.jpeg",
    ]
    return _first_existing_static_path(candidates, fallback)


def resolve(section: str, slot: str, size: str = "md") -> str:
    return f"/static/{resolve_static_path(section, slot, size)}"


def home_image(slot: str, size: str = "md") -> str:
    return resolve("home", slot, size)


def _clean_user_path(raw_path: str | None) -> str | None:
    if not raw_path:
        return None
    cleaned = raw_path.strip()
    if not cleaned:
        return None
    if cleaned.startswith("/static/"):
        cleaned = cleaned[len("/static/") :]
    elif cleaned.startswith("static/"):
        cleaned = cleaned[len("static/") :]
    return cleaned


def _prefer_user_or_generated(raw_path: str | None, generated_candidates: list[str], fallback: str) -> str:
    candidates: list[str] = []
    cleaned = _clean_user_path(raw_path)
    if cleaned:
        candidates.append(cleaned)
    candidates.extend(generated_candidates)
    return _first_existing_static_path(candidates, fallback)


def stage_list_images(stage) -> dict[str, str]:
    slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None))
    img1 = _prefer_user_or_generated(
        getattr(stage, "image_card_1", None),
        _generated_candidates("stages", f"{slot}-card-1"),
        PLACEHOLDERS["stages_card_1"],
    )
    img2 = _prefer_user_or_generated(
        getattr(stage, "image_card_2", None),
        _generated_candidates("stages", f"{slot}-card-2"),
        PLACEHOLDERS["stages_card_2"],
    )
    return {"img1_url": f"/static/{img1}", "img2_url": f"/static/{img2}"}


def stage_hero_image(stage) -> str:
    slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None))
    resolved = _prefer_user_or_generated(
        getattr(stage, "image_hero", None),
        _generated_candidates("stages", slot, sizes=("lg", "md")),
        PLACEHOLDERS["stages_hero"],
    )
    return f"/static/{resolved}"


def step_image(step) -> str:
    step_slot = entity_slot("step", getattr(step, "id", None), getattr(step, "title", None))
    resolved = _prefer_user_or_generated(
        getattr(step, "image", None),
        _generated_candidates("stages", step_slot),
        PLACEHOLDERS["step_default"],
    )
    return f"/static/{resolved}"


def kit_card_image(kit) -> str:
    slot = entity_slot("kit", getattr(kit, "id", None), getattr(kit, "name", None))
    resolved = _prefer_user_or_generated(
        getattr(kit, "image_card", None),
        _generated_candidates("kits", slot),
        PLACEHOLDERS["kits_card"],
    )
    return f"/static/{resolved}"


def kit_result_image(kit) -> str:
    slot = entity_slot("kit-result", getattr(kit, "id", None), getattr(kit, "name", None))
    resolved = _prefer_user_or_generated(
        getattr(kit, "image_result", None),
        _generated_candidates("kits", slot),
        PLACEHOLDERS["kits_result"],
    )
    return f"/static/{resolved}"
