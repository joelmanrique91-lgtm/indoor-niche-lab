from __future__ import annotations

import json

from app.db import get_conn, init_db
from app.models import Kit, Product, Stage, TutorialStep


def _ensure_ready() -> None:
    init_db()


def list_stages() -> list[Stage]:
    _ensure_ready()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM stages ORDER BY order_index ASC, id ASC").fetchall()
    return [
        Stage(
            id=row["id"],
            name=row["name"],
            order_index=row["order_index"],
            image_card_1=row["image_card_1"],
            image_card_2=row["image_card_2"],
            image_hero=row["image_hero"],
        )
        for row in rows
    ]


def get_stage(stage_id: int) -> Stage | None:
    _ensure_ready()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM stages WHERE id = ?", (stage_id,)).fetchone()
    if not row:
        return None
    return Stage(
        id=row["id"],
        name=row["name"],
        order_index=row["order_index"],
        image_card_1=row["image_card_1"],
        image_card_2=row["image_card_2"],
        image_hero=row["image_hero"],
    )


def create_stage(
    name: str,
    order_index: int,
    image_card_1: str | None = None,
    image_card_2: str | None = None,
    image_hero: str | None = None,
) -> int:
    _ensure_ready()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO stages(name, order_index, image_card_1, image_card_2, image_hero) VALUES(?, ?, ?, ?, ?)",
            (name, order_index, image_card_1, image_card_2, image_hero),
        )
        return int(cur.lastrowid)


def update_stage(
    stage_id: int,
    name: str,
    order_index: int,
    image_card_1: str | None = None,
    image_card_2: str | None = None,
    image_hero: str | None = None,
) -> None:
    _ensure_ready()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE stages
            SET name = ?, order_index = ?, image_card_1 = ?, image_card_2 = ?, image_hero = ?
            WHERE id = ?
            """,
            (name, order_index, image_card_1, image_card_2, image_hero, stage_id),
        )


def list_steps_by_stage(stage_id: int) -> list[TutorialStep]:
    _ensure_ready()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tutorial_steps WHERE stage_id = ? ORDER BY id ASC", (stage_id,)
        ).fetchall()
    return [
        TutorialStep(
            id=row["id"],
            stage_id=row["stage_id"],
            title=row["title"],
            content=row["content"],
            tools_json=json.loads(row["tools_json"] or "[]"),
            estimated_cost_usd=row["estimated_cost_usd"],
            image=row["image"],
        )
        for row in rows
    ]


def create_step(
    stage_id: int,
    title: str,
    content: str,
    tools: list[str],
    estimated_cost_usd: float | None,
    image: str | None = None,
) -> int:
    _ensure_ready()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tutorial_steps(stage_id, title, content, tools_json, estimated_cost_usd, image)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (stage_id, title, content, json.dumps(tools, ensure_ascii=False), estimated_cost_usd, image),
        )
        return int(cur.lastrowid)


def replace_steps(stage_id: int, steps: list[dict]) -> None:
    _ensure_ready()
    with get_conn() as conn:
        conn.execute("DELETE FROM tutorial_steps WHERE stage_id = ?", (stage_id,))
        for step in steps:
            conn.execute(
                """
                INSERT INTO tutorial_steps(stage_id, title, content, tools_json, estimated_cost_usd, image)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    stage_id,
                    step["title"],
                    step["content"],
                    json.dumps(step.get("tools", []), ensure_ascii=False),
                    step.get("estimated_cost_usd"),
                    step.get("image"),
                ),
            )


def list_products() -> list[Product]:
    _ensure_ready()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    return [
        Product(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            price=row["price"],
            affiliate_url=row["affiliate_url"],
            internal_product=row["internal_product"],
            image=row["image"],
        )
        for row in rows
    ]



def get_product(product_id: int) -> Product | None:
    _ensure_ready()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        return None
    return Product(
        id=row["id"],
        name=row["name"],
        category=row["category"],
        price=row["price"],
        affiliate_url=row["affiliate_url"],
        internal_product=row["internal_product"],
        image=row["image"],
    )

def create_product(product: Product) -> None:
    _ensure_ready()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO products(name, category, price, affiliate_url, internal_product, image)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (product.name, product.category, product.price, product.affiliate_url, product.internal_product, product.image),
        )


def list_kits() -> list[Kit]:
    _ensure_ready()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM kits ORDER BY name").fetchall()
    return [
        Kit(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            price=row["price"],
            components_json=json.loads(row["components_json"] or "[]"),
            image_card=row["image_card"],
            image_result=row["image_result"],
        )
        for row in rows
    ]


def create_kit(kit: Kit) -> None:
    _ensure_ready()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO kits(name, description, price, components_json, image_card, image_result)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            (
                kit.name,
                kit.description,
                kit.price,
                json.dumps(kit.components_json, ensure_ascii=False),
                kit.image_card,
                kit.image_result,
            ),
        )
