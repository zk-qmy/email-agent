import logging
import os
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)

EMAIL_BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://localhost:5001")


class MailClientError(Exception):
    pass


class MailConnectionError(MailClientError):
    pass


class MailTimeoutError(MailClientError):
    pass


class MailAuthError(MailClientError):
    pass


class MailAPIError(MailClientError):
    pass


class MailClient:
    def __init__(self, base_url: str = EMAIL_BACKEND_URL):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, endpoint: str, **kwargs):
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            logger.error(f"Connection failed to {url}: {e}")
            raise MailConnectionError(f"Failed to connect to {self.base_url}") from e
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout to {url}: {e}")
            raise MailTimeoutError(f"Request timed out for {endpoint}") from e
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in (401, 403):
                logger.error(f"Auth error {status_code} for {url}: {e}")
                raise MailAuthError(f"Authentication failed: {status_code}") from e
            logger.error(f"API error {status_code} for {url}: {e}")
            raise MailAPIError(f"API error {status_code}: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {e}")
            raise MailClientError(f"Request failed: {e}") from e

    async def signup(self, username: str, email: str, password: str):
        return await self._request(
            "POST",
            "/api/auth/signup",
            json={
                "username": username,
                "email": email,
                "password": password,
            },
        )

    async def login(self, email: str, password: str):
        return await self._request(
            "POST",
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    async def send_email(
        self, sender_id: int, recipient_email: str, subject: str, body: str
    ):
        return await self._request(
            "POST",
            "/api/emails/send",
            json={
                "sender_id": sender_id,
                "recipient_email": recipient_email,
                "subject": subject,
                "body": body,
            },
        )

    async def reply_email(self, sender_id: int, parent_email_id: int, body: str):
        return await self._request(
            "POST",
            "/api/emails/reply",
            json={
                "sender_id": sender_id,
                "parent_email_id": parent_email_id,
                "body": body,
            },
        )

    async def get_inbox(self, user_id: int, unread: bool = False):
        return await self._request(
            "GET", f"/api/emails/inbox?user_id={user_id}&unread={unread}"
        )

    async def get_sent(self, user_id: int):
        return await self._request("GET", f"/api/emails/sent?user_id={user_id}")

    async def get_email(self, email_id: int):
        return await self._request("GET", f"/api/emails/{email_id}")

    async def query_emails(
        self,
        user_id: int,
        sender_email: Optional[str] = None,
        subject_kw: Optional[str] = None,
        body_kw: Optional[str] = None,
        folder: Optional[str] = None,
    ):
        payload: dict[str, object] = {"user_id": user_id}
        if sender_email:
            payload["sender_email"] = sender_email
        if subject_kw:
            payload["subject_kw"] = subject_kw
        if body_kw:
            payload["body_kw"] = body_kw
        if folder:
            payload["folder"] = folder
        return await self._request("POST", "/api/emails/query", json=payload)

    async def poll_inbox(self, user_id: int, last_check: Optional[str] = None):
        url = f"/api/emails/poll?user_id={user_id}"
        if last_check:
            url += f"&last_check={last_check}"
        return await self._request("GET", url)

    async def mark_read(self, email_id: int):
        return await self._request(
            "PUT", "/api/emails/mark_read", json={"email_id": email_id}
        )


mail_client = MailClient()
