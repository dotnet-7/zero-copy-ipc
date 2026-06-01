# Architecture Documentation

## Core Design

### Memory Layout

The library uses a fixed slot table + variable heap design:

```
┌─────────────────────────────────────┐
│         Header (64 bytes)            │
│  - Magic: 0x5A45524F                 │
│  - Version: 1                        │
│  - Slot count                        │
│  - Heap size                         │
│  - Used slots                        │
│  - Free list head                    │
│  - Heap used                         │
│  - Reserved                          │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│    Slot Table (24 bytes per slot)    │
│                                      │
│  struct Slot {                       │
│    uint64_t key_offset;              │
│    uint32_t key_size;                │
│    uint64_t value_offset;            │
│    uint32_t value_size;              │
│  }                                   │
│                                      │
│  Total: 24 bytes                     │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│          Heap Area                   │
│                                      │
│  - Keys (variable length)            │
│  - Values (variable length)          │
│  - Sequential allocation             │
│                                      │
└─────────────────────────────────────┘
```

### Key Components

#### 1. MemoryLayout (`memory_layout.py`)
- Manages shared memory region using mmap
- Platform-specific paths (Linux: /dev/shm, Windows: temp dir)
- Header and slot table operations
- Heap read/write operations

#### 2. HashTable (`hash_table.py`)
- Linear probing hash table
- O(1) average lookup/insert/delete
- Slot-based storage
- Collision handling

#### 3. HeapManager (`heap_manager.py`)
- Variable-length data allocation
- Sequential allocation strategy
- Space reuse (future: free list)

#### 4. Serializer (`serializer.py`)
- Uses pickle for Python object serialization
- HIGHEST_PROTOCOL for efficiency
- Key and value serialization

#### 5. ProcessLock (`lock.py`)
- Platform-aware file locking
- Windows: msvcrt.locking
- Unix: fcntl.flock
- Timeout support

#### 6. ZeroCopyDict (`dict.py`)
- Main user-facing API
- Dictionary-like interface
- Context manager support
- Statistics and monitoring

## Performance Characteristics

### Time Complexity

| Operation | Complexity |
|-----------|------------|
| Insert    | O(1) avg   |
| Lookup    | O(1) avg   |
| Delete    | O(1) avg   |
| Update    | O(1) avg   |

### Space Complexity

- Fixed: Header (64B) + Slot table (24B × N)
- Variable: Heap (depends on data size)
- Overhead: ~24 bytes per entry + serialized size

### Memory Operations

1. **Insert**: 
   - Allocate heap space for key and value
   - Write to heap
   - Find slot via hash
   - Update slot pointers (24 bytes)

2. **Update**:
   - Allocate new heap space for value
   - Write new value
   - Update slot's value pointer (8 bytes)
   - Old value space becomes garbage

3. **Delete**:
   - Mark slot as deleted (special marker)
   - Decrement used_slots counter
   - Space remains allocated (future: free list)

## Zero-Copy Benefits

### vs Apache Arrow
- ✅ Mutable: In-place updates
- ✅ No schema: Dynamic Python objects
- ✅ Lower overhead: No Arrow metadata

### vs Serialization
- ✅ No copy: Direct shared memory access
- ✅ No decode: Read directly from memory
- ✅ Instant sync: All processes see updates

### vs Redis/Memcached
- ✅ No network: Local shared memory
- ✅ No protocol: Direct memory access
- ✅ Lower latency: Nanosecond vs millisecond

## Limitations

1. **Platform**: Requires mmap support
2. **Size**: Fixed allocation at creation
3. **Garbage**: No automatic cleanup (future feature)
4. **Locking**: Global lock (could optimize per-slot)
5. **Serialization**: Still uses pickle (could use struct for primitives)

## Future Improvements

1. **Free List**: Reclaim deleted space
2. **Compaction**: Garbage collection
3. **Resize**: Dynamic growth
4. **Per-slot Locks**: Better concurrency
5. **Primitive Optimization**: Direct storage for numbers
6. **Compression**: Reduce serialized size
7. **Transactions**: Atomic multi-key operations

## Usage Patterns

### Single Process
```python
d = ZeroCopyDict.create("name", max_items=1000)
d["key"] = value
d.close()
```

### Multi-Process
```python
# Process 1
d1 = ZeroCopyDict.create("shared", ...)
d1["key"] = "value"

# Process 2
d2 = ZeroCopyDict.attach("shared")
print(d2["key"])  # Instant access
```

### Context Manager
```python
with ZeroCopyDict.create("temp", ...) as d:
    d["key"] = "value"
    # Auto cleanup
```

## Platform Notes

### Linux
- Uses `/dev/shm` for shared memory
- Uses `fcntl.flock` for locking
- Best performance

### Windows
- Uses temp directory for shared memory
- Uses `msvcrt.locking` for locking
- Similar performance

### macOS
- Similar to Linux
- Uses `/tmp` instead of `/dev/shm`