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


# Generación de imágenes IA (Home, slot-driven)
```bash
# modo mock (sin API key)
python scripts/generate_site_images.py --only home --mock

# modo real (requiere OPENAI_API_KEY)
export OPENAI_API_KEY=tu_api_key
python scripts/generate_site_images.py --only home --real
```

Opcional:
```bash
# regenera incluso si los archivos del slot ya existen
python scripts/generate_site_images.py --only home --mock --force
```

El pipeline:
1. genera assets por slot de Home en `app/static/img/generated/home/<slot>/{sm,md,lg}.webp`,
2. mantiene idempotencia (si existe el slot completo, salta salvo `--force`),
3. guarda trazabilidad en `data/generated_images_manifest.json` (source of truth),
4. no modifica templates automáticamente y mantiene fallback a SVG legacy vía resolver.

Smoke test específico:
```bash
python scripts/smoke_test_images.py
```

> `data/generated_images_map.json` queda como archivo legado de un pipeline anterior.

## Generar imágenes por sección
Comando único (modo completo):
```bash
python scripts/generate_section_images.py --url "https://perception-mai-configure-pee.trycloudflare.com/" --out "app/static/section-images" --v 1
```

Opcional para auditoría sin consumir API:
```bash
python scripts/generate_section_images.py --url "https://perception-mai-configure-pee.trycloudflare.com/" --out "app/static/section-images" --v 1 --scan-only
```

Salidas:
- `outputs/section_images/sections.json` (inventario de secciones detectadas)
- `outputs/section_images/manifest.json` (prompts, archivos y cambios de integración)

Si falta `OPENAI_API_KEY`, el script falla con mensaje claro y no afecta el funcionamiento normal de la app.

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


## Generar imágenes (REAL)

PowerShell (Windows):
```powershell
$env:OPENAI_API_KEY="tu_api_key"
python scripts\generate_site_images.py --real --force
```

El script genera archivos en: `app/static/img/generated/{section}/{slot}/{size}.webp`

## Verificar imágenes servidas

Con el server levantado:
```powershell
start http://127.0.0.1:8000/static/img/generated/home/hero/md.webp
start http://127.0.0.1:8000/debug/static-check
```

Tambien podés probar por terminal:
```powershell
Invoke-WebRequest http://127.0.0.1:8000/static/img/generated/home/hero/md.webp -Method Head
Invoke-WebRequest http://127.0.0.1:8000/debug/static-check -Method Get
```
