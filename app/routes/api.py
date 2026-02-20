from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.repositories import get_stage, list_stages, list_steps_by_stage, replace_steps
from app.services.ai_content import generate_stage_tutorial

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/stages")
def api_stages():
    return list_stages()


@router.get("/stages/{stage_id}")
def api_stage_detail(stage_id: int):
    stage = get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")
    steps = list_steps_by_stage(stage_id)
    return {"stage": stage, "steps": steps}


@router.post("/generate/stage/{stage_id}")
def api_generate(stage_id: int):
    stage = get_stage(stage_id)
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    tutorial = generate_stage_tutorial(stage.name)
    steps = []
    for step in tutorial.steps:
        content_lines = [f"Objetivo: {step.objective}", "", "Instrucciones:"]
        content_lines.extend([f"- {line}" for line in step.instructions])
        content_lines.append("")
        content_lines.append("Errores comunes:")
        content_lines.extend([f"- {line}" for line in step.common_mistakes])
        content_lines.append("")
        content_lines.append("Checklist:")
        content_lines.extend([f"- {line}" for line in step.checklist])

        steps.append(
            {
                "title": step.title,
                "content": "\n".join(content_lines),
                "tools": step.materials,
                "estimated_cost_usd": step.estimated_cost_usd,
            }
        )

    replace_steps(stage_id, steps)
    return {"ok": True, "stage_id": stage_id, "generated_steps": len(steps)}
