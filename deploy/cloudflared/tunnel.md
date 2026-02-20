# Cloudflared Tunnel (guía rápida)

1. Instalar `cloudflared`.
2. Ejecutar app local en puerto 8000.
3. Crear túnel:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
4. Usar URL temporal para compartir demo.
