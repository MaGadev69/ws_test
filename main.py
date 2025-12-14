"""
Servidor WebSocket para comunicación entre recepción y odontólogo.
Ejemplo mínimo para probar la funcionalidad de notificación.
"""
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Dict, List


app = FastAPI()

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="."), name="static")

# Almacenar mensajes pendientes
pending_messages = {"recepcion": [], "odontologo": []}


@app.get("/recepcion.html")
async def get_recepcion():
    with open("recepcion.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content)


@app.get("/odontologo.html")
async def get_odontologo():
    with open("odontologo.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content)


# Almacenar conexiones WebSocket
recepcion_connections: List[WebSocket] = []
odontologo_connections: List[WebSocket] = []


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        if client_type == "recepcion":
            recepcion_connections.append(websocket)
            # Enviar mensajes pendientes para recepción
            for msg in pending_messages["recepcion"]:
                await websocket.send_text(msg)
            # Limpiar mensajes pendientes
            pending_messages["recepcion"].clear()
        elif client_type == "odontologo":
            odontologo_connections.append(websocket)
            # Enviar mensajes pendientes para odontólogo
            for msg in pending_messages["odontologo"]:
                await websocket.send_text(msg)
            # Limpiar mensajes pendientes
            pending_messages["odontologo"].clear()

    def disconnect(self, websocket: WebSocket, client_type: str):
        if client_type == "recepcion" and websocket in recepcion_connections:
            recepcion_connections.remove(websocket)
        elif client_type == "odontologo" and websocket in odontologo_connections:
            odontologo_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_recepcion(self, message: str):
        if recepcion_connections:
            for connection in recepcion_connections:
                await connection.send_text(message)
        else:
            # Almacenar mensaje para cuando se reconecte
            pending_messages["recepcion"].append(message)

    async def broadcast_to_odontologo(self, message: str):
        if odontologo_connections:
            for connection in odontologo_connections:
                await connection.send_text(message)
        else:
            # Almacenar mensaje para cuando se reconecte
            pending_messages["odontologo"].append(message)

    async def broadcast_to_all(self, message: str):
        for connection in recepcion_connections + odontologo_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_type: str):
    if client_type not in ["recepcion", "odontologo"]:
        await websocket.close(code=1008)  # HTTP 400 equivalent
        return

    await manager.connect(websocket, client_type)

    try:
        while True:
            try:
                # Recibir datos con timeout de 10 segundos
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                message_data = json.loads(data)

                # Retransmitir el mensaje al otro panel
                if message_data.get("to") == "odontologo":
                    await manager.broadcast_to_odontologo(data)
                elif message_data.get("to") == "recepcion":
                    await manager.broadcast_to_recepcion(data)

            except asyncio.TimeoutError:
                # Si no hay actividad en 10 segundos, se cierra la conexión
                await websocket.close(code=1000)  # Código 1000: cierre normal
                break

    except WebSocketDisconnect:
        pass  # Ya se maneja el cierre arriba
    finally:
        manager.disconnect(websocket, client_type)
        print(f"Cliente {client_type} desconectado (timeout o cierre normal)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)