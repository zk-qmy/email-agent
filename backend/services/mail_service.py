from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import User, Email
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from typing import Optional, List


class MailService:
    def __init__(self):
        pass

    def _get_session(self) -> Session:
        return SessionLocal()

    def signup(self, username: str, email: str, password: str) -> dict:
        session = self._get_session()
        try:
            existing = session.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            if existing:
                return {"success": False, "error": "Username or email already exists"}

            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return {"success": True, "user_id": user.id, "message": "User created successfully"}
        finally:
            session.close()

    def login(self, email: str, password: str) -> dict:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                return {"success": False, "error": "Invalid email or password"}

            if not check_password_hash(user.password_hash, password):
                return {"success": False, "error": "Invalid email or password"}

            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
            }
        finally:
            session.close()

    def send_email(
        self,
        sender_id: int,
        recipient_email: str,
        subject: str,
        body: str,
        parent_id: Optional[int] = None,
    ) -> dict:
        session = self._get_session()
        try:
            recipient = session.query(User).filter(User.email == recipient_email).first()
            if not recipient:
                return {"success": False, "error": "Recipient not found"}

            email = Email(
                sender_id=sender_id,
                recipient_id=recipient.id,
                subject=subject,
                body=body,
                parent_id=parent_id,
                folder="sent",
            )
            session.add(email)

            inbox_email = Email(
                sender_id=sender_id,
                recipient_id=recipient.id,
                subject=subject,
                body=body,
                parent_id=parent_id,
                folder="inbox",
            )
            session.add(inbox_email)
            session.commit()
            session.refresh(email)
            return {"success": True, "email_id": email.id, "message": "Email sent successfully"}
        finally:
            session.close()

    def reply_email(self, sender_id: int, parent_email_id: int, body: str) -> dict:
        session = self._get_session()
        try:
            parent_email = session.query(Email).filter(Email.id == parent_email_id).first()
            if not parent_email:
                return {"success": False, "error": "Parent email not found"}

            subject = f"Re: {parent_email.subject}" if not parent_email.subject.startswith("Re:") else parent_email.subject

            return self.send_email(
                sender_id=sender_id,
                recipient_email=parent_email.sender.email,
                subject=subject,
                body=body,
                parent_id=parent_email_id,
            )
        finally:
            session.close()

    def get_inbox(self, user_id: int, unread_only: bool = False) -> List[dict]:
        session = self._get_session()
        try:
            query = session.query(Email).filter(
                Email.recipient_id == user_id,
                Email.folder == "inbox",
            )
            if unread_only:
                query = query.filter(Email.is_read == False)
            emails = query.order_by(Email.created_at.desc()).all()
            return [e.to_dict() for e in emails]
        finally:
            session.close()

    def get_sent(self, user_id: int) -> List[dict]:
        session = self._get_session()
        try:
            emails = (
                session.query(Email)
                .filter(Email.sender_id == user_id, Email.folder == "sent")
                .order_by(Email.created_at.desc())
                .all()
            )
            return [e.to_dict() for e in emails]
        finally:
            session.close()

    def get_email(self, email_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            email = session.query(Email).filter(Email.id == email_id).first()
            if email:
                return email.to_dict()
            return None
        finally:
            session.close()

    def query_emails(
        self,
        user_id: int,
        sender_email: Optional[str] = None,
        subject_kw: Optional[str] = None,
        body_kw: Optional[str] = None,
        folder: Optional[str] = None,
    ) -> List[dict]:
        session = self._get_session()
        try:
            query = session.query(Email).filter(Email.recipient_id == user_id)

            if sender_email:
                sender = session.query(User).filter(User.email == sender_email).first()
                if sender:
                    query = query.filter(Email.sender_id == sender.id)

            if subject_kw:
                query = query.filter(Email.subject.ilike(f"%{subject_kw}%"))

            if body_kw:
                query = query.filter(Email.body.ilike(f"%{body_kw}%"))

            if folder:
                query = query.filter(Email.folder == folder)

            emails = query.order_by(Email.created_at.desc()).all()
            return [e.to_dict() for e in emails]
        finally:
            session.close()

    def poll_inbox(self, user_id: int, last_check: Optional[str] = None) -> dict:
        session = self._get_session()
        try:
            query = session.query(Email).filter(
                Email.recipient_id == user_id,
                Email.folder == "inbox",
            )

            if last_check:
                last_check_dt = datetime.fromisoformat(last_check)
                query = query.filter(Email.created_at > last_check_dt)

            new_emails = query.order_by(Email.created_at.desc()).all()
            count = len(new_emails)
            return {
                "new_emails": [e.to_dict() for e in new_emails],
                "count": count,
            }
        finally:
            session.close()

    def mark_read(self, email_id: int) -> dict:
        session = self._get_session()
        try:
            email = session.query(Email).filter(Email.id == email_id).first()
            if not email:
                return {"success": False, "error": "Email not found"}

            email.is_read = True
            session.commit()
            return {"success": True}
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return user.to_dict()
            return None
        finally:
            session.close()


mail_service = MailService()
