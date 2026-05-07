import pytest
from unittest.mock import patch, MagicMock
from backend.services.mail_service import MailService
from backend.models import User, Email
from werkzeug.security import generate_password_hash


class TestMailServiceSignup:
    def test_signup_success(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        result = service.signup("alice", "alice@test.com", "password123")

        assert result["success"] is True
        assert "user_id" in result
        assert result["message"] == "User created successfully"

    def test_signup_duplicate_email(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")
        result = service.signup("alice2", "alice@test.com", "password123")

        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_signup_duplicate_username(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")
        result = service.signup("alice", "alice2@test.com", "password123")

        assert result["success"] is False
        assert "already exists" in result["error"]


class TestMailServiceLogin:
    def test_login_success(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        session = test_db()
        user = User(
            username="alice",
            email="alice@test.com",
            password_hash=generate_password_hash("password123"),
        )
        session.add(user)
        session.commit()
        session.close()

        result = service.login("alice@test.com", "password123")

        assert result["success"] is True
        assert result["username"] == "alice"

    def test_login_invalid_password(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")

        session = test_db()
        user = session.query(User).first()
        user.password_hash = generate_password_hash("correct_password")
        session.commit()
        session.close()

        result = service.login("alice@test.com", "wrong_password")

        assert result["success"] is False
        assert "Invalid email or password" in result["error"]

    def test_login_not_found(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        result = service.login("nonexistent@test.com", "password123")

        assert result["success"] is False
        assert "Invalid email or password" in result["error"]


class TestMailServiceSearchUsers:
    def test_search_users_exact(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")

        result = service.search_users("alice")

        assert len(result) == 1
        assert result[0]["username"] == "alice"

    def test_search_users_partial(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")

        result = service.search_users("ali")

        assert len(result) == 1
        assert result[0]["username"] == "alice"

    def test_search_users_empty(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")

        result = service.search_users("xyz")

        assert len(result) == 0

    def test_search_users_empty_query(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")

        result = service.search_users("")

        assert result == []


class TestMailServiceSendEmail:
    def test_send_email_recipient_not_found(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")
        session = test_db()
        sender = session.query(User).first()
        session.close()

        result = service.send_email(
            sender_id=sender.id,
            recipient_email="nonexistent@test.com",
            subject="Test",
            body="Test body"
        )

        assert result["success"] is False
        assert "Recipient not found" in result["error"]

    def test_send_email_success(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")
        service.signup("bob", "bob@test.com", "password123")

        session = test_db()
        sender = session.query(User).filter(User.username == "alice").first()
        recipient = session.query(User).filter(User.username == "bob").first()
        session.close()

        result = service.send_email(
            sender_id=sender.id,
            recipient_email="bob@test.com",
            subject="Test Subject",
            body="Test body"
        )

        assert result["success"] is True
        assert "email_id" in result
        assert result["message"] == "Email sent successfully"


class TestMailServiceGetInbox:
    def test_get_inbox_empty(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")

        session = test_db()
        user = session.query(User).first()
        user_id = user.id
        session.close()

        result = service.get_inbox(user_id)

        assert result == []

    def test_get_inbox_with_emails(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")
        service.signup("bob", "bob@test.com", "password123")

        session = test_db()
        sender = session.query(User).filter(User.username == "alice").first()
        recipient = session.query(User).filter(User.username == "bob").first()
        session.close()

        service.send_email(
            sender_id=sender.id,
            recipient_email="bob@test.com",
            subject="Test",
            body="Test body"
        )

        result = service.get_inbox(recipient.id)

        assert len(result) == 1
        assert result[0]["subject"] == "Test"


class TestMailServiceMarkRead:
    def test_mark_read_success(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        service.signup("alice", "alice@test.com", "password123")
        service.signup("bob", "bob@test.com", "password123")

        session = test_db()
        sender = session.query(User).filter(User.username == "alice").first()
        recipient = session.query(User).filter(User.username == "bob").first()
        session.close()

        service.send_email(
            sender_id=sender.id,
            recipient_email="bob@test.com",
            subject="Test",
            body="Test body"
        )

        inbox = service.get_inbox(recipient.id)
        email_id = inbox[0]["id"]

        result = service.mark_read(email_id)

        assert result["success"] is True

    def test_mark_read_not_found(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        result = service.mark_read(99999)

        assert result["success"] is False
        assert "Email not found" in result["error"]


class TestMailServiceGetUserById:
    def test_get_user_by_id(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        result = service.signup("alice", "alice@test.com", "password123")
        user_id = result["user_id"]

        user = service.get_user_by_id(user_id)

        assert user is not None
        assert user["username"] == "alice"
        assert user["email"] == "alice@test.com"

    def test_get_user_by_id_not_found(self, test_db):
        service = MailService()
        service._get_session = lambda: test_db()

        user = service.get_user_by_id(99999)

        assert user is None