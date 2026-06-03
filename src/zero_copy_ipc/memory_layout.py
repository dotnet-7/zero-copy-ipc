"""Memory layout and slot management with segregated lists."""

import mmap
import os
import platform
import tempfile
from typing import Optional, Tuple, List
import struct

from .constants import (
    HEADER_SIZE, SLOT_SIZE, HEADER_PACK, HEADER_UNPACK,
    SLOT_PACK, SLOT_UNPACK, SLOT_EMPTY, SLOT_DELETED,
    MAGIC_NUMBER, VERSION, HASH_SEED,
    FREE_BLOCK_SIZE, FREE_BLOCK_PACK, FREE_BLOCK_UNPACK,
    FREE_BLOCK_MAGIC, FREE_LIST_END, NUM_SIZE_CLASSES
)


class Slot:
    """Represents a single slot in the slot table."""
    
    __slots__ = ['key_offset', 'key_size', 'value_offset', 'value_size']
    
    def __init__(
        self,
        key_offset: int = SLOT_EMPTY,
        key_size: int = 0,
        value_offset: int = SLOT_EMPTY,
        value_size: int = 0
    ):
        self.key_offset = key_offset
        self.key_size = key_size
        self.value_offset = value_offset
        self.value_size = value_size
    
    def is_empty(self) -> bool:
        return self.key_offset == SLOT_EMPTY
    
    def is_deleted(self) -> bool:
        return self.key_offset == SLOT_DELETED
    
    def is_used(self) -> bool:
        return not self.is_empty() and not self.is_deleted()
    
    def pack(self) -> bytes:
        return SLOT_PACK(self.key_offset, self.key_size, self.value_offset, self.value_size)
    
    @staticmethod
    def unpack(data: bytes) -> 'Slot':
        key_offset, key_size, value_offset, value_size = SLOT_UNPACK(data)
        return Slot(key_offset, key_size, value_offset, value_size)


class MemoryLayout:
    """Manages the shared memory layout with segregated lists."""
    
    def __init__(self, shm_name: str, create: bool = False, 
                 slot_count: int = 0, heap_size: int = 0):
        self.shm_name = shm_name
        self._fd: Optional[int] = None
        self._mmap: Optional[mmap.mmap] = None
        self._create = create
        self._is_windows = platform.system() == 'Windows'
        self._heap_start: Optional[int] = None  # 缓存heap_start
        
        if create:
            self._create_memory(slot_count, heap_size)
        else:
            self._attach_memory()
    
    def _get_shm_path(self) -> str:
        """Get platform-specific shared memory path."""
        if self._is_windows:
            shm_dir = os.path.join(tempfile.gettempdir(), 'zero_copy_ipc')
            os.makedirs(shm_dir, exist_ok=True)
            return os.path.join(shm_dir, f"{self.shm_name}.shm")
        else:
            return f"/dev/shm/{self.shm_name}"
    
    def _create_memory(self, slot_count: int, heap_size: int):
        """Create new shared memory region with segregated lists."""
        # Segregated lists heads需要额外空间
        segregated_heads_size = NUM_SIZE_CLASSES * 8  # 5个size class heads，每个8字节
        total_size = HEADER_SIZE + slot_count * SLOT_SIZE + segregated_heads_size + heap_size
        
        path = self._get_shm_path()
        self._fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        os.ftruncate(self._fd, total_size)
        
        self._mmap = mmap.mmap(self._fd, total_size, access=mmap.ACCESS_WRITE)
        
        header = HEADER_PACK(
            MAGIC_NUMBER, VERSION, slot_count, heap_size,
            0, 0, 0, segregated_heads_size  # heap_used=0, segregated_heads_size在reserved字段
        )
        assert self._mmap is not None
        self._mmap[0:HEADER_SIZE] = header
        
        # 初始化所有slot为empty
        for i in range(slot_count):
            offset = HEADER_SIZE + i * SLOT_SIZE
            self._mmap[offset:offset + SLOT_SIZE] = Slot().pack()
        
        # 初始化segregated lists heads为END
        segregated_heads_start = HEADER_SIZE + slot_count * SLOT_SIZE
        for i in range(NUM_SIZE_CLASSES):
            offset = segregated_heads_start + i * 8
            self._mmap[offset:offset + 8] = struct.pack('<Q', FREE_LIST_END)
        
        # 计算heap_start（缓存）
        self._heap_start = segregated_heads_start + segregated_heads_size
    
    def _attach_memory(self):
        """Attach to existing shared memory region."""
        path = self._get_shm_path()
        self._fd = os.open(path, os.O_RDWR)
        
        self._mmap = mmap.mmap(self._fd, 0, access=mmap.ACCESS_WRITE)
        
        magic, version = self.read_header()[:2]
        if magic != MAGIC_NUMBER:
            raise ValueError(f"Invalid magic number: {magic}")
        if version != VERSION:
            raise ValueError(f"Unsupported version: {version}")
        
        # 计算heap_start（缓存）
        _, _, slot_count, _, _, _, _, segregated_heads_size = self.read_header()
        self._heap_start = HEADER_SIZE + slot_count * SLOT_SIZE + segregated_heads_size
    
    def get_heap_start(self) -> int:
        """Get heap start offset (cached)."""
        if self._heap_start is None:
            _, _, slot_count, _, _, _, _, segregated_heads_size = self.read_header()
            self._heap_start = HEADER_SIZE + slot_count * SLOT_SIZE + segregated_heads_size
        return self._heap_start
    
    def read_header(self) -> Tuple[int, int, int, int, int, int, int, int]:
        """Read header information."""
        assert self._mmap is not None
        data = self._mmap[0:HEADER_SIZE]
        return HEADER_UNPACK(data)
    
    def write_header(
        self,
        slot_count: Optional[int] = None,
        heap_size: Optional[int] = None,
        used_slots: Optional[int] = None,
        free_list_head: Optional[int] = None,
        heap_used: Optional[int] = None
    ):
        """Update header fields."""
        current = list(self.read_header())
        
        if slot_count is not None:
            current[2] = slot_count
        if heap_size is not None:
            current[3] = heap_size
        if used_slots is not None:
            current[4] = used_slots
        if free_list_head is not None:
            current[5] = free_list_head
        if heap_used is not None:
            current[6] = heap_used
        
        assert self._mmap is not None
        header = HEADER_PACK(*current)
        self._mmap[0:HEADER_SIZE] = header
    
    def read_slot(self, index: int) -> Slot:
        """Read a slot from the slot table."""
        assert self._mmap is not None
        offset = HEADER_SIZE + index * SLOT_SIZE
        data = self._mmap[offset:offset + SLOT_SIZE]
        return Slot.unpack(data)
    
    def write_slot(self, index: int, slot: Slot):
        """Write a slot to the slot table."""
        assert self._mmap is not None
        offset = HEADER_SIZE + index * SLOT_SIZE
        self._mmap[offset:offset + SLOT_SIZE] = slot.pack()
    
    def read_heap(self, offset: int, size: int) -> bytes:
        """Read data from heap."""
        heap_size = self.get_heap_size()
        
        if offset + size > heap_size:
            raise ValueError(f"Heap read out of bounds: {offset}+{size} > {heap_size}")
        
        assert self._mmap is not None
        heap_start = self.get_heap_start()
        start = heap_start + offset
        return self._mmap[start:start + size]
    
    def write_heap(self, offset: int, data: bytes):
        """Write data to heap."""
        heap_size = self.get_heap_size()
        size = len(data)
        
        if offset + size > heap_size:
            raise ValueError(f"Heap write out of bounds: {offset}+{size} > {heap_size}")
        
        assert self._mmap is not None
        heap_start = self.get_heap_start()
        start = heap_start + offset
        self._mmap[start:start + size] = data
    
    def get_slot_count(self) -> int:
        """Get total slot count."""
        return self.read_header()[2]
    
    def get_heap_size(self) -> int:
        """Get total heap size."""
        return self.read_header()[3]
    
    def get_used_slots(self) -> int:
        """Get number of used slots."""
        return self.read_header()[4]
    
    def set_used_slots(self, count: int):
        """Set number of used slots."""
        self.write_header(used_slots=count)
    
    def get_heap_used(self) -> int:
        """Get used heap space."""
        return self.read_header()[6]
    
    def set_heap_used(self, used: int):
        """Set used heap space."""
        # heap_used存储在header[6]字段
        self.write_header(heap_used=used)
    
    # ========== Segregated Lists Operations ==========
    
    def get_size_class_head(self, size_class: int) -> int:
        """Get head of segregated list for a size class.
        
        Args:
            size_class: Size class index (0-4)
            
        Returns:
            Head offset of the free list for this size class
        """
        if size_class < 0 or size_class >= NUM_SIZE_CLASSES:
            raise ValueError(f"Invalid size class: {size_class}")
        
        assert self._mmap is not None
        _, _, slot_count, _, _, _, _, _ = self.read_header()
        segregated_heads_start = HEADER_SIZE + slot_count * SLOT_SIZE
        offset = segregated_heads_start + size_class * 8
        
        data = self._mmap[offset:offset + 8]
        return struct.unpack('<Q', data)[0]
    
    def set_size_class_head(self, size_class: int, head: int):
        """Set head of segregated list for a size class.
        
        Args:
            size_class: Size class index (0-4)
            head: New head offset
        """
        if size_class < 0 or size_class >= NUM_SIZE_CLASSES:
            raise ValueError(f"Invalid size class: {size_class}")
        
        assert self._mmap is not None
        _, _, slot_count, _, _, _, _, _ = self.read_header()
        segregated_heads_start = HEADER_SIZE + slot_count * SLOT_SIZE
        offset = segregated_heads_start + size_class * 8
        
        self._mmap[offset:offset + 8] = struct.pack('<Q', head)
    
    def read_free_block(self, offset: int) -> tuple:
        """Read free block header.
        
        Returns:
            (next_offset, size, magic)
        """
        data = self.read_heap(offset, FREE_BLOCK_SIZE)
        return FREE_BLOCK_UNPACK(data)
    
    def write_free_block(self, offset: int, next_offset: int, size: int):
        """Write free block header."""
        header = FREE_BLOCK_PACK(next_offset, size, FREE_BLOCK_MAGIC)
        self.write_heap(offset, header)
    
    def close(self):
        """Close and optionally delete shared memory."""
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        
        if self._create:
            path = self._get_shm_path()
            try:
                os.unlink(path)
            except OSError:
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False