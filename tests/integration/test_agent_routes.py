import pytest
from fastapi.testclient import TestClient


class TestCreateThread:
    def test_create_thread(self, agent_app, seeded_user):
        response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert data["thread_id"].startswith("thread-")

    def test_create_thread_missing_user_id(self, agent_app):
        response = agent_app.post(
            "/api/agent/thread",
            json={}
        )
        assert response.status_code == 422


class TestCreateDraft:
    def test_create_draft(self, agent_app, seeded_user):
        response = agent_app.post(
            "/api/agent/draft",
            json={
                "user_id": seeded_user["id"],
                "prompt": "Schedule a meeting with Bob"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "thread_id" in data

    def test_create_draft_with_thread(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.post(
            "/api/agent/draft",
            json={
                "user_id": seeded_user["id"],
                "prompt": "Schedule a meeting",
                "thread_id": thread_id
            }
        )
        assert response.status_code == 200

    def test_create_draft_missing_prompt(self, agent_app, seeded_user):
        response = agent_app.post(
            "/api/agent/draft",
            json={"user_id": seeded_user["id"]}
        )
        assert response.status_code == 422

    def test_create_draft_missing_user_id(self, agent_app):
        response = agent_app.post(
            "/api/agent/draft",
            json={"prompt": "Schedule a meeting"}
        )
        assert response.status_code == 422


class TestGetThread:
    def test_get_thread(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.get(f"/api/agent/thread/{thread_id}")
        assert response.status_code == 200

    def test_get_thread_not_found(self, agent_app):
        response = agent_app.get("/api/agent/thread/nonexistent-thread")
        assert response.status_code == 404


class TestGetThreadAlias:
    def test_get_thread_via_draft_endpoint(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/draft",
            json={
                "user_id": seeded_user["id"],
                "prompt": "Test"
            }
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.get(f"/api/agent/thread/{thread_id}")
        assert response.status_code == 200


class TestCancelThread:
    def test_cancel_thread(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.delete(f"/api/agent/thread/{thread_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "removed"

    def test_cancel_thread_not_found(self, agent_app):
        response = agent_app.delete("/api/agent/thread/nonexistent-thread")
        assert response.status_code == 400


class TestReplyToDraft:
    def test_reply_to_draft(self, agent_app, seeded_user):
        draft_response = agent_app.post(
            "/api/agent/draft",
            json={
                "user_id": seeded_user["id"],
                "prompt": "Schedule a meeting"
            }
        )
        thread_id = draft_response.json()["thread_id"]

        response = agent_app.post(
            f"/api/agent/thread/{thread_id}/reply",
            json={
                "user_id": seeded_user["id"],
                "response": "yes"
            }
        )
        assert response.status_code == 200

    def test_reply_to_draft_invalid(self, agent_app):
        response = agent_app.post(
            "/api/agent/thread/invalid/reply",
            json={
                "user_id": 1,
                "response": "yes"
            }
        )
        assert response.status_code in [400, 404]

    def test_reply_to_draft_missing_response(self, agent_app, seeded_user):
        response = agent_app.post(
            f"/api/agent/thread/test-thread/reply",
            json={"user_id": seeded_user["id"]}
        )
        assert response.status_code == 422


class TestGetUserThreads:
    def test_get_user_threads(self, agent_app, seeded_user):
        agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )

        response = agent_app.get(f"/api/agent/threads?user_id={seeded_user['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data

    def test_get_user_threads_filter(self, agent_app, seeded_user):
        response = agent_app.get(
            f"/api/agent/threads?user_id={seeded_user['id']}&status=processing"
        )
        assert response.status_code == 200


class TestConfirmMeeting:
    def test_confirm_meeting(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.post(f"/api/agent/thread/{thread_id}/confirm")
        assert response.status_code == 200

    def test_confirm_meeting_not_found(self, agent_app):
        response = agent_app.post("/api/agent/thread/nonexistent/confirm")
        assert response.status_code == 400


class TestDeclineMeeting:
    def test_decline_meeting(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.post(f"/api/agent/thread/{thread_id}/decline")
        assert response.status_code == 200

    def test_decline_meeting_not_found(self, agent_app):
        response = agent_app.post("/api/agent/thread/nonexistent/decline")
        assert response.status_code == 400


class TestGetStatus:
    def test_get_status(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.get(f"/api/agent/status/{thread_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_get_status_not_found(self, agent_app):
        response = agent_app.get("/api/agent/status/nonexistent")
        assert response.status_code == 404


class TestGetHistory:
    def test_get_history(self, agent_app, seeded_user):
        thread_response = agent_app.post(
            "/api/agent/thread",
            json={"user_id": seeded_user["id"]}
        )
        thread_id = thread_response.json()["thread_id"]

        response = agent_app.get(f"/api/agent/history/{thread_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_get_history_not_found(self, agent_app):
        response = agent_app.get("/api/agent/history/nonexistent")
        assert response.status_code == 404