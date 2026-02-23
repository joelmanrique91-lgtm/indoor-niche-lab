from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_conn, init_db


STAGE_CARD_1 = "section-images/stages/stage.card.1.v1.svg"
STAGE_CARD_2 = "section-images/stages/stage.card.2.v1.svg"
STAGE_HERO = "section-images/stages/stage.hero.v1.svg"
KIT_CARD = "section-images/kits/kit.card.v1.svg"
KIT_RESULT = "section-images/kits/kit.result.v1.svg"


def seed_demo_data() -> None:
    """Carga datos demo mínimos para navegar el MVP."""
    with get_conn() as conn:
        conn.execute("DELETE FROM tutorial_steps")
        conn.execute("DELETE FROM stages")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM kits")

        conn.executemany(
            """
            INSERT INTO stages(id, name, order_index, image_card_1, image_card_2, image_hero)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            [
                (23, "Preparación del sustrato", 1, STAGE_CARD_1, STAGE_CARD_2, STAGE_HERO),
                (24, "Inoculación e incubación", 2, STAGE_CARD_1, STAGE_CARD_2, STAGE_HERO),
            ],
        )

        steps = [
            (23, "Hidratación de paja", "Objetivo: lograr humedad óptima (65%).\n\nChecklist:\n- Paja limpia\n- Agua hervida", '["Balde","Termómetro"]', 12, "section-images/steps/step.placeholder.v1.svg"),
            (23, "Pasteurización", "Objetivo: bajar carga microbiana.\n\nChecklist:\n- 65-75°C\n- 90 minutos", '["Olla","Termómetro"]', 18, "section-images/steps/step.placeholder.v1.svg"),
            (23, "Enfriado y escurrido", "Objetivo: dejar el sustrato listo para inocular.", '["Guantes","Bandeja"]', 6, "section-images/steps/step.placeholder.v1.svg"),
            (24, "Mezcla con spawn", "Objetivo: distribución homogénea del micelio.", '["Alcohol 70%","Guantes"]', 20, "section-images/steps/step.placeholder.v1.svg"),
            (24, "Armado de bolsas", "Objetivo: mantener intercambio gaseoso controlado.", '["Bolsas con filtro","Precinto"]', 14, "section-images/steps/step.placeholder.v1.svg"),
            (24, "Incubación controlada", "Objetivo: colonización completa en ambiente oscuro.", '["Estantería","Higrómetro"]', 10, "section-images/steps/step.placeholder.v1.svg"),
        ]
        conn.executemany(
            """
            INSERT INTO tutorial_steps(stage_id, title, content, tools_json, estimated_cost_usd, image)
            VALUES(?, ?, ?, ?, ?, ?)
            """,
            steps,
        )

        products = [
            ("Spawn de Ostra 1kg", "Inóculo", 15.0, "https://example.com/spawn-ostra", 0, "section-images/products/products.card.placeholder.v1.svg"),
            ("Spawn de Melena 1kg", "Inóculo", 18.0, "https://example.com/spawn-melena", 0, "section-images/products/products.card.placeholder.v1.svg"),
            ("Bolsas con filtro x50", "Consumibles", 22.0, "https://example.com/bolsas", 0, "section-images/products/products.card.placeholder.v1.svg"),
            ("Alcohol isopropílico", "Higiene", 8.5, "https://example.com/alcohol", 0, "section-images/products/products.card.placeholder.v1.svg"),
            ("Termómetro digital", "Control", 12.5, "https://example.com/termometro", 0, "section-images/products/products.card.placeholder.v1.svg"),
            ("Higrómetro", "Control", 11.9, "https://example.com/higrometro", 0, "section-images/products/products.card.placeholder.v1.svg"),
            ("Kit Mini Ostra", "Kits", 49.9, "https://example.com/kit-mini-ostra", 1, "section-images/products/products.card.placeholder.v1.svg"),
            ("Kit Inicio Melena", "Kits", 69.9, "https://example.com/kit-melena", 1, "section-images/products/products.card.placeholder.v1.svg"),
        ]
        conn.executemany(
            "INSERT INTO products(name, category, price, affiliate_url, internal_product, image) VALUES(?, ?, ?, ?, ?, ?)",
            products,
        )

        kits = [
            (
                "Kit Ostra Hogar",
                "Ideal para primera cosecha en interior con bajo presupuesto.",
                59.0,
                '["Spawn ostra 1kg","2 bolsas con filtro","Rociador","Guía rápida"]',
                "section-images/kits/kit.card.v1.svg",
                "section-images/kits/kit.result.v1.svg",
            ),
            (
                "Kit Melena de León Pro",
                "Enfoque en control ambiental para mejores resultados.",
                89.0,
                '["Spawn melena 1kg","4 bolsas con filtro","Higrómetro","Termómetro","Manual PDF"]',
                "section-images/kits/kit.card.v1.svg",
                "section-images/kits/kit.result.v1.svg",
            ),
        ]
        conn.executemany(
            "INSERT INTO kits(name, description, price, components_json, image_card, image_result) VALUES(?, ?, ?, ?, ?, ?)",
            kits,
        )


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("✅ Datos demo insertados")
