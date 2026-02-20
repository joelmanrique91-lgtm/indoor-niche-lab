# SPEC - Indoor Niche Lab MVP

## Objetivo
Construir un MVP de portal web para indoor con dos pilares:
1. Tutoriales por etapas (stages).
2. Catálogo de productos para monetización.

## Alcance funcional
- Web pública con Home, listado y detalle de stages, listado de productos.
- Panel admin mínimo (sin auth en esta fase) con dashboard y editor UI.
- API JSON para health, stages y products.
- Persistencia SQLite local.

## Arquitectura
- Backend: FastAPI.
- Base de datos: SQLite con `sqlite3` nativo.
- Renderizado server-side: Jinja2 templates.
- Organización por capas:
  - `routes`: endpoints web/api/admin.
  - `repositories`: acceso a datos.
  - `services`: lógica de construcción de tutoriales y extensión IA futura.

## No objetivos de esta iteración
- Autenticación/roles.
- Integración con APIs externas de IA.
- Pagos o ecommerce real.

## Flujo de datos
1. Scripts inicializan y pueblan DB.
2. Repositorios consultan tablas.
3. Rutas web renderizan templates; rutas API serializan modelos.

## Criterios de aceptación
- Endpoints `/health` y `/api/health` devuelven `{ "ok": true }`.
- `/stages`, `/stages/{slug}`, `/products`, `/admin`, `/admin/editor` responden correctamente.
- Scripts `init_db` y `seed_demo` funcionan sin errores.
- Tests base (`pytest`) pasan.
