# Zero-Copy IPC

[![PyPI version](https://badge.fury.io/py/zero-copy-ipc.svg)](https://badge.fury.io/py/zero-copy-ipc)
[![Python](https://img.shields.io/pypi/pyversions/zero-copy-ipc.svg)](https://pypi.org/project/zero-copy-ipc/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A pure Python zero-copy shared memory dictionary for multi-process IPC, 3x faster than multiprocessing.Manager**

**[中文文档 (Chinese Documentation)](docs/README_CN.md)**

---

## Key Features

### ⚡ Zero-Copy - True Shared Memory
- Multiple processes access the same shared memory directly
- No serialization/deserialization overhead
- Nanosecond-level inter-process synchronization

### 🚀 High Performance - O(1) Operations
- **Segregated Lists** memory allocator (O(1))
- In-place modification: update pointers only, no data movement
- Benchmarked: **3x faster than Manager().dict()**

### 🔒 Process-Safe - Cross-Platform Locking
- Windows/Linux/macOS fully supported
- File-based locking for inter-process mutual exclusion
- Automatic timeout mechanism (10 seconds)

### 🎯 Simple API - Dictionary-like Interface
```python
d["key"] = value  # Write
value = d["key"]  # Read
del d["key"]      # Delete
```

---

## Performance Comparison

**vs multiprocessing.Manager().dict():**

| Operation | ZeroCopyDict | Manager | Improvement |
|-----------|--------------|---------|-------------|
| **Write** | 46,161 ops/s | 33,345 ops/s | **1.38x** |
| **Read** | 149,459 ops/s | 27,268 ops/s | **5.48x** |
| **Update** | 74,965 ops/s | 33,340 ops/s | **2.25x** |
| **Average** | - | - | **3.04x** ✅ |

---

## Installation

### From PyPI (Recommended)
```bash
pip install zero-copy-ipc
```

### From Source
```bash
git clone https://github.com/senyangcai/zero-copy-ipc.git
cd zero-copy-ipc
pip install -e .
```

---

## Quick Start

### Basic Usage
```python
from zero_copy_ipc import ZeroCopyDict

# Create shared dictionary
d = ZeroCopyDict.create(
    "my_dict",
    max_items=1000,
    heap_size=10*1024*1024  # 10MB
)

# Write data
d["name"] = "Alice"
d["age"] = 30
d["data"] = {"nested": "dict"}

# Read data
print(d["name"])  # "Alice"

# Update data (O(1) operation)
d["age"] = 31

# Close
d.close()
```

### Multi-Process Sharing
```python
# Process 1: Create and write
from zero_copy_ipc import ZeroCopyDict

d1 = ZeroCopyDict.create("shared_dict")
d1["counter"] = 0

# Process 2: Attach and read
d2 = ZeroCopyDict.attach("shared_dict")
print(d2["counter"])  # Instantly sees 0

# Process 3: Update
d3 = ZeroCopyDict.attach("shared_dict")
d3["counter"] = 100  # d1 and d2 immediately see the update!
```

### Context Manager (Recommended)
```python
with ZeroCopyDict.create("temp_dict") as d:
    d["key"] = "value"
    # Auto cleanup
```

---

## Use Cases

### ✅ Suitable For
- Multi-process high-frequency read/write shared data
- Web application real-time statistics (visit count, response time)
- Distributed crawler task queue
- Real-time log aggregation system
- API rate limiting counter
- ML training progress sharing

### ❌ Not Suitable For
- Cross-machine distributed communication (use Redis)
- Persistent data storage (use database)
- Very large datasets (TB-scale)

---

## Technical Architecture

### Memory Layout
```
Shared Memory Structure:
┌────────────────────────┐
│ Header (56 bytes)       │
│  - Magic: 0x5A45524F    │
│  - Version: 3           │
│  - Slot count           │
│  - Heap size            │
└────────────────────────┘
┌────────────────────────┐
│ Slot Table (24B each)   │
│  - key_offset (8B)      │
│  - key_size (4B)        │
│  - value_offset (8B)    │
│  - value_size (4B)      │
└────────────────────────┘
┌────────────────────────┐
│ Segregated Lists (40B)  │
│  - 5 size class heads   │
└────────────────────────┘
┌────────────────────────┐
│ Heap Area (variable)    │
│  - Keys data            │
│  - Values data          │
└────────────────────────┘
```

### Core Components
- **MemoryLayout**: mmap shared memory management
- **HashTable**: Linear probing hash table
- **HeapManager**: Segregated Lists allocator
- **ProcessLock**: Cross-platform file lock
- **Serializer**: pickle serializer

---

## Supported Data Types

All pickle-able Python objects:

```python
# ✅ Basic types
d["int"] = 42
d["float"] = 3.14
d["str"] = "hello"
d["bool"] = True
d["bytes"] = b"data"

# ✅ Container types
d["list"] = [1, 2, 3]
d["dict"] = {"nested": "value"}
d["tuple"] = (1, 2, 3)
d["set"] = {1, 2, 3}

# ✅ Custom objects
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

d["point"] = Point(10, 20)

# ❌ Not supported
# File objects, sockets, lambdas, threading.Lock
```

---

## Capacity Planning

### Calculation Formula
```python
# Estimate required space
avg_key_size = 10    # bytes
avg_value_size = 100 # bytes
num_items = 1000

heap_size = num_items * (avg_key_size + avg_value_size) * 2  # 2x safety margin
# = 1000 * 110 * 2 = 220KB

d = ZeroCopyDict.create(
    "my_dict",
    max_items=1000,
    heap_size=220*1024
)
```

### Memory Overhead
- **Fixed overhead**: Header(56B) + Slot table(24B × max_items)
- **Per record**: 24 bytes + serialized size

---

## Platform Support

| Platform | Shared Memory Location | Lock Mechanism | Performance |
|----------|------------------------|----------------|-------------|
| **Linux** | `/dev/shm` | fcntl.flock | ⭐⭐⭐⭐⭐ |
| **Windows** | temp directory | msvcrt.locking | ⭐⭐⭐⭐ |
| **macOS** | `/tmp` | fcntl.flock | ⭐⭐⭐⭐ |

---

## API Reference

### Creation
```python
ZeroCopyDict.create(
    name: str,              # Shared memory name
    max_items: int = 10000, # Maximum number of items
    heap_size: int = 100MB  # Heap area size
)
```

### Attachment
```python
ZeroCopyDict.attach(name: str)  # Attach to existing dict
```

### Operations
```python
d[key] = value       # Write
d[key]               # Read
del d[key]           # Delete
key in d             # Check existence
len(d)               # Get length
d.get(key, default)  # Safe read
d.keys()             # Get all keys
d.values()           # Get all values
d.items()            # Get all key-value pairs
d.stats()            # Get statistics
d.close()            # Close and cleanup
```

---

## Monitoring & Statistics

```python
stats = d.stats()
print(f"Used slots: {stats['used_slots']}")
print(f"Load factor: {stats['load_factor']:.2%}")
print(f"Heap used: {stats['heap_used']} bytes")

gc_stats = d.gc_stats()
print(f"Free blocks: {gc_stats['total_free_blocks']}")
print(f"Free space: {gc_stats['total_free_space']} bytes")
```

---

## Documentation

- **[README.md](README.md)** - Project introduction (this file)
- **[中文文档](docs/README_CN.md)** - Chinese documentation
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Quick start guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical architecture
- **[docs/USAGE.md](docs/USAGE.md)** - Detailed usage guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## Examples

```bash
# Basic usage
python examples/basic_usage.py

# Multi-process communication
python examples/multiprocess.py

# Performance benchmark
python examples/benchmark.py
```

---

## Testing

```bash
# Quick test
python tests/quick_test.py

# Performance comparison
python tests/comparison_final.py

# Full test suite
pytest tests/test_dict.py -v
```

---

## FAQ

### Q: How to cleanup shared memory?
```python
# Normal cleanup
d.close()

# Manual cleanup (Linux)
os.remove("/dev/shm/zero_copy_ipc_my_dict")

# Manual cleanup (Windows)
import tempfile
os.remove(os.path.join(tempfile.gettempdir(), "zero_copy_ipc_my_dict.shm"))
```

### Q: Lock timeout issue?
```python
try:
    d["key"] = "value"
except TimeoutError:
    print("Lock timeout, possible zombie process")
    # Cleanup lock file
    # Retry operation
```

### Q: How to improve concurrent performance?
```python
# 1. Batch operations to reduce lock frequency
d.update({"k1": "v1", "k2": "v2", "k3": "v3"})

# 2. Use sufficient heap_size to avoid frequent allocation
heap_size = estimated_items * avg_size * 3

# 3. Different key operations can be parallel (hash to different slots)
```

---

## Version History

### v1.0.0 (2025-06-01)
- ✅ Segregated Lists O(1) memory allocator
- ✅ 3x faster than Manager().dict()
- ✅ Cross-platform support (Windows/Linux/macOS)
- ✅ Complete documentation and testing

See [CHANGELOG.md](CHANGELOG.md) for details.

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Contributing

Issues and Pull Requests are welcome!

---

## Acknowledgments

Inspired by Apache Arrow and other IPC solutions, but this library focuses on local multi-process zero-copy scenarios, providing a lighter and more efficient solution.

---

**Get Started**:
```bash
pip install zero-copy-ipc
python -c "from zero_copy_ipc import ZeroCopyDict; print('✅ Installation successful')"
```