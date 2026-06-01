# 详细使用指南

## 容量规划

### 如何计算 max_items 和 heap_size？

**公式：**
```
heap_size = max_items × 平均数据大小 × 安全系数(2-3倍)
```

**示例计算：**
```python
# 场景1: 10K个小对象（平均100字节）
max_items = 10000
avg_size = 100  # bytes
heap_size = 10000 × 100 × 2 = 2MB

d = ZeroCopyDict.create("small_objects",
    max_items=10000,
    heap_size=2*1024*1024
)

# 场景2: 1K个大对象（平均10KB）
max_items = 1000
avg_size = 10*1024  # 10KB
heap_size = 1000 × 10*1024 × 2 = 20MB

d = ZeroCopyDict.create("large_objects",
    max_items=1000,
    heap_size=20*1024*1024
)

# 场景3: 混合大小（保守估计）
max_items = 5000
heap_size = 50*1024*1024  # 50MB (足够空间)
```

### 内存开销分析

**固定开销：**
- Header: 56字节
- Slot表: 24字节 × max_items
- Segregated Lists头: 40字节 (5个size classes)

**示例：**
```
max_items=10000:
- Header: 56B
- Slot表: 24B × 10000 = 240KB
- Segregated Lists: 40B
- 总固定开销: ~240KB
```

**每条记录开销：**
- Slot: 24字节（固定）
- Key序列化后大小
- Value序列化后大小
- Free Block元数据: 16字节（如果被释放）

## 进程协调模式

### 模式1: 主进程创建，工作进程附加

```python
# main_process.py
from zero_copy_ipc import ZeroCopyDict
import time

d = ZeroCopyDict.create("shared_config",
    max_items=100,
    heap_size=1*1024*1024
)

d["config"] = {
    "workers": 4,
    "batch_size": 100,
    "timeout": 30
}

d["status"] = "running"

try:
    while True:
        time.sleep(1)  # 保持共享内存存活
finally:
    d.close()

# worker_process.py (可以启动多个)
from zero_copy_ipc import ZeroCopyDict

d = ZeroCopyDict.attach("shared_config")

config = d["config"]
print(f"Workers: {config['workers']}")

while d["status"] == "running":
    # 处理任务
    pass

d.close()
```

### 模式2: 临时共享内存（上下文管理器）

```python
from zero_copy_ipc import ZeroCopyDict
from multiprocessing import Process

def worker(name):
    with ZeroCopyDict.attach(name) as d:
        data = d["data"]
        # 处理数据
        result = process(data)
        d["result"] = result

if __name__ == '__main__':
    with ZeroCopyDict.create("temp_work",
        max_items=10,
        heap_size=1*1024*1024
    ) as d:
        d["data"] = load_data()
        
        # 启动工作进程
        processes = [
            Process(target=worker, args=("temp_work",))
            for _ in range(4)
        ]
        
        for p in processes:
            p.start()
        
        for p in processes:
            p.join()
        
        result = d["result"]
    # 自动清理共享内存
```

### 模式3: 生产者-消费者队列

```python
# producer.py
from zero_copy_ipc import ZeroCopyDict
import time

d = ZeroCopyDict.create("queue",
    max_items=100,
    heap_size=10*1024*1024
)

d["queue_data"] = []
d["queue_lock"] = "free"

for i in range(100):
    # 简单的锁机制
    while d["queue_lock"] != "free":
        time.sleep(0.001)
    
    d["queue_lock"] = "producer"
    queue = d["queue_data"]
    queue.append(f"item_{i}")
    d["queue_data"] = queue
    d["queue_lock"] = "free"
    
    time.sleep(0.01)

d["status"] = "done"
d.close()

# consumer.py
from zero_copy_ipc import ZeroCopyDict
import time

d = ZeroCopyDict.attach("queue")

while d.get("status", "running") != "done":
    while d["queue_lock"] != "free":
        time.sleep(0.001)
    
    d["queue_lock"] = "consumer"
    queue = d["queue_data"]
    if queue:
        item = queue.pop(0)
        d["queue_data"] = queue
        print(f"Consumed: {item}")
    d["queue_lock"] = "free"
    
    time.sleep(0.01)

d.close()
```

## 性能监控

### 使用 stats() 监控负载

```python
from zero_copy_ipc import ZeroCopyDict

d = ZeroCopyDict.create("monitor",
    max_items=1000,
    heap_size=10*1024*1024
)

# 添加数据
for i in range(500):
    d[f"key_{i}"] = f"value_{i}"

# 监控统计
stats = d.stats()
print(f"已用槽位: {stats['used_slots']}/{stats['slot_count']}")
print(f"负载因子: {stats['load_factor']:.2%}")
print(f"堆区使用: {stats['heap_used']}/{stats['heap_size']} bytes")
print(f"堆区使用率: {stats['heap_usage_percent']:.2%}")

# 根据负载调整
if stats['load_factor'] > 0.7:
    print("⚠️ 负载过高，建议增加 max_items")

if stats['heap_usage_percent'] > 80:
    print("⚠️ 堆区接近满，建议增加 heap_size")
```

### 使用 gc_stats() 监控内存回收

```python
from zero_copy_ipc import ZeroCopyDict

d = ZeroCopyDict.create("gc_test",
    max_items=100,
    heap_size=1*1024*1024
)

# 添加数据
for i in range(50):
    d[f"key_{i}"] = f"value_{i}"

# 删除数据（触发内存回收）
for i in range(25):
    del d[f"key_{i}"]

# 查看GC统计
gc_stats = d.gc_stats()
print(f"释放块总数: {gc_stats['total_free_blocks']}")
print(f"释放空间总量: {gc_stats['total_free_space']} bytes")
print(f"平均块大小: {gc_stats['avg_block_size']} bytes")

print("\n各size class详情:")
for i, count in enumerate(gc_stats['size_class_counts']):
    space = gc_stats['size_class_spaces'][i]
    print(f"  Class {i}: {count} blocks, {space} bytes")
```

## 数据类型限制

### 支持的类型

所有可以被 `pickle` 序列化的类型：

```python
from zero_copy_ipc import ZeroCopyDict

d = ZeroCopyDict.create("types_test")

# ✅ 基本类型
d["int"] = 42
d["float"] = 3.14
d["bool"] = True
d["str"] = "hello"
d["bytes"] = b"binary"

# ✅ 容器类型
d["list"] = [1, 2, 3, [4, 5]]
d["tuple"] = (1, 2, 3)
d["dict"] = {"nested": {"deep": "value"}}
d["set"] = {1, 2, 3}

# ✅ 自定义对象（可pickle）
class DataPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

d["point"] = DataPoint(10, 20)

# ✅ None
d["none"] = None
```

### 不支持的类型

```python
# ❌ 文件对象
d["file"] = open("test.txt")  # Error

# ❌ 网络连接
d["socket"] = socket.socket()  # Error

# ❌ lambda函数
d["func"] = lambda x: x+1  # Error

# ❌ 带锁的对象
d["locked"] = threading.Lock()  # Error
```

## 性能优化技巧

### 1. 批量操作减少锁竞争

```python
# ❌ 慢：多次单独操作
for i in range(100):
    d[f"key_{i}"] = f"value_{i}"

# ✅ 快：批量更新
data = {f"key_{i}": f"value_{i}" for i in range(100)}
d.update(data)
```

### 2. 预分配足够空间

```python
# ❌ 慢：动态增长导致重新分配
d = ZeroCopyDict.create("dynamic", max_items=100)
for i in range(1000):  # 会出错！
    d[f"key_{i}"] = i

# ✅ 快：预先分配足够空间
d = ZeroCopyDict.create("prealloc",
    max_items=1000,
    heap_size=10*1024*1024
)
for i in range(1000):
    d[f"key_{i}"] = i
```

### 3. 避免频繁创建/销毁

```python
# ❌ 慢：频繁创建销毁
for i in range(100):
    d = ZeroCopyDict.attach("shared")
    d["counter"] = i
    d.close()

# ✅ 快：保持连接
d = ZeroCopyDict.attach("shared")
for i in range(100):
    d["counter"] = i
d.close()
```

### 4. 使用合适的数据结构

```python
# ❌ 慢：大列表频繁更新
d["list"] = []
for i in range(1000):
    lst = d["list"]
    lst.append(i)
    d["list"] = lst  # 每次都重新序列化整个列表

# ✅ 快：使用多个小键
for i in range(1000):
    d[f"item_{i}"] = i  # O(1)操作
```

## 错误处理

### 常见错误和处理

```python
from zero_copy_ipc import ZeroCopyDict

d = ZeroCopyDict.create("error_test",
    max_items=10,
    heap_size=1*1024*1024
)

# 1. KeyError - 键不存在
try:
    value = d["missing_key"]
except KeyError:
    value = d.get("missing_key", "default")

# 2. MemoryError - 堆区满
try:
    for i in range(1000):
        d[f"key_{i}"] = "x" * 10000
except MemoryError:
    print("堆区已满，增加 heap_size")
    stats = d.stats()
    print(f"当前使用: {stats['heap_used']} bytes")

# 3. RuntimeError - 哈希表满
try:
    for i in range(100):
        d[f"key_{i}"] = i
except RuntimeError as e:
    if "Hash table is full" in str(e):
        print("槽位已满，增加 max_items")

# 4. PermissionError - 锁竞争超时
try:
    d["key"] = "value"
except PermissionError:
    print("无法获取锁，检查是否有僵尸进程")
```

## 跨平台注意事项

### Linux (/dev/shm)

```python
# Linux下共享内存位于 /dev/shm
# 可以直接查看：
import os
print(os.path.exists("/dev/shm/zero_copy_ipc_my_dict"))

# 清理残留共享内存：
os.remove("/dev/shm/zero_copy_ipc_my_dict")
```

### Windows (临时目录)

```python
# Windows下共享内存位于临时目录
import tempfile
import os

temp_dir = tempfile.gettempdir()
shm_path = os.path.join(temp_dir, "zero_copy_ipc_my_dict.shm")
print(shm_path)

# 清理：
if os.path.exists(shm_path):
    os.remove(shm_path)
```

### macOS (/tmp)

```python
# macOS下共享内存位于 /tmp
import os
print(os.path.exists("/tmp/zero_copy_ipc_my_dict.shm"))

# 清理：
os.remove("/tmp/zero_copy_ipc_my_dict.shm")
```

## 最佳实践总结

1. **容量规划**: 预先计算所需空间，预留2-3倍安全余量
2. **资源管理**: 使用上下文管理器或显式调用 close()
3. **进程协调**: 主进程创建并保持运行，工作进程附加
4. **性能监控**: 定期检查 stats() 和 gc_stats()
5. **批量操作**: 减少 lock/unlock 开销
6. **错误处理**: 捕获 KeyError, MemoryError, RuntimeError
7. **平台差异**: 注意不同平台的共享内存路径和清理方式

## 下一步

- 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解技术细节
- 查看 [QUICKSTART.md](QUICKSTART.md) 快速上手
- 运行 `examples/basic_usage.py` 查看示例
- 运行 `tests/comparison_final.py` 查看性能对比