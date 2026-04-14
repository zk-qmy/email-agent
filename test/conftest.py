import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

os.environ["EMAIL_BACKEND_PORT"] = "5001"
os.environ["AGENT_BASE_URL"] = "http://127.0.0.1:8000"

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="function", autouse=True)
def reset_database():
    from backend.models import Base
    from backend import database

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    database.SessionLocal = TestingSessionLocal
    database.engine = engine

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    from backend import database
    from backend import main as backend_main
    from backend.routes import ws_notifications

    database.SessionLocal = TestingSessionLocal
    database.engine = engine

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    @asynccontextmanager
    async def test_lifespan(app):
        yield

    original_lifespan = backend_main.app.router.lifespan_context
    backend_main.app.router.lifespan_context = test_lifespan
    backend_main.app.dependency_overrides[database.get_db] = override_get_db

    class MockConnectionManager:
        async def send_to_user(self, user_id, event):
            pass

        async def shutdown(self):
            pass

    backend_main.app.dependency_overrides[ws_notifications.connection_manager] = (
        MockConnectionManager()
    )

    with TestClient(backend_main.app) as test_client:
        yield test_client

    backend_main.app.router.lifespan_context = original_lifespan
    backend_main.app.dependency_overrides.clear()


@pytest.fixture
def test_users():
    from backend.models import User
    from werkzeug.security import generate_password_hash

    session = TestingSessionLocal()
    alice = User(
        username="alice",
        email="alice@test.com",
        password_hash=generate_password_hash("password123"),
    )
    bob = User(
        username="bob",
        email="bob@test.com",
        password_hash=generate_password_hash("password456"),
    )
    session.add_all([alice, bob])
    session.commit()
    session.refresh(alice)
    session.refresh(bob)

    result = {
        "alice": {"user_id": alice.id, "email": "alice@test.com"},
        "bob": {"user_id": bob.id, "email": "bob@test.com"},
    }
    session.close()
    return result
