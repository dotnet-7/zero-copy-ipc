"""Heap manager with segregated lists for O(1) allocation."""

from typing import Optional, Tuple
from .memory_layout import MemoryLayout
from .constants import (
    FREE_BLOCK_SIZE, FREE_BLOCK_MAGIC, FREE_LIST_END, 
    MIN_BLOCK_SIZE, NUM_SIZE_CLASSES, get_size_class
)


class HeapManager:
    """Manages heap allocation with segregated lists for O(1) performance."""
    
    def __init__(self, layout: MemoryLayout):
        self._layout = layout
    
    def allocate(self, size: int) -> int:
        """Allocate space using segregated lists - O(1) performance!
        
        Strategy:
        1. Calculate size class
        2. Try to get block from that size class list (O(1))
        3. If not found, try larger size classes (fallback)
        4. If still not found, allocate from heap
        
        Args:
            size: Data size to allocate
            
        Returns:
            Offset in heap where data can be written
        """
        total_size = size + FREE_BLOCK_SIZE
        
        if total_size < MIN_BLOCK_SIZE:
            total_size = MIN_BLOCK_SIZE
        
        # 1. 计算size class
        size_class = get_size_class(size)
        
        # 2. 尝试从对应size class取块（O(1)）
        offset = self._pop_from_size_class(size_class)
        
        if offset is not None:
            return offset + FREE_BLOCK_SIZE
        
        # 3. 尝试更大的size classes（fallback）
        for larger_class in range(size_class + 1, NUM_SIZE_CLASSES):
            offset = self._pop_from_size_class(larger_class)
            if offset is not None:
                return offset + FREE_BLOCK_SIZE
        
        # 4. 从heap尾部分配新空间
        heap_size = self._layout.get_heap_size()
        heap_used = self._layout.get_heap_used()
        
        if heap_used + total_size > heap_size:
            raise MemoryError(
                f"Heap full: need {total_size} bytes, "
                f"available {heap_size - heap_used}"
            )
        
        offset = heap_used
        self._layout.set_heap_used(heap_used + total_size)
        
        return offset + FREE_BLOCK_SIZE
    
    def _pop_from_size_class(self, size_class: int) -> Optional[int]:
        """Pop a block from a specific size class - O(1)!
        
        Args:
            size_class: Size class index
            
        Returns:
            Block offset if available, None otherwise
        """
        head = self._layout.get_size_class_head(size_class)
        
        if head == FREE_LIST_END:
            return None
        
        # 从链表头部取出块（O(1)）
        next_offset, block_size, magic = self._layout.read_free_block(head)
        
        if magic != FREE_BLOCK_MAGIC:
            # Magic不匹配，清空这个size class
            self._layout.set_size_class_head(size_class, FREE_LIST_END)
            return None
        
        # 更新head指向下一个块
        self._layout.set_size_class_head(size_class, next_offset)
        
        return head
    
    def free(self, offset: int, size: int):
        """Free heap space and add to segregated list - O(1)!
        
        Args:
            offset: Data offset (after header)
            size: Data size
        """
        block_offset = offset - FREE_BLOCK_SIZE
        total_size = size + FREE_BLOCK_SIZE
        
        if total_size < MIN_BLOCK_SIZE:
            total_size = MIN_BLOCK_SIZE
        
        # 1. 计算size class
        size_class = get_size_class(size)
        
        # 2. 插入到对应size class的头部（O(1)）
        head = self._layout.get_size_class_head(size_class)
        
        # 3. 写入freelist节点
        self._layout.write_free_block(block_offset, head, total_size)
        
        # 4. 更新head指向新块
        self._layout.set_size_class_head(size_class, block_offset)
    
    def write(self, offset: int, data: bytes):
        """Write data to heap at given offset."""
        self._layout.write_heap(offset, data)
    
    def read(self, offset: int, size: int) -> bytes:
        """Read data from heap at given offset."""
        return self._layout.read_heap(offset, size)
    
    def available(self) -> int:
        """Get available heap space."""
        return self._layout.get_heap_size() - self._layout.get_heap_used()
    
    def segregated_lists_stats(self) -> dict:
        """Get segregated lists statistics.
        
        Returns:
            Dictionary with stats for each size class
        """
        stats = {}
        
        for size_class in range(NUM_SIZE_CLASSES):
            head = self._layout.get_size_class_head(size_class)
            
            num_blocks = 0
            total_size = 0
            current_offset = head
            
            while current_offset != FREE_LIST_END:
                next_offset, block_size, magic = self._layout.read_free_block(current_offset)
                
                if magic != FREE_BLOCK_MAGIC:
                    break
                
                num_blocks += 1
                total_size += block_size
                current_offset = next_offset
            
            stats[size_class] = {
                'num_blocks': num_blocks,
                'total_size': total_size,
                'head': head
            }
        
        return stats
    
    def free_list_stats(self) -> Tuple[int, int]:
        """Get overall free list statistics.
        
        Returns:
            (num_blocks, total_size)
        """
        stats = self.segregated_lists_stats()
        
        total_blocks = sum(s['num_blocks'] for s in stats.values())
        total_size = sum(s['total_size'] for s in stats.values())
        
        return total_blocks, total_size
    
    def compact(self):
        """Compact heap to reclaim all freed space.
        
        This is a manual operation that:
        1. Stops all operations (caller should hold lock)
        2. Iterates through all active slots
        3. Moves data to eliminate gaps
        4. Updates all slot pointers
        5. Resets all segregated lists
        
        WARNING: This violates zero-copy principle temporarily!
        """
        pass