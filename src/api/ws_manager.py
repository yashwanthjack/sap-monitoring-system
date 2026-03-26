import json
import asyncio
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

def trigger_dashboard_event(event_type: str, data: dict = None, message: str = ""):
    payload = {
        "type": event_type, 
        "message": message,
        "data": data or {}
    }
    msg_str = json.dumps(payload)
    # Run async function in sync context safely
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(manager.broadcast(msg_str))
        else:
            loop.run_until_complete(manager.broadcast(msg_str))
    except RuntimeError:
        # If no event loop exists in this thread, create one briefly
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.broadcast(msg_str))
        except Exception:
            pass
