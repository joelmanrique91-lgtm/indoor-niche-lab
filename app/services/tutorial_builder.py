from __future__ import annotations

import re
from app.models import Stage


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", base).strip("-") or "stage-demo"


def build_stage_from_prompt(prompt: str) -> Stage:
    title = prompt.strip().capitalize() or "Stage demo"
    slug = _slugify(title)
    body_md = f"## {title}\n\nPaso a paso base para iniciar este stage."
    return Stage(
        slug=slug,
        title=title,
        summary=f"Resumen breve para {title}.",
        body_md=body_md,
        checklist_items=["Preparar espacio", "Configurar luz", "Registrar avances"],
    )
