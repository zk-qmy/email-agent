import asyncio
import nest_asyncio
from typing import Optional

try:
    nest_asyncio.apply()
except ValueError:
    pass  # Already patched or using uvloop

from src.integrations.mail.client import MailClient


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def send_email_sync(sender_id: int, recipient_email: str, subject: str, body: str):
    client = MailClient()
    return _run_async(client.send_email(sender_id, recipient_email, subject, body))


def poll_inbox_sync(user_id: int, last_check: Optional[str] = None):
    client = MailClient()
    return _run_async(client.poll_inbox(user_id, last_check))


def mark_read_sync(email_id: int):
    client = MailClient()
    return _run_async(client.mark_read(email_id))


def get_inbox_sync(user_id: int, unread: bool = False):
    client = MailClient()
    return _run_async(client.get_inbox(user_id, unread))


def get_email_id_sync(user_id: int, index: int = 0) -> int:
    """Get a single email ID from inbox by index."""
    inbox = get_inbox_sync(user_id)
    emails = inbox.get("emails", [])
    if not emails:
        raise ValueError("Inbox is empty")
    return emails[index]["email"]["id"]


def get_email_sync(email_id: int) -> dict:
    """Get full email content by ID."""
    client = MailClient()
    return _run_async(client.get_email(email_id))


def get_email_by_index_sync(user_id: int, index: int = 0) -> dict:
    """Get a whole email from inbox by index."""
    email_id = get_email_id_sync(user_id, index)
    response = get_email_sync(email_id)
    return response["email"]


def get_threads_sync(user_id: int):
    """Get all threads for a user."""
    client = MailClient()
    return _run_async(client.get_threads(user_id))


def get_thread_emails_sync(thread_id: str, user_id: int):
    """Get all emails in a thread."""
    client = MailClient()
    return _run_async(client.get_thread_emails(thread_id, user_id))