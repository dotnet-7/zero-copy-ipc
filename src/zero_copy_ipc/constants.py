"""Constants and memory layout definitions."""

import struct
from typing import Final, List

MAGIC_NUMBER: Final[int] = 0x5A45524F  # "ZERO" in hex
VERSION: Final[int] = 3  # 升级版本号，支持segregated lists

HEADER_SIZE: Final[int] = 56
SLOT_SIZE: Final[int] = 24

HEADER_FORMAT: Final[str] = "<I I Q Q Q Q Q Q"  # magic, version, slot_count, heap_size, used_slots, free_list_head, heap_used, segregated_heads_size
HEADER_PACK = struct.Struct(HEADER_FORMAT).pack
HEADER_UNPACK = struct.Struct(HEADER_FORMAT).unpack

SLOT_FORMAT: Final[str] = "<Q I Q I"  # key_offset, key_size, value_offset, value_size
SLOT_PACK = struct.Struct(SLOT_FORMAT).pack
SLOT_UNPACK = struct.Struct(SLOT_FORMAT).unpack

SLOT_EMPTY: Final[int] = 0xFFFFFFFFFFFFFFFF
SLOT_DELETED: Final[int] = 0xFFFFFFFFFFFFFFFE

MIN_HEAP_SIZE: Final[int] = 1024 * 1024  # 1MB
MIN_SLOT_COUNT: Final[int] = 16

HASH_SEED: Final[int] = 0x9E3779B9

LOCK_TIMEOUT: Final[float] = 10.0
NUM_LOCK_SEGMENTS: Final[int] = 64  # 分段锁数量

FREE_BLOCK_MAGIC: Final[int] = 0xDEADBEEF  # 空闲块标识
FREE_BLOCK_SIZE: Final[int] = 16  # 闲块头大小：next_offset(8) + size(4) + magic(4)

FREE_BLOCK_FORMAT: Final[str] = "<Q I I"  # next_offset, size, magic
FREE_BLOCK_PACK = struct.Struct(FREE_BLOCK_FORMAT).pack
FREE_BLOCK_UNPACK = struct.Struct(FREE_BLOCK_FORMAT).unpack

FREE_LIST_END: Final[int] = 0xFFFFFFFFFFFFFFFF  # 空闲链表结束标记

MIN_BLOCK_SIZE: Final[int] = 32  # 最小块大小（16字节头+至少16字节可用空间）

# Segregated Lists: Size Classes
# 按大小分类，每个size class一个独立的freelist
NUM_SIZE_CLASSES: Final[int] = 5  # 5个大小类别

SIZE_CLASS_BOUNDS: Final[List[int]] = [
    64,    # Class 0: 32-64字节
    128,   # Class 1: 64-128字节
    256,   # Class 2: 128-256字节
    512,   # Class 3: 256-512字节
    1024,  # Class 4: 512+字节（>=1024用这个）
]

def get_size_class(size: int) -> int:
    """根据大小返回对应的size class索引
    
    Args:
        size: 数据大小（不包括header）
        
    Returns:
        Size class索引 (0-4)
    """
    total_size = size + FREE_BLOCK_SIZE
    if total_size < MIN_BLOCK_SIZE:
        total_size = MIN_BLOCK_SIZE
    
    for i, bound in enumerate(SIZE_CLASS_BOUNDS):
        if total_size <= bound:
            return i
    
    return NUM_SIZE_CLASSES - 1  # 最后一个class（最大）