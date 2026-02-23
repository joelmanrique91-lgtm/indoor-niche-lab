#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "generated_images_manifest.json"
GENERATED_ROOT = ROOT / "app" / "static" / "img" / "generated"
TEMPLATES_ROOT = ROOT / "app" / "templates"
WEB_ROUTES_PATH = ROOT / "app" / "routes" / "web.py"


SLOT_RE = re.compile(r"\b(home|stages|kits|products)\.([a-z0-9\-]+)\b")

EXCLUDED_SLOT_TOKENS = {"svg", "html", "css", "js", "png", "jpg", "jpeg", "webp"}


def _load_manifest_slots() -> list[dict]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Manifest no encontrado: {MANIFEST_PATH}")

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("slots"), list):
        return data["slots"]
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        slots: dict[str, dict] = {}
        for item in data["items"]:
            section = item.get("section")
            slot = item.get("slot")
            if not section or not slot:
                continue
            key = f"{section}.{slot}"
            slots.setdefault(
                key,
                {
                    "slot_id": key,
                    "section": section,
                    "entity": {"type": "unknown", "id": None, "slug": None},
                    "prompt": "",
                    "negative_prompt": "",
                    "alt": "",
                    "style_id": "",
                    "model": "",
                    "created_at": "",
                    "updated_at": "",
                    "output_files": {},
                    "status": "missing",
                    "error_message": None,
                },
            )
            size = item.get("size")
            path = item.get("url") or item.get("path")
            if size and path:
                slots[key]["output_files"][size] = path
        return list(slots.values())

    raise SystemExit("Manifest inválido: se esperaba 'slots' o 'items'.")


def _slot_file_exists(rel_url: str) -> bool:
    cleaned = rel_url.removeprefix("/static/").removeprefix("static/")
    target = ROOT / "app" / "static" / cleaned
    return target.exists() and target.stat().st_size > 0


def _expected_manifest_files(slots: list[dict]) -> set[str]:
    paths: set[str] = set()
    for slot in slots:
        for rel in (slot.get("output_files") or {}).values():
            cleaned = str(rel).removeprefix("/static/").removeprefix("static/")
            if cleaned:
                paths.add(cleaned)
    return paths


def _collect_generated_files() -> set[str]:
    files: set[str] = set()
    if not GENERATED_ROOT.exists():
        return files
    for path in GENERATED_ROOT.rglob("*"):
        if path.is_file():
            files.add(path.relative_to(ROOT / "app" / "static").as_posix())
    return files


def _extract_template_slots() -> set[str]:
    slots: set[str] = set()
    for template in TEMPLATES_ROOT.rglob("*.html"):
        text = template.read_text(encoding="utf-8")
        for section, slot in SLOT_RE.findall(text):
            if slot not in EXCLUDED_SLOT_TOKENS:
                slots.add(f"{section}.{slot}")
    if WEB_ROUTES_PATH.exists():
        text = WEB_ROUTES_PATH.read_text(encoding="utf-8")
        for section, slot in SLOT_RE.findall(text):
            if slot not in EXCLUDED_SLOT_TOKENS:
                slots.add(f"{section}.{slot}")
    return slots


def _print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    print(f"\n== {title} ==")
    if not rows:
        print("(none)")
        return
    all_rows = [headers] + rows
    widths = [max(len(str(r[i])) for r in all_rows) for i in range(len(headers))]
    for idx, row in enumerate(all_rows):
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))
        if idx == 0:
            print("-+-".join("-" * widths[i] for i in range(len(headers))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoría integral de imágenes")
    parser.add_argument("--strict", action="store_true", help="falla si hay referencias de template fuera de manifest")
    args = parser.parse_args()

    slots = _load_manifest_slots()
    manifest_slot_ids = {slot.get("slot_id") for slot in slots if slot.get("slot_id")}

    missing_rows: list[list[str]] = []
    for slot in slots:
        slot_id = slot.get("slot_id", "")
        status = slot.get("status", "missing")
        for size, rel in (slot.get("output_files") or {}).items():
            exists = _slot_file_exists(str(rel))
            if not exists and status in {"ok", "missing"}:
                missing_rows.append([slot_id, size, str(rel), status])

    expected_paths = _expected_manifest_files(slots)
    disk_paths = _collect_generated_files()
    orphan = sorted(disk_paths - expected_paths)

    template_slots = _extract_template_slots()
    broken_template = sorted(template_slots - manifest_slot_ids)

    _print_table(
        "missing_by_slot",
        ["slot_id", "size", "expected_file", "manifest_status"],
        sorted(missing_rows, key=lambda r: (r[0], r[1])),
    )
    _print_table("orphan_files", ["static_relative_path"], [[p] for p in orphan])
    _print_table("broken_template_references", ["slot_id"], [[s] for s in broken_template])

    critical = len(missing_rows)
    if args.strict:
        critical += len(broken_template)

    if critical > 0:
        print(f"\nRESULT: FAIL (critical={critical})")
        raise SystemExit(1)

    print("\nRESULT: PASS")


if __name__ == "__main__":
    main()
