from __future__ import annotations
import time
import asyncio
from typing import Optional, Any, List, AsyncIterator, Iterator
from contextlib import asynccontextmanager
import litellm
from litellm import completion, acompletion
from litellm.exceptions import (
    AuthenticationError,
    RateLimitError as LiteLLMRateLimitError,
    APIError,
    Timeout,
    BadRequestError
)

from ..exceptions import APIKeyError, RateLimitError, ModelNotFoundError, LLMError
from .models import ExecutionResult


class LLMClient:
    def __init__(
        self,
        max_connections: int = 100,
        max_keepalive: int = 20,
        enable_cache: bool = False,
        cache_ttl: int = 60
    ):
        litellm.suppress_debug_info = True
        litellm.drop_params = True

        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl

        self._cache: dict[str, tuple[ExecutionResult, float]] = {}
        self._circuit_breaker: dict[str, dict[str, Any]] = {}

    def _get_cache_key(self, prompt: str, model: str, **kwargs: Any) -> str:
        params_str = str(sorted(kwargs.items()))
        return f"{model}:{hash(prompt)}:{hash(params_str)}"

    def _get_from_cache(self, cache_key: str) -> Optional[ExecutionResult]:
        if not self.enable_cache:
            return None

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, result: ExecutionResult):
        if self.enable_cache:
            self._cache[cache_key] = (result, time.time())

    def _check_circuit_breaker(self, provider: str) -> bool:
        if provider not in self._circuit_breaker:
            return True

        breaker = self._circuit_breaker[provider]
        if breaker["state"] == "open":
            if time.time() - breaker["opened_at"] > breaker["timeout"]:
                breaker["state"] = "half-open"
                return True
            return False
        return True

    def _record_failure(self, provider: str):
        if provider not in self._circuit_breaker:
            self._circuit_breaker[provider] = {
                "failures": 0,
                "state": "closed",
                "opened_at": 0,
                "timeout": 30
            }

        breaker = self._circuit_breaker[provider]
        breaker["failures"] += 1

        if breaker["failures"] >= 5:
            breaker["state"] = "open"
            breaker["opened_at"] = time.time()

    def _record_success(self, provider: str):
        if provider in self._circuit_breaker:
            breaker = self._circuit_breaker[provider]
            if breaker["state"] == "half-open":
                breaker["state"] = "closed"
                breaker["failures"] = 0

    def _build_params(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any]:
        params = {
            "model": model,
            "messages": kwargs.pop("messages", [{"role": "user", "content": prompt}]),
            "timeout": kwargs.pop("timeout", 120),
            **kwargs
        }
        return params

    def _parse_response(
        self,
        response: Any,
        model: str,
        start_time: float
    ) -> ExecutionResult:
        latency_ms = int((time.time() - start_time) * 1000)

        output = response.choices[0].message.content or ""
        provider = response._hidden_params.get("custom_llm_provider", "unknown")
        tokens_in = response.usage.prompt_tokens if response.usage else 0
        tokens_out = response.usage.completion_tokens if response.usage else 0

        cost_usd = 0.0
        if hasattr(response, '_hidden_params') and 'response_cost' in response._hidden_params:
            cost_usd = float(response._hidden_params['response_cost'])

        return ExecutionResult(
            output=output,
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            latency_ms=latency_ms
        )

    def _handle_exceptions(self, e: Exception, model: str):
        if isinstance(e, AuthenticationError):
            raise APIKeyError(f"Invalid or missing API key for model '{model}': {str(e)}") from e
        elif isinstance(e, LiteLLMRateLimitError):
            raise RateLimitError(f"Rate limit exceeded for model '{model}': {str(e)}") from e
        elif isinstance(e, BadRequestError):
            if "model" in str(e).lower() or "not found" in str(e).lower():
                raise ModelNotFoundError(f"Model '{model}' not found or not available: {str(e)}") from e
            raise LLMError(f"Bad request for model '{model}': {str(e)}") from e
        elif isinstance(e, Timeout):
            raise LLMError(f"Request timeout for model '{model}': {str(e)}") from e
        elif isinstance(e, APIError):
            raise LLMError(f"API error for model '{model}': {str(e)}") from e
        else:
            raise LLMError(f"Unexpected error executing model '{model}': {str(e)}") from e

    def execute(
        self,
        prompt: str,
        model: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any
    ) -> ExecutionResult:
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        provider = model.split('/')[0] if '/' in model else 'unknown'
        if not self._check_circuit_breaker(provider):
            raise LLMError(f"Circuit breaker open for provider '{provider}'")

        params = self._build_params(prompt, model, **kwargs)

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = completion(**params)
                result = self._parse_response(response, model, start_time)

                self._record_success(provider)
                self._set_cache(cache_key, result)
                return result

            except (LiteLLMRateLimitError, Timeout, APIError) as e:
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                self._record_failure(provider)
                self._handle_exceptions(e, model)
            except Exception as e:
                self._record_failure(provider)
                self._handle_exceptions(e, model)

        raise LLMError(f"Failed to execute model '{model}' after {max_retries} retries")

    async def execute_async(
        self,
        prompt: str,
        model: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs: Any
    ) -> ExecutionResult:
        cache_key = self._get_cache_key(prompt, model, **kwargs)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        provider = model.split('/')[0] if '/' in model else 'unknown'
        if not self._check_circuit_breaker(provider):
            raise LLMError(f"Circuit breaker open for provider '{provider}'")

        params = self._build_params(prompt, model, **kwargs)

        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = await acompletion(**params)
                result = self._parse_response(response, model, start_time)

                self._record_success(provider)
                self._set_cache(cache_key, result)
                return result

            except (LiteLLMRateLimitError, Timeout, APIError) as e:
                if attempt < max_retries - 1:
                    delay = retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                self._record_failure(provider)
                self._handle_exceptions(e, model)
            except Exception as e:
                self._record_failure(provider)
                self._handle_exceptions(e, model)

        raise LLMError(f"Failed to execute model '{model}' after {max_retries} retries")

    def execute_batch(
        self,
        prompts: List[str],
        model: str,
        **kwargs: Any
    ) -> List[ExecutionResult]:
        results = []
        for prompt in prompts:
            result = self.execute(prompt, model, **kwargs)
            results.append(result)
        return results

    async def execute_batch_async(
        self,
        prompts: List[str],
        model: str,
        max_concurrency: int = 10,
        **kwargs: Any
    ) -> List[ExecutionResult]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_with_semaphore(prompt: str):
            async with semaphore:
                return await self.execute_async(prompt, model, **kwargs)

        tasks = [execute_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    def execute_stream(
        self,
        prompt: str,
        model: str,
        **kwargs: Any
    ) -> Iterator[str]:
        params = self._build_params(prompt, model, **kwargs)
        params["stream"] = True

        provider = model.split('/')[0] if '/' in model else 'unknown'
        if not self._check_circuit_breaker(provider):
            raise LLMError(f"Circuit breaker open for provider '{provider}'")

        try:
            response = completion(**params)
            for chunk in response:
                if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self._record_failure(provider)
            self._handle_exceptions(e, model)

    async def execute_stream_async(
        self,
        prompt: str,
        model: str,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        params = self._build_params(prompt, model, **kwargs)
        params["stream"] = True

        provider = model.split('/')[0] if '/' in model else 'unknown'
        if not self._check_circuit_breaker(provider):
            raise LLMError(f"Circuit breaker open for provider '{provider}'")

        try:
            response = await acompletion(**params)
            async for chunk in response:
                if hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            self._record_failure(provider)
            self._handle_exceptions(e, model)

    def clear_cache(self):
        self._cache.clear()

    def reset_circuit_breakers(self):
        self._circuit_breaker.clear()
