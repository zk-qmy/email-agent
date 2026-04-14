import pytest


class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/api/auth/signup",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["message"] == "User created successfully"

    def test_signup_duplicate_username(self, client, test_users):
        response = client.post(
            "/api/auth/signup",
            json={
                "username": "alice",
                "email": "different@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_signup_duplicate_email(self, client, test_users):
        response = client.post(
            "/api/auth/signup",
            json={
                "username": "different",
                "email": "alice@test.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestLogin:
    def test_login_success(self, client, test_users):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "alice@test.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_users["alice"]["user_id"]
        assert data["username"] == "alice"
        assert data["email"] == "alice@test.com"

    def test_login_invalid_email(self, client, test_users):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_invalid_password(self, client, test_users):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "alice@test.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


class TestGetUsers:
    def test_get_users(self, client, test_users):
        response = client.get("/api/auth/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert len(data["users"]) == 2


class TestGetUser:
    def test_get_user_found(self, client, test_users):
        user_id = test_users["alice"]["user_id"]
        response = client.get(f"/api/auth/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "alice"
        assert data["user"]["email"] == "alice@test.com"

    def test_get_user_not_found(self, client, test_users):
        response = client.get("/api/auth/users/9999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class TestUpdateUser:
    def test_update_username(self, client, test_users):
        user_id = test_users["alice"]["user_id"]
        response = client.put(
            f"/api/auth/users/{user_id}",
            json={"username": "alice_updated"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "alice_updated"

    def test_update_email(self, client, test_users):
        user_id = test_users["alice"]["user_id"]
        response = client.put(
            f"/api/auth/users/{user_id}",
            json={"email": "alice_new@test.com"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["email"] == "alice_new@test.com"

    def test_update_password(self, client, test_users):
        user_id = test_users["alice"]["user_id"]
        response = client.put(
            f"/api/auth/users/{user_id}",
            json={"password": "newpassword123"},
        )
        assert response.status_code == 200

    def test_update_duplicate_username(self, client, test_users):
        alice_id = test_users["alice"]["user_id"]
        response = client.put(
            f"/api/auth/users/{alice_id}",
            json={"username": "bob"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_not_found(self, client, test_users):
        response = client.put(
            "/api/auth/users/9999",
            json={"username": "nonexistent"},
        )
        assert response.status_code == 400
        assert "User not found" in response.json()["detail"]


class TestDeleteUser:
    def test_delete_user(self, client, test_users):
        user_id = test_users["alice"]["user_id"]
        response = client.delete(f"/api/auth/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        response = client.get(f"/api/auth/users/{user_id}")
        assert response.status_code == 404

    def test_delete_user_not_found(self, client, test_users):
        response = client.delete("/api/auth/users/9999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
