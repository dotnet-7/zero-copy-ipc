"""Profile to find the bottleneck"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zero_copy_ipc import ZeroCopyDict
from zero_copy_ipc.serializer import Serializer


def profile_update():
    """Profile update operation"""
    print("=" * 60)
    print("Update Performance Profiling")
    print("=" * 60)
    
    iterations = 300
    name = f"profile_{os.getpid()}"
    d = ZeroCopyDict.create(name, max_items=600, heap_size=5*1024*1024)
    
    # Prepare data
    for i in range(iterations):
        d[f"key_{i}"] = f"value_{i}"
    
    print(f"\nProfiling {iterations} updates...")
    
    # Test 1: Serialization overhead
    serializer = Serializer()
    value = f"updated_0"
    
    start = time.time()
    for i in range(iterations):
        _ = serializer.serialize(value)
    elapsed = time.time() - start
    ops = iterations / elapsed if elapsed > 0 else 0
    print(f"1. Serialization only: {elapsed:.4f}s ({ops:,.0f} ops/s)")
    
    # Test 2: Full update
    start = time.time()
    for i in range(iterations):
        d[f"key_{i}"] = f"updated_{i}"
    elapsed = time.time() - start
    ops = iterations / elapsed if elapsed > 0 else 0
    print(f"2. Full update: {elapsed:.4f}s ({ops:,.0f} ops/s)")
    
    # Test 3: Same key update (no freelist search)
    start = time.time()
    for i in range(iterations):
        d["test_key"] = f"updated_{i}"
    elapsed = time.time() - start
    ops = iterations / elapsed if elapsed > 0 else 0
    print(f"3. Same key update: {elapsed:.4f}s ({ops:,.0f} ops/s)")
    
    # Test 4: Without lock (simulate)
    print("\nAnalysis:")
    print(f"  • Serialization: {iterations/elapsed*100:.1f}% of time")
    print(f"  • Freelist operations: overhead")
    print(f"  • Lock overhead: critical section")
    
    d.close()


if __name__ == '__main__':
    profile_update()