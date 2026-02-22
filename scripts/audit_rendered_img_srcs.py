#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import socket
import threading
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app
from app.repositories import list_stages


@dataclass
class ImgCheck:
    page: str
    raw_src: str
    absolute_url: str
    status_code: int
    content_type: str
    byte_size: int
    placeholder: bool


class ImgSrcParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        for key, value in attrs:
            if key.lower() == "src" and value:
                self.sources.append(value.strip())


def _wait_for_health(base_url: str, timeout_s: float = 20.0) -> None:
    deadline = time.time() + timeout_s
    last_err = ""
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                return
            last_err = f"status={response.status_code}"
        except httpx.HTTPError as exc:
            last_err = str(exc)
        time.sleep(0.2)
    raise RuntimeError(f"No fue posible levantar app en {base_url}: {last_err}")


def _build_paths() -> list[str]:
    paths = ["/", "/stages", "/products", "/kits"]
    stages = list_stages()
    if stages:
        paths.append(f"/stages/{stages[0].id}")
    return paths


def _extract_img_srcs(html: str) -> list[str]:
    parser = ImgSrcParser()
    parser.feed(html)
    return parser.sources


def _head_or_get(url: str) -> tuple[int, str, int]:
    try:
        head = httpx.head(url, timeout=5, follow_redirects=True)
        status = head.status_code
        content_type = head.headers.get("content-type", "")
        content_len = head.headers.get("content-length")
        byte_size = int(content_len) if content_len and content_len.isdigit() else 0
        if status < 400:
            return status, content_type, byte_size
    except httpx.HTTPError:
        pass

    try:
        get = httpx.get(url, timeout=10, follow_redirects=True)
        status = get.status_code
        content_type = get.headers.get("content-type", "")
        return status, content_type, len(get.content)
    except httpx.HTTPError:
        return 599, "", 0


def _normalize_src(base_url: str, src: str) -> str:
    if src.startswith("data:"):
        return src
    return urljoin(f"{base_url}/", src)


def _is_placeholder_src(src_url: str) -> bool:
    parsed = urlparse(src_url)
    return parsed.path.endswith("/static/img/placeholder.svg")


def _fmt_table(rows: Iterable[list[str]]) -> str:
    rows_list = list(rows)
    if not rows_list:
        return ""
    widths = [max(len(str(row[i])) for row in rows_list) for i in range(len(rows_list[0]))]
    lines: list[str] = []
    for idx, row in enumerate(rows_list):
        padded = " | ".join(str(col).ljust(widths[i]) for i, col in enumerate(row))
        lines.append(padded)
        if idx == 0:
            sep = "-+-".join("-" * w for w in widths)
            lines.append(sep)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audita src de imágenes renderizadas por la app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument("--home-placeholder-threshold", type=int, default=0)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"

    config = uvicorn.Config(app, host=args.host, port=args.port, log_level="warning")
    server = uvicorn.Server(config=config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        _wait_for_health(base_url)

        checks: list[ImgCheck] = []
        errors: list[str] = []
        per_page_summary: list[list[str]] = [["page", "total", "ok image/*", "err(>=400)", "placeholder"]]

        for path in _build_paths():
            page_url = f"{base_url}{path}"
            response = httpx.get(page_url, timeout=10)
            if response.status_code >= 400:
                errors.append(f"Página no accesible {path}: HTTP {response.status_code}")
                continue

            img_srcs = _extract_img_srcs(response.text)
            page_checks: list[ImgCheck] = []
            for src in img_srcs:
                absolute = _normalize_src(base_url, src)
                if absolute.startswith("data:"):
                    page_checks.append(
                        ImgCheck(path, src, absolute, 200, "image/data-uri", len(absolute), False)
                    )
                    continue
                status, ctype, byte_size = _head_or_get(absolute)
                page_checks.append(
                    ImgCheck(
                        page=path,
                        raw_src=src,
                        absolute_url=absolute,
                        status_code=status,
                        content_type=ctype,
                        byte_size=byte_size,
                        placeholder=_is_placeholder_src(absolute),
                    )
                )

            checks.extend(page_checks)
            ok_image = sum(1 for item in page_checks if item.status_code < 400 and item.content_type.startswith("image/"))
            err_count = sum(1 for item in page_checks if item.status_code >= 400)
            placeholders = sum(1 for item in page_checks if item.placeholder)
            per_page_summary.append([path, str(len(page_checks)), str(ok_image), str(err_count), str(placeholders)])

        broken = [item for item in checks if item.status_code >= 400]
        non_image = [
            item
            for item in checks
            if item.status_code < 400 and not (item.content_type.startswith("image/") or item.content_type == "image/data-uri")
        ]
        placeholders = [item for item in checks if item.placeholder]

        entity_placeholder = [item for item in placeholders if item.page in {"/stages", "/products", "/kits"} or re.match(r"^/stages/\d+$", item.page)]
        home_placeholder = [item for item in placeholders if item.page == "/"]

        print("\n=== Image audit summary ===")
        print(_fmt_table(per_page_summary))

        if broken:
            print("\n[FAIL] Imágenes con status >= 400:")
            for item in broken:
                print(f" - page={item.page} src={item.raw_src} -> {item.absolute_url} status={item.status_code}")

        if non_image:
            print("\n[WARN] Respuestas no image/*:")
            for item in non_image:
                print(
                    f" - page={item.page} src={item.raw_src} -> {item.absolute_url} "
                    f"status={item.status_code} content-type={item.content_type} bytes={item.byte_size}"
                )

        if placeholders:
            print("\n[INFO] Src apuntando a placeholder.svg:")
            for item in placeholders:
                print(f" - page={item.page} src={item.raw_src}")

        if broken:
            errors.append(f"Se detectaron {len(broken)} imágenes con status >= 400.")
        if entity_placeholder:
            errors.append(f"Se detectaron {len(entity_placeholder)} placeholders en páginas de entidades (stages/products/kits).")
        if len(home_placeholder) > args.home_placeholder_threshold:
            errors.append(
                "Se detectaron placeholders en Home por encima del umbral: "
                f"{len(home_placeholder)} > {args.home_placeholder_threshold}."
            )

        if errors:
            print("\nRESULT: FAIL")
            for line in errors:
                print(f" - {line}")
            raise SystemExit(1)

        print("\nRESULT: OK")
    finally:
        server.should_exit = True
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
