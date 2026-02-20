from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterable

from app.config import DB_PATH, ensure_data_dir

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    body_md TEXT NOT NULL,
    checklist_items TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def get_connection(db_path: str | None = None):
    ensure_data_dir()
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def execute_many(sql: str, rows: Iterable[tuple], db_path: str | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.executemany(sql, rows)


def fetch_all(sql: str, params: tuple = (), db_path: str | None = None) -> list[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()


def fetch_one(sql: str, params: tuple = (), db_path: str | None = None) -> sqlite3.Row | None:
    with get_connection(db_path) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchone()
