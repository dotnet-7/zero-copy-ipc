"""Zero-copy shared memory dictionary library."""

from .dict import ZeroCopyDict
from .constants import (
    MAGIC_NUMBER,
    VERSION,
    HEADER_SIZE,
    SLOT_SIZE,
    MIN_HEAP_SIZE,
    MIN_SLOT_COUNT,
)

__version__ = "0.1.0"
__all__ = [
    "ZeroCopyDict",
    "MAGIC_NUMBER",
    "VERSION",
    "HEADER_SIZE",
    "SLOT_SIZE",
    "MIN_HEAP_SIZE",
    "MIN_SLOT_COUNT",
]