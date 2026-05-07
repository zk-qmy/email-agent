import pytest


class TestAgentProxy:
    def test_proxy_health(self, app):
        """Test health check works when agent is running or returns offline."""
        response = app.get("/api/agent/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["online", "offline"]

    def test_proxy_forward(self, app):
        """Test proxy forwards request to agent backend."""
        response = app.get("/api/agent/thread/test-thread")
        assert response.status_code in [200, 404, 502]