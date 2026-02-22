from __future__ import annotations

import argparse
import sys

import httpx

CHECKS = [
    ("/", 1),
    ("/stages", 5),
    ("/stages/23", 4),
    ("/stages/24", 4),
    ("/kits", 3),
    ("/admin", 0),
    ("/admin/editor", 0),
]


def run(base_url: str) -> int:
    failures: list[str] = []
    for path, min_imgs in CHECKS:
        url = f"{base_url.rstrip('/')}{path}"
        try:
            response = httpx.get(url, timeout=10)
        except httpx.HTTPError as exc:
            failures.append(f"FAIL {path}: request error -> {exc}")
            continue

        img_count = response.text.count("<img")
        if response.status_code != 200:
            failures.append(f"FAIL {path}: status {response.status_code}")
            continue
        if img_count < min_imgs:
            failures.append(f"FAIL {path}: expected >= {min_imgs} <img>, got {img_count}")
            continue
        print(f"PASS {path}: status=200 img_count={img_count}")

    if failures:
        print("\nSMOKE FAIL")
        for line in failures:
            print(line)
        return 1

    print("\nSMOKE PASS")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke test de rutas web e imágenes renderizadas")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="URL base del sitio")
    args = parser.parse_args()
    sys.exit(run(args.base_url))
