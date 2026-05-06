import pytest
from unittest.mock import patch, MagicMock
from src.integrations.llm.client import (
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMAPIError,
    _handle_llm_error,
    get_llm,
    get_llm_safe,
)


class TestLLMErrorClasses:
    def test_llm_error_hierarchy(self):
        assert issubclass(LLMConnectionError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMTimeoutError, LLMError)
        assert issubclass(LLMAPIError, LLMError)

    def test_llm_error_can_be_raised(self):
        with pytest.raises(LLMError):
            raise LLMError("Test error")

    def test_llm_api_error_can_be_raised(self):
        with pytest.raises(LLMAPIError):
            raise LLMAPIError("API key error")

    def test_llm_rate_limit_error_can_be_raised(self):
        with pytest.raises(LLMRateLimitError):
            raise LLMRateLimitError("Rate limit exceeded")

    def test_llm_timeout_error_can_be_raised(self):
        with pytest.raises(LLMTimeoutError):
            raise LLMTimeoutError("Request timed out")


class TestHandleLLMError:
    def test_handle_llm_error_api_key(self):
        error = Exception("Invalid API key")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMAPIError)
        assert "api key" in str(result).lower()

    def test_handle_llm_error_permission(self):
        error = Exception("api permission denied")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMAPIError)

    def test_handle_llm_error_rate_limit(self):
        error = Exception("Rate limit exceeded")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMRateLimitError)
        assert "rate limit" in str(result).lower()

    def test_handle_llm_error_quota(self):
        error = Exception("Quota exceeded")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMRateLimitError)

    def test_handle_llm_error_timeout(self):
        error = Exception("Request timed out")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMTimeoutError)
        assert "timed out" in str(result).lower()

    def test_handle_llm_error_timeout_asyncio(self):
        error = Exception("asyncio.TimeoutError")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMTimeoutError)

    def test_handle_llm_error_generic(self):
        error = Exception("Some unexpected error")
        result = _handle_llm_error(error, "fast")
        assert isinstance(result, LLMError)
        assert "unexpected" in str(result).lower()


class TestGetLLM:
    @patch("src.integrations.llm.client._instances", {})
    @patch("src.integrations.llm.client.settings")
    def test_get_llm_invalid_role(self, mock_settings):
        mock_settings.GOOGLE_API_KEY = "test-key"

        with pytest.raises(ValueError) as exc_info:
            get_llm("invalid_role")

        assert "Unknown LLM role" in str(exc_info.value)
        assert "invalid_role" in str(exc_info.value)

    @patch("src.integrations.llm.client._instances", {})
    @patch("src.integrations.llm.client.settings")
    def test_get_llm_no_api_key(self, mock_settings):
        mock_settings.GOOGLE_API_KEY = None

        with pytest.raises(LLMAPIError) as exc_info:
            get_llm("fast")

        assert "not configured" in str(exc_info.value)

    @patch("src.integrations.llm.client._instances", {})
    @patch("src.integrations.llm.client.settings")
    def test_get_llm_valid_role(self, mock_settings):
        mock_settings.GOOGLE_API_KEY = "test-key"

        from langchain_google_genai import ChatGoogleGenerativeAI

        with patch("src.integrations.llm.client.ChatGoogleGenerativeAI") as mock_llm_class:
            mock_llm_class.return_value = MagicMock()
            llm = get_llm("fast")

            assert mock_llm_class.called


class TestGetLLMSafe:
    @patch("src.integrations.llm.client._instances", {})
    @patch("src.integrations.llm.client.get_llm")
    def test_get_llm_safe_success(self, mock_get_llm):
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        result = get_llm_safe("fast")

        assert result is mock_llm

    @patch("src.integrations.llm.client._instances", {})
    @patch("src.integrations.llm.client.get_llm")
    def test_get_llm_safe_failure(self, mock_get_llm):
        mock_get_llm.side_effect = LLMError("Test error")

        result = get_llm_safe("fast")

        assert result is None