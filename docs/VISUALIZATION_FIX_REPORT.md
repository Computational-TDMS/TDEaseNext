# 可视化节点数据加载问题修复报告

## 📋 问题总结

### 发现的问题

1. **工具定义不支持多种输入格式**
   - `featuremap_viewer` 只定义了一个输入端口，期望 `{sample}_ms1.feature` 格式
   - 但工作流中有两个 featuremap_viewer 节点：
     - `featuremap_1` 接收 ProMex 输出 (`.ms1ft`)
     - `featuremap_2` 接收 TopFD 输出 (`.ms1.feature`)
   - 两个工具输出的文件格式和列名都不同

2. **文件名模式不匹配**
   - TopFD 输出: `{sample}_ms1.feature`
   - ProMex 输出: `{sample}.ms1ft`
   - 原始工具定义只支持 TopFD 格式

3. **列名映射不一致**
   - TopFD 列名: `feature_id`, `mz`, `rt`, `intensity`, `charge`, `mass`
   - ProMex 列名: `FeatureID`, `Mass`, `RT`, `Intensity`, `Charge`, `EValue`, `QValue`

4. **缺乏详细日志**
   - 后端无法追踪文件查找过程
   - 前端无法确定是文件未找到还是列名不匹配

## ✅ 修复方案

### 1. 更新工具定义 (`featuremap_viewer.json`)

**修改前:**
```json
{
  "ports": {
    "inputs": [
      {
        "id": "feature_data",
        "name": "Feature Data",
        "dataType": "feature",
        "pattern": "{sample}_ms1.feature"
      }
    ]
  }
}
```

**修改后:**
```json
{
  "ports": {
    "inputs": [
      {
        "id": "topfd_feature",
        "name": "TopFD Feature Data",
        "dataType": "ms1feature",
        "accept": ["ms1feature", "feature"],
        "pattern": "{sample}_ms1.feature",
        "columnMapping": {
          "feature_id": "feature_id",
          "mz": "mz",
          "rt": "rt",
          "intensity": "intensity",
          "charge": "charge",
          "mass": "mass"
        }
      },
      {
        "id": "promex_feature",
        "name": "ProMex Feature Data",
        "dataType": "ms1ft",
        "accept": ["ms1ft", "feature"],
        "pattern": "{sample}.ms1ft",
        "columnMapping": {
          "feature_id": "FeatureID",
          "mz": "Mass",
          "rt": "RT",
          "intensity": "Intensity",
          "charge": "Charge",
          "mass": "Mass"
        }
      }
    ]
  }
}
```

**关键改进:**
- ✅ 支持两种输入格式 (TopFD 和 ProMex)
- ✅ 添加列名映射配置
- ✅ 使用不同的端口 ID 区分数据源

### 2. 增强后端日志 (`node_data_service.py`)

**添加的日志点:**

```python
# 文件解析开始
logger.info(f"[parse_tabular_file] Starting to parse file: {file_path}")
logger.info(f"[parse_tabular_file] File exists: {file_path.exists()}")

# 文件元信息
logger.info(f"[parse_tabular_file] File extension: {extension}, delimiter: '{delimiter}'")

# 列名信息
logger.info(f"[parse_tabular_file] Found {len(columns)} columns: {columns}")

# 解析结果
logger.info(f"[parse_tabular_file] Successfully parsed {len(rows)} rows (total: {total_rows})")

# 节点输出解析
logger.info(f"[resolve_node_outputs] Resolving output paths for node {node_id}")
logger.info(f"[resolve_node_outputs] Sample context: {sample_context}")

# 每个输出文件的详细信息
logger.info(f"[resolve_node_outputs] Processing output {idx}: {file_name}")
logger.info(f"  - Full path: {file_path}")
logger.info(f"  - Exists: {file_exists}")
logger.info(f"  - Size: {file_size} bytes")
logger.info(f"  - Extension: {extension}")
logger.info(f"  - Parseable: {parseable}")
```

**日志输出示例:**
```
[resolve_node_outputs] Resolving output paths for node topfd_1
[resolve_node_outputs] Sample context: {'sample': 'test'}
[resolve_node_outputs] Resolved 6 output paths:
  [0] /workspace/test_ms1.feature - exists: True, size: 45678 bytes
  [1] /workspace/test_ms2.feature - exists: True, size: 12345 bytes
  ...

[parse_tabular_file] Starting to parse file: /workspace/test_ms1.feature
[parse_tabular_file] File exists: True
[parse_tabular_file] File extension: .feature, delimiter: '	'
[parse_tabular_file] Found 7 columns: ['feature_id', 'mz', 'rt', 'intensity', 'charge', 'mass', 'ecscore']
[parse_tabular_file] Successfully parsed 1234 rows (total: 1234)
```

### 3. 增强前端日志 (`visualization.ts`)

**添加的日志点:**

```typescript
// 请求参数
console.log(`[VisualizationStore] Loading node data:`, {
  nodeId,
  executionId,
  upstreamNodeId,
  actualNodeId
})

// API 调用
console.log(`[VisualizationStore] Calling API: /api/executions/${executionId}/nodes/${actualNodeId}/data`)

// 响应概览
console.log(`[VisualizationStore] Number of outputs: ${response.outputs?.length || 0}`)

// 每个输出的详细信息
response.outputs?.forEach((output, idx) => {
  console.log(`[VisualizationStore] Output [${idx}]:`, {
    port_id: output.port_id,
    file_name: output.file_name,
    file_path: output.file_path,
    exists: output.exists,
    parseable: output.parseable,
    has_data: output.data !== null,
    data_rows: output.data?.rows?.length || 0,
    data_columns: output.data?.columns || []
  })
})
```

**控制台输出示例:**
```
[VisualizationStore] Loading node data: {
  nodeId: 'featuremap_2',
  executionId: 'exec_123',
  upstreamNodeId: 'topfd_1',
  actualNodeId: 'topfd_1'
}
[VisualizationStore] Number of outputs: 6
[VisualizationStore] Output [0]: {
  port_id: 'ms1feature',
  file_name: 'test_ms1.feature',
  file_path: '/workspace/test_ms1.feature',
  exists: true,
  parseable: true,
  has_data: true,
  data_rows: 1234,
  data_columns: ['feature_id', 'mz', 'rt', 'intensity', 'charge', 'mass', 'ecscore']
}
```

### 4. 更新测试工作流 (`wf_test_full_fixed.json`)

**关键修改:**

1. **featuremap_1** (ProMex 数据):
```json
{
  "inputs": [
    {
      "id": "promex_feature",
      "name": "ProMex Feature Data",
      "dataType": "ms1ft",
      "required": true
    }
  ]
}
```

2. **featuremap_2** (TopFD 数据):
```json
{
  "inputs": [
    {
      "id": "topfd_feature",
      "name": "TopFD Feature Data",
      "dataType": "ms1feature",
      "required": true
    }
  ]
}
```

3. **连接更新:**
```json
{
  "id": "e_promex_featuremap1",
  "source": "promex_1",
  "target": "featuremap_1",
  "sourceHandle": "output-ms1ft",
  "targetHandle": "input-promex_feature"
},
{
  "id": "e_topfd_featuremap2",
  "source": "topfd_1",
  "target": "featuremap_2",
  "sourceHandle": "output-ms1feature",
  "targetHandle": "input-topfd_feature"
}
```

## 🔍 诊断流程

现在当遇到数据加载问题时，可以通过以下步骤快速定位：

### 步骤 1: 检查前端日志

**问题: 找不到文件**
```
[VisualizationStore] Output [0]: {
  exists: false,
  parseable: false
}
```
→ 检查后端工作流执行状态和文件生成

**问题: 文件存在但无法解析**
```
[VisualizationStore] Output [0]: {
  exists: true,
  parseable: false
}
```
→ 检查文件扩展名是否在 `TABULAR_EXTENSIONS` 中

**问题: 列名不匹配**
```
[VisualizationStore] Output [0]: {
  exists: true,
  parseable: true,
  data_columns: ['FeatureID', 'Mass', 'RT', ...]
}
```
→ 检查工具定义中的 `columnMapping` 配置

### 步骤 2: 检查后端日志

**文件未找到:**
```
[resolve_node_outputs] Processing output 0: test_ms1.feature
  - Exists: False
```
→ 工作流未执行或执行失败

**文件扩展名不支持:**
```
[resolve_node_outputs] Processing output 0: test.unknown
  - Extension: .unknown
  - Parseable: false (in TABULAR_EXTENSIONS: False)
```
→ 将扩展名添加到 `TABULAR_EXTENSIONS`

**解析成功:**
```
[parse_tabular_file] Successfully parsed 1234 rows
[parse_tabular_file] Columns: ['feature_id', 'mz', 'rt', ...]
```
→ 数据已正确加载，检查前端渲染逻辑

## 📝 下一步操作

### 立即测试

1. **重启后端服务**
   ```bash
   cd D:\Projects\TDEase-Backend
   python -m app.main
   ```

2. **重启前端服务**
   ```bash
   cd D:\Projects\TDEase-Backend\TDEase-FrontEnd
   pnpm run dev
   ```

3. **加载修复后的工作流**
   - 导入 `workflows/wf_test_full_fixed.json`
   - 执行工作流
   - 查看可视化节点

### 查看日志

**后端日志** (控制台或 `logs/app.log`):
```
[resolve_node_outputs] Resolving output paths for node topfd_1
[parse_tabular_file] Starting to parse file: /path/to/file.ms1.feature
```

**前端日志** (浏览器开发者工具):
```
[VisualizationStore] Loading node data: {...}
[VisualizationStore] Output [0]: {...}
```

### 如果仍有问题

根据日志信息定位问题：

1. **文件不存在** → 检查工作流执行状态
2. **文件无法解析** → 检查文件格式和扩展名
3. **列名不匹配** → 更新 `columnMapping` 配置
4. **前端渲染失败** → 检查可视化组件配置

## 🎯 预期结果

修复后，你应该看到：

1. ✅ `featuremap_1` 正确显示 ProMex 数据
2. ✅ `featuremap_2` 正确显示 TopFD 数据
3. ✅ 详细的日志输出，便于调试
4. ✅ 清晰的错误消息，帮助快速定位问题

## 📚 相关文件

- `config/tools/featuremap_viewer.json` - 工具定义
- `app/services/node_data_service.py` - 后端数据服务
- `TDEase-FrontEnd/src/stores/visualization.ts` - 前端数据存储
- `workflows/wf_test_full_fixed.json` - 修复后的测试工作流
- `docs/VISUALIZATION_FIX_REPORT.md` - 本文档
