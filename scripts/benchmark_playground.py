#!/usr/bin/env python3
"""
Performance benchmark script for Playground API optimizations.
Tests response times, compression ratios, and cache effectiveness.
"""

import time
import requests
import json
from typing import Dict, List

def benchmark_endpoint(url: str, iterations: int = 10) -> Dict[str, float]:
    """Benchmark an endpoint and return statistics."""
    times = []
    sizes = []
    
    for _ in range(iterations):
        start = time.time()
        response = requests.get(url)
        duration = (time.time() - start) * 1000
        
        times.append(duration)
        sizes.append(len(response.content))
    
    return {
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "avg_size_bytes": sum(sizes) / len(sizes),
    }

def test_compression(url: str) -> Dict[str, float]:
    """Test compression effectiveness."""
    response_plain = requests.get(url, headers={"Accept-Encoding": "identity"})
    plain_size = len(response_plain.content)
    
    response_gzip = requests.get(url, headers={"Accept-Encoding": "gzip"})
    gzip_size = len(response_gzip.content)
    
    compression_ratio = (1 - gzip_size / plain_size) * 100 if plain_size > 0 else 0
    
    return {
        "plain_size": plain_size,
        "gzip_size": gzip_size,
        "compression_ratio": compression_ratio
    }

def test_cache_effectiveness(url: str, iterations: int = 5) -> Dict[str, float]:
    """Test cache hit performance improvement."""
    start = time.time()
    requests.get(url)
    first_request_ms = (time.time() - start) * 1000
    
    cached_times = []
    for _ in range(iterations):
        start = time.time()
        requests.get(url)
        cached_times.append((time.time() - start) * 1000)
    
    avg_cached_ms = sum(cached_times) / len(cached_times)
    improvement = ((first_request_ms - avg_cached_ms) / first_request_ms) * 100
    
    return {
        "first_request_ms": first_request_ms,
        "avg_cached_ms": avg_cached_ms,
        "improvement_pct": improvement
    }

def main():
    base_url = "http://localhost:3000"
    
    print("=" * 60)
    print("Playground API Performance Benchmark")
    print("=" * 60)
    print()
    
    print("Test 1: Response Times")
    print("-" * 60)
    
    endpoints = [
        "/api/templates",
        "/api/examples",
        "/api/health"
    ]
    
    for endpoint in endpoints:
        try:
            stats = benchmark_endpoint(f"{base_url}{endpoint}")
            print(f"\n{endpoint}:")
            print(f"  Average: {stats['avg_ms']:.2f}ms")
            print(f"  Min:     {stats['min_ms']:.2f}ms")
            print(f"  Max:     {stats['max_ms']:.2f}ms")
            print(f"  P95:     {stats['p95_ms']:.2f}ms")
            print(f"  Size:    {stats['avg_size_bytes']:.0f} bytes")
            
            if stats['avg_ms'] < 50:
                print(f"  Target met (<50ms)")
            else:
                print(f"  Target missed (>50ms)")
        except Exception as e:
            print(f"  Error: {e}")
    
    print()
    print("=" * 60)
    
    print("\nTest 2: Compression Effectiveness")
    print("-" * 60)
    
    for endpoint in ["/api/examples", "/api/templates"]:
        try:
            compression = test_compression(f"{base_url}{endpoint}")
            print(f"\n{endpoint}:")
            print(f"  Plain:       {compression['plain_size']:,} bytes")
            print(f"  Compressed:  {compression['gzip_size']:,} bytes")
            print(f"  Ratio:       {compression['compression_ratio']:.1f}%")
            
            if compression['compression_ratio'] >= 70:
                print(f"  Target met (>70%)")
            else:
                print(f"  Target missed (<70%)")
        except Exception as e:
            print(f"  Error: {e}")
    
    print()
    print("=" * 60)
    
    print("\nTest 3: Cache Effectiveness")
    print("-" * 60)
    
    try:
        cache_stats = test_cache_effectiveness(f"{base_url}/api/templates")
        print(f"\nTemplate List Caching:")
        print(f"  First request:  {cache_stats['first_request_ms']:.2f}ms")
        print(f"  Cached avg:     {cache_stats['avg_cached_ms']:.2f}ms")
        print(f"  Improvement:    {cache_stats['improvement_pct']:.1f}%")
        
        if cache_stats['avg_cached_ms'] < 10:
            print(f"  Cache target met (<10ms)")
        else:
            print(f"  Cache could be faster")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    print("=" * 60)
    print("\nBenchmark Complete!")
    print()

if __name__ == "__main__":
    main()
