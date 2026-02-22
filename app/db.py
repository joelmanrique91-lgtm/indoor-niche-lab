from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from app.config import ensure_dirs, settings

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    image_card_1 TEXT,
    image_card_2 TEXT,
    image_hero TEXT
);
CREATE INDEX IF NOT EXISTS idx_stages_order_index ON stages(order_index);

CREATE TABLE IF NOT EXISTS tutorial_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tools_json TEXT NOT NULL DEFAULT '[]',
    estimated_cost_usd REAL,
    image TEXT,
    FOREIGN KEY(stage_id) REFERENCES stages(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tutorial_steps_stage_id ON tutorial_steps(stage_id);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    affiliate_url TEXT NOT NULL,
    internal_product INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

CREATE TABLE IF NOT EXISTS kits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    components_json TEXT NOT NULL DEFAULT '[]',
    image_card TEXT,
    image_result TEXT
);
"""


@contextmanager
def get_conn(db_path: str | None = None):
    """Entrega conexión SQLite con row_factory por nombre de columnas."""
    ensure_dirs()
    conn = sqlite3.connect(db_path or settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, column_sql: str) -> None:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {row[1] for row in rows}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_sql}")


def init_db(db_path: str | None = None) -> None:
    """Crea esquema si no existe y agrega columnas nuevas de forma idempotente."""
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        _add_column_if_missing(conn, "stages", "image_card_1", "TEXT")
        _add_column_if_missing(conn, "stages", "image_card_2", "TEXT")
        _add_column_if_missing(conn, "stages", "image_hero", "TEXT")
        _add_column_if_missing(conn, "tutorial_steps", "image", "TEXT")
        _add_column_if_missing(conn, "kits", "image_card", "TEXT")
        _add_column_if_missing(conn, "kits", "image_result", "TEXT")
