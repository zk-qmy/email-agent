import os
from typing import Optional, List
import httpx

EMAIL_BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://localhost:5001")


class MailClient:
    def __init__(self, base_url: str = EMAIL_BACKEND_URL):
        self.base_url = base_url

    def _request(self, method: str, endpoint: str, **kwargs):
        url = f"{self.base_url}{endpoint}"
        with httpx.Client() as client:
            response = client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    def signup(self, username: str, email: str, password: str):
        return self._request("POST", "/api/auth/signup", json={
            "username": username,
            "email": email,
            "password": password,
        })

    def login(self, email: str, password: str):
        return self._request("POST", "/api/auth/login", json={
            "email": email,
            "password": password,
        })

    def send_email(self, sender_id: int, recipient_email: str, subject: str, body: str):
        return self._request("POST", "/api/emails/send", json={
            "sender_id": sender_id,
            "recipient_email": recipient_email,
            "subject": subject,
            "body": body,
        })

    def reply_email(self, sender_id: int, parent_email_id: int, body: str):
        return self._request("POST", "/api/emails/reply", json={
            "sender_id": sender_id,
            "parent_email_id": parent_email_id,
            "body": body,
        })

    def get_inbox(self, user_id: int, unread: bool = False):
        return self._request("GET", f"/api/emails/inbox?user_id={user_id}&unread={unread}")

    def get_sent(self, user_id: int):
        return self._request("GET", f"/api/emails/sent?user_id={user_id}")

    def get_email(self, email_id: int):
        return self._request("GET", f"/api/emails/{email_id}")

    def query_emails(
        self,
        user_id: int,
        sender_email: Optional[str] = None,
        subject_kw: Optional[str] = None,
        body_kw: Optional[str] = None,
        folder: Optional[str] = None,
    ):
        payload = {"user_id": user_id}
        if sender_email:
            payload["sender_email"] = sender_email
        if subject_kw:
            payload["subject_kw"] = subject_kw
        if body_kw:
            payload["body_kw"] = body_kw
        if folder:
            payload["folder"] = folder
        return self._request("POST", "/api/emails/query", json=payload)

    def poll_inbox(self, user_id: int, last_check: Optional[str] = None):
        url = f"/api/emails/poll?user_id={user_id}"
        if last_check:
            url += f"&last_check={last_check}"
        return self._request("GET", url)

    def mark_read(self, email_id: int):
        return self._request("PUT", "/api/emails/mark_read", json={"email_id": email_id})


mail_client = MailClient()
