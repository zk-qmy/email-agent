import pytest
from starlette.testclient import TestClient
from backend.exceptions import AppError, error_to_dict, GlobalExceptionMiddleware


class TestAppError:
    def test_app_error_creation(self):
        error = AppError("Test error", status_code=400, error_id="abc12345")
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.error_id == "abc12345"

    def test_app_error_default_id(self):
        error = AppError("Test error")
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.error_id is not None
        assert len(error.error_id) == 8

    def test_app_error_str(self):
        error = AppError("Test error")
        assert str(error) == "Test error"


class TestErrorToDict:
    def test_error_to_dict_app_error(self):
        error = AppError("Test error", status_code=400, error_id="abc12345")
        result = error_to_dict(error, "abc12345")
        assert result["error"] == "AppError"
        assert result["error_id"] == "abc12345"
        assert result["message"] == "Test error"

    def test_error_to_dict_value_error(self):
        error = ValueError("Invalid value")
        result = error_to_dict(error, "def67890")
        assert result["error"] == "ValueError"
        assert result["error_id"] == "def67890"
        assert result["message"] == "Invalid value"

    def test_error_to_dict_generic_exception(self):
        error = RuntimeError("Unexpected")
        result = error_to_dict(error, "xyz11111")
        assert result["error"] == "RuntimeError"
        assert result["error_id"] == "xyz11111"
        assert result["message"] == "An unexpected error occurred"
        assert result["detail"] == "Unexpected"

    def test_error_to_dict_type_not_app_or_value(self):
        error = KeyError("Missing key")
        result = error_to_dict(error, "key22222")
        assert result["error"] == "KeyError"
        assert result["message"] == "An unexpected error occurred"
        assert result["detail"] == str(error)


class TestGlobalExceptionMiddleware:
    def test_middleware_catches_app_error(self):
        from fastapi import FastAPI, Request
        from starlette.responses import JSONResponse

        app = FastAPI()

        @app.get("/raise-app-error")
        def raise_app_error():
            raise AppError("App error test", status_code=400)

        app.add_middleware(GlobalExceptionMiddleware)

        client = TestClient(app)
        response = client.get("/raise-app-error")

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "AppError"
        assert "error_id" in data
        assert data["message"] == "App error test"

    def test_middleware_catches_generic_exception(self):
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()

        @app.get("/raise-generic-error")
        def raise_generic_error():
            raise RuntimeError("Generic error test")

        app.add_middleware(GlobalExceptionMiddleware)

        client = TestClient(app)
        response = client.get("/raise-generic-error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "RuntimeError"
        assert "error_id" in data
        assert data["message"] == "An unexpected error occurred"

    def test_middleware_passes_through(self):
        from fastapi import FastAPI
        from starlette.testclient import TestClient

        app = FastAPI()

        @app.get("/success")
        def success():
            return {"status": "ok"}

        app.add_middleware(GlobalExceptionMiddleware)

        client = TestClient(app)
        response = client.get("/success")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}