# Indoor Niche Lab

Indoor Niche Lab es un MVP educativo + catálogo básico para cultivo indoor de hongos gourmet. Está construido con FastAPI + Jinja2 y usa SQLite local.

## Quickstart en Windows (recomendado)

### 1) Prerrequisitos
- Windows 10/11
- Python 3.11 o 3.12 (`py --version`)
- Git (`git --version`)

### 2) Clonar el repo
```powershell
git clone <REPO_URL>
cd indoor-niche-lab
```

### 3) Crear y activar entorno virtual (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4) Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 5) Crear `.env` desde `.env.example`
```powershell
Copy-Item .env.example .env
notepad .env
```

Variables:
- `APP_TITLE`: opcional (nombre visible de la app).
- `DB_PATH`: recomendada (ruta SQLite; default `data/indoor.db`).
- `OPENAI_MODEL`: opcional para IA (default `gpt-4o-mini`).
- `OPENAI_API_KEY`: **obligatoria solo si querés generar tutoriales con IA**.

### 6) Inicializar DB
```powershell
python scripts\init_db.py
```

### 7) Cargar datos demo
```powershell
python scripts\seed_demo.py
```

### 8) Levantar servidor
```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> `uvicorn.sh` es para bash/Linux. En Windows usá el comando anterior.

### 9) Verificar que funciona
Abrí en navegador:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/admin`

### 10) Generar tutoriales con IA (opcional)
Con `OPENAI_API_KEY` configurada:
```powershell
python scripts\generate_tutorials.py --stage-id 1
```

## Script único Windows (idempotente)
Si querés setup + run en un solo comando:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows.ps1
```

Opciones:
```powershell
# Sin seed demo
powershell -ExecutionPolicy Bypass -File scripts\run_windows.ps1 -SkipSeed

# Puerto custom
powershell -ExecutionPolicy Bypass -File scripts\run_windows.ps1 -Port 8010
```

## Cómo funciona internamente
1. `app/main.py` crea la app FastAPI, monta `/static` y registra routers web/API/admin.
2. `app/config.py` carga variables de entorno desde `.env`.
3. `app/db.py` abre SQLite y crea schema cuando hace falta.
4. `app/repositories.py` encapsula consultas/updates de stages, steps, products y kits.
5. `app/routes/web.py` renderiza páginas Jinja.
6. `app/routes/api.py` expone endpoints JSON.
7. `app/routes/admin.py` permite init DB, seed demo, edición y generación IA.
8. `app/services/ai_content.py` llama OpenAI y transforma salida en pasos persistibles.

## Comandos principales
```powershell
# Crear esquema
python scripts\init_db.py

# Cargar demo
python scripts\seed_demo.py

# Generar pasos IA para una etapa
python scripts\generate_tutorials.py --stage-id 1

# Smoke test local (env + DB + health)
python scripts\smoke_test.py

# Tests
pytest
```

## Diagnóstico OpenAI
Ejecutá un check runtime real (sin tocar DB ni levantar servidor):

**Windows PowerShell**
```powershell
python scripts\check_openai.py
```

**Linux/Mac**
```bash
python scripts/check_openai.py
```

El script usa `OPENAI_MODEL` si está seteado. Si está vacío, aplica `gpt-4o-mini` por defecto y lo informa por consola.

Códigos de salida:
- `0`: PASS (OpenAI conectado y respondiendo)
- `2`: falta `OPENAI_API_KEY`
- `3`: error de autenticación/credenciales
- `4`: error de red/timeout/DNS
- `5`: modelo inválido/no disponible

## Outputs y persistencia
- DB SQLite: `data/indoor.db` (o la ruta que definas en `DB_PATH`).
- Contenido generado (manual o IA): se guarda en tablas `stages` y `tutorial_steps`.
- Catálogo demo: tablas `products` y `kits`.
- No se generan logs dedicados por defecto; salida a consola.

## Troubleshooting
- **`ModuleNotFoundError`**: activá el venv e instalá `requirements.txt`.
- **`/api/*` 404**: verificá que corras este repo con `app/main.py` actualizado.
- **Error IA (`Falta OPENAI_API_KEY`)**: completá `OPENAI_API_KEY` en `.env`.
- **No aparece `data/indoor.db`**: revisá `DB_PATH` y corré `python scripts\init_db.py`.
- **Puerto ocupado**: cambiá `--port` en uvicorn o `-Port` en `run_windows.ps1`.
- **PowerShell bloquea scripts**: usá `-ExecutionPolicy Bypass` al ejecutar `run_windows.ps1`.
