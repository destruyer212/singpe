import os
import re
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"
OUT_DIR = BASE_DIR / "frontend_vercel_dist"

API_BASE = os.environ.get("SINGPE_API_BASE", "https://singpe.onrender.com").rstrip("/")


def read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def extract_block(source: str, block: str) -> str:
    match = re.search(r"{% block " + re.escape(block) + r" %}(.*?){% endblock %}", source, re.S)
    return match.group(1).strip() if match else ""


def shell(title: str, content: str, head: str = "", extra_scripts: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      theme: {{
        extend: {{
          colors: {{
            neon: {{ pink: '#ff2fb0', purple: '#9333ea', cyan: '#22d3ee', yellow: '#fde047' }},
          }},
        }},
      }},
    }};
    window.SINGPE_API_BASE = "{API_BASE}";
  </script>
  <link rel="icon" type="image/png" href="/static/img/singpe-app-icon-white.png" />
  <link rel="manifest" href="/static/manifest.webmanifest" />
  <meta name="theme-color" content="#0b0620" />
  <link rel="stylesheet" href="/static/css/style.css" />
  <script src="/static/js/runtime.js"></script>
  {head}
</head>
<body class="min-h-screen bg-gradient-to-br from-[#0b0620] via-[#170a2e] to-[#1a0b30] text-white">
  {content}
  {extra_scripts}
</body>
</html>
"""


def clean_content(name: str) -> tuple[str, str]:
    source = read_template(name)
    return extract_block(source, "content"), extract_block(source, "head")


def write_page(name: str, title: str, content: str, head: str = "", extra_scripts: str = "") -> None:
    (OUT_DIR / name).write_text(shell(title, content, head, extra_scripts), encoding="utf-8")


def copy_static() -> None:
    target = OUT_DIR / "static"
    if target.exists():
        shutil.rmtree(target)

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {"qr", "tts_cache", "__pycache__"}.intersection(names)

    shutil.copytree(STATIC_DIR, target, ignore=ignore)


def build_index() -> None:
    content = """
<div class="max-w-3xl mx-auto px-6 py-16 text-center">
  <div class="mx-auto mb-5 w-full max-w-md rounded-[2rem] bg-white p-5 shadow-2xl shadow-pink-950/40">
    <img src="/static/img/singpe-logo-program-white.png" alt="SingPe" class="w-full" />
  </div>
  <p class="text-white/60 mb-10">Sistema de gestión de karaoke — <span id="evento-nombre">SingPe Karaoke</span></p>

  <div class="grid sm:grid-cols-3 gap-4 mb-12">
    <a href="/dj" class="glass rounded-2xl p-6 hover:bg-white/10 transition">
      <div class="text-4xl mb-2">🎧</div>
      <div class="font-bold">Panel DJ</div>
      <div class="text-sm text-white/50">Controlar la cola</div>
    </a>
    <a href="/tv" class="glass rounded-2xl p-6 hover:bg-white/10 transition">
      <div class="text-4xl mb-2">📺</div>
      <div class="font-bold">Pantalla TV</div>
      <div class="text-sm text-white/50">Proyectar en el local</div>
    </a>
    <a href="/admin" class="glass rounded-2xl p-6 hover:bg-white/10 transition">
      <div class="text-4xl mb-2">⚙️</div>
      <div class="font-bold">Administración</div>
      <div class="text-sm text-white/50">Mesas, canciones, reglas</div>
    </a>
  </div>

  <h2 class="text-lg font-semibold text-white/70 mb-3">Mesas registradas</h2>
  <div id="mesas-lista" class="hidden flex flex-wrap gap-2 justify-center"></div>
  <p id="mesas-vacias" class="text-white/40 text-sm">Aún no hay mesas. Ve a <a href="/admin" class="underline">Administración</a> para generarlas junto con sus códigos QR.</p>
</div>
"""
    write_page("index.html", "SingPe Karaoke", content, extra_scripts='<script src="/static/js/index.js"></script>')


def build_from_template(template: str, output: str, title: str) -> None:
    content, head = clean_content(template)
    content = content.replace("{{ config.nombre_evento }}", '<span class="evento-nombre">SingPe Karaoke</span>')
    content = content.replace("{{ mesa.numero }}", '<span class="mesa-numero-text">1</span>')
    content = re.sub(
        r'<script src="/static/js/mesa\.js"[^>]*></script>',
        '<script src="/static/js/mesa.js"></script>',
        content,
    )
    content = re.sub(r"{%.*?%}", "", content, flags=re.S)
    content = re.sub(r"{{.*?}}", "", content, flags=re.S)
    write_page(output, title, content, head, extra_scripts='<script src="/static/js/static-config.js"></script>')


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    copy_static()
    build_index()
    build_from_template("mesa.html", "mesa.html", "Mesa · SingPe")
    build_from_template("dj.html", "dj.html", "Panel DJ · SingPe")
    build_from_template("tv.html", "tv.html", "Pantalla · SingPe")
    build_from_template("admin.html", "admin.html", "Administración · SingPe")
    print(f"Frontend de Vercel generado en {OUT_DIR}")


if __name__ == "__main__":
    main()
