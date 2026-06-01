"""Tests for ZeroCopyDict."""

import pytest
import multiprocessing as mp
import time
import os

from zero_copy_ipc import ZeroCopyDict


class TestZeroCopyDict:
    """Test cases for ZeroCopyDict."""
    
    def test_create_and_basic_operations(self):
        """Test creating a dictionary and basic operations."""
        name = f"test_dict_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            assert len(d) == 0
            assert "key1" not in d
            
            d["key1"] = "value1"
            assert len(d) == 1
            assert "key1" in d
            assert d["key1"] == "value1"
            
            d["key2"] = 42
            assert d["key2"] == 42
            
            d["key3"] = [1, 2, 3]
            assert d["key3"] == [1, 2, 3]
            
            d["key4"] = {"nested": "dict"}
            assert d["key4"] == {"nested": "dict"}
        finally:
            d.close()
    
    def test_update_and_delete(self):
        """Test updating and deleting values."""
        name = f"test_dict_update_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            d["key"] = "value1"
            assert d["key"] == "value1"
            
            d["key"] = "value2"
            assert d["key"] == "value2"
            
            del d["key"]
            assert "key" not in d
            
            with pytest.raises(KeyError):
                _ = d["key"]
        finally:
            d.close()
    
    def test_get_and_setdefault(self):
        """Test get and setdefault methods."""
        name = f"test_dict_get_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            assert d.get("key") is None
            assert d.get("key", "default") == "default"
            
            d["key"] = "value"
            assert d.get("key") == "value"
            assert d.get("key", "default") == "value"
            
            result = d.setdefault("new_key", "default_value")
            assert result == "default_value"
            assert d["new_key"] == "default_value"
            
            result = d.setdefault("new_key", "another_value")
            assert result == "default_value"
        finally:
            d.close()
    
    def test_pop(self):
        """Test pop method."""
        name = f"test_dict_pop_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            d["key"] = "value"
            
            result = d.pop("key")
            assert result == "value"
            assert "key" not in d
            
            result = d.pop("nonexistent", "default")
            assert result == "default"
            
            with pytest.raises(KeyError):
                d.pop("nonexistent")
        finally:
            d.close()
    
    def test_update_and_clear(self):
        """Test update and clear methods."""
        name = f"test_dict_update_clear_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            d.update({"key1": "value1", "key2": "value2"})
            assert len(d) == 2
            assert d["key1"] == "value1"
            assert d["key2"] == "value2"
            
            d.clear()
            assert len(d) == 0
        finally:
            d.close()
    
    def test_keys_values_items(self):
        """Test keys, values, and items methods."""
        name = f"test_dict_kvi_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            d["key1"] = "value1"
            d["key2"] = "value2"
            d["key3"] = "value3"
            
            keys = d.keys()
            assert set(keys) == {"key1", "key2", "key3"}
            
            values = d.values()
            assert set(values) == {"value1", "value2", "value3"}
            
            items = d.items()
            assert set(items) == {("key1", "value1"), ("key2", "value2"), ("key3", "value3")}
        finally:
            d.close()
    
    def test_iteration(self):
        """Test iteration over dictionary."""
        name = f"test_dict_iter_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            d["key1"] = "value1"
            d["key2"] = "value2"
            
            keys = list(d)
            assert set(keys) == {"key1", "key2"}
        finally:
            d.close()
    
    def test_stats(self):
        """Test statistics method."""
        name = f"test_dict_stats_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024)
        
        try:
            stats = d.stats()
            assert stats['name'] == name
            assert stats['slot_count'] == 100
            assert stats['used_slots'] == 0
            assert stats['is_owner'] == True
            
            d["key"] = "value"
            stats = d.stats()
            assert stats['used_slots'] == 1
        finally:
            d.close()
    
    def test_context_manager(self):
        """Test context manager usage."""
        name = f"test_dict_ctx_{os.getpid()}_{int(time.time()*1000000)}"
        
        with ZeroCopyDict.create(name, slot_count=100, heap_size=1024*1024) as d:
            d["key"] = "value"
            assert d["key"] == "value"
    
    def test_large_values(self):
        """Test storing large values."""
        name = f"test_dict_large_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=100, heap_size=10*1024*1024)
        
        try:
            large_list = list(range(10000))
            d["large"] = large_list
            assert d["large"] == large_list
            
            large_dict = {f"key{i}": i for i in range(1000)}
            d["large_dict"] = large_dict
            assert d["large_dict"] == large_dict
        finally:
            d.close()


def worker_process(name: str, results: mp.Queue):
    """Worker process for multi-process testing."""
    try:
        d = ZeroCopyDict.attach(name)
        
        d["worker_key"] = "worker_value"
        
        for i in range(10):
            key = f"shared_{i}"
            if key in d:
                results.put(("found", key, d[key]))
                break
        
        time.sleep(0.1)
        
        results.put(("done", None, None))
        
        d.close()
    except Exception as e:
        results.put(("error", str(e), None))


class TestMultiProcess:
    """Test multi-process access."""
    
    def test_multiprocess_access(self):
        """Test concurrent access from multiple processes."""
        name = f"test_dict_mp_{os.getpid()}_{int(time.time()*1000000)}"
        
        d = ZeroCopyDict.create(name, slot_count=1000, heap_size=10*1024*1024)
        
        try:
            for i in range(10):
                d[f"shared_{i}"] = f"value_{i}"
            
            results = mp.Queue()
            
            processes = []
            for _ in range(3):
                p = mp.Process(target=worker_process, args=(name, results))
                p.start()
                processes.append(p)
            
            for p in processes:
                p.join(timeout=5)
            
            d.close()
            
            found_count = 0
            done_count = 0
            errors = []
            
            while not results.empty():
                msg_type, key, value = results.get()
                if msg_type == "found":
                    found_count += 1
                elif msg_type == "done":
                    done_count += 1
                elif msg_type == "error":
                    errors.append(key)
            
            assert done_count == 3
            assert len(errors) == 0
        finally:
            try:
                d.close()
            except:
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])