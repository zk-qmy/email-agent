# src/integrations/llm/client.py

from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

_instances: dict[str, ChatGoogleGenerativeAI] = {}

_role_config = {
    "fast": {"model": "gemini-2.0-flash", "temperature": 1.0},
    "strong": {"model": "gemini-2.0-pro", "temperature": 1.0},
}


def get_llm(role: str = "fast") -> ChatGoogleGenerativeAI:
    if role not in _instances:
        _instances[role] = ChatGoogleGenerativeAI(
            **_role_config[role],
            google_api_key=settings.GOOGLE_API_KEY,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
    return _instances[role]
