import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only-32chars"
os.environ["AGENT_BASE_URL"] = "http://localhost:8000"

from backend.database import Base
from backend.models import User, Email
from backend.main import app as backend_app
from backend.services.mail_service import MailService


@pytest.fixture(scope="function")
def test_db():
    """Create in-memory test database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def mail_service(test_db):
    """MailService instance with test database."""
    service = MailService()
    service._get_session = lambda: test_db()
    return service


@pytest.fixture(scope="function")
def app(test_db):
    """Backend FastAPI test client."""
    from backend.main import app as backend_app

    original_get_session = MailService._get_session

    def override_get_session(self):
        return test_db()

    MailService._get_session = override_get_session

    client = TestClient(backend_app, raise_server_exceptions=False)

    yield client

    MailService._get_session = original_get_session


@pytest.fixture(scope="function")
def agent_app():
    """Agent FastAPI test client."""
    from agent.main import app as agent_app

    return TestClient(agent_app, raise_server_exceptions=False)


@pytest.fixture
def seeded_user(mail_service, test_db):
    """Pre-seeded alice user."""
    session = test_db()
    user = User(
        username="alice",
        email="alice@test.com",
        password_hash="pbkdf2:sha256:260000$test$hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return {"id": user.id, "username": user.username, "email": user.email}


@pytest.fixture
def seeded_recipient(mail_service, test_db):
    """Pre-seeded bob user as recipient."""
    session = test_db()
    user = User(
        username="bob",
        email="bob@test.com",
        password_hash="pbkdf2:sha256:260000$test$hash",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return {"id": user.id, "username": user.username, "email": user.email}


@pytest.fixture
def auth_cookies(app, seeded_user):
    """Authenticated session cookie."""
    from backend.main import app as backend_app
    from backend.services.mail_service import MailService

    session = MailService._get_session(None)
    user = session.query(User).filter(User.email == "alice@test.com").first()
    from werkzeug.security import check_password_hash

    class MockUser:
        def __init__(self):
            pass

        def __init__(self, user_id, username, email):
            self.id = user_id
            self.username = username
            self.email = email

        @staticmethod
        def check_password(hash, password):
            return True

    user.check_password = lambda p: True
    user.password_hash = "pbkdf2:sha256:260000$test$hash"

    session.close()

    response = app.post(
        "/api/auth/login",
        json={"email": "alice@test.com", "password": "password123"},
    )
    return response.cookies


@pytest.fixture
def sample_thread_id(agent_app, seeded_user):
    """Create a thread and return its ID."""
    response = agent_app.post(
        "/api/agent/thread",
        json={"user_id": seeded_user["id"]},
    )
    return response.json()["thread_id"]


@pytest.fixture
async def backend_ws_url():
    """Backend WebSocket URL."""
    return "ws://localhost:5001/ws/push/1"


@pytest.fixture
async def agent_ws_url():
    """Agent WebSocket URL."""
    return "ws://localhost:8000/api/agent/ws/1"