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

## 2.5 性能与可靠性
- **ProcessRegistry**：全局管理所有后台子进程，支持优雅中断（SIGTERM）与强制回收（SIGKILL）。
- **LRU Cache**：对频繁访问的节点输出列数据进行内存缓存，大幅降低磁盘 I/O。
- **Resume 跳过策略**：断点续跑时，只要节点声明的输出中任意一个已存在，即视为该节点已完成并跳过；这可兼容带条件输出的工具（例如 MSPathFinderT）。
