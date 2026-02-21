from __future__ import annotations

import os
import socket
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv


def _mask_key(value: str) -> str:
    if not value:
        return "(vacía)"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _openai_version() -> str:
    try:
        from importlib.metadata import version

        return version("openai")
    except Exception:
        return "no disponible"


def _print_env_summary(api_key: str, model_from_env: str, model_effective: str) -> None:
    print("== OpenAI Runtime Connectivity Check ==")
    print(f".env detectado: {'sí' if Path('.env').exists() else 'no'}")
    print(f"OPENAI_API_KEY: {'presente' if bool(api_key) else 'ausente'} ({_mask_key(api_key)})")
    print(f"OPENAI_MODEL (env): {model_from_env or '(vacío)'}")
    if not model_from_env:
        print(f"OPENAI_MODEL (efectivo): {model_effective} (default aplicado)")
    else:
        print(f"OPENAI_MODEL (efectivo): {model_effective}")
    print(f"openai package version: {_openai_version()}")


def main() -> int:
    # Igual que app/config.py: carga variables desde .env si existe.
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model_from_env = os.getenv("OPENAI_MODEL", "").strip()
    model = model_from_env or "gpt-4o-mini"

    _print_env_summary(api_key, model_from_env, model)

    if not api_key:
        print("FAIL: falta OPENAI_API_KEY. Configurala en tu entorno o archivo .env")
        return 2

    try:
        from openai import APIConnectionError, AuthenticationError, BadRequestError, OpenAI
    except Exception as exc:
        print(f"FAIL: no se pudo importar el SDK de OpenAI: {exc}")
        return 1

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input="ping",
            max_output_tokens=20,
        )
        output_text = getattr(response, "output_text", "") or "(sin output_text)"
        response_id = getattr(response, "id", "(sin id)")
        print("PASS: OpenAI conectado y respondiendo")
        print(f"response_id: {response_id}")
        print(f"output_text: {output_text}")
        return 0
    except AuthenticationError as exc:
        print(f"FAIL(auth): credenciales inválidas o sin permiso. Detalle: {exc}")
        return 3
    except BadRequestError as exc:
        msg = str(exc).lower()
        if "model" in msg:
            print(f"FAIL(model): modelo inválido/no disponible ({model}). Detalle: {exc}")
            return 5
        print(f"FAIL(request): request inválido. Detalle: {exc}")
        return 1
    except APIConnectionError as exc:
        print(f"FAIL(red): error de conexión hacia OpenAI. Detalle: {exc}")
        return 4
    except (TimeoutError, socket.gaierror) as exc:
        print(f"FAIL(red): timeout/DNS al conectar con OpenAI. Detalle: {exc}")
        return 4
    except Exception as exc:
        msg = str(exc).lower()
        if any(token in msg for token in ["timeout", "name or service not known", "temporary failure in name resolution", "dns", "connection"]):
            print(f"FAIL(red): problema de red/timeout/DNS. Detalle: {exc}")
            return 4
        if any(token in msg for token in ["invalid api key", "incorrect api key", "unauthorized", "authentication"]):
            print(f"FAIL(auth): credenciales inválidas. Detalle: {exc}")
            return 3
        if "model" in msg and any(token in msg for token in ["not found", "does not exist", "invalid", "unavailable"]):
            print(f"FAIL(model): modelo inválido/no disponible ({model}). Detalle: {exc}")
            return 5

        print("FAIL: error inesperado durante el check")
        print(f"error_type: {type(exc).__name__}")
        print(f"error: {exc}")
        print("stack (resumen):")
        print("".join(traceback.format_exception_only(type(exc), exc)).strip())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
