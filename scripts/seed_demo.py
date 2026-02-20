from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import get_conn, init_db


def seed_demo_data() -> None:
    """Carga datos demo mínimos para navegar el MVP."""
    with get_conn() as conn:
        conn.execute("DELETE FROM tutorial_steps")
        conn.execute("DELETE FROM stages")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM kits")

        conn.executemany(
            "INSERT INTO stages(name, order_index) VALUES(?, ?)",
            [
                ("Preparación del sustrato", 1),
                ("Inoculación e incubación", 2),
            ],
        )

        stage_rows = conn.execute("SELECT id, name FROM stages ORDER BY order_index").fetchall()
        ids = {row["name"]: row["id"] for row in stage_rows}

        steps = [
            (ids["Preparación del sustrato"], "Hidratación de paja", "Objetivo: lograr humedad óptima (65%).\n\nChecklist:\n- Paja limpia\n- Agua hervida", '["Balde","Termómetro"]', 12),
            (ids["Preparación del sustrato"], "Pasteurización", "Objetivo: bajar carga microbiana.\n\nChecklist:\n- 65-75°C\n- 90 minutos", '["Olla","Termómetro"]', 18),
            (ids["Preparación del sustrato"], "Enfriado y escurrido", "Objetivo: dejar el sustrato listo para inocular.", '["Guantes","Bandeja"]', 6),
            (ids["Inoculación e incubación"], "Mezcla con spawn", "Objetivo: distribución homogénea del micelio.", '["Alcohol 70%","Guantes"]', 20),
            (ids["Inoculación e incubación"], "Armado de bolsas", "Objetivo: mantener intercambio gaseoso controlado.", '["Bolsas con filtro","Precinto"]', 14),
            (ids["Inoculación e incubación"], "Incubación controlada", "Objetivo: colonización completa en ambiente oscuro.", '["Estantería","Higrómetro"]', 10),
        ]
        conn.executemany(
            """
            INSERT INTO tutorial_steps(stage_id, title, content, tools_json, estimated_cost_usd)
            VALUES(?, ?, ?, ?, ?)
            """,
            steps,
        )

        products = [
            ("Spawn de Ostra 1kg", "Inóculo", 15.0, "https://example.com/spawn-ostra", 0),
            ("Spawn de Melena 1kg", "Inóculo", 18.0, "https://example.com/spawn-melena", 0),
            ("Bolsas con filtro x50", "Consumibles", 22.0, "https://example.com/bolsas", 0),
            ("Alcohol isopropílico", "Higiene", 8.5, "https://example.com/alcohol", 0),
            ("Termómetro digital", "Control", 12.5, "https://example.com/termometro", 0),
            ("Higrómetro", "Control", 11.9, "https://example.com/higrometro", 0),
            ("Kit Mini Ostra", "Kits", 49.9, "https://example.com/kit-mini-ostra", 1),
            ("Kit Inicio Melena", "Kits", 69.9, "https://example.com/kit-melena", 1),
        ]
        conn.executemany(
            "INSERT INTO products(name, category, price, affiliate_url, internal_product) VALUES(?, ?, ?, ?, ?)",
            products,
        )

        kits = [
            (
                "Kit Ostra Hogar",
                "Ideal para primera cosecha en interior con bajo presupuesto.",
                59.0,
                '["Spawn ostra 1kg","2 bolsas con filtro","Rociador","Guía rápida"]',
            ),
            (
                "Kit Melena de León Pro",
                "Enfoque en control ambiental para mejores resultados.",
                89.0,
                '["Spawn melena 1kg","4 bolsas con filtro","Higrómetro","Termómetro","Manual PDF"]',
            ),
        ]
        conn.executemany(
            "INSERT INTO kits(name, description, price, components_json) VALUES(?, ?, ?, ?)",
            kits,
        )


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("✅ Datos demo insertados")
