# Indoor Niche Lab

Indoor Niche Lab es un MVP educativo + e-commerce básico para cultivo indoor de hongos gourmet (principalmente Ostra y Melena de León). La app expone una web en Jinja, endpoints API con FastAPI, persistencia local en SQLite y utilidades de carga de datos demo/IA para explorar flujos de aprendizaje y catálogo sin infraestructura externa.

## Quickstart (copy/paste)

### Linux / macOS (bash)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
python scripts/seed_demo.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts\init_db.py
python scripts\seed_demo.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verificación rápida de endpoints

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/api/health
curl -i http://127.0.0.1:8000/api/stages
```

## Script de smoke test

Valida el happy path local (env + DB + seed + HTTP health):

```bash
python scripts/smoke_test.py
```

Si todo sale bien imprime `OK`.

## Estructura de carpetas

- `app/main.py`: bootstrap de FastAPI (routers + static files).
- `app/config.py`: settings por entorno (`.env`).
- `app/db.py`: conexión SQLite + creación de schema.
- `app/models.py`: modelos Pydantic.
- `app/routes/`: rutas web, API y admin.
- `app/services/`: integración IA y helpers.
- `app/templates/`: templates Jinja.
- `app/static/`: CSS/JS/imagenes.
- `scripts/`: inicialización DB, seed demo, generación IA y smoke test.
- `docs/`: documentación técnica y de prompts.
- `deploy/`: guías de despliegue/túnel.
- `tests/`: tests API/DB.

## Scripts disponibles

```bash
python scripts/init_db.py
python scripts/seed_demo.py
python scripts/generate_tutorials.py --stage-id 1
python scripts/smoke_test.py
```

## Uso de Admin

- Abrí `http://localhost:8000/admin`
- Botón **Inicializar DB**: crea tablas e índices.
- Botón **Cargar demo**: inserta 2 etapas, 6 pasos, 8 productos y 2 kits.
- Botones **Generar con IA** por etapa: crea pasos con OpenAI y los guarda.
- En `/admin/editor` podés crear/editar etapas y cargar pasos manuales.

## Troubleshooting

1. **`ModuleNotFoundError: No module named 'fastapi'`**
   - Activá el entorno virtual y reinstalá deps con `pip install -r requirements.txt`.

2. **`/api/*` devuelve 404**
   - Verificá que estés corriendo este repo actualizado con `app/main.py` incluyendo routers.

3. **Error al generar contenido IA (`Falta OPENAI_API_KEY`)**
   - Seteá `OPENAI_API_KEY` en `.env`.
   - La app sigue funcionando con datos demo aunque no haya key.

4. **No se crea `data/indoor.db`**
   - Revisá `DB_PATH` en `.env` y ejecutá `python scripts/init_db.py`.
   - Asegurate de tener permisos de escritura en la carpeta destino.

5. **Puerto 8000 ocupado**
   - Corré `uvicorn app.main:app --reload --port 8010`.

6. **`scripts/smoke_test.py` falla por timeout**
   - Verificá que no haya firewall bloqueando loopback y que `uvicorn` esté instalado en el venv.

## Cloudflare Tunnel (placeholder)

Guía inicial disponible en `deploy/cloudflared/tunnel.md`.
Si necesitás túnel productivo con autenticación y dominio, definir variables/credenciales del entorno objetivo.

## Notas

- No subir `.env` con credenciales al repositorio.
- DB por defecto: SQLite local (`data/indoor.db`) para correr sin infraestructura externa.
