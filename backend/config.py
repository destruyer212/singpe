"""Configuración global del sistema SingPe Karaoke."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR / "static"
YOUTUBE_API_KEY_FILE = BASE_DIR / "youtube_api_key.txt"
DATABASE_URL_FILE = BASE_DIR / "database_url.txt"
DATA_DIR = Path(os.environ["SINGPE_DATA_DIR"]) if os.environ.get("SINGPE_DATA_DIR") else None

if DATA_DIR:
    LIBRARY_DIR = DATA_DIR / "karaoke_library"
    QR_DIR = DATA_DIR / "qr"
    TTS_CACHE_DIR = DATA_DIR / "tts_cache"
else:
    LIBRARY_DIR = BASE_DIR / "karaoke_library"
    QR_DIR = STATIC_DIR / "qr"
    TTS_CACHE_DIR = STATIC_DIR / "tts_cache"


def _cargar_database_url() -> str:
    """Busca la cadena de conexión a PostgreSQL primero en la variable de
    entorno DATABASE_URL y luego en database_url.txt (mismo patrón que la
    API key de YouTube: fácil de pegar sin tocar código)."""
    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url:
        if env_url.startswith("postgres://"):
            return env_url.replace("postgres://", "postgresql+psycopg2://", 1)
        if env_url.startswith("postgresql://"):
            return env_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return env_url
    if DATABASE_URL_FILE.exists():
        archivo_url = DATABASE_URL_FILE.read_text(encoding="utf-8").strip()
        if archivo_url:
            return archivo_url
    # Valor por defecto para desarrollo local: base "singpe" en un Postgres
    # instalado localmente con el usuario/clave por defecto "postgres".
    return "postgresql+psycopg2://postgres:postgres@localhost:5432/singpe"


DATABASE_URL = _cargar_database_url()


def _cargar_youtube_api_key() -> str:
    """Busca la API key de YouTube primero en la variable de entorno
    YOUTUBE_API_KEY y si no, en un archivo local youtube_api_key.txt
    (más cómodo para un dueño de bar no técnico: solo pega la clave ahí)."""
    env_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if env_key:
        return env_key
    if YOUTUBE_API_KEY_FILE.exists():
        return YOUTUBE_API_KEY_FILE.read_text(encoding="utf-8").strip()
    return ""


# Necesaria para buscar y reproducir el catálogo completo de YouTube
# (millones de canciones) en vez de depender solo de karaoke_library/.
# Obtenerla en https://console.cloud.google.com/apis/credentials
# (habilitar "YouTube Data API v3") y pegarla en youtube_api_key.txt.
YOUTUBE_API_KEY = _cargar_youtube_api_key()

# URL base usada para generar los códigos QR de cada mesa.
# En Render se toma automáticamente de BASE_URL, por ejemplo:
# https://singpe.onrender.com
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")

# Reglas de negocio por defecto (editables luego desde /admin).
SEGUNDOS_ENTRE_PEDIDOS = 60
MAX_PENDIENTES_POR_MESA = 3
PUNTOS_POR_CANCION = 10

LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
QR_DIR.mkdir(parents=True, exist_ok=True)
TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
