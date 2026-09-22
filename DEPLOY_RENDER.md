# Despliegue en Render

Este proyecto está listo para desplegarse con Render Blueprint usando `render.yaml`.

## Pasos

1. Sube el repo a GitHub.
2. En Render, crea un **Blueprint** desde el repo.
3. Render detectará `render.yaml` y creará:
   - Web service `singpe`
   - PostgreSQL `singpe-db`
4. Cuando Render pregunte por `YOUTUBE_API_KEY`, pega tu clave de YouTube Data API.
5. Luego del primer deploy, entra a `/admin`, genera mesas y QR.

## URL base

El Blueprint usa:

```text
https://singpe.onrender.com
```

Si Render asigna otro dominio o configuras dominio propio, cambia `BASE_URL` en las variables del servicio y vuelve a generar los QR desde `/admin`.

## Archivos subidos y canciones

En plan Free, Render no conserva archivos subidos al disco después de reinicios o redeploys. La base de datos sí queda en PostgreSQL, pero canciones subidas, QR generados y caché de voz viven en filesystem efímero.

Para producción real, cambia el servicio web a un plan pagado, adjunta un disco persistente y define:

```text
SINGPE_DATA_DIR=/var/data
```

Con eso, SingPe guardará ahí:

- `karaoke_library/`
- `qr/`
- `tts_cache/`
