"""Simple test for free list."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from zero_copy_ipc import ZeroCopyDict
    from zero_copy_ipc.constants import HEADER_SIZE
    
    print(f"HEADER_SIZE = {HEADER_SIZE}")
    
    # Test basic creation
    name = f"test_simple_{os.getpid()}"
    print(f"Creating dict: {name}")
    
    d = ZeroCopyDict.create(name, max_items=10, heap_size=10240)
    print(f"Created successfully!")
    
    # Write
    d["test"] = "value"
    print(f"Written: d['test'] = {d['test']}")
    
    # Update
    d["test"] = "new_value"
    print(f"Updated: d['test'] = {d['test']}")
    
    # Stats
    stats = d.stats()
    print(f"Stats: {stats}")
    
    # GC stats
    gc_stats = d.gc_stats()
    print(f"GC Stats: {gc_stats}")
    
    # Delete
    del d["test"]
    print(f"Deleted")
    
    gc_stats = d.gc_stats()
    print(f"After delete GC Stats: {gc_stats}")
    
    d.close()
    print("✓ Test passed!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)