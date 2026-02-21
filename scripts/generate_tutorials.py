from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import init_db
from app.repositories import get_stage, replace_steps
from app.services.ai_content import generate_stage_tutorial


def main() -> None:
    parser = argparse.ArgumentParser(description="Generar pasos de tutorial con OpenAI por etapa")
    parser.add_argument("--stage-id", type=int, required=True, help="ID de la etapa")
    args = parser.parse_args()

    init_db()
    stage = get_stage(args.stage_id)
    if not stage:
        raise SystemExit(f"No existe la etapa con id {args.stage_id}")

    try:
        tutorial = generate_stage_tutorial(stage.name)
    except Exception as exc:
        print(f"❌ No se pudo generar contenido IA: {exc}")
        raise SystemExit(2)
    payload = []
    for step in tutorial.steps:
        text = (
            f"Objetivo: {step.objective}\n\n"
            + "Instrucciones:\n"
            + "\n".join([f"- {item}" for item in step.instructions])
            + "\n\nErrores comunes:\n"
            + "\n".join([f"- {item}" for item in step.common_mistakes])
            + "\n\nChecklist:\n"
            + "\n".join([f"- {item}" for item in step.checklist])
        )
        payload.append(
            {
                "title": step.title,
                "content": text,
                "tools": step.materials,
                "estimated_cost_usd": step.estimated_cost_usd,
            }
        )

    replace_steps(args.stage_id, payload)
    print(f"✅ Se generaron {len(payload)} pasos para la etapa {stage.name}")


if __name__ == "__main__":
    main()
