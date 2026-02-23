from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = ROOT / "app" / "static"
PLACEHOLDER_STATIC_PATH = "img/placeholder.svg"

SECTION_DEFAULT_PLACEHOLDERS = {
    "home": "img/placeholder.svg",
    "stages": "section-images/stages/stages.card.placeholder.v1.svg",
    "kits": "section-images/kits/kits.card.placeholder.v1.svg",
    "products": "section-images/products/products.card.placeholder.v1.svg",
}

SLOT_PLACEHOLDERS = {
    "stages.hero": "section-images/stages/stage.hero.v1.svg",
    "stages.step-default": "section-images/steps/step.placeholder.v1.svg",
    "kits.card": "section-images/kits/kit.card.v1.svg",
    "kits.result": "section-images/kits/kit.result.v1.svg",
    "stages.card-1": "section-images/stages/stage.card.1.v1.svg",
    "stages.card-2": "section-images/stages/stage.card.2.v1.svg",
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
    return f"{prefix}-{slug}-{safe_id}" if slug else f"{prefix}-{safe_id}"


def _existing_static_path(path: str) -> bool:
    candidate = STATIC_ROOT / path
    return candidate.exists() and candidate.stat().st_size > 0


def _generated_candidates(section: str, slot: str, sizes: tuple[str, ...]) -> list[str]:
    rows: list[str] = []
    for size in sizes:
        rows.extend(
            [
                f"img/generated/{section}/{slot}/{size}.webp",
                f"img/generated/{section}/{slot}/{size}.png",
                f"img/generated/{section}/{slot}/{size}.jpg",
                f"img/generated/{section}/{slot}/{size}.jpeg",
            ]
        )
    return rows


def _normalize_user_path(raw_path: str | None) -> str | None:
    if not raw_path:
        return None
    cleaned = raw_path.strip()
    if not cleaned:
        return None
    if cleaned.startswith("/static/"):
        return cleaned.removeprefix("/static/")
    if cleaned.startswith("static/"):
        return cleaned.removeprefix("static/")
    return cleaned


def _section_fallback(section: str) -> str:
    return SECTION_DEFAULT_PLACEHOLDERS.get(section, PLACEHOLDER_STATIC_PATH)


def resolve_static_path(section: str, slot: str, size: str = "md", fallback: str | None = None, raw_path: str | None = None) -> str:
    size_chain = (size, "md", "lg", "sm")
    ordered_sizes = tuple(dict.fromkeys(size_chain))
    candidates = _generated_candidates(section, slot, ordered_sizes)

    user_path = _normalize_user_path(raw_path)
    if user_path:
        candidates.append(user_path)

    for candidate in candidates:
        if _existing_static_path(candidate):
            return candidate

    slot_fallback = fallback or _section_fallback(section)
    if _existing_static_path(slot_fallback):
        return slot_fallback

    if _existing_static_path(PLACEHOLDER_STATIC_PATH):
        return PLACEHOLDER_STATIC_PATH
    return slot_fallback


def resolve(section: str, slot: str, size: str = "md") -> str:
    return f"/static/{resolve_static_path(section, slot, size=size)}"


def home_image(slot: str, size: str = "md") -> str:
    return resolve("home", slot, size)


def stage_list_images(stage) -> dict[str, str]:
    slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None))
    img1 = resolve_static_path(
        "stages",
        f"{slot}-card-1",
        size="md",
        fallback=SLOT_PLACEHOLDERS["stages.card-1"],
        raw_path=getattr(stage, "image_card_1", None),
    )
    img2 = resolve_static_path(
        "stages",
        f"{slot}-card-2",
        size="md",
        fallback=SLOT_PLACEHOLDERS["stages.card-2"],
        raw_path=getattr(stage, "image_card_2", None),
    )
    return {"img1_path": img1, "img2_path": img2}


def stage_hero_image(stage) -> str:
    slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None))
    return resolve_static_path(
        "stages",
        slot,
        size="md",
        fallback=SLOT_PLACEHOLDERS["stages.hero"],
        raw_path=getattr(stage, "image_hero", None),
    )


def step_image_cards(step, stage=None) -> dict[str, str]:
    step_slot = entity_slot("step", getattr(step, "id", None), getattr(step, "title", None))
    stage_slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None)) if stage else ""

    card_1 = resolve_static_path(
        "stages",
        f"{step_slot}-card-1",
        size="md",
        fallback=SLOT_PLACEHOLDERS["stages.step-default"],
        raw_path=getattr(step, "image", None),
    )
    card_2 = resolve_static_path(
        "stages",
        f"{step_slot}-card-2",
        size="md",
        fallback=card_1,
        raw_path=getattr(step, "image", None),
    )

    # fallback extra a imagen general de etapa si ambos faltan
    if card_1 == SLOT_PLACEHOLDERS["stages.step-default"] and stage_slot:
        card_1 = resolve_static_path("stages", stage_slot, size="md", fallback=SLOT_PLACEHOLDERS["stages.step-default"])
    if card_2 == card_1 and stage_slot:
        card_2 = resolve_static_path("stages", stage_slot, size="md", fallback=card_1)

    return {"card_1": card_1, "card_2": card_2}


def step_image(step, stage=None) -> str:
    return step_image_cards(step, stage=stage)["card_1"]


def kit_card_image(kit) -> str:
    slot = entity_slot("kit", getattr(kit, "id", None), getattr(kit, "name", None))
    return resolve_static_path(
        "kits",
        slot,
        size="md",
        fallback=SLOT_PLACEHOLDERS["kits.card"],
        raw_path=getattr(kit, "image_card", None),
    )


def kit_result_image(kit) -> str:
    slot = entity_slot("kit-result", getattr(kit, "id", None), getattr(kit, "name", None))
    return resolve_static_path(
        "kits",
        slot,
        size="md",
        fallback=SLOT_PLACEHOLDERS["kits.result"],
        raw_path=getattr(kit, "image_result", None),
    )


def resolution_debug(section: str, slot: str, raw_path: str | None = None) -> dict[str, object]:
    candidates = _generated_candidates(section, slot, ("md", "lg", "sm"))
    user = _normalize_user_path(raw_path)
    if user:
        candidates.append(user)
    chosen = resolve_static_path(section, slot, raw_path=raw_path)
    return {
        "section": section,
        "slot": slot,
        "raw_path": raw_path,
        "raw_candidate": user,
        "generated_candidates": candidates,
        "chosen": chosen,
        "exists": _existing_static_path(chosen),
    }
