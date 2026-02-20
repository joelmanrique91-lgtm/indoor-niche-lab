from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"


def _print(msg: str) -> None:
    print(f"[smoke] {msg}")


def _ensure_env() -> None:
    if not ENV_FILE.exists():
        raise SystemExit("Falta .env. Copiá .env.example a .env antes de correr smoke_test.")

    required = ["APP_TITLE", "DB_PATH", "OPENAI_MODEL"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        _print(f"Aviso: variables no seteadas explícitamente (se usarán defaults): {', '.join(missing)}")


def _run_script(script_name: str) -> None:
    script_path = ROOT / "scripts" / script_name
    _print(f"Ejecutando {script_path.relative_to(ROOT)}")
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=ROOT)


def _wait_for_health(url: str, timeout_s: int = 20) -> int:
    started = time.time()
    while time.time() - started < timeout_s:
        try:
            with urlopen(url, timeout=2) as response:  # nosec B310 (localhost only)
                return response.status
        except URLError:
            time.sleep(0.5)
    raise TimeoutError(f"Timeout esperando respuesta de {url}")


def _check_http_health() -> None:
    port = int(os.getenv("SMOKE_TEST_PORT", "8011"))
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    _print("Levantando servidor uvicorn temporal")
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        status = _wait_for_health(f"http://127.0.0.1:{port}/health")
    finally:
        proc.terminate()
        proc.wait(timeout=10)

    if status != 200:
        raise SystemExit(f"Health check devolvió status inesperado: {status}")


def main() -> None:
    _ensure_env()
    _run_script("init_db.py")
    _run_script("seed_demo.py")

    db_path = Path(os.getenv("DB_PATH", "data/indoor.db"))
    if not db_path.exists():
        raise SystemExit(f"La DB no fue creada en {db_path}")

    _check_http_health()
    print("OK")


if __name__ == "__main__":
    main()
