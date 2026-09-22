import qrcode

from backend.config import BASE_URL, QR_DIR


def generar_qr_mesa(numero: int) -> str:
    """Genera (o regenera) el PNG del QR de una mesa y devuelve su ruta pública."""
    url = f"{BASE_URL}/mesa/{numero}"
    img = qrcode.make(url)
    nombre_archivo = f"mesa_{numero}.png"
    img.save(QR_DIR / nombre_archivo)
    return f"/static/qr/{nombre_archivo}"
