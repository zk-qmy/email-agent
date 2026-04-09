import asyncio
import json
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[int, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections[user_id] = websocket
        print(f"[ws_manager] Client connected: user_id={user_id}")

    async def disconnect(self, user_id: int):
        async with self._lock:
            if user_id in self._connections:
                del self._connections[user_id]
        print(f"[ws_manager] Client disconnected: user_id={user_id}")

    async def send_to_user(self, user_id: int, event: dict):
        async with self._lock:
            websocket = self._connections.get(user_id)

        if websocket:
            try:
                await websocket.send_json(event)
            except Exception as e:
                print(f"[ws_manager] Send failed for user {user_id}: {e}")
                await self.disconnect(user_id)

    async def shutdown(self):
        async with self._lock:
            for ws in list(self._connections.values()):
                try:
                    await ws.close()
                except Exception:
                    pass
            self._connections.clear()


connection_manager = ConnectionManager()


@router.websocket("/ws/push/{user_id}")
async def websocket_push(user_id: int, websocket: WebSocket):
    await connection_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await connection_manager.disconnect(user_id)
    except Exception:
        await connection_manager.disconnect(user_id)
