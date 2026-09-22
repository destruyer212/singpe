# 🎤 SingPe — Sistema de gestión de karaoke para bares

MVP funcional: cada mesa pide canciones desde su celular escaneando un QR,
el sistema aplica reglas anti-spam y arma una cola inteligente en tiempo real,
el DJ la controla desde un panel, y la pantalla del local reproduce la canción
con letra sincronizada.

## Arquitectura

```
Cliente (celular, escanea QR)
        |
   frontend/  (HTML + JS + CSS, servidos por el backend)
        |
   backend/  FastAPI (Python) ---- WebSockets (tiempo real) ---- Panel DJ / Pantalla TV
        |
   PostgreSQL (mesas, canciones, cola, historial)
        |
   karaoke_library/  (biblioteca propia opcional: audio, video, letras .lrc)
        |
   YouTube Data API   (catálogo prácticamente ilimitado de canciones)
```

## Estructura de carpetas

```
singpe/
  backend/                 API, lógica de negocio, base de datos (Python/FastAPI)
    main.py                  punto de entrada de la app FastAPI
    config.py                configuración (rutas, DB, claves)
    database.py               conexión a PostgreSQL (SQLAlchemy)
    models.py                  tablas: Mesa, Cancion, Solicitud, Configuracion
    schemas.py                  esquemas Pydantic (entrada/salida de la API)
    crud.py                      reglas de negocio (anti-spam, cola, puntos)
    library.py                    escaneo/registro de karaoke_library/
    youtube.py                     búsqueda de karaoke en YouTube
    qr.py                           generación de códigos QR por mesa
    ws_manager.py                   WebSocket (tiempo real)
    routers/                        endpoints HTTP agrupados por área
      pages.py                        páginas HTML (/, /mesa, /dj, /tv, /admin)
      api_mesas.py                     API del cliente (buscar, pedir)
      api_dj.py                         API del panel DJ (controlar cola)
      api_admin.py                       API de administración
      ws.py                               endpoint WebSocket /ws
  frontend/                 Todo lo visual (HTML/CSS/JS, sin build step)
    templates/                plantillas Jinja2 (una por pantalla)
    static/
      css/style.css            estilos propios
      js/                       lógica de cada pantalla (mesa.js, dj.js, tv.js...)
      qr/                        códigos QR generados por mesa
  karaoke_library/          biblioteca propia opcional (audio/video/letras)
  scripts/                  utilidades de línea de comandos
  run.py                    arranca el servidor (uvicorn)
```

- **Backend**: FastAPI + SQLAlchemy + WebSockets, todo en `backend/`.
- **Base de datos**: PostgreSQL (ver instalación abajo). Cadena de conexión configurable sin tocar código.
- **Frontend**: HTML servido por Jinja2 + JS puro + Tailwind (CDN), sin Node/npm, todo en `frontend/`.
- **Tiempo real**: un único canal WebSocket (`/ws`) notifica a mesas, panel DJ y pantalla TV cuando cambia la cola.
- **Catálogo de canciones**: búsqueda en YouTube (millones de canciones, reproducidas embebidas en `/tv`) + biblioteca propia opcional en `karaoke_library/` para pistas curadas con letra sincronizada.

## Reglas de negocio implementadas

1. **Anti-spam por tiempo**: una mesa no puede pedir otra canción hasta que pasen N segundos desde su último pedido (configurable, 60s por defecto).
2. **Máximo de pendientes por mesa**: evita que una mesa acapare la cola (3 por defecto).
3. **Cola con orden explícito**: reordenable por el DJ (subir/bajar).
4. **Solo una canción "cantando" a la vez**: al iniciar una nueva, la anterior se finaliza automáticamente y se otorgan puntos.
5. **Puntos por canción cantada**: acumulados por mesa (base para futuras competencias).

## Instalación

```powershell
cd "C:\Programa Karaoke\singpe"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Base de datos: PostgreSQL

El sistema usa PostgreSQL (no SQLite). Pasos:

1. Instala PostgreSQL si no lo tienes: https://www.postgresql.org/download/windows/
2. Crea la base de datos `singpe` (con `psql` o pgAdmin):
   ```sql
   CREATE DATABASE singpe;
   ```
3. Dile al sistema cómo conectarse. Lo más simple: crea un archivo
   `database_url.txt` en la raíz del proyecto (junto a `run.py`) con una sola línea:
   ```
   postgresql+psycopg2://postgres:TU_CONTRASEÑA@localhost:5432/singpe
   ```
   (o define la variable de entorno `DATABASE_URL` con el mismo valor).
   Sin ese archivo, por defecto intenta `postgres:postgres@localhost:5432/singpe`.

Las tablas se crean solas la primera vez que arranca el servidor.

## Búsqueda de canciones en YouTube (catálogo casi ilimitado)

El formulario de mesa deja escribir cualquier canción libremente, y además
puede buscar y enlazar un video real de YouTube para reproducirlo embebido
y automático en `/tv`. Para activar la búsqueda:

1. Ve a https://console.cloud.google.com/apis/credentials
2. Crea un proyecto (o usa uno existente) y habilita **"YouTube Data API v3"**.
3. Crea una **API key**.
4. Crea un archivo `youtube_api_key.txt` en la raíz del proyecto y pega la clave ahí
   (o define la variable de entorno `YOUTUBE_API_KEY`).

Sin la clave, la búsqueda simplemente queda desactivada y el cliente puede
seguir escribiendo el nombre de la canción a mano (el DJ la busca y reproduce
por su cuenta). La capa gratuita de esta API alcanza para ~100 búsquedas/día.

## Cargar una canción de demostración (sin necesidad de archivos con derechos de autor)

```powershell
python scripts\make_demo_song.py
```

Esto crea un tono sintético con letra sincronizada en
`karaoke_library/SingPe_Demo/Cancion_de_Prueba/`, solo para probar todo el flujo.

## Ejecutar el servidor

```powershell
python run.py
```

Abre `http://localhost:8000`.

- `/admin` → genera mesas + QR, edita las reglas, escanea la biblioteca de canciones.
- `/dj` → panel del DJ para controlar la cola.
- `/tv` → pantalla para proyectar en el local (reproductor + letras + próximos).
- `/mesa/{numero}` → lo que ve el cliente al escanear el QR de su mesa.

**Primeros pasos:**
1. Entra a `/admin`, genera por ejemplo 10 mesas (crea los QR automáticamente).
2. Ejecuta `python scripts\make_demo_song.py` y luego presiona "Escanear karaoke_library/" en `/admin`.
3. Abre `/tv` en la pantalla del local y `/dj` en el celular/laptop del DJ.
4. Abre `/mesa/1` (o escanea su QR) y pide la canción de prueba.

## Agregar tu propio catálogo de canciones

Crea una carpeta por canción dentro de `karaoke_library/`:

```
karaoke_library/
  Queen/
    Bohemian_Rhapsody/
      audio.mp3       (obligatorio: pista instrumental)
      video.mp4        (opcional: video de fondo, ya con el audio incluido)
      lyrics.lrc        (opcional: letra sincronizada, formato LRC estándar)
      cover.jpg         (opcional: portada)
      meta.json         (opcional: {"genero": "Rock", "tiene_voz_guia": true})
```

Luego entra a `/admin` y presiona **"Escanear karaoke_library/"**, o usa el
formulario de subida directo en la misma página para cargar audio/video/letra
sin tocar carpetas a mano.

Para generar tus propias pistas instrumentales y letras sincronizadas a partir
de canciones originales, se puede usar un pipeline de separación de voz con IA
(Demucs / UVR para quitar la voz, Whisper para transcribir y sincronizar la
letra). Eso queda fuera del MVP pero la carpeta `karaoke_library/` ya está
lista para recibir esos archivos apenas los generes.

## Configuración importante antes de imprimir los QR

Edita `backend/config.py` → `BASE_URL` con la IP o dominio real donde correrá
el servidor en el local (ej. `http://192.168.1.50:8000`), y vuelve a generar
los QR desde `/admin` para que apunten correctamente.

## Roadmap (post-MVP, ya pensado en la arquitectura)

- 🥊 Modo batalla entre mesas con votación del público.
- 🤖 Recomendador de canciones por IA ("quiero algo romántico").
- 🏆 Ranking / leaderboard de puntos en la pantalla TV.
- 📱 Empaquetar la web de mesa como PWA instalable (manifest + service worker).
