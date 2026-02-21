from __future__ import annotations

from app.models import AIStageTutorial, AIStep


def build_stage_from_prompt(prompt: str) -> AIStageTutorial:
    """Construye un tutorial base compatible con los modelos vigentes."""
    stage_title = (prompt or "Etapa demo").strip() or "Etapa demo"

    step = AIStep(
        title=f"Introducción a {stage_title}",
        objective=f"Entender los objetivos de la etapa {stage_title}",
        materials=["Guantes", "Alcohol 70%"],
        estimated_cost_usd=10,
        instructions=[
            "Prepará un área de trabajo limpia.",
            "Verificá temperatura y humedad básicas.",
            "Documentá cada ajuste realizado.",
        ],
        common_mistakes=[
            "No desinfectar herramientas antes de manipular sustrato.",
            "Cambios bruscos de humedad en menos de 24 horas.",
        ],
        checklist=[
            "Área sanitizada",
            "Materiales listos",
            "Registro inicial completado",
        ],
    )

    return AIStageTutorial(stage_title=stage_title, steps=[step])
