from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class Stage(BaseModel):
    id: int | None = None
    slug: str
    title: str
    summary: str
    body_md: str
    checklist_items: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class Product(BaseModel):
    id: int | None = None
    sku: str
    name: str
    category: str
    price: float
    url: str
    created_at: datetime | None = None
