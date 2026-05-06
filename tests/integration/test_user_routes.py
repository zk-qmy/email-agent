import pytest
from fastapi.testclient import TestClient


class TestGetUser:
    def test_get_user(self, app, seeded_user):
        response = app.get(f"/api/auth/users/{seeded_user['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "alice"

    def test_get_user_not_found(self, app):
        response = app.get("/api/auth/users/99999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestUpdateUser:
    def test_update_user(self, app, seeded_user):
        response = app.put(
            f"/api/auth/users/{seeded_user['id']}",
            json={"username": "new_username"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "new_username"

    def test_update_user_partial(self, app, seeded_user):
        from backend.services.mail_service import MailService
        from backend.models import User
        session = MailService._get_session(None)
        user = session.query(User).filter(User.id == seeded_user["id"]).first()
        original_email = user.email
        session.close()

        response = app.put(
            f"/api/auth/users/{seeded_user['id']}",
            json={"username": "alice"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == original_email

    def test_update_user_duplicate(self, app, seeded_user, test_db):
        from backend.services.mail_service import MailService
        from backend.models import User

        session = test_db()
        user = User(
            username="bob",
            email="bob@test.com",
            password_hash="pbkdf2:sha256:260000$test$hash",
        )
        session.add(user)
        session.commit()
        session.close()

        response = app.put(
            f"/api/auth/users/{seeded_user['id']}",
            json={"username": "bob"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_user_not_found(self, app):
        response = app.put(
            "/api/auth/users/99999",
            json={"username": "newuser"}
        )
        assert response.status_code in [400, 404, 500]


class TestDeleteUser:
    def test_delete_user(self, app, seeded_user):
        response = app.delete(f"/api/auth/users/{seeded_user['id']}")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_user_not_found(self, app):
        response = app.delete("/api/auth/users/99999")
        assert response.status_code == 404


class TestSearchUsers:
    def test_search_users(self, app, seeded_user):
        response = app.get(f"/api/auth/search-users?q=alice")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 1

    def test_search_users_empty_query(self, app):
        response = app.get("/api/auth/search-users?q=")
        assert response.status_code == 422

    def test_search_users_no_results(self, app):
        response = app.get("/api/auth/search-users?q=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["users"] == []

    def test_search_users_partial(self, app, seeded_user):
        response = app.get("/api/auth/search-users?q=ali")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1

    def test_search_users_email(self, app, seeded_user):
        response = app.get("/api/auth/search-users?q=alice@test.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1