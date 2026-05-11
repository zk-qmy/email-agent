import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models import Base, User, Email
from werkzeug.security import generate_password_hash

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///email-agent.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_add_thread_id()
    print("Database initialized.")


def _migrate_add_thread_id():
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("emails")]
    if "thread_id" not in columns:
        session = SessionLocal()
        try:
            session.execute(text("ALTER TABLE emails ADD COLUMN thread_id VARCHAR(64)"))
            session.commit()
            print("Added thread_id column to emails table.")
        finally:
            session.close()


def seed_data():
    session = SessionLocal()
    try:
        if session.query(User).count() > 0:
            print("Database already seeded.")
            return

        alice = User(
            username="alice",
            email="alice@example.com",
            password_hash=generate_password_hash("password123"),
            role="admin",
        )
        bob = User(
            username="bob",
            email="bob@example.com",
            password_hash=generate_password_hash("password123"),
            role="student",
        )
        charlie = User(
            username="charlie",
            email="charlie@example.com",
            password_hash=generate_password_hash("password123"),
            role="student",
        )
        session.add_all([alice, bob, charlie])
        session.commit()
        session.refresh(alice)
        session.refresh(bob)
        session.refresh(charlie)

        email1 = Email(
            sender_id=alice.id,
            recipient_id=bob.id,
            subject="Meeting Request",
            body="Hi Bob,\n\nCan we meet tomorrow at 2pm?\n\nBest,\nAlice",
            folder="sent",
        )
        email2 = Email(
            sender_id=bob.id,
            recipient_id=alice.id,
            subject="Re: Meeting Request",
            body="Hi Alice,\n\nFriday works better for me. How about 3pm?\n\nBest,\nBob",
            parent_id=email1.id,
            folder="sent",
        )
        email3 = Email(
            sender_id=charlie.id,
            recipient_id=alice.id,
            subject="Quick question",
            body="Hey Alice,\n\nQuick question about the project...\n\nBest,\nCharlie",
            folder="sent",
        )
        session.add_all([email1, email2, email3])
        session.commit()

        print(f"Seeded users: alice (id={alice.id}), bob (id={bob.id}), charlie (id={charlie.id})")
        print(f"Seeded emails: {email1.id}, {email2.id}, {email3.id}")
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    seed_data()
    print("Database setup complete!")
