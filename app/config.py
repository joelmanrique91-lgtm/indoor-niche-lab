from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Configuración principal de la app cargada desde variables de entorno."""

    app_title: str = os.getenv("APP_TITLE", "Indoor Niche Lab")
    db_path: str = os.getenv("DB_PATH", "data/indoor.db")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()


def ensure_dirs() -> None:
    """Asegura que exista el directorio de la base de datos."""
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
