## Context

当前后端已具备完整的工作流执行引擎（FlowEngine + LocalExecutor），执行完成后文件存储在 `workspace_path/` 下。但前端无法可靠地访问这些文件内容。

现有 `app/api/visualization.py` 的问题：
- **路由混乱**：router prefix 是 `/nodes`，在 main.py 挂载时无额外 prefix，导致路径为 `/nodes/{execution_id}/data`，与 `/api/executions/` 风格不一致
- **文件定位脆弱**：`get_node_data` 用 `results_dir.glob(f"*{node_id}*")` 匹配文件，不可靠
- **职责不清**：同一文件混合了执行数据查询和工作区文件浏览

现有可复用的基础设施：
- `workflow_service.py` 中 `_resolve_output_paths()` 和 `_get_output_patterns()` 已实现从工具定义推导输出路径
- `tool_registry` 保存了所有工具定义，包含 `ports.outputs[].pattern`
- `executions` 表存有 `workflow_snapshot`（完整 VueFlow JSON）和 `sample_id`
- `workspace.py` 已实现 `/users/{user_id}/workspaces/{workspace_id}` 路由模式

## Goals / Non-Goals

**Goals:**

1. 提供可靠的节点输出数据 API，基于工具定义的 `ports.outputs.pattern` 推导路径（而非文件名匹配）
2. 提供工作区文件浏览 API，支持目录树和文件内容预览
3. 统一 API 路由风格，与现有 `/api/executions/` 和 `/api/workspaces/` 保持一致
4. 提供最新执行查询端点，支持工作流编辑模式下的数据预览
5. 所有端点的响应格式标准化，便于前端类型化对接

**Non-Goals:**

- 不做数据分页（交互式节点全量加载，由 P2 决定渲染策略）
- 不做数据溯源（`_source` 字段），当前阶段无明确需求
- 不做批量节点数据获取端点（单节点端点足够，前端可并发请求）
- 不做文件侧边栏与节点的联动（侧边栏是独立浏览工具）
- 不改变现有数据库 schema（通过推导而非持久化解决文件定位）

## Decisions

### Decision 1: 节点输出路径通过工具定义推导，不扩展 DB

**选择**：查询时从 `workflow_snapshot` + `tool_registry` + `sample_context` 实时推导输出路径

**替代方案**：在 `execution_nodes` 表新增 `output_files` 列持久化

**理由**：
- 工具定义的 `ports.outputs[].pattern` 已完整描述输出模式，`_resolve_output_paths()` 已实现推导逻辑
- 无需任何 DB 迁移，不改执行流程
- 推导逻辑与执行引擎共享同一套代码，保证一致性
- 如果未来 pattern 不可靠（如动态输出），再追加持久化方案

### Decision 2: 抽取 NodeDataService 服务层

**选择**：新建 `app/services/node_data_service.py`，封装路径推导 + 文件解析

**理由**：
- `_resolve_output_paths` 和 `_get_output_patterns` 目前在 `workflow_service.py` 中作为模块级函数存在，需要复用但不应直接 import（耦合执行逻辑）
- 将路径推导逻辑提取为独立的可复用函数，供执行引擎和数据查询两处调用
- 文件解析（TSV/CSV/feature 等格式）是独立关注点，不应混入 API 层

**具体做法**：
- 从 `workflow_service.py` 提取 `_get_output_patterns()` 和 `_resolve_output_paths()` 到新的 `app/services/node_data_service.py`
- `workflow_service.py` 改为 import 这些函数（保持向后兼容）
- 新增 `resolve_node_outputs(execution_id, node_id, db)` 方法，组合查询 + 推导流程
- 新增 `parse_tabular_file(file_path, max_rows=None)` 方法，返回标准化表格数据

### Decision 3: API 路由整理方案

**选择**：按资源类型分配端点

```
执行相关（app/api/execution.py，已有 /api/executions prefix）:
  GET /api/executions/{execution_id}/nodes/{node_id}/data    — 节点输出数据
  GET /api/executions/{execution_id}/nodes/{node_id}/files   — 节点输出文件列表

工作区相关（app/api/workspace.py，已有 /api prefix，路由 /users/.../workspaces/...）:
  GET /api/users/{user_id}/workspaces/{workspace_id}/files         — 目录树
  GET /api/users/{user_id}/workspaces/{workspace_id}/file-content  — 文件内容预览

工作流相关（app/api/workflow.py，已有 /api/workflows prefix）:
  GET /api/workflows/{workflow_id}/latest-execution                 — 最新执行
```

**替代方案**：保留 `visualization.py` 独立 router

**理由**：
- 端点按操作的资源归类（execution / workspace / workflow），而非按功能模块
- 与现有路由风格完全一致：`execution.py` 已有 `/{execution_id}/nodes/{node_id}` 路径模式
- `visualization.py` 的现有端点将被替代，文件可移除

### Decision 4: 响应格式标准化

**选择**：所有数据端点返回统一的结构化格式

```python
# 节点输出数据响应
{
    "execution_id": str,
    "node_id": str,
    "outputs": [
        {
            "port_id": str,          # 端口 ID（如 "ms1ft"）
            "data_type": str,        # 数据类型（如 "ms1ft"）
            "file_name": str,        # 文件名
            "file_path": str,        # 相对路径
            "file_size": int,        # 字节
            "exists": bool,          # 文件是否存在
            "parseable": bool,       # 是否可解析为表格
            "data": {                # 仅当 parseable=true 且请求 include_data=true
                "columns": [...],
                "rows": [...],
                "total_rows": int
            } | null
        }
    ]
}

# 文件内容预览响应
{
    "file_path": str,
    "file_name": str,
    "file_size": int,
    "file_type": "tabular" | "text" | "binary",
    "content": {                     # tabular
        "columns": [str],
        "rows": [dict],
        "total_rows": int,
        "preview_rows": int
    } | str | null                   # text | binary(null)
}
```

**理由**：
- 节点可能有多个输出端口（如 ProMex 输出 ms1ft + png + pbf），逐端口列出
- `include_data` query param 控制是否内联数据，支持前端分步加载（先列表后数据）
- 前端可直接定义 TypeScript 接口对应此格式

### Decision 5: 文件解析策略

**选择**：按扩展名分类，支持 TSV/CSV/TXT（tab-separated）三种表格格式

**支持的格式**：
| 扩展名 | 分隔符 | 典型文件 |
|--------|--------|----------|
| .tsv | `\t` | TopPIC 输出 |
| .csv | `,` | 通用导出 |
| .txt | `\t` | feature 文件、msalign |
| .ms1ft | `\t` | ProMex 输出 |
| .feature | `\t` | TopFD 输出 |

**不解析的格式**（返回文件元信息）：
- .pbf, .raw, .mzml — 二进制/大型文件
- .png, .jpg — 图片文件
- .fasta — 序列文件（可后续扩展）

**理由**：
- 蛋白质组学工具输出多为 tab-separated 文本文件
- 对于非标准扩展名（如 `.ms1ft`, `.feature`），按 tab-separated 解析即可
- 图片文件可通过 `FileResponse` 直接返回（已有 `/download` 端点）

## Risks / Trade-offs

### [Risk] 推导路径与实际文件不一致
- **场景**：工具定义的 pattern 更新后，历史执行的输出文件名不匹配
- **缓解**：`exists` 字段明确标记文件是否存在，前端据此显示状态；`workflow_snapshot` 保存了执行时的 vueflow_data，可回溯当时的 tool_id

### [Risk] 大文件全量传输导致响应缓慢
- **场景**：某些 feature 文件可能有数万行，全量加载 JSON 响应体较大
- **缓解**：`include_data` 默认 false，前端需显式请求数据内联；响应压缩（FastAPI gzip middleware）

### [Risk] 路由重构导致前端旧请求失败
- **场景**：移除 `visualization.py` 后，前端硬编码的旧路径失效
- **缓解**：当前前端尚未大量使用这些端点（仅 preview 有少量调用），重构窗口期可控；可保留旧路由作为 redirect（非必须）

### [Risk] sample_context 查询复杂
- **场景**：推导路径需要 sample_context，但 `executions` 表只存 `sample_id`，需要二次查询 `samples` 表
- **缓解**：`NodeDataService.resolve_node_outputs()` 封装完整查询链，API 层无需关心
