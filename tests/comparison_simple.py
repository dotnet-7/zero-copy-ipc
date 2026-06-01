"""Simple comparison between ZeroCopyDict and multiprocessing.Manager().dict()"""

import time
import multiprocessing as mp
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zero_copy_ipc import ZeroCopyDict


def benchmark_write(d, iterations):
    """Test write performance"""
    start = time.time()
    for i in range(iterations):
        d[f"key_{i}"] = f"value_{i}"
    elapsed = time.time() - start
    return elapsed, iterations / elapsed


def benchmark_read(d, iterations):
    """Test read performance"""
    start = time.time()
    for i in range(iterations):
        _ = d[f"key_{i}"]
    elapsed = time.time() - start
    return elapsed, iterations / elapsed


def benchmark_update(d, iterations):
    """Test update performance (KEY DIFFERENCE!)"""
    start = time.time()
    for i in range(iterations):
        d[f"key_{i}"] = f"updated_value_{i}"
    elapsed = time.time() - start
    return elapsed, iterations / elapsed


def benchmark_delete(d, iterations):
    """Test delete performance"""
    start = time.time()
    for i in range(iterations):
        del d[f"key_{i}"]
    elapsed = time.time() - start
    return elapsed, iterations / elapsed


def worker_zerocopy(name, iterations, results):
    """Worker process for ZeroCopyDict"""
    try:
        d = ZeroCopyDict.attach(name)
        
        # Read test
        start = time.time()
        for i in range(iterations):
            _ = d[f"key_{i}"]
        elapsed = time.time() - start
        
        results.put(('zerocopy_read', elapsed, iterations / elapsed))
        
        # Update test (one key)
        start = time.time()
        for i in range(100):
            d["test_key"] = f"value_{i}"
        elapsed = time.time() - start
        
        results.put(('zerocopy_update', elapsed, 100 / elapsed))
        
        d.close()
    except Exception as e:
        results.put(('error', str(e), 0))


def worker_manager(shared_dict, iterations, results):
    """Worker process for multiprocessing.Manager"""
    try:
        # Read test
        start = time.time()
        for i in range(iterations):
            _ = shared_dict[f"key_{i}"]
        elapsed = time.time() - start
        
        results.put(('manager_read', elapsed, iterations / elapsed))
        
        # Update test (one key)
        start = time.time()
        for i in range(100):
            shared_dict["test_key"] = f"value_{i}"
        elapsed = time.time() - start
        
        results.put(('manager_update', elapsed, 100 / elapsed))
    except Exception as e:
        results.put(('error', str(e), 0))


def main():
    """Run comparison"""
    print("=" * 70)
    print("ZeroCopyDict vs multiprocessing.Manager().dict() Comparison")
    print("=" * 70)
    
    iterations = 1000  # 测试规模
    
    # ==================== 单进程对比 ====================
    print(f"\n[Single Process Tests] - {iterations} iterations")
    print("-" * 70)
    
    # 1. ZeroCopyDict
    print("\n1. ZeroCopyDict (Zero-Copy)")
    name = f"comparison_{os.getpid()}"
    d1 = ZeroCopyDict.create(name, max_items=iterations*2, heap_size=10*1024*1024)
    
    try:
        time_write, ops_write = benchmark_write(d1, iterations)
        time_read, ops_read = benchmark_read(d1, iterations)
        time_update, ops_update = benchmark_update(d1, iterations)
        time_delete, ops_delete = benchmark_delete(d1, iterations)
        
        print(f"   Write:   {time_write:.4f}s  ({ops_write:,.0f} ops/s)")
        print(f"   Read:    {time_read:.4f}s  ({ops_read:,.0f} ops/s)")
        print(f"   Update:  {time_update:.4f}s  ({ops_update:,.0f} ops/s) ← KEY!")
        print(f"   Delete:  {time_delete:.4f}s  ({ops_delete:,.0f} ops/s)")
        
        # Memory stats
        stats = d1.stats()
        gc_stats = d1.gc_stats()
        print(f"   Memory:  {stats['heap_used']/1024:.1f} KB used")
        print(f"   Free:    {gc_stats['free_blocks']} blocks, {gc_stats['free_size']/1024:.1f} KB")
        
    finally:
        d1.close()
    
    # 2. multiprocessing.Manager
    print("\n2. multiprocessing.Manager().dict() (IPC + Serialization)")
    manager = mp.Manager()
    d2 = manager.dict()
    
    time_write_m, ops_write_m = benchmark_write(d2, iterations)
    time_read_m, ops_read_m = benchmark_read(d2, iterations)
    time_update_m, ops_update_m = benchmark_update(d2, iterations)
    time_delete_m, ops_delete_m = benchmark_delete(d2, iterations)
    
    print(f"   Write:   {time_write_m:.4f}s  ({ops_write_m:,.0f} ops/s)")
    print(f"   Read:    {time_read_m:.4f}s  ({ops_read_m:,.0f} ops/s)")
    print(f"   Update:  {time_update_m:.4f}s  ({ops_update_m:,.0f} ops/s) ← KEY!")
    print(f"   Delete:  {time_delete_m:.4f}s  ({ops_delete_m:,.0f} ops/s)")
    
    # ==================== 性能对比 ====================
    print("\n[Performance Comparison]")
    print("-" * 70)
    print(f"{'Operation':<10} {'ZeroCopyDict':<15} {'Manager.dict':<15} {'Ratio':<10}")
    print("-" * 70)
    
    ratios = {
        'Write': ops_write / ops_write_m,
        'Read': ops_read / ops_read_m,
        'Update': ops_update / ops_update_m,
        'Delete': ops_delete / ops_delete_m,
    }
    
    print(f"{'Write':<10} {ops_write:>12,.0f}   {ops_write_m:>12,.0f}   {ratios['Write']:>6.2f}x")
    print(f"{'Read':<10} {ops_read:>12,.0f}   {ops_read_m:>12,.0f}   {ratios['Read']:>6.2f}x")
    print(f"{'Update':<10} {ops_update:>12,.0f}   {ops_update_m:>12,.0f}   {ratios['Update']:>6.2f}x ⭐")
    print(f"{'Delete':<10} {ops_delete:>12,.0f}   {ops_delete_m:>12,.0f}   {ratios['Delete']:>6.2f}x")
    
    avg_ratio = sum(ratios.values()) / len(ratios)
    print("-" * 70)
    print(f"Average Performance: {avg_ratio:.2f}x faster")
    
    # ==================== 多进程IPC对比 ====================
    print(f"\n[Multi-Process IPC Tests] - Worker reads from shared dict")
    print("-" * 70)
    
    # ZeroCopyDict multi-process
    print("\n1. ZeroCopyDict Multi-Process")
    name = f"mp_test_{os.getpid()}"
    d_mp1 = ZeroCopyDict.create(name, max_items=iterations*2, heap_size=10*1024*1024)
    
    # Prepare data
    for i in range(iterations):
        d_mp1[f"key_{i}"] = f"value_{i}"
    d_mp1["test_key"] = "initial"
    
    results = mp.Queue()
    
    try:
        p1 = mp.Process(target=worker_zerocopy, args=(name, iterations, results))
        p1.start()
        p1.join(timeout=10)
        
        if p1.exitcode == 0:
            zerocopy_read_time = 0
            zerocopy_update_time = 0
            
            while not results.empty():
                op, time_val, ops = results.get()
                if op == 'zerocopy_read':
                    zerocopy_read_time = time_val
                    zerocopy_read_ops = ops
                elif op == 'zerocopy_update':
                    zerocopy_update_time = time_val
                    zerocopy_update_ops = ops
            
            print(f"   IPC Read:  {zerocopy_read_time:.4f}s  ({zerocopy_read_ops:,.0f} ops/s)")
            print(f"   IPC Update: {zerocopy_update_time:.4f}s  ({zerocopy_update_ops:,.0f} ops/s)")
        else:
            print("   Worker failed")
        
    finally:
        d_mp1.close()
    
    # multiprocessing.Manager multi-process
    print("\n2. multiprocessing.Manager Multi-Process")
    d_mp2 = manager.dict()
    
    # Prepare data
    for i in range(iterations):
        d_mp2[f"key_{i}"] = f"value_{i}"
    d_mp2["test_key"] = "initial"
    
    results2 = mp.Queue()
    
    p2 = mp.Process(target=worker_manager, args=(d_mp2, iterations, results2))
    p2.start()
    p2.join(timeout=10)
    
    if p2.exitcode == 0:
        manager_read_time = 0
        manager_update_time = 0
        
        while not results2.empty():
            op, time_val, ops = results2.get()
            if op == 'manager_read':
                manager_read_time = time_val
                manager_read_ops = ops
            elif op == 'manager_update':
                manager_update_time = time_val
                manager_update_ops = ops
        
        print(f"   IPC Read:  {manager_read_time:.4f}s  ({manager_read_ops:,.0f} ops/s)")
        print(f"   IPC Update: {manager_update_time:.4f}s  ({manager_update_ops:,.0f} ops/s)")
    else:
        print("   Worker failed")
    
    # ==================== IPC性能对比 ====================
    print("\n[IPC Performance Comparison]")
    print("-" * 70)
    print(f"{'Operation':<15} {'ZeroCopyDict':<15} {'Manager.dict':<15} {'Ratio':<10}")
    print("-" * 70)
    
    ipc_read_ratio = zerocopy_read_ops / manager_read_ops if manager_read_ops > 0 else 0
    ipc_update_ratio = zerocopy_update_ops / manager_update_ops if manager_update_ops > 0 else 0
    
    print(f"{'IPC Read':<15} {zerocopy_read_ops:>12,.0f}   {manager_read_ops:>12,.0f}   {ipc_read_ratio:>6.2f}x")
    print(f"{'IPC Update':<15} {zerocopy_update_ops:>12,.0f}   {manager_update_ops:>12,.0f}   {ipc_update_ratio:>6.2f}x ⭐")
    
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  • Single Process: ZeroCopyDict is {avg_ratio:.2f}x faster on average")
    print(f"  • Multi-Process IPC: ZeroCopyDict is {(ipc_read_ratio+ipc_update_ratio)/2:.2f}x faster")
    print(f"  • Update Performance: {ratios['Update']:.2f}x faster (zero-copy advantage!)")
    print(f"  • Memory Efficiency: No serialization overhead")
    print("=" * 70)
    
    manager.shutdown()


if __name__ == "__main__":
    main()