"""Segmented locks for better concurrency."""

import os
import time
import platform
from typing import List, Optional
from contextlib import contextmanager
from .constants import LOCK_TIMEOUT


NUM_SEGMENTS: int = 64  # 64个分段锁


class SegmentedLock:
    """分段锁管理器：每个槽位组一把锁，提高并发性能"""
    
    def __init__(self, shm_name: str, num_segments: int = NUM_SEGMENTS):
        self._shm_name = shm_name
        self._num_segments = num_segments
        self._is_windows = platform.system() == 'Windows'
        self._fds: List[Optional[int]] = [None] * num_segments
        self._lock_paths: List[str] = []
        
        for i in range(num_segments):
            self._lock_paths.append(self._get_lock_path(i))
    
    def _get_lock_path(self, segment_id: int) -> str:
        """获取分段锁文件路径"""
        if platform.system() == 'Windows':
            import tempfile
            lock_dir = os.path.join(tempfile.gettempdir(), 'zero_copy_ipc')
            os.makedirs(lock_dir, exist_ok=True)
            return os.path.join(lock_dir, f"{self._shm_name}_seg{segment_id}.lock")
        else:
            return f"/tmp/zero_copy_ipc_{self._shm_name}_seg{segment_id}.lock"
    
    def _get_segment_id(self, slot_index: int) -> int:
        """根据槽位索引计算分段ID"""
        return slot_index % self._num_segments
    
    def acquire_segment(self, slot_index: int, timeout: float = LOCK_TIMEOUT):
        """获取指定槽位的分段锁"""
        segment_id = self._get_segment_id(slot_index)
        
        if self._is_windows:
            self._acquire_windows(segment_id, timeout)
        else:
            self._acquire_unix(segment_id, timeout)
    
    def _acquire_windows(self, segment_id: int, timeout: float):
        """Windows: msvcrt.locking"""
        import msvcrt
        
        if self._fds[segment_id] is None:
            self._fds[segment_id] = os.open(
                self._lock_paths[segment_id],
                os.O_CREAT | os.O_RDWR,
                0o600
            )
        
        start_time = time.time()
        
        while True:
            try:
                msvcrt.locking(self._fds[segment_id], msvcrt.LK_NBLCK, 1)
                return
            except (IOError, OSError):
                if time.time() - start_time >= timeout:
                    raise TimeoutError(
                        f"Could not acquire segment {segment_id} lock within {timeout} seconds"
                    )
                time.sleep(0.001)
    
    def _acquire_unix(self, segment_id: int, timeout: float):
        """Unix: fcntl.flock"""
        import fcntl
        
        if self._fds[segment_id] is None:
            self._fds[segment_id] = os.open(
                self._lock_paths[segment_id],
                os.O_CREAT | os.O_RDWR,
                0o600
            )
        
        start_time = time.time()
        
        while True:
            try:
                fcntl.flock(self._fds[segment_id], fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except (IOError, OSError):
                if time.time() - start_time >= timeout:
                    raise TimeoutError(
                        f"Could not acquire segment {segment_id} lock within {timeout} seconds"
                    )
                time.sleep(0.001)
    
    def release_segment(self, slot_index: int):
        """释放指定槽位的分段锁"""
        segment_id = self._get_segment_id(slot_index)
        
        if self._fds[segment_id] is None:
            return
        
        try:
            if self._is_windows:
                import msvcrt
                msvcrt.locking(self._fds[segment_id], msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fds[segment_id], fcntl.LOCK_UN)
        except (IOError, OSError):
            pass
    
    @contextmanager
    def locked_segment(self, slot_index: int, timeout: float = LOCK_TIMEOUT):
        """上下文管理器：自动获取和释放分段锁"""
        self.acquire_segment(slot_index, timeout)
        try:
            yield
        finally:
            self.release_segment(slot_index)
    
    def acquire_all(self, timeout: float = LOCK_TIMEOUT):
        """获取所有分段锁（用于全局操作如clear）"""
        for i in range(self._num_segments):
            self.acquire_segment(i * self._num_segments, timeout)
    
    def release_all(self):
        """释放所有分段锁"""
        for i in range(self._num_segments):
            self.release_segment(i * self._num_segments)
    
    @contextmanager
    def locked_all(self, timeout: float = LOCK_TIMEOUT):
        """上下文管理器：获取所有分段锁"""
        self.acquire_all(timeout)
        try:
            yield
        finally:
            self.release_all()
    
    def close(self):
        """关闭所有锁文件"""
        for i in range(self._num_segments):
            if self._fds[i] is not None:
                try:
                    os.close(self._fds[i])
                except OSError:
                    pass
                self._fds[i] = None
        
        for lock_path in self._lock_paths:
            try:
                os.unlink(lock_path)
            except OSError:
                pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False