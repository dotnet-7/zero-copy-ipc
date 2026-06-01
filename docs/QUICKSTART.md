# Quick Start Guide

## Installation

### Option 1: Using pip
```bash
cd zero_copy_ipc
pip install -e .
```

### Option 2: Using setup script
```bash
# Linux/Mac
./install.sh

# Windows
install.bat
```

## Basic Usage

### 1. Create a shared dictionary
```python
from zero_copy_ipc import ZeroCopyDict

# Create with default settings
d = ZeroCopyDict.create("my_dict")

# Create with custom settings
d = ZeroCopyDict.create(
    "my_dict",
    max_items=10000,        # Maximum number of items
    heap_size=100*1024*1024 # 100MB heap space
)
```

### 2. Basic operations
```python
# Write
d["key"] = "value"
d["number"] = 42
d["list"] = [1, 2, 3]
d["dict"] = {"nested": "data"}

# Read
print(d["key"])      # "value"
print(d["number"])   # 42

# Update (O(1) operation)
d["key"] = "new_value"

# Delete
del d["key"]

# Check existence
if "number" in d:
    print("Found!")

# Get with default
value = d.get("missing", "default")

# Length
print(len(d))
```

### 3. Multi-process sharing
```python
# Process 1: Create and write
import time
from zero_copy_ipc import ZeroCopyDict

d1 = ZeroCopyDict.create("shared_data", max_items=1000)
d1["status"] = "processing"
d1["progress"] = 0

for i in range(100):
    d1["progress"] = i
    time.sleep(0.01)

d1["status"] = "done"

# Process 2: Attach and read
from zero_copy_ipc import ZeroCopyDict

d2 = ZeroCopyDict.attach("shared_data")

while d2["status"] != "done":
    print(f"Progress: {d2['progress']}")
    time.sleep(0.1)

print("Task completed!")
```

### 4. Context manager (auto cleanup)
```python
with ZeroCopyDict.create("temp_dict") as d:
    d["key"] = "value"
    # Do work...
    # Auto cleanup when exiting
```

### 5. Get statistics
```python
stats = d.stats()
print(f"Used slots: {stats['used_slots']}")
print(f"Load factor: {stats['load_factor']}")
print(f"Heap used: {stats['heap_used']}")
```

## Running Examples

```bash
# Basic usage
python examples/basic_usage.py

# Multi-process communication
python examples/multiprocess.py

# Performance benchmark
python examples/benchmark.py
```

## Running Tests

```bash
# Quick test (no pytest needed)
python tests/quick_test.py

# Full test suite (requires pytest)
pytest tests/test_dict.py -v
```

## Common Patterns

### Pattern 1: Shared counter
```python
# Process 1
d = ZeroCopyDict.create("counter")
d["count"] = 0

# Multiple processes can increment
d["count"] = d.get("count", 0) + 1
```

### Pattern 2: Shared queue
```python
d = ZeroCopyDict.create("queue")
d["queue_data"] = []

# Producer
queue = d.get("queue_data", [])
queue.append("item1")
d["queue_data"] = queue

# Consumer
queue = d.get("queue_data", [])
if queue:
    item = queue.pop(0)
    d["queue_data"] = queue
```

### Pattern 3: Shared configuration
```python
# Main process sets config
d = ZeroCopyDict.create("config")
d["settings"] = {
    "timeout": 30,
    "retry": 3,
    "debug": False
}

# Worker processes read config
settings = d["settings"]
timeout = settings["timeout"]
```

## Best Practices

1. **Estimate size**: Calculate max_items and heap_size before creation
   - Each item: ~24 bytes overhead + serialized size
   - Example: 10K items with average 1KB data → heap_size = 10MB

2. **Use context manager**: Ensures cleanup
   ```python
   with ZeroCopyDict.create(...) as d:
       # work
   ```

3. **Check stats**: Monitor load factor and heap usage
   ```python
   stats = d.stats()
   if stats['load_factor'] > 0.7:
       print("Consider larger slot_count")
   ```

4. **Clean up**: Call close() or use context manager
   ```python
   d.close()  # Explicit cleanup
   ```

5. **Handle errors**: Catch KeyError and MemoryError
   ```python
   try:
       value = d[key]
   except KeyError:
       # Key doesn't exist
   except MemoryError:
       # Heap full
   ```

## Platform Notes

### Linux
- Best performance
- Shared memory in /dev/shm
- Works out of the box

### Windows
- Similar performance
- Shared memory in temp directory
- Works out of the box

### macOS
- Similar to Linux
- Shared memory in /tmp
- Works out of the box

## Troubleshooting

### Issue: "Heap full" error
**Solution**: Increase heap_size when creating
```python
d = ZeroCopyDict.create("name", heap_size=200*1024*1024)
```

### Issue: "Hash table full" error
**Solution**: Increase max_items/slot_count
```python
d = ZeroCopyDict.create("name", max_items=20000)
```

### Issue: "Could not acquire lock"
**Solution**: Check for zombie processes holding the lock
```bash
# Kill stale processes
pkill -f your_program
```

### Issue: Shared memory not found
**Solution**: Ensure creator process is running
```python
# Creator must be running before attachers
d1 = ZeroCopyDict.create("name")  # Keep running
# d2 = ZeroCopyDict.attach("name")  # Can attach now
```

## Performance Tips

1. **Batch updates**: Minimize lock contention
   ```python
   # Instead of many small updates
   d.update({
       "key1": "value1",
       "key2": "value2",
       "key3": "value3"
   })
   ```

2. **Reuse connections**: Don't repeatedly create/attach
   ```python
   # Bad
   for i in range(100):
       d = ZeroCopyDict.attach("name")
       d[f"key{i}"] = i
       d.close()
   
   # Good
   d = ZeroCopyDict.attach("name")
   for i in range(100):
       d[f"key{i}"] = i
   d.close()
   ```

3. **Preallocate**: Estimate size upfront
   ```python
   # Calculate needed size
   estimated_items = 10000
   avg_item_size = 1024  # 1KB
   heap_size = estimated_items * avg_item_size * 2  # 2x safety
   
   d = ZeroCopyDict.create("name",
       max_items=estimated_items,
       heap_size=heap_size
   )
   ```

## Next Steps

- Read ARCHITECTURE.md for technical details
- Run examples/basic_usage.py
- Run examples/multiprocess.py
- Run tests/quick_test.py
- Check examples/benchmark.py for performance