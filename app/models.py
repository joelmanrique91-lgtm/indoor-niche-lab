from __future__ import annotations

from pydantic import BaseModel, Field


class Stage(BaseModel):
    id: int | None = None
    name: str
    order_index: int
    image_card_1: str | None = None
    image_card_2: str | None = None
    image_hero: str | None = None


class TutorialStep(BaseModel):
    id: int | None = None
    stage_id: int
    title: str
    content: str
    tools_json: list[str] = Field(default_factory=list)
    estimated_cost_usd: float | None = None
    image: str | None = None


class Product(BaseModel):
    id: int | None = None
    name: str
    category: str
    price: float
    affiliate_url: str
    internal_product: int = 0
    image: str | None = None


class Kit(BaseModel):
    id: int | None = None
    name: str
    description: str
    price: float
    components_json: list[str] = Field(default_factory=list)
    image_card: str | None = None
    image_result: str | None = None


class AIStep(BaseModel):
    title: str
    objective: str
    materials: list[str] = Field(default_factory=list)
    estimated_cost_usd: float = 0
    instructions: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(default_factory=list)
    checklist: list[str] = Field(default_factory=list)


class AIStageTutorial(BaseModel):
    stage_title: str
    steps: list[AIStep]
