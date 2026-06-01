"""Process synchronization using platform-specific locks."""

import os
import time
import platform
from typing import Optional
from contextlib import contextmanager

from .constants import LOCK_TIMEOUT


class ProcessLock:
    """Platform-aware file-based lock for multi-process synchronization."""
    
    def __init__(self, shm_name: str):
        self._shm_name = shm_name
        self._lock_path = self._get_lock_path()
        self._fd: Optional[int] = None
        self._is_windows = platform.system() == 'Windows'
        self._lock_file = None
    
    def _get_lock_path(self) -> str:
        """Get platform-specific lock file path."""
        if platform.system() == 'Windows':
            import tempfile
            lock_dir = os.path.join(tempfile.gettempdir(), 'zero_copy_ipc')
            os.makedirs(lock_dir, exist_ok=True)
            return os.path.join(lock_dir, f"{self._shm_name}.lock")
        else:
            return f"/tmp/zero_copy_ipc_{self._shm_name}.lock"
    
    def acquire(self, timeout: float = LOCK_TIMEOUT):
        """Acquire the lock.
        
        Args:
            timeout: Maximum time to wait for lock (seconds)
            
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        if self._is_windows:
            self._acquire_windows(timeout)
        else:
            self._acquire_unix(timeout)
    
    def _acquire_windows(self, timeout: float):
        """Windows-specific lock acquisition using msvcrt."""
        import msvcrt
        
        if self._fd is None:
            self._fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        
        start_time = time.time()
        
        while True:
            try:
                msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
                return
            except (IOError, OSError):
                if time.time() - start_time >= timeout:
                    raise TimeoutError(f"Could not acquire lock within {timeout} seconds")
                time.sleep(0.001)
    
    def _acquire_unix(self, timeout: float):
        """Unix-specific lock acquisition using fcntl."""
        import fcntl
        
        if self._fd is None:
            self._fd = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        
        start_time = time.time()
        
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except (IOError, OSError):
                if time.time() - start_time >= timeout:
                    raise TimeoutError(f"Could not acquire lock within {timeout} seconds")
                time.sleep(0.001)
    
    def release(self):
        """Release the lock."""
        if self._fd is None:
            return
        
        try:
            if self._is_windows:
                import msvcrt
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fd, fcntl.LOCK_UN)
        except (IOError, OSError):
            pass
    
    @contextmanager
    def locked(self, timeout: float = LOCK_TIMEOUT):
        """Context manager for acquiring and releasing lock.
        
        Args:
            timeout: Maximum time to wait for lock
            
        Yields:
            None
        """
        self.acquire(timeout)
        try:
            yield
        finally:
            self.release()
    
    def close(self):
        """Close and cleanup lock."""
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        
        try:
            os.unlink(self._lock_path)
        except OSError:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False