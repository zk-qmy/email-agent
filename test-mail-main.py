import asyncio
from src.integrations.mail.client import MailClient
from src.integrations.mail.sync_client import get_email_by_index_sync

async def main():
    client = MailClient()
    
    # Check inbox response
    inbox = await client.get_inbox(user_id=1)
    print("=== INBOX ===")
    import json
    print(json.dumps(inbox, indent=2))
    
    # Check single email response
    email = await client.get_email(email_id=13)
    print("=== SINGLE EMAIL ===")
    print(json.dumps(email, indent=2))
    email = get_email_by_index_sync(user_id=1, index=0)
    print(email["subject"])   # → "Re: bruh"
    print(email["body"])      # → "bruh\n"
    print(email["sender_email"])  # → "linh.huynh@fulbright.edu.vn"

asyncio.run(main())