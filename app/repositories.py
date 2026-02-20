from __future__ import annotations

import json

from app.db import fetch_all, fetch_one, get_connection
from app.models import Product, Stage


def _row_to_stage(row) -> Stage:
    return Stage(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        summary=row["summary"],
        body_md=row["body_md"],
        checklist_items=json.loads(row["checklist_items"]),
        created_at=row["created_at"],
    )


def _row_to_product(row) -> Product:
    return Product(
        id=row["id"],
        sku=row["sku"],
        name=row["name"],
        category=row["category"],
        price=row["price"],
        url=row["url"],
        created_at=row["created_at"],
    )


def list_stages() -> list[Stage]:
    rows = fetch_all("SELECT * FROM stages ORDER BY created_at DESC")
    return [_row_to_stage(r) for r in rows]


def get_stage_by_slug(slug: str) -> Stage | None:
    row = fetch_one("SELECT * FROM stages WHERE slug = ?", (slug,))
    return _row_to_stage(row) if row else None


def list_products() -> list[Product]:
    rows = fetch_all("SELECT * FROM products ORDER BY created_at DESC")
    return [_row_to_product(r) for r in rows]


def upsert_stage(stage: Stage) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO stages (slug, title, summary, body_md, checklist_items)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
              title=excluded.title,
              summary=excluded.summary,
              body_md=excluded.body_md,
              checklist_items=excluded.checklist_items
            """,
            (
                stage.slug,
                stage.title,
                stage.summary,
                stage.body_md,
                json.dumps(stage.checklist_items),
            ),
        )


def upsert_product(product: Product) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO products (sku, name, category, price, url)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
              name=excluded.name,
              category=excluded.category,
              price=excluded.price,
              url=excluded.url
            """,
            (product.sku, product.name, product.category, product.price, product.url),
        )
