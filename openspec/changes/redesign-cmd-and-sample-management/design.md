## Context

TDEase 是一个自顶向下蛋白质组学数据分析平台，采用节点化工作流架构。当前执行链路为：

```
Frontend JSON → WorkflowNormalizer → WorkflowService → FlowEngine → LocalExecutor → CommandBuilder → ShellRunner
```

现有问题集中在三个环节：
1. **CommandBuilder** 采用大量 `if tool_type == "command"` 分支，参数过滤散落在 normalizer、command_builder、前端三处
2. **Sample Context** 是一个 flat dict (`{sample: str, fasta_filename: str}`)，由 `_extract_sample_ctx_from_workflow` 从节点 params 中脆弱推导
3. **Tool Definition** 前后端各自维护 `config/tools/*.json`，结构不完全一致，缺乏 schema 校验

当前已支持的工具类型：native command（TopFD/TopPIC/MSConvert）、Python script（data_loader/fasta_loader）。未来需支持 Docker 容器、R 脚本等。

## Goals / Non-Goals

**Goals:**
- 建立以 Tool Definition 为唯一真相源（Single Source of Truth）的命令构建管线
- 设计结构化 Sample Table 替代 flat dict，支持多样本 + 多关联文件
- 统一前后端工具定义 Schema，前端根据 Schema 渲染参数表单
- 参数过滤在管线入口统一处理一次，而非散布多处
- 保持向后兼容：现有 `tests/test.json` 格式经归一化后仍可执行
- 预留交互式可视化节点的类型扩展点

**Non-Goals:**
- 本轮不实现 Docker/远程执行引擎（仅预留 executionMode 字段）
- 不重写 FlowEngine DAG 调度逻辑（保持现有拓扑排序）
- 不实现前端可视化节点的完整功能（仅设计类型扩展点）
- 不重新设计数据库 schema（在现有 metadata JSON 列中扩展）

## Decisions

### D1: Tool Definition Schema 作为唯一驱动源

**决策**: 将 `config/tools/*.json` 升级为严格的 JSON Schema，CommandBuilder 完全依据此 Schema 构建命令，消除所有 tool_type 分支硬编码。

**新 Schema 结构**:
```jsonc
{
  "id": "string",                    // 工具唯一标识
  "name": "string",                  // 显示名称
  "version": "string",               // 工具版本
  "executionMode": "native | script | docker",
  "command": {
    "executable": "string",          // 可执行文件路径或命令名
    "interpreter": "python | Rscript | null",  // script 模式下的解释器
    "useUv": true                    // 是否使用 uv run
  },
  "ports": {
    "inputs": [
      {
        "id": "string",             // 端口标识
        "name": "string",           // 显示名称
        "dataType": "string",       // 数据类型 (mzml, fasta, msalign, raw, tsv...)
        "required": true,
        "accept": ["string"],       // 可接受的数据类型列表
        "positional": true,         // 是否作为位置参数
        "positionalOrder": 0        // 位置参数的顺序
      }
    ],
    "outputs": [
      {
        "id": "string",
        "name": "string",
        "dataType": "string",
        "pattern": "{sample}_ms2.msalign",   // 输出文件模式
        "handle": "string"                    // handle 标识
      }
    ]
  },
  "parameters": {
    "<param_id>": {
      "flag": "-a",                  // CLI flag
      "type": "value | boolean | choice",
      "label": "string",            // 前端显示标签
      "description": "string",
      "default": "any",             // 默认值
      "required": false,
      "choices": {},                // choice 类型的可选值
      "group": "string",            // 参数分组（前端渲染用）
      "advanced": false             // 是否为高级参数
    }
  },
  "output": {
    "flagSupported": false,          // 是否支持 -o 输出路径
    "flag": "-o",                    // 输出 flag
    "flagValue": "."                 // 固定输出值（如 msconvert 的 -o .）
  }
}
```

**理由**: 当前 `param_mapping`、`positional_params`、`output_flag_supported` 等字段散落且缺乏约束。统一到一个清晰的 Schema 后，CommandBuilder 只需遍历 Schema 即可，无需知道具体工具类型。

**替代方案考虑**:
- 方案 B：保持当前结构，仅修补 CommandBuilder 分支 → 否决：补丁越多越脆弱
- 方案 C：使用 YAML 代替 JSON → 否决：前端直接消费 JSON 更方便

### D2: 命令构建管线（Pipeline 模式）

**决策**: CommandBuilder 重构为 Pipeline 模式，按固定步骤执行：

```
ToolDef + NodeParams + InputPaths + OutputPaths
  → Step 1: 参数过滤（移除 null/empty/None）
  → Step 2: 解析 executable（根据 executionMode 确定命令前缀）
  → Step 3: 输出 flag（根据 output.flagSupported 决定是否添加）
  → Step 4: 参数 flags（遍历 parameters，按 type 生成 flag）
  → Step 5: 位置参数（按 positionalOrder 排序，从 input_paths 映射）
  → 组装为最终命令字符串
```

**理由**: 每一步职责单一，可独立测试，新工具类型只需在 Step 2 扩展。

### D3: Sample Table 设计

**决策**: 引入 `SampleTable` 结构，替代 flat dict `sample_context`。

```jsonc
{
  "sample_table": [
    {
      "sample_id": "Sorghum-Histone0810162L20",
      "files": {
        "raw": "D:/data/Sorghum-Histone0810162L20.raw",
        "fasta": "D:/data/UniProt_sorghum_focus1.fasta"
      },
      "metadata": {}  // 可扩展的样本元数据
    }
  ]
}
```

**占位符解析**: output_patterns 中的 `{sample}` 从 `sample_id` 解析，`{fasta_filename}` 从 `files.fasta` 的 stem 解析。解析逻辑统一在 `SampleResolver` 类中，不再从节点 params 中脆弱推导。

**存储位置**: 存于 workflow JSON 的 `metadata.sample_table` 中。批量执行时，遍历 sample_table 中的每一行。

**兼容性**: 如果 `sample_table` 为空，fallback 到从 data_loader/fasta_loader 节点推导（保持向后兼容），但会发出 deprecation warning。

**理由**: 当前 `_extract_sample_ctx_from_workflow` 需要遍历节点猜测 sample 和 fasta_filename，每增加一种关联文件就需要新增推导逻辑，不可扩展。

**替代方案考虑**:
- 方案 B：保持 flat dict 但添加更多 key → 否决：不支持多样本
- 方案 C：独立的 sample CSV 文件 → 否决：增加文件管理复杂度，JSON 内嵌更简洁

### D4: 前端参数渲染基于 Tool Definition

**决策**: 前端 PropertyPanel 直接消费 Tool Definition 的 `parameters` 字段渲染表单，而非维护独立的参数配置。

- `type: "value"` → 文本输入框
- `type: "boolean"` → 开关/复选框
- `type: "choice"` → 下拉选择器
- `advanced: true` → 折叠到"高级参数"区域
- `group` → 参数分组展示
- `required: true` → 必填标记
- `default` → 预填充值

保存时，前端仅序列化用户实际修改过的值（非默认值），或所有非空值。CommandBuilder 侧使用 Tool Definition 的 `default` 填充未提供的值。

**理由**: 消除前后端工具定义不一致的根源。

### D5: 可视化节点类型扩展点

**决策**: 在 Tool Definition Schema 中预留 `executionMode: "interactive"` 类型，用于未来的交互式可视化节点。

此类节点不执行 CLI 命令，而是：
1. 后端提供数据读取 API（读取上游节点的输出文件）
2. 前端渲染可视化组件（表格、图表、筛选器）
3. 用户交互后，将筛选结果写回为节点输出

本轮不实现具体功能，仅在 Schema 中预留字段，确保新增此类型时不需要修改 Schema 结构。

## Risks / Trade-offs

**[Tool Definition 迁移成本]** → 需要更新所有现有 `config/tools/*.json` 和前端对应文件。通过编写迁移脚本自动转换，减少手工操作。

**[向后兼容]** → 旧格式 workflow JSON 中的 `sample_context` flat dict 需要兼容。在 `SampleResolver` 中实现 fallback 路径：flat dict → 自动转换为单行 SampleTable。

**[前端改动范围]** → PropertyPanel 需要适配新的 Tool Definition 结构。通过 adapter layer 将新旧格式映射，逐步迁移。

**[多样本并行]** → SampleTable 多行时，FlowEngine 需要为每个 sample 生成独立的执行路径。当前 FlowEngine 不支持样本维度展开。短期方案：在 WorkflowService 层循环执行，长期方案：FlowEngine 支持样本维度 DAG 展开。

**[参数默认值策略]** → 前端只序列化非默认值 vs 序列化所有非空值。选择后者更安全（避免 Tool Definition 默认值变更导致行为变化），但 JSON 体积更大。可接受的 trade-off。
