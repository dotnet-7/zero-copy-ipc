"""Serializer for Python objects to/from bytes."""

import pickle
from typing import Any, Tuple


class Serializer:
    """Serialize Python objects to bytes and back."""
    
    @staticmethod
    def serialize(obj: Any) -> bytes:
        """Serialize a Python object to bytes.
        
        Args:
            obj: Any Python object
            
        Returns:
            Serialized bytes
        """
        return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    
    @staticmethod
    def deserialize(data: bytes) -> Any:
        """Deserialize bytes to Python object.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized Python object
        """
        return pickle.loads(data)
    
    @staticmethod
    def serialize_key(key: Any) -> Tuple[bytes, int]:
        """Serialize a dictionary key.
        
        Args:
            key: Dictionary key (must be hashable)
            
        Returns:
            Tuple of (serialized bytes, hash value)
        """
        key_bytes = pickle.dumps(key, protocol=pickle.HIGHEST_PROTOCOL)
        hash_val = hash(key) & 0x7FFFFFFFFFFFFFFF
        return key_bytes, hash_val