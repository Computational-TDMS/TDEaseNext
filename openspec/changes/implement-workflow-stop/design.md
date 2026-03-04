# Workflow Cancellation Design

## Context

### Current State

TDEase 后端使用以下架构执行工作流：

1. **API 层** (`app/api/execution.py`): `POST /api/executions/{id}/stop` 调用 `execution_manager.stop()`
2. **ExecutionManager** (`app/services/runner.py`): 内存中的执行记录管理，`stop()` 方法只更新状态
3. **WorkflowService** (`app/services/workflow_service.py`): 遍历节点，为每个节点创建 `TaskSpec` 并调用 `executor.execute()`
4. **LocalExecutor** (`app/core/executor/local.py`): 使用 `CommandPipeline` 构建命令，通过 `ShellRunner` 执行
5. **ShellRunner** (`app/core/executor/shell_runner.py`): 使用 `subprocess.Popen` 执行命令，但进程对象是局部变量

### Problem

`subprocess.Popen` 创建的进程对象没有在全局保存，导致：
- 无法后续访问进程来调用 `terminate()` 或 `kill()`
- `LocalExecutor.cancel()` 只返回 `False`
- 停止操作只更新状态，不触及底层进程

### Constraints

- 使用 Python 标准库（`threading.Lock`, `subprocess`）
- 不引入新的外部依赖
- 保持向后兼容
- 支持并发执行（多个工作流同时运行）
- 确保线程安全

## Goals / Non-Goals

**Goals:**
1. 实现真正的工作流停止功能，能够终止运行中的子进程
2. 提供进程注册表机制来追踪运行中的进程
3. 支持优雅终止（SIGTERM）和强制终止（SIGKILL）
4. 确保取消操作正确传播到数据库状态
5. 保持线程安全，支持并发执行

**Non-Goals:**
1. 不实现暂停/恢复功能（仅支持完全取消）
2. 不实现部分取消（取消时停止所有运行中的节点）
3. 不修改数据库 schema（现有 `execution_nodes` 表已支持 `cancelled` 状态）
4. 不实现跨机器的进程管理（仅限本地进程）

## Decisions

### 1. 进程注册表设计

**Decision**: 创建全局单例 `ProcessRegistry` 类，使用 `threading.Lock` 保证线程安全。

**Rationale**:
- 单例模式确保全局唯一的进程注册表
- `threading.Lock` 提供线程安全的读写操作
- 字典存储 `task_id -> subprocess.Popen` 映射，O(1) 查找和删除

**Alternatives Considered**:
- **使用全局字典 + Lock**: 同当前方案，但封装成类更清晰
- **使用 `threading.local()`**: 每个线程独立存储，但取消操作可能在不同线程，不适用
- **使用 `multiprocessing.Manager`**: 支持多进程，但增加复杂度，当前使用 asyncio 在单进程中

### 2. 任务 ID 生成策略

**Decision**: 使用 `execution_id + node_id` 组合作为 `task_id`，格式为 `{execution_id}:{node_id}`。

**Rationale**:
- 保证唯一性（execution_id 是 UUID，node_id 是前端 ID）
- 可读性强，便于调试
- 天然支持一对多关系（一个执行有多个节点）

**Alternatives Considered**:
- **使用 UUID**: 完全唯一但可读性差
- **使用递增计数器**: 简单但需要全局状态管理
- **使用进程 PID**: 不唯一（PID 可能复用）

### 3. 进程终止策略

**Decision**: 两阶段终止：先发送 `terminate()` (SIGTERM)，等待 3 秒后如果进程仍在运行则发送 `kill()` (SIGKILL)。

**Rationale**:
- `terminate()` 允许进程优雅退出，清理资源（如临时文件）
- 3 秒超时平衡响应速度和优雅退出
- `kill()` 确保进程最终被终止

**Alternatives Considered**:
- **仅使用 `kill()`**: 立即终止但不优雅，可能导致资源泄漏
- **无限等待 `terminate()`**: 可能导致取消操作挂起
- **使用超时但不强制 kill**: 可能导致僵尸进程

### 4. ShellRunner 修改策略

**Decision**: 修改 `_run_with_capture()` 函数签名，添加 `task_id` 参数，在创建 `Popen` 后立即注册到进程注册表，进程退出时自动注销。

**Rationale**:
- 最小化代码改动，集中在一处
- 注册和注销在同一函数中，减少遗漏风险
- 使用 `finally` 块确保进程退出时一定会注销

**Alternatives Considered**:
- **在 LocalExecutor 中注册**: 需要暴露 `Popen` 对象，增加耦合
- **创建新的 AsyncShellRunner**: 需要大量重构
- **使用回调机制**: 增加复杂度，当前方案足够

### 5. ExecutionManager 改造

**Decision**: 在 `ExecutionManager` 中添加 `executors: Dict[str, Executor]` 字典，存储每个执行对应的 executor 实例，`stop()` 方法调用对应 executor 的 `cancel()`。

**Rationale**:
- 保持 executor 实例可访问，以便调用 `cancel()`
- 使用 execution_id 作为 key，便于查找
- 不改变现有 Execution 对象结构

**Alternatives Considered**:
- **在 WorkflowService 中直接 cancel**: 违反单一职责原则
- **使用全局 executor 变量**: 不支持并发执行
- **创建新的 CancelManager**: 增加不必要的抽象层

## Risks / Trade-offs

### Risk 1: 进程注册表内存泄漏
**Risk**: 进程退出时未正确注销，导致字典无限增长
**Mitigation**:
- 使用 `try-finally` 确保注销逻辑一定执行
- 添加定期清理机制（可选）
- 单元测试覆盖注册/注销流程

### Risk 2: 竞态条件
**Risk**: 并发取消和进程退出可能导致重复注销或访问已注销的进程
**Mitigation**:
- 使用 `threading.Lock` 保护所有注册表操作
- 注销前检查进程是否仍在运行 (`poll()`)
- 忽略 `KeyError`（已注销的情况）

### Risk 3: 取消操作不彻底
**Risk**: 子进程可能 spawn 子进程，终止父进程后子进程仍在运行
**Mitigation**:
- 文档说明此限制
- 考虑使用进程组（Windows: `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`, Unix: 使用 `os.killpg`）
- 在未来版本中改进

### Risk 4: 数据库状态不一致
**Risk**: 进程被终止但数据库状态未更新为 "cancelled"
**Mitigation**:
- 在 `cancel()` 方法中同时更新数据库状态
- 使用事务确保原子性
- 添加日志记录取消操作

### Trade-off 1: 响应速度 vs 优雅退出
**Trade-off**: 立即 kill 更快但不优雅，terminate + 等待更优雅但响应慢
**Decision**: 使用两阶段终止，平衡两者

### Trade-off 2: 代码改动 vs 架构重构
**Trade-off**: 最小改动风险低但可能不优雅，重构风险高但更清晰
**Decision**: 选择最小改动，在现有架构上增强

## Migration Plan

### Deployment Steps

1. **部署新代码**:
   - 添加 `ProcessRegistry` 类
   - 修改 `ShellRunner`, `LocalExecutor`, `ExecutionManager`
   - 无需数据库 migration

2. **验证测试**:
   - 运行单元测试
   - 运行集成测试（启动工作流后取消）
   - 手动测试（UI 点击停止按钮）

3. **监控观察**:
   - 监控进程注册表大小
   - 检查是否有未注销的进程
   - 观察取消操作的成功率

### Rollback Strategy

- 如果出现严重问题，可以回滚到旧代码
- 旧代码中 `cancel()` 返回 `False`，不影响现有功能
- 已取消的执行在数据库中状态为 "cancelled"，回滚后仍可查询

### Compatibility

- **向后兼容**: 旧代码中 `cancel()` 返回 `False`，新代码返回 `True`
- **API 兼容**: `POST /api/executions/{id}/stop` 接口不变，只是行为变化
- **数据库兼容**: 无 schema 变更，`execution_nodes` 表已支持 `cancelled` 状态

## Open Questions

1. **Q**: 是否需要支持取消单个节点？
   **A**: 当前不支持，只支持取消整个工作流。如果需要，可以在未来添加 `POST /api/executions/{id}/nodes/{node_id}/stop` 端点。

2. **Q**: 如何处理取消后的输出文件？
   **A**: 当前保留所有输出文件（包括部分完成的节点）。如果需要清理，可以在未来添加清理机制。

3. **Q**: 是否需要重试机制？
   **A**: 不需要。取消操作是幂等的，重复调用 `stop()` 是安全的。

4. **Q**: 如何处理已完成的执行？
   **A**: `stop()` 方法会检查执行状态，如果已完成则直接返回，不做任何操作。

## Implementation Notes

### ProcessRegistry API

```python
class ProcessRegistry:
    def register(self, task_id: str, process: subprocess.Popen) -> None
    def unregister(self, task_id: str) -> None
    def get(self, task_id: str) -> Optional[subprocess.Popen]
    def cancel(self, task_id: str, timeout: int = 3) -> bool
    def list_active(self) -> List[str]
    def clear(self) -> None
```

### TaskSpec Modification

```python
@dataclass
class TaskSpec:
    # ... existing fields ...
    task_id: str  # New field for process tracking
```

### ShellRunner Signature Change

```python
def _run_with_capture(
    cmd: str,
    workdir: Path,
    conda_env: Optional[str],
    log_callback: Callable[[str, str], None],
    task_id: str,  # New parameter
) -> None
```

### ExecutionManager Enhancement

```python
class ExecutionManager:
    def __init__(self):
        self.executions: Dict[str, Execution] = {}
        self.executors: Dict[str, Executor] = {}  # New field

    async def stop(self, execution_id: str) -> None:
        # Call executor.cancel() for each node in the execution
        pass
```
