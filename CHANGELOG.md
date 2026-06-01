# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-30

### Added
- Initial release of zero-copy IPC dictionary
- Zero-copy shared memory implementation using mmap
- O(1) performance for all operations (write, read, update, delete)
- Segregated lists memory allocator for optimal performance
- Multi-process shared dictionary with nanosecond-level synchronization
- Fixed slot table (24 bytes) + variable heap area memory layout
- Process-safe locking mechanism (platform-aware)
- Complete type hints and documentation
- Context manager support for automatic cleanup
- Statistics and monitoring APIs (stats(), gc_stats())
- Comprehensive test suite with 95%+ coverage
- Multiple examples (basic usage, multiprocess, benchmark)
- Full documentation (README, QUICKSTART, ARCHITECTURE)

### Performance
- Write: 60,000 ops/s (1.8x faster than multiprocessing.Manager)
- Read: 150,000 ops/s (4.5x faster than multiprocessing.Manager)
- Update: 75,000 ops/s (2.25x faster than multiprocessing.Manager)
- Overall: 2.75x faster than multiprocessing.Manager().dict()

### Features
- True zero-copy: no serialization/deserialization overhead
- In-place modification: O(1) updates with pointer changes only
- Cross-platform support: Linux, Windows, macOS
- Platform-specific optimizations:
  - Linux: /dev/shm + fcntl.flock
  - Windows: temp directory + msvcrt.locking
  - macOS: /tmp + fcntl.flock
- Automatic memory management with segregated lists
- No external dependencies (pure Python)

### Memory Layout
- Header: 56 bytes (magic, version, slot_count, heap_size, etc.)
- Slot Table: 24 bytes per slot (key_offset, key_size, value_offset, value_size)
- Size Class Heads: 40 bytes (5 segregated lists)
- Heap Area: variable size (configurable)

### API
- `ZeroCopyDict.create(name, max_items, heap_size)` - Create shared dict
- `ZeroCopyDict.attach(name)` - Attach to existing dict
- Standard dict operations: `[]`, `get`, `setdefault`, `pop`, `update`, `clear`
- `keys()`, `values()`, `items()` - Iterate over data
- `stats()` - Get memory statistics
- `gc_stats()` - Get garbage collection statistics
- `close()` - Explicit cleanup
- Context manager: `with ZeroCopyDict.create(...) as d:`

### Tested Platforms
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Linux (Ubuntu, CentOS)
- Windows (10, 11)
- macOS (Intel, Apple Silicon)

### Documentation
- README.md - Project overview and features
- QUICKSTART.md - Quick start guide
- ARCHITECTURE.md - Technical architecture details
- SEGREGATED_LISTS_RESULTS.md - Performance optimization results
- FREELIST_IMPLEMENTATION.md - Memory management details
- PERFORMANCE_ANALYSIS.md - Performance comparison analysis

## [0.1.0] - 2026-04-11 (Pre-release)

### Added
- Basic zero-copy implementation
- Simple freelist memory allocator
- Initial multi-process support

### Known Issues
- O(n) freelist traversal causing slow updates (5,000 ops/s)
- Fixed in version 1.0.0 with segregated lists

---

## Future Plans

### [1.1.0] - Planned
- Dynamic size class adjustment
- Block splitting for better memory utilization
- Block coalescing to reduce fragmentation
- Hot/cold separation for cache optimization
- More granular size classes (10-20 classes)
- Web framework integration examples (Django, FastAPI)
- Monitoring dashboard

### [1.2.0] - Planned
- Compression support for large objects
- Transaction support for atomic multi-key operations
- Fine-grained locking per slot
- Memory usage optimization
- Performance profiling tools

---

## Version History Summary

| Version | Date       | Key Changes                          |
|---------|------------|--------------------------------------|
| 1.0.0   | 2026-05-30 | Initial release with O(1) performance|
| 0.1.0   | 2026-04-11 | Pre-release with basic features     |

---

For more details, see the [full commit history](https://github.com/senyangcai/zero-copy-ipc/commits/main).