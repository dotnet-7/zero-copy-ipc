"""Minimal comparison: ZeroCopyDict vs multiprocessing.Manager().dict()"""

import time
import multiprocessing as mp
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zero_copy_ipc import ZeroCopyDict


def main():
    """Main test function"""
    print("=" * 60)
    print("ZeroCopyDict vs multiprocessing.Manager().dict()")
    print("=" * 60)
    
    iterations = 300
    
    # ========== ZeroCopyDict 测试 ==========
    print(f"\n[ZeroCopyDict] - {iterations} iterations")
    
    name = f"test_{os.getpid()}"
    d1 = ZeroCopyDict.create(name, max_items=600, heap_size=5*1024*1024)
    
    try:
        # Write
        start = time.time()
        for i in range(iterations):
            d1[f"key_{i}"] = f"value_{i}"
        write_time = time.time() - start
        write_ops = iterations / write_time if write_time > 0 else 0
        print(f"Write: {write_time:.4f}s ({write_ops:,.0f} ops/s)")
        
        # Read
        start = time.time()
        for i in range(iterations):
            _ = d1[f"key_{i}"]
        read_time = time.time() - start
        read_ops = iterations / read_time if read_time > 0 else 0
        print(f"Read:  {read_time:.4f}s ({read_ops:,.0f} ops/s)")
        
        # Update (重点!)
        start = time.time()
        for i in range(iterations):
            d1[f"key_{i}"] = f"updated_{i}"
        update_time = time.time() - start
        update_ops = iterations / update_time if update_time > 0 else 0
        print(f"Update: {update_time:.4f}s ({update_ops:,.0f} ops/s) ⭐")
        
        # GC stats
        gc_stats = d1.gc_stats()
        print(f"Free blocks: {gc_stats['free_blocks']}, Free size: {gc_stats['free_size']} bytes")
        
    finally:
        d1.close()
    
    # ========== Manager.dict 测试 ==========
    print(f"\n[multiprocessing.Manager().dict()] - {iterations} iterations")
    
    manager = mp.Manager()
    d2 = manager.dict()
    
    try:
        # Write
        start = time.time()
        for i in range(iterations):
            d2[f"key_{i}"] = f"value_{i}"
        write_time_m = time.time() - start
        write_ops_m = iterations / write_time_m if write_time_m > 0 else 0
        print(f"Write: {write_time_m:.4f}s ({write_ops_m:,.0f} ops/s)")
        
        # Read
        start = time.time()
        for i in range(iterations):
            _ = d2[f"key_{i}"]
        read_time_m = time.time() - start
        read_ops_m = iterations / read_time_m if read_time_m > 0 else 0
        print(f"Read:  {read_time_m:.4f}s ({read_ops_m:,.0f} ops/s)")
        
        # Update (重点!)
        start = time.time()
        for i in range(iterations):
            d2[f"key_{i}"] = f"updated_{i}"
        update_time_m = time.time() - start
        update_ops_m = iterations / update_time_m if update_time_m > 0 else 0
        print(f"Update: {update_time_m:.4f}s ({update_ops_m:,.0f} ops/s) ⭐")
        
    finally:
        manager.shutdown()
    
    # ========== 性能对比 ==========
    print("\n" + "=" * 60)
    print("Performance Comparison")
    print("=" * 60)
    
    if write_ops_m > 0 and read_ops_m > 0 and update_ops_m > 0:
        print(f"{'Operation':<10} {'ZeroCopy':<12} {'Manager':<12} {'Ratio':<8}")
        print("-" * 60)
        print(f"{'Write':<10} {write_ops:>8,.0f}    {write_ops_m:>8,.0f}    {write_ops/write_ops_m:>5.2f}x")
        print(f"{'Read':<10} {read_ops:>8,.0f}    {read_ops_m:>8,.0f}    {read_ops/read_ops_m:>5.2f}x")
        print(f"{'Update':<10} {update_ops:>8,.0f}    {update_ops_m:>8,.0f}    {update_ops/update_ops_m:>5.2f}x ⭐")
        print("-" * 60)
        
        avg_ratio = (write_ops/write_ops_m + read_ops/read_ops_m + update_ops/update_ops_m) / 3
        print(f"Average: {avg_ratio:.2f}x faster")
    
    print("=" * 60)
    
    print("\nKey Insights:")
    print("  • ZeroCopyDict: Zero-copy, in-place modification")
    print("  • Manager.dict: IPC + serialization overhead")
    print("  • Update advantage: Freelist GC + pointer update")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)