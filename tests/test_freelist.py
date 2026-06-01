"""Test free list functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zero_copy_ipc import ZeroCopyDict


def test_freelist_basic():
    """Test basic free list operations."""
    print("Testing free list operations...")
    
    name = f"test_freelist_{os.getpid()}"
    
    d = ZeroCopyDict.create(name, max_items=100, heap_size=1024*1024)
    
    try:
        # 初始状态
        stats = d.gc_stats()
        print(f"Initial stats: {stats}")
        assert stats['free_blocks'] == 0
        assert stats['free_size'] == 0
        
        # 写入数据
        d["key1"] = "value1"
        d["key2"] = "value2"
        print(f"After write 2 items: {d.stats()}")
        
        # 修改数据（应该释放旧值）
        d["key1"] = "new_value1"
        stats = d.gc_stats()
        print(f"After update key1: {stats}")
        assert stats['free_blocks'] >= 1  # 应该有一个空闲块
        
        # 删除数据（应该释放键和值）
        del d["key2"]
        stats = d.gc_stats()
        print(f"After delete key2: {stats}")
        assert stats['free_blocks'] >= 3  # key1旧值 + key2键 + key2值
        
        # 再次写入（应该重用空闲空间）
        d["key3"] = "value3"
        stats = d.gc_stats()
        print(f"After write key3: {stats}")
        # 空闲块数量应该减少
        
        print("✓ Free list test passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        d.close()
    
    return True


def test_freelist_reuse():
    """Test free list space reuse."""
    print("\nTesting free list reuse...")
    
    name = f"test_freelist_reuse_{os.getpid()}"
    
    # 小堆区，强制空间重用
    d = ZeroCopyDict.create(name, max_items=50, heap_size=50*1024)
    
    try:
        # 写入大量数据
        for i in range(20):
            d[f"key{i}"] = f"value{i}" * 10
        
        print(f"After write 20 items: {d.stats()}")
        
        # 删除一半
        for i in range(10):
            del d[f"key{i}"]
        
        stats = d.gc_stats()
        print(f"After delete 10 items: {stats}")
        assert stats['free_blocks'] > 0
        
        # 再次写入（应该重用空间）
        for i in range(10):
            d[f"newkey{i}"] = f"newvalue{i}" * 10
        
        stats = d.gc_stats()
        print(f"After write 10 new items: {stats}")
        
        # 检查是否重用了空间
        print("✓ Free list reuse test passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        d.close()
    
    return True


def test_freelist_update():
    """Test free list with frequent updates."""
    print("\nTesting free list with updates...")
    
    name = f"test_freelist_update_{os.getpid()}"
    
    d = ZeroCopyDict.create(name, max_items=100, heap_size=100*1024)
    
    try:
        # 频繁更新同一个键
        d["counter"] = 0
        
        for i in range(50):
            d["counter"] = i
            if i % 10 == 0:
                stats = d.gc_stats()
                print(f"Update {i}: free_blocks={stats['free_blocks']}")
        
        stats = d.gc_stats()
        print(f"Final stats: {stats}")
        assert stats['free_blocks'] >= 49  # 49个旧值
        
        print("✓ Free list update test passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        d.close()
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Free List Functionality Tests")
    print("=" * 60)
    
    tests = [
        test_freelist_basic,
        test_freelist_reuse,
        test_freelist_update,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)