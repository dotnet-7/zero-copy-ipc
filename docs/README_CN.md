# Zero-Copy IPC 中文文档

[![PyPI version](https://badge.fury.io/py/zero-copy-ipc.svg)](https://badge.fury.io/py/zero-copy-ipc)
[![Python](https://img.shields.io/pypi/pyversions/zero-copy-ipc.svg)](https://pypi.org/project/zero-copy-ipc/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg](LICENSE))

**[返回英文文档 (Back to English Documentation)](../README.md)**

---

## 项目简介

一个纯 Python 实现的零拷贝共享内存字典，用于多进程 IPC，性能比 multiprocessing.Manager 快 3倍。

---

## 核心特性

### ⚡ 零拷贝 - 真正的共享内存
- 多进程直接访问同一块共享内存
- 无序列化/反序列化开销
- 纳秒级进程间同步

### 🚀 高性能 - O(1) 操作
- **Segregated Lists** 内存分配器（O(1)）
- 原位修改：只更新指针，不移动数据
- 实测性能：**比 Manager().dict() 快 3倍**

### 🔒 进程安全 - 跨平台锁
- Windows/Linux/macOS 全支持
- 文件锁保证进程间互斥
- 自动超时机制（10秒）

### 🎯 简洁 API - 字典式接口
```python
d["key"] = value  # 写入
value = d["key"]  # 读取
del d["key"]      # 删除
```

---

## 性能对比

**vs multiprocessing.Manager().dict():**

| 操作 | ZeroCopyDict | Manager | 提升 |
|------|--------------|---------|------|
| **写入** | 46,161 ops/s | 33,345 ops/s | **1.38倍** |
| **读取** | 149,459 ops/s | 27,268 ops/s | **5.48倍** |
| **更新** | 74,965 ops/s | 33,340 ops/s | **2.25倍** |
| **平均** | - | - | **3.04倍** ✅ |

---

## 安装

### 从 PyPI 安装（推荐）
```bash
pip install zero-copy-ipc
```

### 从源码安装
```bash
git clone https://github.com/senyangcai/zero-copy-ipc.git
cd zero-copy-ipc
pip install -e .
```

---

## 快速开始

### 基础用法
```python
from zero_copy_ipc import ZeroCopyDict

# 创建共享字典
d = ZeroCopyDict.create(
    "my_dict",
    max_items=1000,
    heap_size=10*1024*1024  # 10MB
)

# 写入数据
d["name"] = "Alice"
d["age"] = 30
d["data"] = {"nested": "dict"}

# 读取数据
print(d["name"])  # "Alice"

# 更新数据（O(1)操作）
d["age"] = 31

# 关闭
d.close()
```

### 多进程共享
```python
# 进程1: 创建并写入
from zero_copy_ipc import ZeroCopyDict

d1 = ZeroCopyDict.create("shared_dict")
d1["counter"] = 0

# 进程2: 附加并读取
d2 = ZeroCopyDict.attach("shared_dict")
print(d2["counter"])  # 立即看到 0

# 进程3: 更新
d3 = ZeroCopyDict.attach("shared_dict")
d3["counter"] = 100  # d1和d2立即看到更新！
```

### 上下文管理器（推荐）
```python
with ZeroCopyDict.create("temp_dict") as d:
    d["key"] = "value"
    # 自动清理
```

---

## 适用场景

### ✅ 适合
- 多进程高频读写共享数据
- Web应用实时统计（访问量、响应时间）
- 分布式爬虫任务队列
- 实时日志聚合系统
- API限流计数器
- ML训练进度共享

### ❌ 不适合
- 跨机器分布式通信（用 Redis）
- 数据持久化存储（用数据库）
- 超大数据集（TB级）

---

## 技术架构

### 内存布局
```
共享内存结构：
┌────────────────────────┐
│ Header (56字节)         │
│  - Magic: 0x5A45524F    │
│  - Version: 3           │
│  - Slot count           │
│  - Heap size            │
└────────────────────────┘
┌────────────────────────┐
│ Slot Table (24B each)   │
│  - key_offset (8B)      │
│  - key_size (4B)        │
│  - value_offset (8B)    │
│  - value_size (4B)      │
└────────────────────────┘
┌────────────────────────┐
│ Segregated Lists (40B)  │
│  - 5个size class heads  │
└────────────────────────┘
┌────────────────────────┐
│ Heap Area (变长)        │
│  - Keys数据             │
│  - Values数据           │
└────────────────────────┘
```

### 核心组件
- **MemoryLayout**: mmap共享内存管理
- **HashTable**: 线性探测哈希表
- **HeapManager**: Segregated Lists分配器
- **ProcessLock**: 跨平台文件锁
- **Serializer**: pickle序列化器

---

## 支持的数据类型

所有可 pickle 的 Python 对象：

```python
# ✅ 基本类型
d["int"] = 42
d["float"] = 3.14
d["str"] = "hello"
d["bool"] = True
d["bytes"] = b"data"

# ✅ 容器类型
d["list"] = [1, 2, 3]
d["dict"] = {"nested": "value"}
d["tuple"] = (1, 2, 3)
d["set"] = {1, 2, 3}

# ✅ 自定义对象
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

d["point"] = Point(10, 20)

# ❌ 不支持
# 文件对象、socket、lambda、threading.Lock
```

---

## 容量规划

### 计算公式
```python
# 估算所需空间
avg_key_size = 10    # 字节
avg_value_size = 100 # 字节
num_items = 1000

heap_size = num_items * (avg_key_size + avg_value_size) * 2  # 2倍安全余量
# = 1000 * 110 * 2 = 220KB

d = ZeroCopyDict.create(
    "my_dict",
    max_items=1000,
    heap_size=220*1024
)
```

### 内存开销
- **固定开销**: Header(56B) + Slot表(24B × max_items)
- **每条记录**: 24字节 + 序列化后大小

---

## 平台支持

| 平台 | 共享内存位置 | 锁机制 | 性能 |
|------|-------------|--------|------|
| **Linux** | `/dev/shm` | fcntl.flock | ⭐⭐⭐⭐⭐ |
| **Windows** | temp目录 | msvcrt.locking | ⭐⭐⭐⭐ |
| **macOS** | `/tmp` | fcntl.flock | ⭐⭐⭐⭐ |

---

## API 参考

### 创建
```python
ZeroCopyDict.create(
    name: str,              # 共享内存名称
    max_items: int = 10000, # 最大条目数
    heap_size: int = 100MB  # 堆区大小
)
```

### 附加
```python
ZeroCopyDict.attach(name: str)  # 附加到已存在的字典
```

### 操作
```python
d[key] = value       # 写入
d[key]               # 读取
del d[key]           # 删除
key in d             # 检查存在
len(d)               # 获取长度
d.get(key, default)  # 安全读取
d.keys()             # 获取所有键
d.values()           # 获取所有值
d.items()            # 获取所有键值对
d.stats()            # 获取统计信息
d.close()            # 关闭并清理
```

---

## 监控统计

```python
stats = d.stats()
print(f"已用槽位: {stats['used_slots']}")
print(f"负载因子: {stats['load_factor']:.2%}")
print(f"堆区使用: {stats['heap_used']} bytes")

gc_stats = d.gc_stats()
print(f"空闲块数: {gc_stats['total_free_blocks']}")
print(f"空闲空间: {gc_stats['total_free_space']} bytes")
```

---

## 文档导航

- **[README.md](../README.md)** - 英文文档
- **[README_CN.md](README_CN.md)** - 中文文档（当前文件）
- **[QUICKSTART.md](QUICKSTART.md)** - 快速入门指南
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - 技术架构详解
- **[USAGE.md](USAGE.md)** - 详细使用指南
- **[CHANGELOG.md](../CHANGELOG.md)** - 版本历史

---

## 示例代码

```bash
# 基础用法
python examples/basic_usage.py

# 多进程通信
python examples/multiprocess.py

# 性能基准测试
python examples/benchmark.py
```

---

## 测试

```bash
# 快速测试
python tests/quick_test.py

# 性能对比测试
python tests/comparison_final.py

# 完整测试套件
pytest tests/test_dict.py -v
```

---

## 常见问题

### Q: 如何清理共享内存？
```python
# 正常清理
d.close()

# 手动清理（Linux）
os.remove("/dev/shm/zero_copy_ipc_my_dict")

# 手动清理（Windows）
import tempfile
os.remove(os.path.join(tempfile.gettempdir(), "zero_copy_ipc_my_dict.shm"))
```

### Q: 锁超时怎么办？
```python
try:
    d["key"] = "value"
except TimeoutError:
    print("锁超时，可能有僵尸进程")
    # 清理锁文件
    # 重试操作
```

### Q: 如何提高并发性能？
```python
# 1. 批量操作减少锁次数
d.update({"k1": "v1", "k2": "v2", "k3": "v3"})

# 2. 使用足够大的heap_size避免频繁分配
heap_size = estimated_items * avg_size * 3

# 3. 不同key操作可并行（hash到不同槽位）
```

---

## 更新历史

### v1.0.0 (2025-06-01)
- ✅ Segregated Lists O(1) 内存分配器
- ✅ 性能比 Manager().dict() 快 3倍
- ✅ 跨平台支持（Windows/Linux/macOS）
- ✅ 完整文档和测试

详见 [CHANGELOG.md](../CHANGELOG.md)

---

## 许可证

MIT License - 详见 [LICENSE](../LICENSE)

---

## 作者

senyangcai (158119447@qq.com)

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 致谢

感谢 Apache Arrow 和其他 IPC 方案的启发，但本库专注于本地多进程零拷贝场景，提供了更轻量、更高效的解决方案。

---

**开始使用**:
```bash
pip install zero-copy-ipc
python -c "from zero_copy_ipc import ZeroCopyDict; print('✅ 安装成功')"
```