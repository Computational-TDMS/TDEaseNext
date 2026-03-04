# 节点连接与数据传递

**更新日期**: 2026-03-04
**版本**: 1.1

## 概述

本文档详细说明了 TDEase 工作流中节点之间的连接方式、数据传递机制以及文件路径解析。

---

## 节点连接类型

### 1. 处理节点 → 处理节点

**连接方式**：通过 VueFlow 的 edge 连接，定义数据流向

**数据传递**：文件路径
- 上游节点的输出文件 → 下游节点的输入参数
- 通过 `WorkflowService._resolve_input_paths()` 解析路径
- 支持多输出端口到多输入端口的映射

**示例**：
```
[data_loader] → [msconvert]
  output: raw_file    input: ms2_file
```

### 2. 处理节点 → 交互式节点（规划中）

**连接方式**：VueFlow edge 连接

**数据传递**：文件加载到前端
- 节点激活时，前端通过 API 加载上游节点的输出文件
- 数据全量传输到前端，缓存在 Pinia Store
- 后续交互操作（筛选、框选）在前端完成

**API**：
```
GET /api/executions/{execution_id}/nodes/{node_id}/data
```

### 3. 交互式节点 → 交互式节点（规划中）

**连接方式**：VueFlow edge 连接

**数据传递**：前端选择状态
- 不触发后端 API 调用
- 通过 Pinia Store 传播状态
- 用户在节点 A 的选择自动更新节点 B 的显示

**示例**：
```
[FeatureMap] → [Spectrum]
  用户框选区域 → Spectrum 显示对应的质谱图
```

### 4. 交互式节点 → 处理节点（规划中）

**连接方式**：VueFlow edge 连接

**数据传递**：状态 → 临时文件
- 用户触发执行时，前端将选择状态转换为临时文件
- 临时文件作为处理节点的输入
- 执行完成后，临时文件可被清理

**流程**：
1. 用户在交互式节点中选择数据
2. 用户点击"执行下游节点"
3. 前端生成临时文件（包含选择的数据）
4. 后端处理节点读取临时文件
5. 返回处理结果

---

## 数据流详解

### 输入路径解析

**函数**：`WorkflowService._resolve_input_paths()`

**职责**：根据 edges 和上游节点输出解析输入路径

**参数**：
- `node_id`: 当前节点 ID
- `edges`: VueFlow edges 列表
- `nodes_map`: 所有节点的映射
- `tools_registry`: 工具定义注册表
- `completed_outputs`: 已完成节点的输出文件

**解析策略（2026-03-04 更新）**：

1. **按 targetHandle 筛选边**：
   - 只关注 target 为当前节点的边

2. **提取连接信息**：
   - `source`: 上游节点 ID
   - `sourceHandle`: 上游输出端口（如 "output-ms1_file"）
   - `targetHandle`: 下游输入端口（如 "input-ms2_file"）

3. **解析目标端口 ID（targetHandle 宽松匹配）**：
   - 优先按输入端口 `id` 匹配
   - 其次按 `handle`（若定义）匹配
   - 再按输入 `dataType` 或 `accept` 扩展名匹配
   - 若目标工具只有一个输入端口，自动回退到该端口

4. **匹配上游输出文件（多信号评分）**：
   - 信号 A：`sourceHandle` 与上游输出 `handle/id/dataType/provides` 是否匹配
   - 信号 B：目标输入端口与上游输出是否兼容（`dataType/provides/accept/实际文件扩展名`）
   - 兼容错误句柄：即使 `sourceHandle` 不准确（例如 `output-mzml` 连到只定义 `handle=output` 的节点），仍可通过目标端口兼容性和文件扩展名选中正确文件
   - 单输出兜底：上游仅一个输出文件时，直接映射到目标端口

5. **处理交互式节点穿越**：
   - 如果上游是交互式节点，递归查找真实的数据源
   - 交互式节点不产生文件，需要找到其上游的处理节点

**支持穿越交互式节点**：
```python
def find_real_source(interactive_src_id, visited):
    """递归查找真实的非交互式源节点"""
    if is_intermediate_node(interactive_src_id):
        # 继续向上游查找
        return find_real_source(upstream_src_id, visited)
    else:
        return interactive_src_id
```

### 输出路径解析

**函数**：`WorkflowService._resolve_output_paths()`

**职责**：根据工具定义推导输出文件路径

**参数**：
- `tool_info`: 工具定义
- `sample_context`: 样品上下文
- `output_dir`: 输出目录

**推导规则**：
1. 从 `tool_info['ports']['outputs']` 获取输出端口定义
2. 每个输出端口有 `pattern` 字段（如 `"{sample}_ms1.msalign"`）
3. 用 `sample_context` 替换占位符：
   - `{sample}` → 样品 ID
   - `{basename}` → 输入文件名（不含扩展名）
   - `{dir}` → 输入文件目录
   - 其他自定义键 → 从 `sample_context` 获取

**示例**：
```python
# 工具定义
{
  "ports": {
    "outputs": [
      {"id": "ms1_file", "pattern": "{sample}_ms1.msalign"}
    ]
  }
}

# sample_context
{"sample": "sample1"}

# 推导结果
output_path = "results/sample1_ms1.msalign"
```

---

## 占位符系统

### 占位符类型

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{sample}` | 样品 ID | `sample1` |
| `{basename}` | 输入文件名（不含扩展名） | `Sorghum-Histone0810162L20` |
| `{extension}` | 输入文件扩展名 | `.raw` |
| `{dir}` | 输入文件目录 | `data/raw` |
| 自定义键 | 从 `sample_context` 获取 | `{fasta_filename}` |

### 占位符推导

**优先级**：
1. `sample_context` 中的显式值
2. 输入文件的 basename
3. 默认值（如 "sample"）

**示例**：
```json
{
  "context": {
    "sample": "sample1",
    "fasta_filename": "UniProt_sorghum_focus1"
  },
  "data_paths": {
    "raw": "data/raw/Sorghum-Histone0810162L20.raw"
  }
}
```

- `{sample}` → `"sample1"`（来自 context）
- `{basename}` → `"Sorghum-Histone0810162L20"`（来自 raw 文件）
- `{fasta_filename}` → `"UniProt_sorghum_focus1"`（来自 context）

---

## 输入端口定义

### positional 参数

**定义方式**：在 `ports.inputs` 中设置 `positional: true`

**作用**：标记该输入为位置参数，按 `positionalOrder` 顺序传递

**示例**：
```json
{
  "ports": {
    "inputs": [
      {
        "id": "input_file",
        "dataType": "ms2",
        "required": true,
        "positional": true,
        "positionalOrder": 1
      }
    ]
  }
}
```

### 兼容性：positional_params

**旧格式**：使用顶层 `positional_params` 数组

```json
{
  "positional_params": ["ms2_file", "database"]
}
```

**解析优先级**：
1. 优先使用 `ports.inputs` 中的 `positional` 字段
2. 如果不存在，回退到 `positional_params`

---

## 连接验证

### 验证规则

1. **端口类型匹配**：
   - 输出的 `dataType` 必须兼容输入的 `dataType`

2. **必需端口检查**：
   - 所有 `required: true` 的输入端口都必须连接

3. **循环依赖检测**：
   - 工作流不能有循环依赖
   - FlowEngine 通过拓扑排序检测

4. **交互式节点穿越**：
   - 交互式节点可以有下游处理节点
   - 但必须最终连接到处理节点才有数据

### 前端验证

**时机**：用户连接节点时

**实现**：
- VueFlow 的 `onConnect` 事件
- 检查源端口和目标端口的类型兼容性
- 显示错误提示（如不兼容）

---

## 相关文档

- [系统架构](ARCHITECTURE.md) - 完整的系统架构说明
- [工作流格式](guides/workflow-format.md) - VueFlow JSON 格式
- [工具注册指南](guides/tool-registration.md) - 如何定义工具的输入输出
