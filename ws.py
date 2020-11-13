from typing import List
from collections import Counter
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

with open("ws.html") as f:
    user = "\n".join(f.readlines())

with open("admin.html") as f:
    admin = "\n".join(f.readlines())


@app.get("/")
async def get():
    return HTMLResponse(user)


@app.get("/admin")
async def get():
    return HTMLResponse(admin)


database = {}
def show_results():
    c = Counter(database.values())
    return str(dict(c.most_common()))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    global database
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data in ["VERT", "ROSE"]:
                database[client_id] = data
                print(data, database)
                await manager.send_personal_message(data, websocket)
                await manager.broadcast(show_results())
            elif data == "RESULTS":
                await manager.broadcast(show_results())
            elif data == "CLEAR":
                await manager.broadcast("CLEAR")
                database = {}

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        del database[client_id]
        # await manager.broadcast(f"Client #{client_id} left the chat")