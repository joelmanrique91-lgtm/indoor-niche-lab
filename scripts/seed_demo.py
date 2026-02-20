from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import init_db
from app.models import Product, Stage
from app.repositories import upsert_product, upsert_stage


def seed_stages() -> None:
    stages = [
        Stage(slug="germinacion", title="Germinación", summary="Inicio del cultivo.", body_md="Semillas y humedad.", checklist_items=["Semillas", "Jiffy", "Agua"]),
        Stage(slug="vegetativo", title="Vegetativo", summary="Crecimiento vegetativo.", body_md="Luz y nutrición base.", checklist_items=["Luz 18/6", "Nutrientes grow"]),
        Stage(slug="floracion", title="Floración", summary="Fase de floración.", body_md="Control de EC/PH.", checklist_items=["Luz 12/12", "Filtro carbón"]),
    ]
    for stage in stages:
        upsert_stage(stage)


def seed_products() -> None:
    products = [
        Product(sku="LED-100", name="Panel LED 100W", category="Iluminación", price=149.99, url="https://example.com/led-100"),
        Product(sku="SOIL-20", name="Sustrato 20L", category="Sustrato", price=18.5, url="https://example.com/soil-20"),
        Product(sku="NPK-GROW", name="Fertilizante Grow", category="Nutrientes", price=22.9, url="https://example.com/npk-grow"),
        Product(sku="NPK-BLOOM", name="Fertilizante Bloom", category="Nutrientes", price=24.9, url="https://example.com/npk-bloom"),
        Product(sku="PH-UP", name="pH Up", category="Control", price=9.99, url="https://example.com/ph-up"),
        Product(sku="PH-DOWN", name="pH Down", category="Control", price=9.99, url="https://example.com/ph-down"),
        Product(sku="FAN-CLIP", name="Ventilador Clip", category="Clima", price=29.9, url="https://example.com/fan-clip"),
        Product(sku="FILTER-4", name="Filtro de Carbón 4\"", category="Clima", price=79.0, url="https://example.com/filter-4"),
    ]
    for product in products:
        upsert_product(product)


if __name__ == "__main__":
    init_db()
    seed_stages()
    seed_products()
    print("Demo data inserted.")
