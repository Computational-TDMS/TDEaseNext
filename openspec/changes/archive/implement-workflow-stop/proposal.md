# Workflow Cancellation Proposal

## Why

TDEase 后端虽然已经实现了工作流执行功能，但目前**无法真正停止运行中的工作流**。

当前的 `stop_execution` API 端点（`app/api/execution.py:146-152`）只更新内存中的执行状态为 "cancelled"，但底层的子进程仍在继续运行。这意味着：

1. **资源浪费**: 已经启动的命令行工具（如 TopPIC, MSFragger 等）会继续占用 CPU 和内存
2. **用户体验差**: 用户点击"停止"按钮后，任务仍然在后台运行，产生误导
3. **数据污染**: 工作流被取消后，部分节点可能仍在执行并产生输出文件，导致工作空间状态不一致
4. **无法中断**: 对于长时间运行的流程（如大型质谱数据分析），用户无法在中途取消

虽然 `Executor` 接口定义了 `cancel()` 方法，但 `LocalExecutor` 的实现只返回 `False`，并没有真正的取消逻辑。此外，`ShellRunner` 使用 `subprocess.Popen` 执行命令后没有保存进程引用，导致无法后续调用 `terminate()` 或 `kill()`。

## What Changes

### 核心变更

1. **进程注册表 (Process Registry)**
   - 新增 `ProcessRegistry` 类用于管理运行中的子进程
   - 维护 `task_id -> subprocess.Popen` 映射
   - 支持进程注册、注销和查询操作
   - 线程安全设计，支持并发访问

2. **实现 Executor.cancel() 方法**
   - `LocalExecutor.cancel()`: 通过进程注册表获取并终止子进程
   - `MockExecutor.cancel()`: 更新为返回 `True`（模拟取消成功）
   - 支持优雅终止（SIGTERM）和强制终止（SIGKILL）

3. **增强 ShellRunner**
   - 修改 `_run_with_capture()` 函数，在创建 `subprocess.Popen` 后立即注册到进程注册表
   - 进程退出时自动从注册表注销
   - 添加任务 ID 参数用于进程标识

4. **更新 ExecutionManager.stop()**
   - 调用底层 executor 的 `cancel()` 方法
   - 更新数据库状态为 "cancelled"
   - 记录取消操作的日志

5. **改进任务状态管理**
   - 在 `TaskSpec` 中添加 `task_id` 字段用于进程追踪
   - 更新 `ExecutionStore.update_node_status()` 支持 "cancelled" 状态
   - 确保取消操作正确传播到节点状态

### 数据库变更
- 无需 schema 变更（`execution_nodes` 表已支持 `status='cancelled'`）

### API 变更
- `POST /api/executions/{execution_id}/stop` 现在会真正终止底层进程

## Capabilities

### New Capabilities
- `workflow-cancellation`: 工作流取消能力，支持在运行中终止工作流执行并清理相关资源
- `process-registry`: 进程注册表，用于管理和追踪运行中的子进程
- `task-lifecycle`: 任务生命周期管理，支持任务的创建、执行、取消和清理

### Modified Capabilities
- 无（现有规范没有定义取消行为的 REQUIREMENTS）

## Impact

### 受影响的代码文件

**核心执行器**:
- `app/core/executor/base.py`: 添加 `task_id` 到 `TaskSpec`
- `app/core/executor/local.py`: 实现 `cancel()` 方法
- `app/core/executor/shell_runner.py`: 修改 `_run_with_capture()` 注册进程
- `app/core/executor/mock.py`: 更新 `cancel()` 返回值

**服务层**:
- `app/services/runner.py`: 更新 `ExecutionManager.stop()` 调用 executor cancel
- `app/services/workflow_service.py`: 在创建 `TaskSpec` 时生成 `task_id`
- `app/services/execution_store.py`: 确保 "cancelled" 状态正确处理（已支持）

**新增文件**:
- `app/core/executor/process_registry.py`: 进程注册表实现

### API 变更
- `POST /api/executions/{execution_id}/stop`: 行为变化（从仅更新状态到真正终止进程）

### 依赖关系
- 无需新增外部依赖（使用标准库 `threading.Lock` 和 `subprocess`）

### 系统影响
- **正面**: 用户可以真正停止工作流，节省资源，改善用户体验
- **风险**: 需要确保进程注册表不会内存泄漏（进程退出时必须注销）
- **兼容性**: 向后兼容，不影响现有功能

### 测试需求
- 单元测试: 进程注册表的注册/注销操作
- 单元测试: `LocalExecutor.cancel()` 方法
- 集成测试: 启动工作流后调用 stop API，验证进程被终止
- 边界测试: 取消已完成的任务、取消不存在的任务
