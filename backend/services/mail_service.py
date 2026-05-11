import json
import hashlib
import re
from sqlalchemy.orm import Session
from sqlalchemy import update as sql_update
from typing import cast
from backend.database import SessionLocal
from backend.models import User, Email
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from typing import Optional, List
import asyncio


def _get_connection_manager():
    try:
        from backend.routes.ws_notifications import connection_manager

        return connection_manager
    except Exception:
        return None


class MailService:
    def __init__(self):
        pass

    @staticmethod
    def _normalize_subject(subject: str) -> str:
        s = subject.strip()
        return re.sub(r"^(Re|Fwd|FW|RE|re|fwd|R|r)\s*:\s*", "", s).strip()

    @staticmethod
    def _generate_thread_id(sender_id: int, recipient_id: int, subject: str) -> str:
        norm = MailService._normalize_subject(subject)
        a, b = sorted([sender_id, recipient_id])
        raw = f"{a}:{b}:{norm}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    def _get_session(self) -> Session:
        return SessionLocal()

    def signup(self, username: str, email: str, password: str, role: str = "student") -> dict:
        session = self._get_session()
        try:
            existing = (
                session.query(User)
                .filter((User.email == email) | (User.username == username))
                .first()
            )
            if existing:
                return {"success": False, "error": "Username or email already exists"}

            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return {
                "success": True,
                "user_id": user.id,
                "role": user.role,
                "message": "User created successfully",
            }
        finally:
            session.close()

    def login(self, email: str, password: str) -> dict:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                return {"success": False, "error": "Invalid email or password"}

            if not check_password_hash(str(user.password_hash), password):
                return {"success": False, "error": "Invalid email or password"}

            return {
                "success": True,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        finally:
            session.close()

    def search_users(self, query: str) -> List[dict]:
        from sqlalchemy import or_

        tokens = query.lower().split()
        if not tokens:
            return []

        session = self._get_session()
        try:
            conditions = [
                or_(
                    User.username.ilike(f"%{t}%"),
                    User.email.ilike(f"%{t}%")
                ) for t in tokens if t
            ]

            if not conditions:
                return []

            users = session.query(User).filter(or_(*conditions)).all()

            scored = []
            for u in users:
                match_count = sum(
                    1 for t in tokens
                    if t in u.username.lower() or t in u.email.lower()
                )
                scored.append((match_count, u))

            scored.sort(key=lambda x: -x[0])

            return [
                {"id": u.id, "username": u.username, "email": u.email, "role": u.role}
                for _, u in scored
            ]
        finally:
            session.close()

    def _resolve_user(self, session: Session, email_addr: str) -> Optional[User]:
        return session.query(User).filter(User.email == email_addr).first()

    def _notify_user(self, user_id: int, email_obj: Email):
        try:
            cm = _get_connection_manager()
            if cm:
                asyncio.create_task(
                    cm.send_to_user(
                        cast(int, user_id),
                        {
                            "event": "new_email",
                            "email": email_obj.to_dict(),
                        },
                    )
                )
        except Exception:
            pass

    def send_email(
        self,
        sender_id: int,
        recipient_email: str,
        subject: str,
        body: str,
        parent_id: Optional[int] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> dict:
        session = self._get_session()
        try:
            recipient = self._resolve_user(session, recipient_email)
            if not recipient:
                return {"success": False, "error": "Recipient not found"}

            cc = cc or []
            bcc = bcc or []

            all_cc: List[User] = []
            for addr in cc:
                u = self._resolve_user(session, addr)
                if not u:
                    return {"success": False, "error": f"CC recipient '{addr}' not found"}
                all_cc.append(u)

            all_bcc: List[User] = []
            for addr in bcc:
                u = self._resolve_user(session, addr)
                if not u:
                    return {"success": False, "error": f"BCC recipient '{addr}' not found"}
                all_bcc.append(u)

            cc_json = json.dumps(cc) if cc else None
            bcc_json = json.dumps(bcc) if bcc else None

            thread_id = None
            if parent_id:
                parent = session.query(Email).filter(Email.id == parent_id).first()
                thread_id = parent.thread_id if parent and parent.thread_id else None

            if not thread_id:
                thread_id = self._generate_thread_id(sender_id, recipient.id, subject)

            sent_email = Email(
                sender_id=sender_id,
                recipient_id=recipient.id,
                subject=subject,
                body=body,
                parent_id=parent_id,
                thread_id=thread_id,
                folder="sent",
                cc=cc_json,
                bcc=bcc_json,
            )
            session.add(sent_email)

            def _make_inbox(recip: User, cc_field: Optional[str] = None) -> Email:
                return Email(
                    sender_id=sender_id,
                    recipient_id=recip.id,
                    subject=subject,
                    body=body,
                    parent_id=parent_id,
                    folder="inbox",
                    thread_id=thread_id,
                    cc=cc_field,
                )

            inbox_primary = _make_inbox(recipient, cc_field=cc_json)
            session.add(inbox_primary)

            inbox_cc: List[Email] = []
            for ccu in all_cc:
                e = _make_inbox(ccu, cc_field=cc_json)
                session.add(e)
                inbox_cc.append(e)

            inbox_bcc: List[Email] = []
            for bccu in all_bcc:
                e = _make_inbox(bccu)
                session.add(e)
                inbox_bcc.append(e)
            session.commit()
            session.refresh(sent_email)
            session.refresh(inbox_primary)
            for e in inbox_cc:
                session.refresh(e)
            for e in inbox_bcc:
                session.refresh(e)

            self._notify_user(recipient.id, inbox_primary)
            for e in inbox_cc:
                self._notify_user(e.recipient_id, e)
            for e in inbox_bcc:
                self._notify_user(e.recipient_id, e)

            self._notify_user(sender_id, sent_email)

            return {
                "success": True,
                "email_id": sent_email.id,
                "message": "Email sent successfully",
            }
        finally:
            session.close()

    def reply_email(self, sender_id: int, parent_email_id: int, body: str) -> dict:
        session = self._get_session()
        try:
            parent_email = (
                session.query(Email).filter(Email.id == parent_email_id).first()
            )
            if not parent_email:
                return {"success": False, "error": "Parent email not found"}

            parent_subject = cast(str, parent_email.subject)
            subject = (
                f"Re: {parent_subject}"
                if not parent_subject.startswith("Re:")
                else parent_subject
            )

            return self.send_email(
                sender_id=sender_id,
                recipient_email=cast(str, parent_email.sender.email),
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
                query = query.filter(Email.is_read.is_(True))
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
            result = session.execute(
                sql_update(Email).where(Email.id == email_id).values(is_read=True)
            )
            session.commit()
            if result.rowcount == 0:  # type: ignore[union-attr]
                return {"success": False, "error": "Email not found"}
            return {"success": True}
        finally:
            session.close()

    def get_threads(self, user_id: int) -> List[dict]:
        session = self._get_session()
        try:
            emails = (
                session.query(Email)
                .filter(
                    (Email.sender_id == user_id) | (Email.recipient_id == user_id),
                    Email.thread_id.isnot(None),
                )
                .order_by(Email.created_at.desc())
                .all()
            )

            threads = {}
            for email in emails:
                tid = email.thread_id
                if tid not in threads:
                    threads[tid] = {
                        "thread_id": tid,
                        "subject": self._normalize_subject(email.subject),
                        "participants": set(),
                        "emails": [],
                    }
                threads[tid]["emails"].append(email.to_dict())
                threads[tid]["participants"].add(email.sender_id)
                threads[tid]["participants"].add(email.recipient_id)

            result = []
            for tid, data in threads.items():
                data["emails"].sort(key=lambda e: e["created_at"])
                data["participants"] = list(data["participants"])
                data["email_count"] = len(data["emails"])
                data["last_email_at"] = data["emails"][-1]["created_at"]
                result.append(data)

            result.sort(key=lambda t: t["last_email_at"], reverse=True)
            return result
        finally:
            session.close()

    def get_thread_emails(self, thread_id: str, user_id: int) -> List[dict]:
        session = self._get_session()
        try:
            emails = (
                session.query(Email)
                .filter(
                    Email.thread_id == thread_id,
                    (Email.sender_id == user_id) | (Email.recipient_id == user_id),
                )
                .order_by(Email.created_at.asc())
                .all()
            )
            return [e.to_dict() for e in emails]
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

    def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> dict:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}

            if username is not None:
                existing = (
                    session.query(User)
                    .filter(User.username == username, User.id != user_id)
                    .first()
                )
                if existing:
                    return {"success": False, "error": "Username already exists"}
                user.username = username

            if email is not None:
                existing = (
                    session.query(User)
                    .filter(User.email == email, User.id != user_id)
                    .first()
                )
                if existing:
                    return {"success": False, "error": "Email already exists"}
                user.email = email

            if password is not None:
                user.password_hash = generate_password_hash(password)

            if role is not None:
                user.role = role

            session.commit()
            return {"success": True, "user": user.to_dict()}
        finally:
            session.close()

    def delete_user(self, user_id: int) -> dict:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "User not found"}

            session.query(Email).filter(
                (Email.sender_id == user_id) | (Email.recipient_id == user_id)
            ).delete()

            session.delete(user)
            session.commit()
            return {"success": True}
        finally:
            session.close()


mail_service = MailService()
