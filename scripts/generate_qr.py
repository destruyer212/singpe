"""Genera mesas y sus códigos QR desde la línea de comandos, sin abrir /admin.
Uso: python scripts/generate_qr.py 20    (crea las mesas 1..20)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import Base, SessionLocal, engine
from backend import crud
from backend.qr import generar_qr_mesa

Base.metadata.create_all(bind=engine)


def main():
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    db = SessionLocal()
    try:
        for numero in range(1, cantidad + 1):
            crud.get_or_create_mesa(db, numero)
            ruta = generar_qr_mesa(numero)
            print(f"Mesa {numero}: {ruta}")
    finally:
        db.close()
    print(f"\n{cantidad} mesas listas. Los QR están en frontend/static/qr/")


if __name__ == "__main__":
    main()
