from __future__ import annotations

import json

from openai import OpenAI

from app.config import settings
from app.models import AIStageTutorial

BASE_PROMPT = """
Sos un experto en cultivo indoor de hongos gourmet (Ostra y Melena de León).
Generá contenido educativo para la etapa: "{stage_name}".
Devolvé SOLO JSON válido sin markdown y sin comentarios, con esta forma exacta:
{
  "stage_title": "string",
  "steps": [
    {
      "title": "string",
      "objective": "string",
      "materials": ["string"],
      "estimated_cost_usd": 0,
      "instructions": ["string"],
      "common_mistakes": ["string"],
      "checklist": ["string"]
    }
  ]
}
""".strip()


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise ValueError("Falta OPENAI_API_KEY. Configurala en el archivo .env")
    return OpenAI(api_key=settings.openai_api_key)


def _parse_or_raise(text: str) -> AIStageTutorial:
    payload = json.loads(text)
    return AIStageTutorial.model_validate(payload)


def generate_stage_tutorial(stage_name: str) -> AIStageTutorial:
    """Genera tutorial por etapa; reintenta una vez con prompt de reparación."""
    client = _client()
    prompt = BASE_PROMPT.format(stage_name=stage_name)

    response = client.responses.create(model=settings.openai_model, input=prompt)
    raw_text = response.output_text

    try:
        return _parse_or_raise(raw_text)
    except Exception:
        repair_prompt = (
            "El JSON anterior no fue válido. Reparalo y devolvé SOLO JSON válido "
            "con la estructura solicitada, sin texto extra. JSON a reparar:\n"
            f"{raw_text}"
        )
        repaired = client.responses.create(model=settings.openai_model, input=repair_prompt)
        return _parse_or_raise(repaired.output_text)
