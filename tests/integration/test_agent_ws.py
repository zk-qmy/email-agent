import pytest
from unittest.mock import patch, MagicMock


class TestAgentWebSocket:
    def test_ws_connect(self):
        from agent.services.agent_service import AgentService

        service = AgentService()
        mock_ws = MagicMock()

        service.add_websocket(1, mock_ws)

        from agent.services.agent_service import ws_connections
        assert 1 in ws_connections
        assert mock_ws in ws_connections[1]

    def test_ws_remove(self):
        from agent.services.agent_service import AgentService
        from agent.services.agent_service import ws_connections

        ws_connections.clear()

        service = AgentService()
        mock_ws = MagicMock()

        service.add_websocket(1, mock_ws)
        service.remove_websocket(1, mock_ws)

        assert 1 not in ws_connections or len(ws_connections[1]) == 0


class TestAgentWebSocketEdgeCases:
    def test_ws_duplicate_connection(self):
        from agent.services.agent_service import AgentService
        from agent.services.agent_service import ws_connections

        ws_connections.clear()

        service = AgentService()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        service.add_websocket(1, mock_ws1)
        service.add_websocket(1, mock_ws2)

        assert 1 in ws_connections

    def test_ws_remove_nonexistent(self):
        from agent.services.agent_service import AgentService
        from agent.services.agent_service import ws_connections

        ws_connections.clear()

        service = AgentService()
        mock_ws = MagicMock()

        service.remove_websocket(1, mock_ws)

        assert 1 not in ws_connections

    def test_ws_multiple_users(self):
        from agent.services.agent_service import AgentService
        from agent.services.agent_service import ws_connections

        ws_connections.clear()

        service = AgentService()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        service.add_websocket(1, mock_ws1)
        service.add_websocket(2, mock_ws2)

        assert 1 in ws_connections
        assert 2 in ws_connections