# TDEase 工作空间架构与文件传递模式

## 核心设计原则

### 1. 文件流架构
```
外部文件 (完整路径) → data_loader/fasta_loader → 工作流目录/{sample}.raw/{fasta_filename}.fasta → 后续工具
```


在我们工作流之间进行文件传递是怎么做的?






### 2. 工作目录管理
- **每个工作流独立工作目录**: `data/workflows/{workflow_id}/`
- **扁平化文件管理**: 所有文件在工作目录根目录（简化路径处理）
- **路径统一**: 所有工具使用相对路径访问文件

### 3. 样品命名原则
- **sample**: 从 `data_loader.input_sources[0]` 的文件名提取（不含扩展名）
- **fasta_filename**: 从 `fasta_loader.fasta_file` 的文件名提取（不含扩展名）
- **通配符解析**: `{sample}` 和 `{fasta_filename}` 在工作流执行时被具体值替换

## 当前实现状态

### ✅ 已实现功能
1. **工作流目录创建**: 自动创建 `data/workflows/{workflow_id}/`
2. **文件复制机制**: `data_loader` 和 `fasta_loader` 将外部文件复制到工作目录
3. **通配符系统**: 支持 `{sample}` 和 `{fasta_filename}` 通配符
4. **工具链执行**: 支持多工具顺序执行（data_loader → msconvert_docker → topfd → toppic）

### ⚠️ 当前问题
1. **data_loader执行失败**: 规则构建或执行环境问题
2. **路径管理不完整**: workspace目录的路径管理逻辑缺失
3. **工具输出控制**: 某些工具（如topfd）默认输出到输入文件目录

## 文件传递模式

### 前端 → 后端传递
```json
{
  "input_sources": ["/home/ray/TDEase-Backend/data/Sorghum-Histone0810162L20.raw"],
  "fasta_file": "/home/ray/TDEase-Backend/data/UniProt_sorghum_focus1.fasta"
}
```

### 后端处理流程
1. **路径验证**: 检查文件是否存在
2. **样品名提取**: 从文件名提取 `sample` 和 `fasta_filename`
3. **文件复制**: 使用 `data_loader`/`fasta_loader` 复制到工作目录
4. **通配符替换**: 在工作流规则中替换 `{sample}` 和 `{fasta_filename}`

## 工具执行环境

### 工作目录设置
```python
# Snakemake工作流配置
workflow = Workflow(
    overwrite_workdir=workspace_dir,  # 设置工作目录
    # ... 其他设置
)
```

### 工具命令构建
- **loader工具**: `--output .`（输出到当前工作目录）
- **其他工具**: `--output {output}`（使用Snakemake输出占位符）
- **参数传递**: 支持JSON参数和直接参数映射

## 待修复问题

### 1. data_loader执行问题
- **症状**: 规则执行失败，无详细错误信息
- **可能原因**: 工作目录设置、shell命令构建、执行环境
- **解决方案**: 添加详细日志，修复命令构建逻辑

### 2. 路径管理补全
- **缺失功能**: workspace目录的完整路径管理
- **需要添加**: 输入文件验证、输出文件收集、中间文件清理
- **实现方案**: 创建WorkspaceManager类统一管理

### 3. 工具输出适配
- **问题工具**: topfd等无法指定输出位置的工具
- **解决方案**: 运行前切换目录或使用符号链接
- **实现方式**: 在工具定义中添加`output_behavior`字段

## 测试工作流修复重点

### 测试工作流: wf_test_full
```
data_loader → msconvert_docker → topfd → toppic
```

### 修复步骤
1. **验证data_loader执行**: 确保文件正确复制到工作目录
2. **检查通配符解析**: 确保`{sample}`和`{fasta_filename}`正确替换
3. **验证工具链连接**: 确保每个工具的输出是下一个工具的输入
4. **检查最终输出**: 确保`{sample}_proteoforms.tsv`正确生成

## 架构优势

### 1. 简化前端传递
- 前端只需传递完整文件路径
- 样品名自动提取，无需手动指定
- 工作流定义与具体文件解耦

### 2. 统一执行环境
- 所有工具在相同工作目录执行
- 使用相对路径，避免绝对路径依赖
- 支持工具链的自动连接

### 3. 可扩展性
- 支持多样品批量处理
- 支持工具插件化扩展
- 支持工作流模板化

## 后续优化方向

### 短期优化
1. 修复当前测试工作流执行问题
2. 补全workspace路径管理逻辑
3. 增强错误处理和日志记录

### 中期优化
1. 支持分层目录结构（inputs/, intermediates/, outputs/）
2. 增强样品管理（支持别名、元数据）
3. 优化前端文件选择器

### 长期优化
1. 工作流版本管理
2. 批量样品处理
3. 性能优化和缓存机制

