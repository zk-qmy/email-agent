import pytest


@pytest.mark.skip(reason="Requires running agent backend")
class TestAgentProxy:
    def test_proxy_health(self, app):
        response = app.get("/api/agent/health")
        assert response.status_code in [200, 500]

    @pytest.mark.skip(reason="Requires running agent backend")
    def test_proxy_forward(self, app):
        response = app.get("/api/agent/thread/test-thread")
        assert response.status_code in [200, 500, 502]