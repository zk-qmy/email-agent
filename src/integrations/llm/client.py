import logging
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_core.exceptions import LangChainException
from config.settings import settings

logger = logging.getLogger(__name__)

_instances: dict[str, ChatGoogleGenerativeAI] = {}

_role_config = {
    "fast": {"model": "gemini-3-flash-preview", "temperature": 1.0},
    "strong": {"model": "gemini-2.0-pro", "temperature": 1.0},
}


class LLMError(Exception):
    pass


class LLMConnectionError(LLMError):
    pass


class LLMRateLimitError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass


class LLMAPIError(LLMError):
    pass


def _handle_llm_error(e: Exception, role: str) -> LLMError:
    error_msg = str(e).lower()

    if "api" in error_msg and ("key" in error_msg or "permission" in error_msg):
        logger.error(f"[LLM] API key error for role '{role}': {e}")
        return LLMAPIError(f"Invalid or missing API key: {e}")
    elif "rate" in error_msg or "quota" in error_msg:
        logger.warning(f"[LLM] Rate limit exceeded for role '{role}': {e}")
        return LLMRateLimitError(f"Rate limit exceeded: {e}")
    elif "timeout" in error_msg or "timed out" in error_msg:
        logger.warning(f"[LLM] Timeout for role '{role}': {e}")
        return LLMTimeoutError(f"Request timed out: {e}")
    elif isinstance(e, LangChainException):
        logger.error(f"[LLM] LangChain error for role '{role}': {e}")
        return LLMError(f"LLM processing failed: {e}")
    else:
        logger.exception(f"[LLM] Unexpected error for role '{role}': {e}")
        return LLMError(f"Unexpected LLM error: {e}")


def get_llm(role: str = "fast") -> ChatGoogleGenerativeAI:
    if role not in _role_config:
        raise ValueError(f"Unknown LLM role: {role}. Available: {list(_role_config.keys())}")

    if role not in _instances:
        if not settings.GOOGLE_API_KEY:
            logger.error(f"[LLM] No API key configured for role '{role}'")
            raise LLMAPIError("Google API key not configured")

        try:
            _instances[role] = ChatGoogleGenerativeAI(
                **_role_config[role],
                google_api_key=settings.GOOGLE_API_KEY,
                max_tokens=None,
                timeout=60,
                max_retries=2,
            )
        except Exception as e:
            logger.exception(f"[LLM] Failed to initialize LLM for role '{role}': {e}")
            raise _handle_llm_error(e, role) from e

    return _instances[role]


def get_llm_safe(role: str = "fast") -> Optional[ChatGoogleGenerativeAI]:
    try:
        return get_llm(role)
    except LLMError:
        return None