"""Benchmark for ZeroCopyDict performance."""

import time
import os
from zero_copy_ipc import ZeroCopyDict


def benchmark_operations():
    """Benchmark basic operations."""
    name = f"benchmark_{os.getpid()}"
    iterations = 10000
    
    print("Zero-Copy Dictionary Benchmark")
    print("=" * 60)
    
    d = ZeroCopyDict.create(name, max_items=iterations*2, heap_size=100*1024*1024)
    
    try:
        print(f"\nIterations: {iterations}")
        
        print("\n1. Write Performance...")
        start = time.time()
        for i in range(iterations):
            d[f"key_{i}"] = f"value_{i}"
        elapsed = time.time() - start
        ops_per_sec = iterations / elapsed
        print(f"   Time: {elapsed:.4f}s")
        print(f"   Ops/sec: {ops_per_sec:.2f}")
        print(f"   Latency: {elapsed/iterations*1000000:.2f} μs")
        
        print("\n2. Read Performance...")
        start = time.time()
        for i in range(iterations):
            _ = d[f"key_{i}"]
        elapsed = time.time() - start
        ops_per_sec = iterations / elapsed
        print(f"   Time: {elapsed:.4f}s")
        print(f"   Ops/sec: {ops_per_sec:.2f}")
        print(f"   Latency: {elapsed/iterations*1000000:.2f} μs")
        
        print("\n3. Update Performance...")
        start = time.time()
        for i in range(iterations):
            d[f"key_{i}"] = f"updated_value_{i}"
        elapsed = time.time() - start
        ops_per_sec = iterations / elapsed
        print(f"   Time: {elapsed:.4f}s")
        print(f"   Ops/sec: {ops_per_sec:.2f}")
        print(f"   Latency: {elapsed/iterations*1000000:.2f} μs")
        
        print("\n4. Delete Performance...")
        start = time.time()
        for i in range(iterations):
            del d[f"key_{i}"]
        elapsed = time.time() - start
        ops_per_sec = iterations / elapsed
        print(f"   Time: {elapsed:.4f}s")
        print(f"   Ops/sec: {ops_per_sec:.2f}")
        print(f"   Latency: {elapsed/iterations*1000000:.2f} μs")
        
        print("\n5. Complex Data Performance...")
        d["complex"] = {
            "nested": {
                "data": [1, 2, 3, 4, 5],
                "string": "test string",
                "number": 42.5
            }
        }
        
        start = time.time()
        for i in range(iterations):
            _ = d["complex"]
        elapsed = time.time() - start
        ops_per_sec = iterations / elapsed
        print(f"   Time: {elapsed:.4f}s")
        print(f"   Ops/sec: {ops_per_sec:.2f}")
        print(f"   Latency: {elapsed/iterations*1000000:.2f} μs")
        
        print("\n" + "=" * 60)
        
    finally:
        d.close()


if __name__ == "__main__":
    benchmark_operations()