# QA rápido de UX visual en `/admin`

1. Levantar la app (`uvicorn app.main:app --host 127.0.0.1 --port 8000`).
2. Abrir `http://127.0.0.1:8000/admin`.
3. Verificar que:
   - aparece el logo en navbar y favicon en pestaña,
   - cada link del navbar muestra icono + texto,
   - no hay 404 en `/static/assets/...` en la consola/red.
4. Ejecutar acciones:
   - `Inicializar DB`,
   - `Cargar demo`,
   - `Generar con IA` en una etapa.
5. Confirmar para cada acción:
   - estado visual por botón (loading/success/error),
   - mensaje de texto global existente (notice) se conserva,
   - la página sigue navegable y el resto de botones no queda bloqueado.
6. Navegar a `Etapas`, `Productos`, `Kits` y volver a `Admin` para validar enlaces.
7. En ancho mobile (devtools), confirmar que icono + texto no se superponen y hacen wrap.
