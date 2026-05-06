import pytest


class TestBackendHealth:
    def test_backend_health(self, app):
        response = app.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_backend_health_json(self, app):
        response = app.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestAgentHealth:
    def test_agent_health(self, agent_app):
        response = agent_app.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_agent_health_json(self, agent_app):
        response = agent_app.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestRoot:
    def test_backend_root(self, app):
        response = app.get("/")
        assert response.status_code in [200, 404]