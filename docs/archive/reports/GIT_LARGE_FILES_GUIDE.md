# Git 大文件处理指南

## 问题说明

在 Git 历史中发现了大文件（超过 50MB），特别是：
- `toppic-windows-1.8.0/resources/envcnn_models/envcnn_two_block.onnx` (83.35 MB)
- `toppic-windows-1.8.0/resources/ecscore_models/ecscore_seven_attr.onnx`

这些文件已经被提交到 Git 历史中，即使现在从工作目录中删除，它们仍然存在于 Git 历史记录中，会增加仓库大小。

## 解决方案

### 方案 1: 使用 git filter-repo（推荐）

`git filter-repo` 是 `git filter-branch` 的现代替代品，更快速、更安全。

#### 安装 git filter-repo

```bash
# Windows (使用 pip)
pip install git-filter-repo

# 或使用 scoop
scoop install git-filter-repo
```

#### 从历史中移除大文件

```bash
# 1. 备份当前仓库
git clone --mirror . ../TDEase-Backend-backup.git

# 2. 移除特定的大文件
git filter-repo --path toppic-windows-1.8.0/resources/envcnn_models/envcnn_two_block.onnx --invert-paths
git filter-repo --path toppic-windows-1.8.0/resources/ecscore_models/ecscore_seven_attr.onnx --invert-paths

# 或者移除整个 toppic-windows 目录（如果不需要）
git filter-repo --path toppic-windows-1.8.0/ --invert-paths

# 3. 强制推送到远程（⚠️ 警告：这会重写历史）
git push origin --force --all
git push origin --force --tags
```

### 方案 2: 使用 Git LFS（如果文件需要保留）

如果这些文件是必需的，可以使用 Git LFS (Large File Storage) 来管理：

#### 安装 Git LFS

```bash
# Windows
# 下载并安装: https://git-lfs.github.com/
# 或使用 scoop
scoop install git-lfs

# 初始化 Git LFS
git lfs install
```

#### 迁移大文件到 LFS

```bash
# 1. 配置 LFS 跟踪 onnx 文件
git lfs track "*.onnx"
git lfs track "toppic-windows-1.8.0/**/*.onnx"

# 2. 添加 .gitattributes
git add .gitattributes

# 3. 迁移现有文件到 LFS
git lfs migrate import --include="*.onnx" --everything

# 4. 推送到远程
git push origin --force --all
```

### 方案 3: 完全移除第三方工具目录（推荐用于生产环境）

如果 `toppic-windows-1.8.0/` 是第三方工具，应该通过其他方式分发（如单独的下载链接、包管理器等），而不是包含在 Git 仓库中：

```bash
# 1. 从 Git 历史中移除整个目录
git filter-repo --path toppic-windows-1.8.0/ --invert-paths

# 2. 更新文档，说明如何获取工具
# 在 README.md 中添加说明：
# "TopPIC 工具需要单独下载，请访问 [下载链接]"

# 3. 更新配置文件中的路径引用
# 确保 config/tools/toppic.json 中的路径指向外部安装位置

# 4. 强制推送
git push origin --force --all
```

## 预防措施

已更新 `.gitignore` 文件，包含以下规则：

- `*.onnx` - 忽略所有 ONNX 模型文件
- `toppic-windows-*/` - 忽略第三方工具目录
- `*.exe`, `*.dll` - 忽略可执行文件和库文件
- 其他常见的大文件和临时文件

## 验证清理效果

清理后，检查仓库大小：

```bash
# 查看仓库大小
git count-objects -vH

# 查看最大的文件
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {print substr($0,6)}' | sort --numeric-sort --key=2 | tail -10
```

## 注意事项

⚠️ **重要警告**：

1. **重写历史的影响**：使用 `git filter-repo` 或 `git filter-branch` 会重写 Git 历史，所有协作者都需要重新克隆仓库或重置他们的本地分支。

2. **备份**：在执行任何历史重写操作之前，务必备份仓库。

3. **团队协作**：如果这是一个多人协作的项目，需要：
   - 通知所有团队成员
   - 协调一个时间窗口进行迁移
   - 确保所有本地更改都已提交和推送

4. **GitHub 限制**：GitHub 对单个文件有 100MB 的硬限制，对仓库大小有建议限制。超过这些限制可能导致推送失败。

## 推荐操作步骤

1. ✅ **已完成**：更新 `.gitignore` 文件
2. 🔄 **下一步**：选择上述方案之一处理历史中的大文件
3. 📝 **文档更新**：更新 README，说明如何获取第三方工具
4. 🔍 **验证**：检查仓库大小，确保清理成功

## 参考资源

- [git filter-repo 文档](https://github.com/newren/git-filter-repo)
- [Git LFS 文档](https://git-lfs.github.com/)
- [GitHub 关于大文件的帮助](https://docs.github.com/en/repositories/working-with-files/managing-large-files)
