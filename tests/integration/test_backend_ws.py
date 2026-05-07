import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio


class TestBackendWebSocket:
    @pytest.mark.asyncio
    async def test_ws_connect(self):
        from backend.routes.ws_notifications import ConnectionManager
        from fastapi import WebSocket

        cm = ConnectionManager()
        mock_ws = MagicMock(spec=WebSocket)

        await cm.connect(1, mock_ws)

        assert 1 in cm._connections

    @pytest.mark.asyncio
    async def test_ws_disconnect(self):
        from backend.routes.ws_notifications import ConnectionManager
        from fastapi import WebSocket

        cm = ConnectionManager()
        mock_ws = MagicMock(spec=WebSocket)

        await cm.connect(1, mock_ws)
        assert 1 in cm._connections

        await cm.disconnect(1)

        assert 1 not in cm._connections

    @pytest.mark.asyncio
    async def test_ws_send_to_disconnected(self):
        from backend.routes.ws_notifications import ConnectionManager

        cm = ConnectionManager()
        await cm.send_to_user(999, {"event": "test"})

    @pytest.mark.asyncio
    async def test_ws_concurrent_connect(self):
        from backend.routes.ws_notifications import ConnectionManager
        from fastapi import WebSocket

        cm = ConnectionManager()
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws2 = MagicMock(spec=WebSocket)

        await cm.connect(1, mock_ws1)
        await cm.connect(1, mock_ws2)

    @pytest.mark.asyncio
    async def test_ws_shutdown(self):
        from backend.routes.ws_notifications import ConnectionManager
        from fastapi import WebSocket

        cm = ConnectionManager()
        mock_ws = MagicMock(spec=WebSocket)
        mock_ws.close = AsyncMock()

        await cm.connect(1, mock_ws)
        await cm.shutdown()

        mock_ws.close.assert_called_once()


class TestConnectionManagerEdgeCases:
    @pytest.mark.asyncio
    async def test_connect_idempotent(self):
        from backend.routes.ws_notifications import ConnectionManager
        from fastapi import WebSocket

        cm = ConnectionManager()
        mock_ws = MagicMock(spec=WebSocket)

        await cm.connect(1, mock_ws)
        await cm.connect(1, mock_ws)

        assert 1 in cm._connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self):
        from backend.routes.ws_notifications import ConnectionManager

        cm = ConnectionManager()
        await cm.disconnect(999)