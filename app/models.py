from __future__ import annotations

from pydantic import BaseModel, Field


class Stage(BaseModel):
    id: int | None = None
    name: str
    order_index: int


class TutorialStep(BaseModel):
    id: int | None = None
    stage_id: int
    title: str
    content: str
    tools_json: list[str] = Field(default_factory=list)
    estimated_cost_usd: float | None = None


class Product(BaseModel):
    id: int | None = None
    name: str
    category: str
    price: float
    affiliate_url: str
    internal_product: int = 0


class Kit(BaseModel):
    id: int | None = None
    name: str
    description: str
    price: float
    components_json: list[str] = Field(default_factory=list)


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
