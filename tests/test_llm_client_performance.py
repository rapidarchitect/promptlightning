import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from litellm.exceptions import RateLimitError as LiteLLMRateLimitError, Timeout, APIError

from promptlightning.llm.client import LLMClient
from promptlightning.exceptions import LLMError


@pytest.fixture
def llm_client():
    return LLMClient(enable_cache=True, cache_ttl=60)


@pytest.fixture
def mock_litellm_response():
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Test response"
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response._hidden_params = {
        "custom_llm_provider": "openai",
        "response_cost": 0.02
    }
    return mock_response


@pytest.fixture
def mock_async_response():
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Async response"
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 120
    mock_response.usage.completion_tokens = 60
    mock_response._hidden_params = {
        "custom_llm_provider": "anthropic",
        "response_cost": 0.03
    }
    return mock_response


class TestCaching:
    def test_cache_enabled(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion", return_value=mock_litellm_response) as mock_completion:
            result1 = llm_client.execute("Test prompt", "gpt-4")
            result2 = llm_client.execute("Test prompt", "gpt-4")

            mock_completion.assert_called_once()
            assert result1.output == result2.output
            assert result1.latency_ms == result2.latency_ms

    def test_cache_different_prompts(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion", return_value=mock_litellm_response) as mock_completion:
            llm_client.execute("Prompt 1", "gpt-4")
            llm_client.execute("Prompt 2", "gpt-4")

            assert mock_completion.call_count == 2

    def test_cache_disabled(self, mock_litellm_response):
        client = LLMClient(enable_cache=False)
        with patch("promptlightning.llm.client.completion", return_value=mock_litellm_response) as mock_completion:
            client.execute("Test prompt", "gpt-4")
            client.execute("Test prompt", "gpt-4")

            assert mock_completion.call_count == 2

    def test_clear_cache(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion", return_value=mock_litellm_response) as mock_completion:
            llm_client.execute("Test prompt", "gpt-4")
            llm_client.clear_cache()
            llm_client.execute("Test prompt", "gpt-4")

            assert mock_completion.call_count == 2


class TestRetryLogic:
    def test_retry_on_rate_limit(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = [
                LiteLLMRateLimitError("Rate limit", llm_provider="openai", model="gpt-4"),
                mock_litellm_response
            ]

            with patch("time.sleep"):
                result = llm_client.execute("Test prompt", "gpt-4", max_retries=2)

            assert result.output == "Test response"
            assert mock_completion.call_count == 2

    def test_retry_on_timeout(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = [
                Timeout(message="Timeout", model="gpt-4", llm_provider="openai"),
                mock_litellm_response
            ]

            with patch("time.sleep"):
                result = llm_client.execute("Test prompt", "gpt-4", max_retries=2)

            assert result.output == "Test response"
            assert mock_completion.call_count == 2

    def test_retry_exponential_backoff(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = [
                Timeout(message="Timeout", model="gpt-4", llm_provider="openai"),
                Timeout(message="Timeout", model="gpt-4", llm_provider="openai"),
                mock_litellm_response
            ]

            with patch("time.sleep") as mock_sleep:
                result = llm_client.execute("Test prompt", "gpt-4", max_retries=3, retry_delay=1.0)

            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0][0][0] == 1.0
            assert mock_sleep.call_args_list[1][0][0] == 2.0

    def test_max_retries_exceeded(self, llm_client):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = Timeout(message="Timeout", model="gpt-4", llm_provider="openai")

            with patch("time.sleep"):
                with pytest.raises(LLMError) as exc_info:
                    llm_client.execute("Test prompt", "gpt-4", max_retries=2)

            assert "Request timeout" in str(exc_info.value)


class TestCircuitBreaker:
    def test_circuit_breaker_opens_after_failures(self, llm_client):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = APIError(
                status_code=500,
                message="Server error",
                llm_provider="openai",
                model="gpt-4"
            )

            for _ in range(5):
                with pytest.raises(LLMError):
                    llm_client.execute("Test", "openai/gpt-4", max_retries=1)

            with pytest.raises(LLMError) as exc_info:
                llm_client.execute("Test", "openai/gpt-4")

            assert "Circuit breaker open" in str(exc_info.value)

    def test_circuit_breaker_reset_on_success(self, llm_client, mock_litellm_response):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = [
                APIError(status_code=500, message="Error", llm_provider="openai", model="gpt-4"),
                mock_litellm_response
            ]

            with pytest.raises(LLMError):
                llm_client.execute("Test", "openai/gpt-4", max_retries=1)

            with patch("time.sleep"):
                result = llm_client.execute("Test", "openai/gpt-4", max_retries=2)

            assert result.output == "Test response"

    def test_reset_circuit_breakers(self, llm_client):
        with patch("promptlightning.llm.client.completion") as mock_completion:
            mock_completion.side_effect = APIError(
                status_code=500,
                message="Server error",
                llm_provider="openai",
                model="gpt-4"
            )

            for _ in range(5):
                with pytest.raises(LLMError):
                    llm_client.execute("Test", "openai/gpt-4", max_retries=1)

            llm_client.reset_circuit_breakers()

            with pytest.raises(LLMError):
                llm_client.execute("Test", "openai/gpt-4", max_retries=1)


class TestAsyncExecution:
    @pytest.mark.asyncio
    async def test_execute_async_success(self, llm_client, mock_async_response):
        with patch("promptlightning.llm.client.acompletion", return_value=mock_async_response):
            result = await llm_client.execute_async("Test prompt", "claude-3-opus")

            assert result.output == "Async response"
            assert result.provider == "anthropic"
            assert result.tokens_in == 120
            assert result.tokens_out == 60

    @pytest.mark.asyncio
    async def test_execute_async_with_cache(self, llm_client, mock_async_response):
        with patch("promptlightning.llm.client.acompletion", return_value=mock_async_response) as mock_acompletion:
            result1 = await llm_client.execute_async("Test prompt", "claude-3-opus")
            result2 = await llm_client.execute_async("Test prompt", "claude-3-opus")

            mock_acompletion.assert_called_once()
            assert result1.output == result2.output

    @pytest.mark.asyncio
    async def test_execute_async_retry(self, llm_client, mock_async_response):
        with patch("promptlightning.llm.client.acompletion") as mock_acompletion:
            mock_acompletion.side_effect = [
                LiteLLMRateLimitError("Rate limit", llm_provider="anthropic", model="claude-3-opus"),
                mock_async_response
            ]

            result = await llm_client.execute_async("Test prompt", "claude-3-opus", max_retries=2)

            assert result.output == "Async response"
            assert mock_acompletion.call_count == 2


class TestBatchExecution:
    def test_execute_batch(self, llm_client, mock_litellm_response):
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        with patch("promptlightning.llm.client.completion", return_value=mock_litellm_response):
            results = llm_client.execute_batch(prompts, "gpt-4")

            assert len(results) == 3
            assert all(r.output == "Test response" for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_async(self, llm_client, mock_async_response):
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        with patch("promptlightning.llm.client.acompletion", return_value=mock_async_response):
            results = await llm_client.execute_batch_async(prompts, "claude-3-opus")

            assert len(results) == 3
            assert all(r.output == "Async response" for r in results)

    @pytest.mark.asyncio
    async def test_execute_batch_async_concurrency_limit(self, llm_client, mock_async_response):
        prompts = [f"Prompt {i}" for i in range(20)]

        with patch("promptlightning.llm.client.acompletion", return_value=mock_async_response) as mock_acompletion:
            results = await llm_client.execute_batch_async(prompts, "claude-3-opus", max_concurrency=5)

            assert len(results) == 20
            assert mock_acompletion.call_count == 20


class TestStreamingExecution:
    def test_execute_stream(self, llm_client):
        mock_chunks = []
        for text in ["Hello", " world", "!"]:
            chunk = Mock()
            chunk.choices = [Mock()]
            chunk.choices[0].delta = Mock()
            chunk.choices[0].delta.content = text
            mock_chunks.append(chunk)

        with patch("promptlightning.llm.client.completion", return_value=iter(mock_chunks)):
            chunks = list(llm_client.execute_stream("Test prompt", "gpt-4"))

            assert chunks == ["Hello", " world", "!"]

    @pytest.mark.asyncio
    async def test_execute_stream_async(self, llm_client):
        async def mock_async_iter():
            for text in ["Hello", " async", "!"]:
                chunk = Mock()
                chunk.choices = [Mock()]
                chunk.choices[0].delta = Mock()
                chunk.choices[0].delta.content = text
                yield chunk

        with patch("promptlightning.llm.client.acompletion", return_value=mock_async_iter()):
            chunks = []
            async for chunk in llm_client.execute_stream_async("Test prompt", "gpt-4"):
                chunks.append(chunk)

            assert chunks == ["Hello", " async", "!"]

    def test_execute_stream_error_handling(self, llm_client):
        with patch("promptlightning.llm.client.completion", side_effect=APIError(
            status_code=500,
            message="Server error",
            llm_provider="openai",
            model="gpt-4"
        )):
            with pytest.raises(LLMError) as exc_info:
                list(llm_client.execute_stream("Test prompt", "gpt-4"))

            assert "API error" in str(exc_info.value)
