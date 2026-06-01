# PyPI 发布指南

## ✅ 已完成的优化

1. **LICENSE** - MIT 许可证
2. **MANIFEST.in** - 包文件清单
3. **pyproject.toml** - 完整的 PyPI 元数据和构建配置
4. **CHANGELOG.md** - 版本历史和性能数据
5. **py.typed** - 类型提示标记文件
6. **README.md** - 更新性能对比数据和安装方式

## 📦 构建结果

已成功构建两个发布文件：
- `dist/zero_copy_ipc-1.0.0.tar.gz` (源码包)
- `dist/zero_copy_ipc-1.0.0-py3-none-any.whl` (wheel包)

twine检查通过：✅ PASSED

## 🚀 发布步骤

### 1. 注册 PyPI 账号
访问 https://pypi.org/account/register/ 注册账号

### 2. 创建 API Token
访问 https://pypi.org/manage/account/token/ 创建 API token

### 3. 上传到 PyPI
```bash
# 使用 twine 上传
twine upload dist/*

# 或使用 API token
twine upload dist/* --username __token__ --password <your-api-token>
```

### 4. 验证发布
```bash
# 发布后验证安装
pip install zero-copy-ipc

# 测试导入
python -c "from zero_copy_ipc import ZeroCopyDict; print('✅ Installation successful')"
```

## 📋 发布前检查清单

- ✅ 代码无编译错误
- ✅ 测试通过
- ✅ README 包含完整文档
- ✅ LICENSE 文件存在
- ✅ CHANGELOG.md 记录版本历史
- ✅ pyproject.toml 元数据完整
- ✅ py.typed 标记文件存在
- ✅ 构建成功（无警告）
- ✅ twine check 通过

## 🔗 发布后的链接

发布成功后，用户可以通过以下方式访问：

- PyPI页面: https://pypi.org/project/zero-copy-ipc/
- GitHub仓库: https://github.com/senyangcai/zero-copy-ipc
- 安装命令: `pip install zero-copy-ipc`

## 📊 包含的文件

**源码包 (tar.gz):**
- 源代码 (src/zero_copy_ipc/)
- 测试代码 (tests/)
- 示例代码 (examples/)
- 文档文件 (README.md, ARCHITECTURE.md, QUICKSTART.md, CHANGELOG.md)
- 配置文件 (pyproject.toml, MANIFEST.in, LICENSE)

**Wheel包 (.whl):**
- 源代码 (zero_copy_ipc/)
- 类型标记 (py.typed)
- 元数据 (dist-info/)

## 🎯 性能亮点

README 已包含性能对比数据：
- 更新性能: 75K ops/s vs Manager 33K ops/s (2.25倍)
- 读取性能: 150K ops/s vs Manager 33K ops/s (4.5倍)
- O(1) segregated lists allocator

## 📝 下次版本发布

更新版本号和 CHANGELOG.md：
```bash
# 1. 更新 pyproject.toml 中的 version
# 2. 更新 CHANGELOG.md 添加新版本记录
# 3. 清理旧构建文件
rm -rf dist/ build/ src/*.egg-info

# 4. 重新构建
python -m build

# 5. 检查
twine check dist/*

# 6. 上传
twine upload dist/*
```

## ⚠️ 注意事项

1. **不要覆盖已发布的版本** - PyPI 不允许重复上传相同版本
2. **版本号遵循语义化版本** - MAJOR.MINOR.PATCH
3. **测试发布到 TestPyPI** - 可先发布到 https://test.pypi.org 测试
   ```bash
   twine upload --repository testpypi dist/*
   ```

## 🎉 发布成功！

用户即可通过以下命令安装使用：
```bash
pip install zero-copy-ipc
```

全球开发者都能享受到零拷贝、O(1)性能的多进程共享内存字典！