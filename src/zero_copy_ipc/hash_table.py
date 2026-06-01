"""Hash table with linear probing for slot lookup."""

from typing import Optional, Tuple
from .memory_layout import MemoryLayout, Slot
from .heap_manager import HeapManager
from .constants import SLOT_EMPTY, SLOT_DELETED, HASH_SEED


class HashTable:
    """Hash table implementation using linear probing."""
    
    def __init__(self, layout: MemoryLayout, heap: HeapManager):
        self._layout = layout
        self._heap = heap
    
    def _hash(self, key_bytes: bytes) -> int:
        """Compute hash value for key bytes."""
        h = HASH_SEED
        for byte in key_bytes:
            h ^= byte
            h = (h * 16777619) & 0xFFFFFFFFFFFFFFFF
        return h
    
    def _find_slot(self, key: bytes, key_hash: int) -> Tuple[int, Optional[Slot], bool]:
        """Find slot for key.
        
        Returns:
            (slot_index, slot, found)
            - slot_index: index where key is or should be inserted
            - slot: the slot at that index (or None if empty)
            - found: True if key exists, False otherwise
        """
        slot_count = self._layout.get_slot_count()
        index = key_hash % slot_count
        first_deleted = -1
        
        for _ in range(slot_count):
            slot = self._layout.read_slot(index)
            
            if slot.is_empty():
                if first_deleted >= 0:
                    return first_deleted, None, False
                return index, None, False
            
            if slot.is_deleted():
                if first_deleted < 0:
                    first_deleted = index
            elif slot.key_size == len(key):
                key_data = self._layout.read_heap(slot.key_offset, slot.key_size)
                if key_data == key:
                    return index, slot, True
            
            index = (index + 1) % slot_count
        
        if first_deleted >= 0:
            return first_deleted, None, False
        
        raise RuntimeError("Hash table is full")
    
    def get(self, key: bytes) -> Tuple[Optional[bytes], bool, int]:
        """Get value for key.
        
        Returns:
            (value_bytes, exists, slot_index)
        """
        key_hash = self._hash(key)
        index, slot, found = self._find_slot(key, key_hash)
        
        if not found or slot is None:
            return None, False, index
        
        value_data = self._layout.read_heap(slot.value_offset, slot.value_size)
        return value_data, True, index
    
    def set(self, key: bytes, value: bytes) -> int:
        """Set value for key.
        
        Returns:
            Slot index where key was inserted/updated
        """
        key_hash = self._hash(key)
        index, slot, found = self._find_slot(key, key_hash)
        
        if found and slot is not None:
            # 修改：释放旧值，分配新值
            self._heap.free(slot.value_offset, slot.value_size)
            
            new_value_offset = self._heap.allocate(len(value))
            self._heap.write(new_value_offset, value)
            
            new_slot = Slot(
                key_offset=slot.key_offset,
                key_size=slot.key_size,
                value_offset=new_value_offset,
                value_size=len(value)
            )
            self._layout.write_slot(index, new_slot)
        else:
            # 新增：分配键和值
            key_offset = self._heap.allocate(len(key))
            self._heap.write(key_offset, key)
            
            value_offset = self._heap.allocate(len(value))
            self._heap.write(value_offset, value)
            
            new_slot = Slot(
                key_offset=key_offset,
                key_size=len(key),
                value_offset=value_offset,
                value_size=len(value)
            )
            self._layout.write_slot(index, new_slot)
            self._layout.set_used_slots(self._layout.get_used_slots() + 1)
        
        return index
    
    def delete(self, key: bytes) -> Tuple[bool, int]:
        """Delete key from hash table.
        
        Returns:
            (success, slot_index)
        """
        key_hash = self._hash(key)
        index, slot, found = self._find_slot(key, key_hash)
        
        if not found or slot is None:
            return False, index
        
        # 释放键和值的内存
        self._heap.free(slot.key_offset, slot.key_size)
        self._heap.free(slot.value_offset, slot.value_size)
        
        deleted_slot = Slot(
            key_offset=SLOT_DELETED,
            key_size=0,
            value_offset=SLOT_DELETED,
            value_size=0
        )
        self._layout.write_slot(index, deleted_slot)
        self._layout.set_used_slots(self._layout.get_used_slots() - 1)
        
        return True, index
    
    def keys(self) -> list:
        """Get all keys in the hash table."""
        result = []
        slot_count = self._layout.get_slot_count()
        
        for i in range(slot_count):
            slot = self._layout.read_slot(i)
            if slot.is_used():
                key_data = self._layout.read_heap(slot.key_offset, slot.key_size)
                result.append(key_data)
        
        return result
    
    def items(self) -> list:
        """Get all (key, value) pairs in the hash table."""
        result = []
        slot_count = self._layout.get_slot_count()
        
        for i in range(slot_count):
            slot = self._layout.read_slot(i)
            if slot.is_used():
                key_data = self._layout.read_heap(slot.key_offset, slot.key_size)
                value_data = self._layout.read_heap(slot.value_offset, slot.value_size)
                result.append((key_data, value_data))
        
        return result
    
    def count(self) -> int:
        """Get number of entries in hash table."""
        return self._layout.get_used_slots()
    
    def load_factor(self) -> float:
        """Get load factor of hash table."""
        slot_count = self._layout.get_slot_count()
        if slot_count == 0:
            return 0.0
        return self._layout.get_used_slots() / slot_count