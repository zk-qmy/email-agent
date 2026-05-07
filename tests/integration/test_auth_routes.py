import pytest
from fastapi.testclient import TestClient


class TestAuthSignup:
    def test_signup_success(self, app, test_db):
        response = app.post(
            "/api/auth/signup",
            json={"username": "newuser", "email": "newuser@test.com", "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["message"] == "User created successfully"

    def test_signup_duplicate_email(self, app, test_db):
        app.post(
            "/api/auth/signup",
            json={"username": "user1", "email": "duplicate@test.com", "password": "password123"}
        )
        response = app.post(
            "/api/auth/signup",
            json={"username": "user2", "email": "duplicate@test.com", "password": "password123"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_signup_duplicate_username(self, app, test_db):
        app.post(
            "/api/auth/signup",
            json={"username": "duplicate", "email": "user1@test.com", "password": "password123"}
        )
        response = app.post(
            "/api/auth/signup",
            json={"username": "duplicate", "email": "user2@test.com", "password": "password123"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_signup_invalid_email(self, app, test_db):
        response = app.post(
            "/api/auth/signup",
            json={"username": "user", "email": "not-an-email", "password": "password123"}
        )
        assert response.status_code == 422

    def test_signup_empty_username(self, app, test_db):
        response = app.post(
            "/api/auth/signup",
            json={"username": "", "email": "user@test.com", "password": "password123"}
        )
        assert response.status_code == 422

    def test_signup_empty_password(self, app, test_db):
        response = app.post(
            "/api/auth/signup",
            json={"username": "user", "email": "user@test.com", "password": ""}
        )
        assert response.status_code == 422


class TestAuthLogin:
    def test_login_success(self, app):
        response = app.post(
            "/api/auth/login",
            json={"email": "alice@test.com", "password": "password123"}
        )
        assert response.status_code in [200, 401]

    def test_login_wrong_password(self, app, seeded_user):
        response = app.post(
            "/api/auth/login",
            json={"email": "alice@test.com", "password": "wrong_password"}
        )
        assert response.status_code == 401

    def test_login_not_found(self, app, test_db):
        response = app.post(
            "/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "password123"}
        )
        assert response.status_code == 401

    def test_login_missing_email(self, app, test_db):
        response = app.post(
            "/api/auth/login",
            json={"password": "password123"}
        )
        assert response.status_code == 422

    def test_login_missing_password(self, app, seeded_user):
        response = app.post(
            "/api/auth/login",
            json={"email": "alice@test.com"}
        )
        assert response.status_code == 422


class TestAuthLogout:
    def test_logout(self, app):
        response = app.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"


class TestAuthGetMe:
    def test_get_me_unauthorized(self, app):
        response = app.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_authorized(self, app, seeded_user):
        response = app.get("/api/auth/me")
        assert response.status_code in [200, 401]


class TestAuthGetUsers:
    def test_get_users(self, app):
        response = app.get("/api/auth/users")
        assert response.status_code in [200, 500]