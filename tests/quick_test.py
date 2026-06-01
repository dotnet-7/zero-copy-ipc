"""Quick test without pytest."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zero_copy_ipc import ZeroCopyDict


def test_basic():
    """Test basic functionality."""
    print("Testing basic operations...")
    
    name = f"quick_test_{os.getpid()}"
    
    try:
        d = ZeroCopyDict.create(name, max_items=100, heap_size=1024*1024)
        
        d["key1"] = "value1"
        assert d["key1"] == "value1"
        print("✓ Write and read")
        
        d["key2"] = 42
        assert d["key2"] == 42
        print("✓ Integer value")
        
        d["key3"] = [1, 2, 3]
        assert d["key3"] == [1, 2, 3]
        print("✓ List value")
        
        d["key4"] = {"nested": "dict"}
        assert d["key4"] == {"nested": "dict"}
        print("✓ Dict value")
        
        del d["key1"]
        assert "key1" not in d
        print("✓ Delete")
        
        stats = d.stats()
        print(f"✓ Stats: {stats}")
        
        d.close()
        print("\nAll tests passed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_basic()
    sys.exit(0 if success else 1)