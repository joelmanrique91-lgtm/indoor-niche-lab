# Deploy en Railway (guía rápida)

1. Crear nuevo proyecto en Railway.
2. Conectar repositorio.
3. Definir comando de start:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Configurar variables opcionales:
   - `APP_ENV=prod`
   - `DB_PATH=data/indoor.db`
