from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sent_emails = relationship("Email", foreign_keys="Email.sender_id", back_populates="sender")
    received_emails = relationship("Email", foreign_keys="Email.recipient_id", back_populates="recipient")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    folder = Column(String(10), nullable=False, default="inbox")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_emails")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_emails")
    parent = relationship("Email", remote_side=[id], backref="replies")

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_email": self.sender.email if self.sender else None,
            "recipient_id": self.recipient_id,
            "recipient_email": self.recipient.email if self.recipient else None,
            "subject": self.subject,
            "body": self.body,
            "parent_id": self.parent_id,
            "folder": self.folder,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }
