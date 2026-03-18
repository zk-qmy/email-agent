import asyncio
import nest_asyncio
from typing import Optional

nest_asyncio.apply()

from src.integrations.mail.client import mail_client


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
    return _run_async(mail_client.send_email(sender_id, recipient_email, subject, body))


def poll_inbox_sync(user_id: int, last_check: Optional[str] = None):
    return _run_async(mail_client.poll_inbox(user_id, last_check))


def mark_read_sync(email_id: int):
    return _run_async(mail_client.mark_read(email_id))
