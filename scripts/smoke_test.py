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


def _load_env_if_present() -> None:
    env_file = ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        _print(".env cargado")
    else:
        _print("WARN: .env no encontrado; continúo con variables de entorno exportadas")


def _warn_missing_critical_vars() -> None:
    # OPENAI_API_KEY es opcional para smoke básico, no debe bloquear.
    missing = [name for name in ["DB_PATH"] if not os.getenv(name)]
    if missing:
        _print(f"WARN: faltan variables recomendadas: {', '.join(missing)} (uso defaults)")


def _run_script(script_name: str) -> None:
    script_path = ROOT / "scripts" / script_name
    _print(f"Ejecutando {script_path.relative_to(ROOT)}")
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=ROOT)


def _ensure_db() -> None:
    db_path = ROOT / Path(os.getenv("DB_PATH", "data/indoor.db"))
    if not db_path.exists() or db_path.stat().st_size == 0:
        _print(f"DB no lista en {db_path}. Ejecutando init + seed...")
        _run_script("init_db.py")
        _run_script("seed_demo.py")


def _check_http_with_testclient() -> None:
    from app.main import app

    client = TestClient(app)

    checks = {
        "/api/health": 200,
        "/api/stages": 200,
    }

    failures: list[str] = []
    for path, expected_status in checks.items():
        response = client.get(path)
        if response.status_code == expected_status:
            _print(f"PASS {path} status={response.status_code}")
        else:
            failures.append(f"FAIL {path} status={response.status_code} body={response.text[:220]}")

    if failures:
        raise SystemExit("\n".join(failures))


def main() -> None:
    _load_env_if_present()
    _warn_missing_critical_vars()
    _ensure_db()
    _check_http_with_testclient()
    print("OK")


if __name__ == "__main__":
    main()
