import os
import asyncio
import websockets
from typing import Optional, Callable, Awaitable, Any
import httpx

EMAIL_BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://localhost:5001")
WS_BACKEND_URL = os.getenv("WS_BACKEND_URL", "ws://localhost:5001")
MAX_RECONNECT_DELAY = 60
INITIAL_RECONNECT_DELAY = 1


class BackendWSClient:
    def __init__(self):
        self._connections: dict[int, Any] = {}
        self._listeners: dict[int, asyncio.Queue] = {}
        self._push_handler: Optional[Callable[[int, dict], Awaitable[None]]] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._running = False
        self._reconnect_attempts: dict[int, int] = {}

    def set_push_handler(self, handler: Callable[[int, dict], Awaitable[None]]):
        self._push_handler = handler

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self):
        self._running = False
        for ws in list(self._connections.values()):
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def connect(self, user_id: int) -> bool:
        if user_id in self._connections:
            try:
                ws = self._connections[user_id]
                await ws.ping()
                return True
            except Exception:
                await self._disconnect(user_id)

        delay = INITIAL_RECONNECT_DELAY
        attempt = self._reconnect_attempts.get(user_id, 0)

        for _ in range(3):
            try:
                ws_url = f"{WS_BACKEND_URL}/ws/push/{user_id}"
                ws = await websockets.connect(ws_url, ping_interval=20, ping_timeout=10)
                self._connections[user_id] = ws
                self._reconnect_attempts[user_id] = 0
                asyncio.create_task(self._listen_loop(user_id, ws))
                return True
            except Exception as e:
                print(f"[ws_client] Connect attempt {attempt + 1} failed for user {user_id}: {e}")
                await asyncio.sleep(delay)
                delay = min(delay * 2, MAX_RECONNECT_DELAY)
                attempt += 1

        self._reconnect_attempts[user_id] = attempt
        return False

    async def _disconnect(self, user_id: int):
        if user_id in self._connections:
            try:
                await self._connections[user_id].close()
            except Exception:
                pass
            del self._connections[user_id]
        if user_id in self._listeners:
            del self._listeners[user_id]

    async def disconnect(self, user_id: int):
        await self._disconnect(user_id)

    async def _listen_loop(self, user_id: int, ws: Any):
        try:
            while self._running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    if isinstance(msg, bytes):
                        msg = msg.decode()
                    if isinstance(msg, str):
                        import json
                        event = json.loads(msg)
                    else:
                        event = msg
                    if event and self._push_handler:
                        await self._push_handler(user_id, event)
                except asyncio.TimeoutError:
                    try:
                        await ws.ping()
                    except Exception:
                        break
                except websockets.ConnectionClosed:
                    break
                except Exception as e:
                    print(f"[ws_client] Listen error user {user_id}: {e}")
                    break
        except Exception as e:
            print(f"[ws_client] Listen loop exited user {user_id}: {e}")
        finally:
            await self._disconnect(user_id)
            if self._running:
                asyncio.create_task(self._reconnect(user_id))

    async def _reconnect(self, user_id: int):
        await asyncio.sleep(INITIAL_RECONNECT_DELAY)
        if self._running and user_id not in self._connections:
            success = await self.connect(user_id)
            if not success:
                print(f"[ws_client] Reconnect failed for user {user_id}, will retry later")

    async def send(self, user_id: int, event: dict):
        ws = self._connections.get(user_id)
        if ws:
            try:
                import json
                await ws.send(json.dumps(event))
            except Exception as e:
                print(f"[ws_client] Send failed for user {user_id}: {e}")

    def is_connected(self, user_id: int) -> bool:
        return user_id in self._connections


backend_ws_client = BackendWSClient()
