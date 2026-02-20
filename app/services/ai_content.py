from __future__ import annotations


def generate_markdown_from_prompt(prompt: str) -> str:
    """Stub extension point for future AI integrations.

    For now, it returns deterministic markdown and does not call external APIs.
    """
    return f"# Borrador\n\nContenido base generado localmente para: {prompt.strip()}"
