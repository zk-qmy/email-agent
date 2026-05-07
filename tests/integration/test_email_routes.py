import pytest
from fastapi.testclient import TestClient


class TestSendEmail:
    def test_send_email(self, app, seeded_user, seeded_recipient):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test Subject",
                "body": "Test body content"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_id" in data
        assert data["message"] == "Email sent successfully"

    def test_send_email_missing_sender(self, app, seeded_recipient):
        response = app.post(
            "/api/emails/send",
            json={
                "recipient_email": seeded_recipient["email"],
                "subject": "Test Subject",
                "body": "Test body content"
            }
        )
        assert response.status_code == 422

    def test_send_email_missing_recipient(self, app, seeded_user):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "subject": "Test Subject",
                "body": "Test body content"
            }
        )
        assert response.status_code == 422

    def test_send_email_missing_subject(self, app, seeded_user, seeded_recipient):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "body": "Test body content"
            }
        )
        assert response.status_code == 422

    def test_send_email_missing_body(self, app, seeded_user, seeded_recipient):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test Subject"
            }
        )
        assert response.status_code == 422

    def test_send_email_invalid_recipient(self, app, seeded_user):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": "nonexistent@test.com",
                "subject": "Test Subject",
                "body": "Test body content"
            }
        )
        assert response.status_code == 400
        assert "Recipient not found" in response.json()["detail"]

    def test_send_email_empty_subject(self, app, seeded_user, seeded_recipient):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "",
                "body": "Test body content"
            }
        )
        assert response.status_code == 200

    def test_send_email_empty_body(self, app, seeded_user, seeded_recipient):
        response = app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test Subject",
                "body": ""
            }
        )
        assert response.status_code == 200


class TestReplyEmail:
    def test_reply_email(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Original Subject",
                "body": "Original body"
            }
        )

        from backend.services.mail_service import MailService
        from backend.models import Email
        session = MailService._get_session(None)
        email = session.query(Email).first()
        parent_id = email.id
        session.close()

        response = app.post(
            "/api/emails/reply",
            json={
                "sender_id": seeded_recipient["id"],
                "parent_email_id": parent_id,
                "body": "Reply body"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "email_id" in data

    def test_reply_email_not_found(self, app, seeded_user):
        response = app.post(
            "/api/emails/reply",
            json={
                "sender_id": seeded_user["id"],
                "parent_email_id": 99999,
                "body": "Reply body"
            }
        )
        assert response.status_code == 400
        assert "Parent email not found" in response.json()["detail"]

    def test_reply_email_missing_parent(self, app, seeded_user):
        response = app.post(
            "/api/emails/reply",
            json={
                "sender_id": seeded_user["id"],
                "body": "Reply body"
            }
        )
        assert response.status_code == 422


class TestGetInbox:
    def test_get_inbox(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test",
                "body": "Test"
            }
        )

        response = app.get(f"/api/emails/inbox?user_id={seeded_recipient['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert len(data["emails"]) == 1

    def test_get_inbox_unread(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test",
                "body": "Test"
            }
        )

        response = app.get(f"/api/emails/inbox?user_id={seeded_recipient['id']}&unread=true")
        assert response.status_code == 200

    def test_get_inbox_empty_user(self, app):
        response = app.get("/api/emails/inbox?user_id=99999")
        assert response.status_code == 200
        data = response.json()
        assert data["emails"] == []

    def test_get_inbox_missing_user_id(self, app):
        response = app.get("/api/emails/inbox")
        assert response.status_code == 422


class TestGetSent:
    def test_get_sent(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test",
                "body": "Test"
            }
        )

        response = app.get(f"/api/emails/sent?user_id={seeded_user['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data
        assert len(data["emails"]) == 1


class TestGetEmail:
    def test_get_email(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test",
                "body": "Test"
            }
        )

        from backend.services.mail_service import MailService
        from backend.models import Email
        session = MailService._get_session(None)
        email = session.query(Email).first()
        email_id = email.id
        session.close()

        response = app.get(f"/api/emails/{email_id}")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"]["subject"] == "Test"

    def test_get_email_not_found(self, app):
        response = app.get("/api/emails/99999")
        assert response.status_code == 404
        assert "Email not found" in response.json()["detail"]


class TestQueryEmails:
    def test_query_emails(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Searchable Subject",
                "body": "Searchable body"
            }
        )

        response = app.post(
            "/api/emails/query",
            json={
                "user_id": seeded_recipient["id"],
                "subject_kw": "Searchable"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "emails" in data

    def test_query_emails_no_filters(self, app, seeded_user):
        response = app.post(
            "/api/emails/query",
            json={"user_id": seeded_user["id"]}
        )
        assert response.status_code == 200


class TestMarkRead:
    def test_mark_read(self, app, seeded_user, seeded_recipient):
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test",
                "body": "Test"
            }
        )

        from backend.services.mail_service import MailService
        from backend.models import Email
        session = MailService._get_session(None)
        email = session.query(Email).first()
        email_id = email.id
        session.close()

        response = app.put(
            "/api/emails/mark_read",
            json={"email_id": email_id}
        )
        assert response.status_code == 200

    def test_mark_read_not_found(self, app):
        response = app.put(
            "/api/emails/mark_read",
            json={"email_id": 99999}
        )
        assert response.status_code == 404


class TestPollInbox:
    def test_poll_inbox(self, app, seeded_user, seeded_recipient):
        """Test poll inbox returns new emails."""
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test Poll",
                "body": "Test body"
            }
        )

        response = app.get(f"/api/emails/poll?user_id={seeded_recipient['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "new_emails" in data
        assert "count" in data

    def test_poll_inbox_with_last_check(self, app, seeded_user, seeded_recipient):
        """Test poll inbox with last_check filter."""
        app.post(
            "/api/emails/send",
            json={
                "sender_id": seeded_user["id"],
                "recipient_email": seeded_recipient["email"],
                "subject": "Test Poll 2",
                "body": "Test body 2"
            }
        )

        response = app.get(f"/api/emails/poll?user_id={seeded_recipient['id']}&last_check=2020-01-01T00:00:00")
        assert response.status_code == 200
        data = response.json()
        assert "new_emails" in data