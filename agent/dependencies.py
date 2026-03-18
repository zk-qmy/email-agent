import os
from httpx import Client

EMAIL_BACKEND_URL = os.getenv("EMAIL_BACKEND_URL", "http://localhost:5001")

mail_client = Client(base_url=EMAIL_BACKEND_URL, timeout=30.0)
