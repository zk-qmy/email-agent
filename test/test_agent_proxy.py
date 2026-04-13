import pytest
from unittest.mock import patch, AsyncMock


class TestAgentHealth:
    def test_health_online(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value = mock_async_client

            response = client.get("/api/agent/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "online"

    def test_health_offline(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value.get.side_effect = Exception(
                "Connection error"
            )
            mock_client.return_value = mock_async_client

            response = client.get("/api/agent/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "offline"


class Mock:
    pass


class TestAgentProxy:
    def test_proxy_get(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b'{"status": "ok"}'
            mock_response.headers = {"content-type": "application/json"}

            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value.request.return_value = (
                mock_response
            )
            mock_client.return_value = mock_async_client

            response = client.get("/api/agent/test")
            assert response.status_code == 200

    def test_proxy_post(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.content = b'{"result": "created"}'
            mock_response.headers = {"content-type": "application/json"}

            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value.request.return_value = (
                mock_response
            )
            mock_client.return_value = mock_async_client

            response = client.post("/api/agent/test", json={"key": "value"})
            assert response.status_code == 201

    def test_proxy_connect_error(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            from httpx import ConnectError

            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value.request.side_effect = (
                ConnectError("Connection failed")
            )
            mock_client.return_value = mock_async_client

            response = client.get("/api/agent/test")
            assert response.status_code == 502

    def test_proxy_read_timeout(self, client):
        with patch("httpx.AsyncClient") as mock_client:
            from httpx import ReadTimeout

            mock_async_client = AsyncMock()
            mock_async_client.__aenter__.return_value.request.side_effect = ReadTimeout(
                "Timeout"
            )
            mock_client.return_value = mock_async_client

            response = client.get("/api/agent/test")
            assert response.status_code == 502
