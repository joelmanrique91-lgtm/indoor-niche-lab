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


def _generated_candidates(section: str, slot: str, sizes: tuple[str, ...] = ("md", "lg", "sm")) -> list[str]:
    candidates: list[str] = []
    for size in sizes:
        candidates.extend(
            [
                f"img/generated/{section}/{slot}/{size}.webp",
                f"img/generated/{section}/{slot}/{size}.png",
                f"img/generated/{section}/{slot}/{size}.jpg",
                f"img/generated/{section}/{slot}/{size}.jpeg",
            ]
        )
    return candidates


def resolve_static_path(section: str, slot: str, size: str = "md") -> str:
    fallback = PLACEHOLDERS["default"]
    return _first_existing_static_path(_generated_candidates(section, slot, sizes=(size, "md", "lg", "sm")), fallback)


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


def _prefer_generated_then_user(
    *,
    generated_candidates: list[str],
    raw_path: str | None,
    fallback: str,
) -> str:
    candidates: list[str] = []
    candidates.extend(generated_candidates)
    cleaned = _clean_user_path(raw_path)
    if cleaned:
        candidates.append(cleaned)
    return _first_existing_static_path(candidates, fallback)


def stage_list_images(stage) -> dict[str, str]:
    slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None))
    img1 = _prefer_generated_then_user(
        generated_candidates=_generated_candidates("stages", f"{slot}-card-1") + _generated_candidates("stages", slot),
        raw_path=getattr(stage, "image_card_1", None),
        fallback=PLACEHOLDERS["stages_card_1"],
    )
    img2 = _prefer_generated_then_user(
        generated_candidates=_generated_candidates("stages", f"{slot}-card-2") + _generated_candidates("stages", slot),
        raw_path=getattr(stage, "image_card_2", None),
        fallback=PLACEHOLDERS["stages_card_2"],
    )
    return {"img1_path": img1, "img2_path": img2}


def stage_hero_image(stage) -> str:
    slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None))
    resolved = _prefer_generated_then_user(
        generated_candidates=_generated_candidates("stages", slot),
        raw_path=getattr(stage, "image_hero", None),
        fallback=PLACEHOLDERS["stages_hero"],
    )
    return resolved


def step_image(step, stage=None) -> str:
    step_slot = entity_slot("step", getattr(step, "id", None), getattr(step, "title", None))
    stage_slot = entity_slot("stage", getattr(stage, "id", None), getattr(stage, "name", None)) if stage else ""
    generated = _generated_candidates("stages", step_slot)
    if stage_slot:
        generated.extend(_generated_candidates("stages", stage_slot))

    resolved = _prefer_generated_then_user(
        generated_candidates=generated,
        raw_path=getattr(step, "image", None),
        fallback=PLACEHOLDERS["step_default"],
    )
    return resolved


def kit_card_image(kit) -> str:
    slot = entity_slot("kit", getattr(kit, "id", None), getattr(kit, "name", None))
    resolved = _prefer_generated_then_user(
        generated_candidates=_generated_candidates("kits", slot),
        raw_path=getattr(kit, "image_card", None),
        fallback=PLACEHOLDERS["kits_card"],
    )
    return resolved


def kit_result_image(kit) -> str:
    slot = entity_slot("kit-result", getattr(kit, "id", None), getattr(kit, "name", None))
    resolved = _prefer_generated_then_user(
        generated_candidates=_generated_candidates("kits", slot),
        raw_path=getattr(kit, "image_result", None),
        fallback=PLACEHOLDERS["kits_result"],
    )
    return resolved


def resolution_debug(section: str, slot: str, raw_path: str | None = None) -> dict[str, object]:
    generated_candidates = _generated_candidates(section, slot)
    raw_candidate = _clean_user_path(raw_path)
    chosen = _prefer_generated_then_user(
        generated_candidates=generated_candidates,
        raw_path=raw_path,
        fallback=PLACEHOLDERS["default"],
    )
    checks = []
    for candidate in generated_candidates + ([raw_candidate] if raw_candidate else []):
        if not candidate:
            continue
        file_path = STATIC_ROOT / candidate
        checks.append(
            {
                "path": candidate,
                "exists": file_path.exists() and file_path.stat().st_size > 0 if file_path.exists() else False,
                "url": f"/static/{candidate}",
            }
        )
    return {
        "section": section,
        "slot": slot,
        "raw_path": raw_candidate,
        "selected_path": chosen,
        "selected_url": f"/static/{chosen}",
        "checks": checks,
    }
