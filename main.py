"""
Servidor WebSocket para comunicación entre recepción y odontólogo.
Optimizado para Dokploy.
"""
import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List


app = FastAPI()

# CORS para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta según tu dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="."), name="static")

# Almacenar mensajes pendientes
pending_messages = {"recepcion": [], "odontologo": []}


# Health check para Dokploy
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "websocket"}


@app.get("/")
async def root():
    return {"message": "WebSocket Server Running", "endpoints": ["/recepcion.html", "/odontologo.html"]}


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
        # Limit one connection per client type per server instance
        self.client_type_connections: Dict[str, WebSocket] = {}  # "recepcion" -> WebSocket, "odontologo" -> WebSocket

    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()

        # Check if there's already a connection for this client type
        # If so, remove the old connection to prevent duplicates
        if client_type in self.client_type_connections:
            old_connection = self.client_type_connections[client_type]
            # Try to close the old connection gracefully
            try:
                await old_connection.close(code=1000)  # Normal closure
            except:
                pass  # Connection might already be closed

        # Store the new connection
        self.client_type_connections[client_type] = websocket

        if client_type == "recepcion":
            # Remove any existing recepcion connections in the list
            recepcion_connections.clear()
            recepcion_connections.append(websocket)
            # Enviar mensajes pendientes para recepción
            for msg in pending_messages["recepcion"]:
                await websocket.send_text(msg)
            # Limpiar mensajes pendientes
            pending_messages["recepcion"].clear()
        elif client_type == "odontologo":
            # Remove any existing odontologo connections in the list
            odontologo_connections.clear()
            odontologo_connections.append(websocket)
            # Enviar mensajes pendientes para odontólogo
            for msg in pending_messages["odontologo"]:
                await websocket.send_text(msg)
            # Limpiar mensajes pendientes
            pending_messages["odontologo"].clear()

    def disconnect(self, websocket: WebSocket, client_type: str):
        # Remove from client type mapping if it matches
        if client_type in self.client_type_connections and self.client_type_connections[client_type] == websocket:
            del self.client_type_connections[client_type]

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
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, client_type)
    print(f"Cliente {client_type} conectado")

    try:
        while True:
            try:
                # Timeout más largo para producción (60 segundos)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message_data = json.loads(data)

                # Retransmitir el mensaje al otro panel
                if message_data.get("to") == "odontologo":
                    await manager.broadcast_to_odontologo(data)
                elif message_data.get("to") == "recepcion":
                    await manager.broadcast_to_recepcion(data)

            except asyncio.TimeoutError:
                # Enviar ping para mantener la conexión viva
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error en WebSocket: {e}")
    finally:
        manager.disconnect(websocket, client_type)
        print(f"Cliente {client_type} desconectado")


if __name__ == "__main__":
    import uvicorn
    # Usar variable de entorno PORT si existe (para Dokploy)
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)