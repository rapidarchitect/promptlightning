"""
LLM Client Performance Features Example

Demonstrates the optimized LLM client capabilities:
- Connection pooling and caching
- Async execution for concurrent requests
- Batch processing
- Streaming responses
- Retry logic with exponential backoff
- Circuit breaker pattern
"""

import asyncio
import time
from promptlightning.llm.client import LLMClient


def example_basic_usage():
    """Basic usage with caching enabled"""
    print("=== Basic Usage with Caching ===")

    client = LLMClient(enable_cache=True, cache_ttl=60)

    prompt = "Write a haiku about programming"

    print(f"First call (uncached)...")
    start = time.time()
    result1 = client.execute(prompt, "gpt-3.5-turbo", max_tokens=50)
    elapsed1 = time.time() - start

    print(f"Output: {result1.output}")
    print(f"Latency: {result1.latency_ms}ms, Total time: {elapsed1*1000:.0f}ms")

    print(f"\nSecond call (cached)...")
    start = time.time()
    result2 = client.execute(prompt, "gpt-3.5-turbo", max_tokens=50)
    elapsed2 = time.time() - start

    print(f"Output: {result2.output}")
    print(f"Latency: {result2.latency_ms}ms, Total time: {elapsed2*1000:.0f}ms")
    print(f"Speedup: {elapsed1/elapsed2:.1f}x faster\n")


async def example_async_usage():
    """Async execution for concurrent requests"""
    print("=== Async Execution ===")

    client = LLMClient()

    prompts = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?"
    ]

    print(f"Processing {len(prompts)} prompts concurrently...")
    start = time.time()

    tasks = [
        client.execute_async(prompt, "gpt-3.5-turbo", max_tokens=30)
        for prompt in prompts
    ]

    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    for i, result in enumerate(results):
        print(f"\nPrompt {i+1}: {prompts[i]}")
        print(f"Response: {result.output[:80]}...")
        print(f"Provider: {result.provider}, Latency: {result.latency_ms}ms")

    print(f"\nTotal time: {elapsed:.2f}s")
    print(f"Average per request: {elapsed/len(prompts):.2f}s\n")


async def example_batch_async():
    """Batch processing with concurrency control"""
    print("=== Batch Async Execution ===")

    client = LLMClient()

    prompts = [f"Count to {i}" for i in range(1, 6)]

    print(f"Processing batch of {len(prompts)} prompts with concurrency limit of 2...")
    start = time.time()

    results = await client.execute_batch_async(
        prompts,
        "gpt-3.5-turbo",
        max_concurrency=2,
        max_tokens=20
    )

    elapsed = time.time() - start

    for i, result in enumerate(results):
        print(f"Result {i+1}: {result.output[:50]}...")

    print(f"\nTotal time: {elapsed:.2f}s")
    print(f"Tokens used: {sum(r.tokens_in + r.tokens_out for r in results)}")
    print(f"Total cost: ${sum(r.cost_usd for r in results):.4f}\n")


def example_streaming():
    """Streaming responses for lower latency to first token"""
    print("=== Streaming Execution ===")

    client = LLMClient()

    prompt = "Write a short story about a robot learning to paint"

    print(f"Streaming response...")
    print("Output: ", end="", flush=True)

    start = time.time()
    for chunk in client.execute_stream(prompt, "gpt-3.5-turbo", max_tokens=100):
        print(chunk, end="", flush=True)

    elapsed = time.time() - start
    print(f"\n\nTotal time: {elapsed:.2f}s\n")


async def example_streaming_async():
    """Async streaming for maximum performance"""
    print("=== Async Streaming ===")

    client = LLMClient()

    prompt = "Explain quantum computing in simple terms"

    print(f"Async streaming response...")
    print("Output: ", end="", flush=True)

    start = time.time()
    async for chunk in client.execute_stream_async(prompt, "gpt-3.5-turbo", max_tokens=100):
        print(chunk, end="", flush=True)

    elapsed = time.time() - start
    print(f"\n\nTotal time: {elapsed:.2f}s\n")


def example_retry_logic():
    """Retry logic with exponential backoff"""
    print("=== Retry Logic ===")

    client = LLMClient()

    prompt = "Hello, world!"

    print("Executing with retry logic (max_retries=3, retry_delay=1.0)...")

    try:
        result = client.execute(
            prompt,
            "gpt-3.5-turbo",
            max_retries=3,
            retry_delay=1.0,
            max_tokens=20
        )
        print(f"Success: {result.output}")
        print(f"Latency: {result.latency_ms}ms\n")

    except Exception as e:
        print(f"Failed after retries: {e}\n")


def example_circuit_breaker():
    """Circuit breaker pattern for failing providers"""
    print("=== Circuit Breaker ===")

    client = LLMClient()

    print("Circuit breaker automatically opens after 5 consecutive failures")
    print("and transitions to half-open state after timeout")
    print("This prevents cascading failures and reduces load on failing services\n")

    print("To reset circuit breakers manually:")
    print("client.reset_circuit_breakers()\n")


def example_cache_management():
    """Cache management utilities"""
    print("=== Cache Management ===")

    client = LLMClient(enable_cache=True, cache_ttl=60)

    print("Cache enabled with 60s TTL")

    result = client.execute("Test prompt", "gpt-3.5-turbo", max_tokens=10)
    print(f"First call: {result.latency_ms}ms")

    result = client.execute("Test prompt", "gpt-3.5-turbo", max_tokens=10)
    print(f"Cached call: {result.latency_ms}ms (instant)")

    print("\nClearing cache...")
    client.clear_cache()

    result = client.execute("Test prompt", "gpt-3.5-turbo", max_tokens=10)
    print(f"After clear: {result.latency_ms}ms\n")


def example_performance_comparison():
    """Compare sync vs async vs batch performance"""
    print("=== Performance Comparison ===")

    prompts = [
        "What is AI?",
        "What is ML?",
        "What is DL?",
        "What is NLP?",
        "What is CV?"
    ]

    print(f"Processing {len(prompts)} prompts...\n")

    client = LLMClient()

    print("1. Synchronous (sequential):")
    start = time.time()
    for prompt in prompts:
        client.execute(prompt, "gpt-3.5-turbo", max_tokens=20)
    sync_time = time.time() - start
    print(f"   Time: {sync_time:.2f}s\n")

    print("2. Batch (sequential internally):")
    start = time.time()
    client.execute_batch(prompts, "gpt-3.5-turbo", max_tokens=20)
    batch_time = time.time() - start
    print(f"   Time: {batch_time:.2f}s\n")


async def async_comparison():
    client = LLMClient()

    prompts = [
        "What is AI?",
        "What is ML?",
        "What is DL?",
        "What is NLP?",
        "What is CV?"
    ]

    print("3. Async batch (concurrent):")
    start = time.time()
    await client.execute_batch_async(prompts, "gpt-3.5-turbo", max_tokens=20)
    async_time = time.time() - start
    print(f"   Time: {async_time:.2f}s\n")

    print(f"Speedup (async vs sync): {5.0/async_time:.1f}x faster (theoretical)")


if __name__ == "__main__":
    print("=" * 60)
    print("LLM Client Performance Features Examples")
    print("=" * 60)
    print("\nNOTE: These examples require valid API keys in environment")
    print("Set OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.\n")

    example_basic_usage()

    asyncio.run(example_async_usage())

    asyncio.run(example_batch_async())

    example_streaming()

    asyncio.run(example_streaming_async())

    example_retry_logic()

    example_circuit_breaker()

    example_cache_management()

    example_performance_comparison()

    asyncio.run(async_comparison())

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
