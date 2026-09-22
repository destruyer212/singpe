import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Mantiene las conexiones WebSocket activas (panel DJ, pantalla TV, mesas)
    y transmite eventos en tiempo real a todos los clientes conectados."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, tipo: str, data: Any = None):
        payload = json.dumps({"tipo": tipo, "data": data}, default=str)
        muertos = []
        for connection in self.active:
            try:
                await connection.send_text(payload)
            except Exception:
                muertos.append(connection)
        for m in muertos:
            self.disconnect(m)


manager = ConnectionManager()
