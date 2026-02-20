from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import init_db
from app.repositories import upsert_stage
from app.services.tutorial_builder import build_stage_from_prompt


if __name__ == "__main__":
    init_db()
    stage = build_stage_from_prompt("entrenamiento de bajo estrés lst")
    upsert_stage(stage)
    print(f"Generated stage: {stage.slug}")
