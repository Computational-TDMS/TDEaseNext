# Section 2: 全局数据处理与运行架构 (Global Execution Architecture)

## 2.1 工作区管理系统 (Unified Workspace Manager)
TDEase 采用严格的文件层级结构，支持隔离的样品处理与结果溯源：
- **用户根目录** (`users/{user_id}`)：存储用户配置 `user.json`。
- **工作区隔离** (`workspaces/{workspace_id}`)：包含 `workflows`（定义）与 `executions`（实例）。
- **执行隔离区** (`executions/{exec_id}`)：每次运行对应一个独立目录，包含：
    - `/inputs`：所有外部输入文件的映射/副本。
    - `/outputs`：该次运行生成的中间与最终文件。
    - `/logs`：标准输出与错误流实时记录。
- **共享数据区** (`data/`)：存放原始 `raw` 和 `fasta` 公用数据库。

## 2.2 核心执行流水线 (Command Pipeline)
任何节点（Node）被调度后，都会进入 5 步流水线：
1.  **Resolved (解析态)**：根据 `UnifiedWorkspaceManager` 注入物理文件路径和样本上下文（`{sample}`, `{fasta_filename}`）。
2.  **Planned (计划态)**：根据工具定义的 JSON 模板，将参数转化为 CLI 标记位（Flags）。
3.  **Configured (配置态)**：处理 Conda 环境、Docker 容器挂载等运行时环境。
4.  **Executing (执行态)**：通过 `ShellRunner` 异步触发子进程，并将输出实时重定向至 WebSocket。
5.  **Completed/Failed (终态)**：采集产物，更新状态码。

## 2.3 多引擎转换器 (Engine Adapters)
- **LocalExecutor**：默认运行在本地。
- **CWL Exporter**：核心全局特性。系统允许将 TDEase 专有的图形化流程转化为通用的 CWL 原本，使得流程可以在 Arvados, Galaxy 等外部平台上无缝迁移。
- **Batch Dispatcher**：处理多样品执行，将单一样本的上下文自动应用到工作流的每一个节点。

## 2.4 工具定义驱动 (Tool Schema)
全系统的工具（Tool）均通过单一配置描述，不再硬编码 CLI 逻辑：
- **Port Definitions**：显式声明物理输入/输出。
- **Parameter Meta**：控制 UI 渲染的控件类型（Slider, Multi-select, FilePicker）。
- **Mapping Logic**：定义前端交互时，文件中的哪个列对应到 X 轴或 Y 轴。
- **subResources**（可选）：在输出端口上声明子资源路径模式（如 `**/data_js/prsms/prsm{id}.js`），供 DataResolverRegistry 等解析器使用，避免路径硬编码。
- **contextHooks**（可选）：声明式上下文注入与参数注入（如 `enrichSampleContext`、`injectParams`），由 WorkflowService 统一处理，替代针对特定 tool_id 的 if/else。
- **interactiveBehavior**（可选）：对 `executionMode: interactive` 的节点显式声明 `dataPassthrough`、`stateEmitter`、`outputProduces`，供 InputBindingPlanner 的 `find_real_source()` 等逻辑使用。

## 2.5 性能与可靠性
- **ProcessRegistry**：全局管理所有后台子进程，支持优雅中断（SIGTERM）与强制回收（SIGKILL）。
- **LRU Cache**：对频繁访问的节点输出列数据进行内存缓存，大幅降低磁盘 I/O。
- **Resume 跳过策略**：断点续跑基于 required 输出与节点完成 manifest 判定，不再使用“任一输出存在即可跳过”的宽松规则。

## 2.6 Typed Edge 语义与依赖规则
- **语义保留**：工作流归一化后保留 `connectionKind` 与 `semanticType`，缺失 `connectionKind` 时默认按 `data` 处理（向后兼容旧流程）。
- **依赖边类型**：调度依赖仅由 `data` / `control` 边构建；`state` 边不计入 predecessor，不阻塞计算节点就绪。
- **可观测性**：即使 `state` 边不参与调度依赖，也会保留在运行时 `edge_metadata` 中，便于 API 查询与问题定位。

## 2.7 持久状态与 Resume 准则
- **状态读穿**：执行状态 API 先读内存运行态；未命中时回退到 `ExecutionStore` 持久记录，支持进程重启后的状态查询。
- **终态对齐**：当内存态与持久态冲突且持久态为终态（`completed/failed/cancelled`）时，以持久态为准返回。
- **Resume 判定**：节点仅在“完成证据充分”时跳过：
  - 优先使用节点完成 manifest（含 `required_outputs`）；
  - 否则要求 required 输出全部存在（默认按声明输出集合判定），不再使用“任一输出存在即可跳过”。

## 2.8 Tool Registry 分层与遗留兼容
- **唯一权威实现**：生产执行链路统一使用 `app/services/tool_registry.py`。
- **配置分层优先级**（低 -> 高）：
  1. `config/tools/*.json`（共享基线，必须可移植）
  2. `config/tools/profiles/<profile>/*.json`（按 profile 顺序叠加）
  3. `data/tools/*.json`（本机/本环境覆盖，允许绝对路径）
- **Profile 选择**：通过环境变量 `TDEASE_TOOL_PROFILE`（单个）或 `TDEASE_TOOL_PROFILES`（逗号分隔）控制。
- **可移植性约束**：共享层（`config/tools` 与 profile 层）禁止机器绝对路径；命中时会拒绝该定义并输出迁移提示。

### Legacy 映射
- `src.nodes.tool_registry.ToolRegistry` -> `app.services.tool_registry.ToolRegistry`
- 旧 `registry_file` 直接注册表加载 -> 改为 `data/tools/*.json` 本地覆盖（避免仓库内机器路径漂移）
- 旧双实现并存 -> 现为兼容 shim，保留导入但不再作为主执行路径
