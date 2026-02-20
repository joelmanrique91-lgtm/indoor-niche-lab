# Indoor Niche Lab

MVP educativo + e-commerce básico para cultivo indoor de hongos gourmet (Ostra y Melena de León).

## Requisitos
- Python 3.11+
- `pip`

## Setup rápido
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Inicializar y poblar base de datos
```bash
python scripts/init_db.py
python scripts/seed_demo.py
```

## Ejecutar servidor
```bash
uvicorn app.main:app --reload --port 8000
```

## Scripts disponibles
```bash
python scripts/init_db.py
python scripts/seed_demo.py
python scripts/generate_tutorials.py --stage-id 1
```

## Uso de Admin
- Abrí `http://localhost:8000/admin`
- Botón **Inicializar DB**: crea tablas e índices si no existen.
- Botón **Cargar demo**: inserta 2 etapas, 6 pasos, 8 productos y 2 kits.
- Botones **Generar con IA** por etapa: crea pasos con OpenAI y los guarda.
- En `/admin/editor` podés crear/editar etapas y cargar pasos manuales.

## Rutas web
- `/`
- `/stages`
- `/stages/{id}`
- `/products`
- `/kits`
- `/admin`
- `/admin/editor`

## Exponer temporalmente con Cloudflare Tunnel
Ver guía: `deploy/cloudflared/tunnel.md`.

## Notas
- Si no configurás `OPENAI_API_KEY`, la web funciona igual con datos demo.
- No subir `.env` con credenciales al repositorio.
