# Auditoría técnica - Indoor Niche Lab

## Resumen ejecutivo
Indoor Niche Lab es un MVP en FastAPI para publicar tutoriales por etapas sobre cultivo indoor de hongos gourmet y un catálogo básico de productos/kits. Combina vistas web renderizadas con Jinja, endpoints API JSON y una base SQLite local para correr sin infraestructura externa. La generación de contenido por IA está implementada vía OpenAI y es opcional (requiere `OPENAI_API_KEY`).

Estado actual auditado:
- Arquitectura por capas (`routes` → `repositories` → `db`), con modelos Pydantic y scripts de bootstrap.
- Persistencia local estable en SQLite (`data/indoor.db`).
- Flujo demo funcional con `init_db.py` + `seed_demo.py`.
- GAPs de consistencia documental: parte de `docs/` describe un esquema viejo (con `slug/sku`) que no coincide con el esquema real.
- GAP de código no usado: `app/services/tutorial_builder.py` construye un `Stage` con campos inexistentes en el modelo actual.

---

## 1) Inventario real del repositorio

### Estructura actual (alto nivel)
- `app/`: aplicación FastAPI, rutas, acceso a datos, servicios, templates y estáticos.
- `scripts/`: inicialización de DB, seed demo, generación IA y smoke test.
- `tests/`: pruebas unitarias/API base.
- `docs/`: especificación y documentos técnicos (algunos desactualizados respecto al código).
- `deploy/`: notas de despliegue (Railway/Cloudflared).
- `data/`: carpeta para SQLite local y backups.

### Entrypoint principal
- `app/main.py`.
- Crea la app FastAPI, monta `/static`, registra routers web/API/admin y expone `/health`.

### Configuración (env vars)
- Fuente: `.env` cargado por `python-dotenv`.
- Definición en `app/config.py`:
  - `APP_TITLE` (default `Indoor Niche Lab`)
  - `DB_PATH` (default `data/indoor.db`)
  - `OPENAI_API_KEY` (vacío por defecto)
  - `OPENAI_MODEL` (default `gpt-4o-mini`)
- Plantilla disponible: `.env.example`.

### Dependencias y para qué se usan
- `fastapi`, `uvicorn`: API server y runtime ASGI.
- `jinja2`: templates SSR.
- `python-dotenv`: carga `.env`.
- `pydantic`: modelos de datos.
- `openai`: integración para generación de pasos.
- `python-multipart`: formularios del admin.
- `pytest`, `httpx`: testing.

### Base de datos
- Motor: SQLite nativo (`sqlite3`).
- Archivo por defecto: `data/indoor.db`.
- Inicialización: `app/db.py:init_db()` ejecuta `SCHEMA_SQL`.
- Tablas reales: `stages`, `tutorial_steps`, `products`, `kits`.

---

## 2) Auditoría de funcionamiento (flujo E2E)

## Diagrama textual E2E
`Comando uvicorn/scripts`  
→ `app/main.py` crea app y registra routers  
→ `app/config.py` carga `.env` y defaults  
→ `app/db.py` asegura directorio DB + conexión SQLite (FK ON)  
→ `app/repositories.py` ejecuta CRUD/queries  
→ `app/services/ai_content.py` (opcional) llama OpenAI y valida JSON con Pydantic  
→ `app/routes/web.py` renderiza Jinja / `app/routes/api.py` devuelve JSON / `app/routes/admin.py` orquesta init/seed/generación  
→ `scripts/*.py` automatizan init, seed, generación IA y smoke test.

### Módulos clave

#### `app/db.py`
- Responsabilidad: conexión SQLite y creación de esquema.
- Entradas: `db_path` opcional; si no, usa `settings.db_path`.
- Salidas: conexión context-managed y tablas/índices creados.
- Supuestos: ruta escribible, permisos de FS.

#### `app/models.py`
- Responsabilidad: contratos de datos (stages, steps, products, kits y payload IA).
- Entradas: datos DB/API.
- Salidas: objetos validados Pydantic.
- Supuestos: tipos y shape consistentes.

#### `app/repositories.py`
- Responsabilidad: capa de acceso a datos y operaciones CRUD.
- Entradas: IDs, campos de formularios, payload de pasos.
- Salidas: listas/objetos Pydantic e IDs insertados.
- Supuestos: DB inicializable; JSON de `tools_json/components_json` válido.

#### `app/services/ai_content.py`
- Responsabilidad: generar tutorial por etapa con OpenAI y validar JSON de respuesta.
- Entradas: `stage_name` + `OPENAI_API_KEY` + `OPENAI_MODEL`.
- Salidas: `AIStageTutorial` validado.
- Supuestos: API key presente, modelo accesible, salida parseable; incluye un intento de reparación si el primer JSON falla.

#### `app/services/tutorial_builder.py`
- Responsabilidad declarada: construir stage desde prompt.
- Entradas: texto de prompt.
- Salidas: intenta devolver `Stage`.
- GAP: usa campos (`slug`, `title`, `summary`, etc.) que no existen en `Stage` actual; módulo inconsistente/no usado por rutas ni scripts.

#### `app/routes/api.py`
- Responsabilidad: API JSON (`/api/health`, `/api/stages`, detalle por etapa y generación IA por stage).
- Entradas: path params (`stage_id`).
- Salidas: JSON con entidades o errores HTTP 404.
- Supuestos: etapas existentes para detalle/generación; API key para generar.

#### `app/routes/web.py`
- Responsabilidad: páginas SSR (`/`, `/stages`, `/stages/{id}`, `/products`, `/kits`).
- Entradas: request HTTP + `stage_id`.
- Salidas: templates Jinja con datos consultados.
- Supuestos: templates presentes; DB disponible.

#### `app/routes/admin.py`
- Responsabilidad: panel operativo (`/admin`) para init DB, seed demo, edición y generación IA.
- Entradas: forms (`name`, `order_index`, etc.) y acciones POST.
- Salidas: redirects con mensaje y cambios persistidos.
- Supuestos: sin autenticación (acceso abierto); scripts importables.

#### `scripts/init_db.py`
- Responsabilidad: crear esquema.
- Entrada: sin args.
- Salida: mensaje de confirmación.
- Supuesto: entorno Python y dependencia del proyecto disponibles.

#### `scripts/seed_demo.py`
- Responsabilidad: borrar y recargar dataset demo.
- Entrada: sin args.
- Salida: stages, steps, products y kits de demostración.
- Supuesto: esquema ya creado (aunque el `__main__` ya ejecuta `init_db()`).

#### `scripts/generate_tutorials.py`
- Responsabilidad: generar/reemplazar pasos IA para una etapa.
- Entrada: `--stage-id`.
- Salida: reemplazo de `tutorial_steps` para esa etapa.
- Supuesto: etapa existente + API key configurada.

#### `scripts/smoke_test.py`
- Responsabilidad: chequeo de “happy path” local.
- Entrada: `.env` + ejecución interna de init/seed + health HTTP temporal.
- Salida: `OK` si todo funciona.
- Supuesto: puede abrir puerto local (`8011` por defecto).

---

## 3) ¿Para qué sirve? (usuario final)
- Permite explorar una guía práctica de cultivo indoor por etapas desde una web simple.
- Muestra pasos accionables por etapa con objetivo, checklist, herramientas y costo estimado.
- Incluye catálogo básico de productos y kits para acompañar el aprendizaje.
- Ofrece panel admin para inicializar DB, cargar demo y editar contenido manualmente.
- Puede generar o regenerar pasos de una etapa con OpenAI (si hay API key).
- Expone API JSON para integraciones o consumo frontend (`/api/stages`, `/api/stages/{id}`).
- Corre 100% local con SQLite, ideal para pruebas rápidas sin DevOps.
- Incluye smoke test y tests base para validar instalación.

### Lo que sí puede hacer hoy
- Crear/editar etapas y agregar pasos.
- Cargar dataset demo completo.
- Generar pasos por IA y guardarlos en DB.
- Renderizar web y API sobre los mismos datos.

### Lo que NO puede hoy (limitaciones observadas)
- No tiene autenticación/autorización en admin.
- No hay e-commerce real (checkout/pagos/inventario).
- No hay migraciones versionadas (solo `executescript` de esquema).
- `tutorial_builder.py` está inconsistente con el modelo vigente.
- Parte de `docs/DB_SCHEMA.md` y `docs/SPEC.md` no refleja el esquema/rutas actuales.

---

## 4) Riesgos / GAPs técnicos
1. **Desalineación docs vs código**: documentación menciona campos/tablas viejas (`slug`, `sku`) que no existen en esquema actual.
2. **Módulo inconsistente**: `tutorial_builder.py` no es utilizable con el modelo actual.
3. **Admin sin auth**: cualquier usuario con acceso HTTP puede modificar datos.
4. **Sin migraciones**: cambios de esquema futuros pueden requerir intervención manual.

---

## 5) Recomendaciones mínimas (sin rediseño)
1. Mantener `README.md` como fuente operativa principal (Windows-first) con pasos exactos.
2. Marcar explícitamente en docs que `OPENAI_API_KEY` es opcional para uso demo y obligatoria para generación IA.
3. Corregir o retirar `app/services/tutorial_builder.py` para evitar deuda/confusión.
4. Actualizar `docs/DB_SCHEMA.md` y `docs/SPEC.md` al estado real (o etiquetarlos como “histórico”).
5. Agregar script `scripts/run_windows.ps1` idempotente para setup rápido en Windows.
