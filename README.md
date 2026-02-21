# Indoor Niche Lab

Indoor Niche Lab es un MVP educativo + catálogo básico para cultivo indoor de hongos gourmet. Está construido con FastAPI + Jinja2 y usa SQLite local.

## Windows 11 (camino recomendado, único)

### Prerrequisitos
- Python Launcher (`py`) con Python 3.12 o 3.11 (preferido 3.12)
- Git
- VS Code

### Setup + run (PowerShell)
```powershell
git clone <REPO_URL>
cd indoor-niche-lab
powershell -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

Ese comando:
1. crea `.venv` si falta,
2. instala dependencias,
3. crea `.env` desde `.env.example` si falta,
4. inicializa DB,
5. inserta seed demo,
6. levanta la API en `http://127.0.0.1:8000`.

---

## Configuración `.env`
Base:
```env
APP_TITLE=Indoor Niche Lab
DB_PATH=data/indoor.db
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_KEY=
```

- `APP_TITLE`: título visible en FastAPI.
- `DB_PATH`: ruta del archivo SQLite.
- `OPENAI_MODEL`: modelo para generación IA.
- `OPENAI_API_KEY`: **opcional**. Si está vacía, la app sigue funcionando y solo falla la generación IA con mensaje claro.

---

## Verificación rápida (PowerShell)
Con el server corriendo:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/stages
```

También podés abrir:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/admin`

---

## Fallback corto para levantar servidor
Si ya hiciste setup:
```powershell
.\uvicorn.cmd
```

`uvicorn.cmd` requiere que exista `.venv`.

---

## IA (opcional)
Para generar tutoriales IA por etapa:
1. completá `OPENAI_API_KEY` en `.env`,
2. ejecutá:

```powershell
.\.venv\Scripts\python.exe scripts\generate_tutorials.py --stage-id 1
```

Si `OPENAI_API_KEY` no está configurada, el script termina con error controlado y mensaje claro (sin stacktrace):
`No se pudo generar contenido IA: Falta OPENAI_API_KEY...`

---

## Scripts principales
```powershell
# Inicializar esquema
python scripts\init_db.py

# Cargar demo
python scripts\seed_demo.py

# Smoke test local
python scripts\smoke_test.py

# Tests
pytest
```

## Linux/macOS
Existe `uvicorn.sh` para arranque rápido en bash.
