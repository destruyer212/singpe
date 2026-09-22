# 🎤 SingPe — Sistema de gestión de karaoke para bares

Cada mesa pide canciones desde su celular escaneando un QR. El sistema aplica
reglas anti-spam, arma la cola en tiempo real, el DJ la controla (o ni
siquiera hace falta: avanza sola), y una pantalla en el local reproduce todo
automáticamente — video de YouTube o biblioteca propia, letra sincronizada,
voz de anuncios, efectos de sonido, votos del público en vivo y hasta
"batallas" entre mesas.

## Arquitectura

```
Cliente (celular, escanea QR)
        |
   frontend/  (HTML + JS + CSS, servidos por el backend — sin Node/npm)
        |
   backend/  FastAPI (Python) ---- WebSockets (tiempo real) ---- Panel DJ / Pantalla TV
        |
   PostgreSQL (mesas, canciones, cola, historial, votos, ranking)
        |
   karaoke_library/  (biblioteca propia opcional: audio, video, letras .lrc)
        |
   YouTube Data API   (catálogo prácticamente ilimitado de canciones)
        |
   edge-tts   (voz natural gratis para anuncios y avisos)
```

- **Backend**: FastAPI + SQLAlchemy + WebSockets, todo en `backend/`.
- **Base de datos**: PostgreSQL. Cadena de conexión configurable sin tocar código.
- **Frontend**: HTML servido por Jinja2 + JS puro + Tailwind (CDN), sin build step.
- **Tiempo real**: un único canal WebSocket (`/ws`) notifica a mesas, panel DJ
  y pantalla TV. Los mensajes llevan un `tipo` (`cola_actualizada`, `efecto`,
  `anuncio`) para que cada pantalla reaccione solo a lo que le importa.
- **Catálogo de canciones**: búsqueda en YouTube (millones de canciones,
  reproducidas embebidas en `/tv`, con reintento automático a otra versión si
  una está bloqueada) + biblioteca propia opcional en `karaoke_library/` para
  pistas curadas con letra sincronizada.
- **Voz**: `edge-tts` (voces neuronales gratis de Microsoft) para anuncios,
  avisos "sigues pronto" y resultados de batalla. Sin API key, sin costo.

## Estructura de carpetas

```
singpe/
  backend/
    main.py            punto de entrada de la app FastAPI
    config.py           configuración (rutas, DB, claves, BASE_URL)
    database.py          conexión a PostgreSQL (SQLAlchemy)
    models.py             tablas: Mesa, Cancion, Solicitud, Configuracion
    schemas.py              esquemas Pydantic (entrada/salida de la API)
    crud.py                   reglas de negocio (anti-spam, cola, votos, ranking)
    library.py                 escaneo/registro de karaoke_library/
    youtube.py                  búsqueda y verificación de título en YouTube
    qr.py                        generación de códigos QR por mesa
    tts.py                        voz natural (edge-tts) con caché en disco
    ws_manager.py                  WebSocket (tiempo real)
    routers/                        endpoints HTTP agrupados por área
      pages.py                        páginas HTML (/, /mesa, /dj, /tv, /admin)
      api_mesas.py                     API del cliente (buscar, pedir, votar)
      api_dj.py                         API del DJ (cola, soundboard, anuncios, ranking)
      api_admin.py                       API de administración (mesas, canciones, reglas)
      ws.py                               endpoint WebSocket /ws
  frontend/
    templates/            plantillas Jinja2 (una por pantalla)
    static/
      css/style.css          estilos propios y animaciones
      js/                      mesa.js, dj.js, tv.js, admin.js, lrc.js
      qr/                       códigos QR generados por mesa
      sfx/                       efectos de sonido del soundboard (.wav)
      tts_cache/                 audios de voz generados (caché, no se sube a git)
  karaoke_library/       biblioteca propia opcional (audio/video/letras)
  scripts/               utilidades de línea de comandos
  run.py                 arranca el servidor (uvicorn)
```

## Las 4 pantallas

### `/mesa/{numero}` — lo que ve el cliente al escanear el QR de su mesa
- Busca la canción escribiendo el nombre (busca en YouTube en vivo, mostrando
  resultados con miniatura) o simplemente la escribe libre si no la encuentra.
- Elige modo: **Karaoke (sin voz)** o **Con letra (con voz)** — la búsqueda
  cambia según el modo (instrumental puro vs. la canción normal).
- Puede pedirla **en dueto o grupo** (hasta 4 cantantes).
- Puede **retar a otra mesa** (dropdown con las mesas realmente activas).
- Puede dejar un **mensaje** que se lee en voz alta cuando suena su canción.
- Mientras su canción siga "en espera", puede **corregirla o eliminarla sin
  perder su turno** en la cola (no reinicia el contador anti-spam).
- Botón flotante **🔥** para votar por quien está cantando (aparece solo si
  es otra mesa la que canta).
- Reglas anti-spam visibles: burbuja con cuenta regresiva mientras espera.

### `/dj` — panel de control
- Tarjeta de "ahora sonando" con botón Finalizar, origen (YouTube / biblioteca
  / pedido libre), votos, mensaje y badge de reto si aplica.
- Cola con botones para reordenar (▲▼), iniciar (▶) o cancelar (✕).
- **🎛️ Soundboard**: 8 botones con efectos de sonido reales (aplausos, bocina
  de estadio, sirena, campana, redoble, buzzer, fanfarria) que disparan un
  sticker animado + sonido en la pantalla TV.
- **📢 Anuncio rápido**: texto que se lee en voz alta al instante en la TV.

### `/tv` — la pantalla que se proyecta en el local
- Un solo toque al empezar la noche ("Toca para iniciar la función") para
  desbloquear el audio del navegador — después de eso, **todo es automático**:
  arranca sola la primera canción apenas alguien pide, y avanca sola a la
  siguiente cuando una termina (o se cancela). El desbloqueo se recuerda en
  la pestaña, así un F5 accidental no lo vuelve a pedir.
- Reproduce el video de YouTube embebido con controles ocultos, o el
  audio/video de la biblioteca propia con letra sincronizada.
- Si un video de YouTube está bloqueado para reproducirse en el sitio,
  **prueba automáticamente otra versión** de la misma canción (subida por
  otro canal) antes de rendirse.
- Muestra el contador de **votos 🔥** en vivo junto al nombre del cantante.
- Banner especial **"⚔️ BATALLA"** cuando la canción es un reto entre mesas,
  con anuncio de voz al empezar y recuento de fuegos al terminar.
- Avisa por voz a la siguiente mesa en la fila: *"Mesa X, prepárate, sigues
  pronto"* (una sola vez por canción).
- Pantalla de reposo con QR/nombre del evento y **ranking de la noche** 🏆
  (top 3 con insignias "Más ovacionada" / "Maratónica").
- Recibe y muestra los efectos del soundboard y los anuncios del DJ.

### `/admin` — configuración del negocio
- Reglas del evento: nombre, segundos entre pedidos, máximo de pendientes,
  puntos por canción.
- Mesas: generar mesas + códigos QR, **capacidad** por mesa (12 personas por
  defecto, editable), **activar/desactivar** mesas.
- Biblioteca de canciones: escanear `karaoke_library/` o subir audio/video/
  letra directo desde un formulario.

## Reglas de negocio implementadas

1. **Anti-spam por tiempo**: una mesa no puede pedir otra canción hasta que
   pasen N segundos desde su último pedido (configurable, 60s por defecto).
2. **Máximo de pendientes por mesa**: evita que una mesa acapare la cola (3 por defecto).
3. **Cola con orden explícito**: reordenable por el DJ, y una mesa puede
   corregir/eliminar su propio pedido pendiente sin perder su lugar.
4. **Solo una canción "cantando" a la vez**: al iniciar una nueva, la
   anterior se finaliza automáticamente y se otorgan puntos.
5. **Puntos y votos por mesa**: acumulados para el ranking de la noche.
6. **Avance 100% automático**: la pantalla TV arranca y avanza la cola sola,
   sin necesitar que nadie la esté operando.

## Instalación

```powershell
cd "C:\Programa Karaoke\singpe"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Base de datos: PostgreSQL

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

Las tablas se crean solas la primera vez que arranca el servidor. Si el
esquema cambia (nuevas funciones), a veces hace falta un `ALTER TABLE` manual
— revisa los comentarios de migración en el historial de commits si migras
una base ya existente.

## Búsqueda de canciones en YouTube (catálogo casi ilimitado)

1. Ve a https://console.cloud.google.com/apis/credentials
2. Crea un proyecto (o usa uno existente) y habilita **"YouTube Data API v3"**.
3. Crea una **API key**.
4. Crea un archivo `youtube_api_key.txt` en la raíz del proyecto y pega la clave ahí
   (o define la variable de entorno `YOUTUBE_API_KEY`).

Sin la clave, la búsqueda simplemente queda desactivada y el cliente puede
seguir escribiendo el nombre de la canción a mano. La capa gratuita de esta
API alcanza para ~100 búsquedas/día.

## Voz natural para anuncios (gratis, sin configurar nada)

Los anuncios, avisos "sigues pronto" y resultados de batalla usan
[`edge-tts`](https://pypi.org/project/edge-tts/) — las mismas voces
neuronales gratuitas del "Leer en voz alta" de Microsoft Edge. No necesita
API key. La voz por defecto es `es-PE-AlexNeural` (peruana, con ritmo y tono
ligeramente elevados para sonar como animador de fiesta); se puede cambiar en
`backend/tts.py`. Los audios generados se cachean en
`frontend/static/tts_cache/` para no regenerar un texto repetido.

## Soundboard del DJ

Los efectos de `frontend/static/sfx/` son grabaciones reales (no sintéticas),
descargadas de freesoundslibrary.com bajo licencia CC BY 4.0 (uso libre con
atribución — ver `frontend/static/sfx/CREDITOS.txt`) y recortadas con ffmpeg
a duración de "stinger". Para regenerarlos o cambiarlos, `scripts/make_efectos.py`
tiene las URLs de origen (requiere `ffmpeg` instalado y en el PATH).

## Ejecutar el servidor

```powershell
python run.py
```

Abre `http://localhost:8000`.

**Primeros pasos:**
1. Entra a `/admin`, genera por ejemplo 10 mesas (crea los QR automáticamente).
2. Ejecuta `python scripts\make_demo_song.py` y luego presiona "Escanear karaoke_library/" en `/admin` (opcional, solo para probar sin canciones reales).
3. Abre `/tv` en la pantalla del local y toca "Iniciar función" una vez.
4. Abre `/dj` en el celular/laptop del DJ.
5. Abre `/mesa/1` (o escanea su QR) y pide una canción — de ahí en adelante casi todo corre solo.

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
formulario de subida directo en la misma página.

## Configuración importante antes de imprimir los QR

Edita `backend/config.py` → `BASE_URL` con la IP o dominio real donde correrá
el servidor en el local (ej. `http://192.168.1.50:8000`), y vuelve a generar
los QR desde `/admin` para que apunten correctamente.

## Desplegar fuera de tu computadora

El sistema necesita un servidor que pueda correr un proceso Python
persistente + WebSockets + PostgreSQL — **no funciona en hosting compartido
tipo Hostinger básico**. Sí funciona en un **VPS** (Hostinger VPS, DigitalOcean,
Railway, Render, etc.), donde se instala igual que en local.

## Roadmap pendiente

- 💡 Integración con luces (Hue/DMX) — falta definir el equipo real del local.
- 🤖 Recomendador de canciones por IA ("quiero algo romántico").
- 📱 Empaquetar la web de mesa como PWA instalable (manifest + service worker).
- 🚀 Despliegue en un servidor real (VPS) para usarlo fuera de la red local.
