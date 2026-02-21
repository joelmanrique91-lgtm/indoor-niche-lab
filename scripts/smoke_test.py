from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))


def _print(msg: str) -> None:
    print(f"[smoke] {msg}")


def _ensure_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        raise SystemExit("Falta .env. Copiá .env.example a .env antes de correr smoke_test.")
    load_dotenv(env_file)


def _run_script(script_name: str) -> None:
    script_path = ROOT / "scripts" / script_name
    _print(f"Ejecutando {script_path.relative_to(ROOT)}")
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=ROOT)


def _ensure_db() -> None:
    db_path = ROOT / Path(os.getenv("DB_PATH", "data/indoor.db"))
    if not db_path.exists():
        _print(f"DB no encontrada en {db_path}. Ejecutando init + seed...")
        _run_script("init_db.py")
        _run_script("seed_demo.py")
    elif db_path.stat().st_size == 0:
        _print("DB vacía detectada. Ejecutando init + seed...")
        _run_script("init_db.py")
        _run_script("seed_demo.py")


def _check_http_health_with_testclient() -> None:
    from app.main import app

    client = TestClient(app)
    health = client.get("/health")
    if health.status_code != 200 or health.json() != {"ok": True}:
        raise SystemExit(f"/health inesperado: status={health.status_code} body={health.text}")

    api_health = client.get("/api/health")
    if api_health.status_code != 200 or api_health.json() != {"ok": True}:
        raise SystemExit(f"/api/health inesperado: status={api_health.status_code} body={api_health.text}")


def main() -> None:
    _ensure_env()
    _run_script("init_db.py")
    _run_script("seed_demo.py")
    _ensure_db()
    _check_http_health_with_testclient()
    print("OK")


if __name__ == "__main__":
    main()
