# 执行引擎架构说明

## 概述

TDEase 已完全解耦 Snakemake，采用自研的 FlowEngine + ShellRunner 架构实现工作流执行。

## 当前架构（2024+）

```
Frontend JSON → WorkflowNormalizer → WorkflowService → FlowEngine → LocalExecutor → ShellRunner
```

### 核心组件

| 组件 | 位置 | 职责 |
|------|------|------|
| **FlowEngine** | `app/core/engine/scheduler.py` | DAG 调度，拓扑遍历，节点状态管理 |
| **LocalExecutor** | `app/core/executor/local.py` | 任务执行，构建命令并调用 ShellRunner |
| **ShellRunner** | `app/core/executor/shell_runner.py` | Shell 命令执行，支持 `conda run` |
| **CommandBuilder** | `app/core/executor/command_builder.py` | 从 ToolRegistry 构建可执行命令 |

### 执行流程

1. **WorkflowService.execute_workflow()** 接收规范化后的工作流 JSON
2. **FlowEngine** 从 nodes + edges 构建 WorkflowGraph，拓扑排序
3. 对每个就绪节点：**output_check_fn** 检查输出存在则跳过（resume 模式）
4. **LocalExecutor** 通过 CommandBuilder 生成命令，**ShellRunner** 执行
5. **ExecutionStore** 持久化节点状态到 SQLite

### ShellRunner

- 无 Snakemake 依赖
- 无 Conda：`subprocess.run(cmd, shell=True, cwd=workdir)`
- 有 Conda：`conda run -n <env> --no-capture-output bash -c "<cmd>"`

## 迁移说明

- **src/snakemake/** 已移除
- **SnakemakeCLIAdapter** 保留为可选（需 `pip install snakemake`），未接入主流程
- 数据库 `executions.snakemake_args` 列保留以兼容现有数据

## 相关文档

- [ARCHITECTURE.md](ARCHITECTURE.md) - 系统整体架构
- [ROADMAP.md](ROADMAP.md) - 项目路线图
