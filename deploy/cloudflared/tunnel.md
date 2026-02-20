# Cloudflare Tunnel para Indoor Niche Lab

## 1) Instalar cloudflared
Elegí una opción según tu sistema operativo: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

## 2) Correr la aplicación local
```bash
uvicorn app.main:app --reload --port 8000
```

## 3) Abrir túnel público temporal
```bash
cloudflared tunnel --url http://localhost:8000
```

Cloudflared te va a mostrar una URL pública `https://...trycloudflare.com`.

## 4) Seguridad básica
- Este túnel es útil para demos, no para producción.
- **No expongas `/admin` en producción** sin autenticación y controles de acceso.
- No compartas tu `.env` ni tu `OPENAI_API_KEY`.
