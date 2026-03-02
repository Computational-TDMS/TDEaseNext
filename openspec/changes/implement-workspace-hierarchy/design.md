## Context

### Current State

TDEase 当前使用扁平化的工作空间结构：
- `data/workflows/{workflow_id}/` - 所有工作流共享同一目录
- 样品信息分散在多处：`ExecutionRequest.samples`、`params.sample_context`、`data_loader.input_sources`
- 占位符解析使用危险的 `re.sub(r"\{\w+\}", "out")` 后备机制
- 缺少用户隔离：所有用户共享相同的数据和工作空间

### Constraints

- **向后兼容性**：需要支持现有工作流的迁移
- **测试环境**：已创建测试用户和工作区结构（`data/users/test_user/`）
- **服务一致性**：避免 `workspace_manager.py` 和 `user_workspace_manager.py` 的功能重叠
- **性能要求**：支持多样本并行执行

### Stakeholders

- **开发者**：需要清晰的 API 和服务接口
- **测试人员**：需要可复现的测试环境
- **最终用户**：需要简单的工作区和样品管理界面

## Goals / Non-Goals

**Goals:**
- 实现用户-工作区-样品的层次化管理结构
- 移除危险的占位符后备机制，实现严格的占位符验证
- 统一服务层，消除 `workspace_manager` 和 `user_workspace_manager` 的矛盾
- 支持多样本并行执行和执行隔离
- 完成测试环境的迁移

**Non-Goals:**
- 用户认证和授权（留待后续）
- 工作流的版本控制
- 分布式执行或跨节点调度
- Web UI 实现（仅 API 层）

## Decisions

### 1. 服务层统一：合并 WorkspaceManager

**Decision**: 将 `workspace_manager.py` 和 `user_workspace_manager.py` 合并为单一服务

**Rationale:**
- 当前两个服务功能重叠，容易造成混淆
- `workspace_manager.py` 提供工作目录管理（inputs/outputs/logs 分隔）
- `user_workspace_manager.py` 提供层次化路径管理（users/workspaces/executions）
- 合并后可以统一接口，减少代码重复

**Alternatives Considered:**
- A. 保持两个服务独立：❌ 导致 API 分裂，调用者需要选择使用哪个服务
- B. 完全删除 `workspace_manager.py`：❌ 丢失了有用的目录结构管理功能
- C. **合并为统一服务**：✅ 保留两个服务的优点，提供统一的 API

**Implementation:**
```python
class UnifiedWorkspaceManager:
    """统一的 Workspace 管理：
    - 用户/工作区路径管理（来自 user_workspace_manager）
    - 工作目录结构管理（来自 workspace_manager）
    """
    def get_workspace_path(user_id, workspace_id) -> Path
    def create_execution_dir(user_id, workspace_id, exec_id) -> Path
    def ensure_directory_structure(workspace_path) -> None
    # ... 其他方法
```

### 2. 占位符验证策略

**Decision**: 在执行前进行严格的占位符验证，失败时抛出明确的异常

**Rationale:**
- 当前的静默后备机制隐藏了错误，导致输出文件名错误
- 早期验证可以快速失败，避免浪费计算资源
- 明确的错误信息有助于调试

**Alternatives Considered:**
- A. 使用默认值填充缺失占位符：❌ 仍会生成错误的文件名
- B. 警告但继续执行：❌ 会导致不可预期的结果
- C. **严格验证 + 明确错误**：✅ 快速失败，错误信息清晰

**Implementation:**
```python
def validate_placeholders(pattern: str, context: Dict[str, str]) -> None:
    """验证占位符是否都在 context 中"""
    required = set(re.findall(r"\{(\w+)\}", pattern))
    missing = required - set(context.keys())
    if missing:
        raise ValueError(
            f"Missing placeholders in pattern '{pattern}': {missing}. "
            f"Available: {list(context.keys())}"
        )
```

### 3. 样品上下文来源

**Decision**: 样品上下文从工作区的 `samples.json` 加载，作为唯一数据源

**Rationale:**
- 提供单一数据源，避免混乱
- 样品定义在工作区级别，可在多个工作流间复用
- 支持样品的版本管理和追踪

**Alternatives Considered:**
- A. 从执行请求传递样品上下文：❌ 每次执行都需要手动指定
- B. 从 data_loader 节点推导：❌ 不支持多样本和样品复用
- C. **从 samples.json 加载**：✅ 集中管理，易于维护

**Context Building Strategy:**
```python
def build_sample_context(sample_def: Dict, input_files: List[Path]) -> Dict[str, str]:
    """构建完整的样品上下文"""
    # 1. 自动推导值
    derived = {
        "sample": sample_def["id"],
        "input_basename": input_files[0].stem if input_files else sample_def["id"],
        "input_dir": str(input_files[0].parent) if input_files else ".",
        "input_ext": input_files[0].suffix[1:] if input_files else "",
    }

    # 2. 显式定义值（覆盖推导值）
    explicit = sample_def.get("context", {})

    # 3. 合并（显式优先）
    return {**derived, **explicit}
```

### 4. 执行隔离策略

**Decision**: 每次执行创建独立的执行目录，包含 inputs/outputs/logs 子目录

**Rationale:**
- 支持多次执行同一工作流而不互相干扰
- 便于追踪和调试特定执行
- 支持执行结果的归档和清理

**Directory Structure:**
```
exec_20250302_001/
├── execution.json      # 执行元数据
├── inputs/             # 本次执行的输入文件（符号链接或复制）
├── outputs/            # 本次执行的输出文件
├── logs/               # 执行日志
└── .snakemake/         # Snakemake 临时文件
```

### 5. API 设计

**Decision**: 使用 RESTful API 设计，支持用户、工作区、样品的层级资源访问

**Rationale:**
- 符合 REST 原则，易于理解和使用
- 支持标准的 HTTP 方法（GET/POST/PUT/DELETE）
- 便于前端集成和测试

**API Structure:**
```
GET    /api/users/{user_id}/workspaces
POST   /api/users/{user_id}/workspaces
GET    /api/users/{user_id}/workspaces/{workspace_id}
DELETE /api/users/{user_id}/workspaces/{workspace_id}

GET    /api/users/{user_id}/workspaces/{workspace_id}/samples
POST   /api/users/{user_id}/workspaces/{workspace_id}/samples
GET    /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}
PUT    /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}
DELETE /api/users/{user_id}/workspaces/{workspace_id}/samples/{sample_id}

POST   /api/workflows/execute  # 更新以支持 user_id + workspace_id + sample_ids
```

## Risks / Trade-offs

### Risk 1: 现有工作流迁移复杂

**Risk**: 用户可能已有很多工作流使用旧的路径结构

**Mitigation**:
- 提供迁移脚本自动转换路径
- 支持向后兼容的 API（保留旧的 `workspace_path` 参数）
- 在文档中提供清晰的迁移指南

### Risk 2: 性能影响

**Risk**: 每次执行都需要加载 `samples.json`，可能影响性能

**Mitigation**:
- 实现样品上下文缓存
- 延迟加载：仅在执行时加载上下文
- 监控性能并在必要时优化

### Risk 3: 测试覆盖不足

**Risk**: 重构可能引入新的 bug

**Mitigation**:
- 在重构前完善现有测试
- 添加新的测试用例覆盖新功能
- 使用集成测试验证端到端流程

### Risk 4: 服务合并导致的 API 变更

**Risk**: 合并 `workspace_manager` 和 `user_workspace_manager` 可能破坏现有代码

**Mitigation**:
- 仔细审查两个服务的所有调用点
- 提供适配器函数保持向后兼容
- 分阶段迁移，先合并后删除旧代码

## Migration Plan

### Phase 1: 准备阶段（不影响现有功能）

1. 创建测试用户和工作区结构 ✅（已完成）
2. 实现 `UnifiedWorkspaceManager`，与现有服务并存
3. 添加新的 API 端点，不影响现有端点
4. 编写测试用例

### Phase 2: 重构阶段（功能切换）

1. 更新 `WorkflowService` 使用 `UnifiedWorkspaceManager`
2. 更新 API 端点使用新的路径结构
3. 添加占位符验证逻辑
4. 更新测试用例

### Phase 3: 清理阶段（移除旧代码）

1. 删除旧的 `workspace_manager.py`
2. 删除旧的 `user_workspace_manager.py`（如果合并）
3. 移除向后兼容的代码
4. 更新文档

### Rollback Strategy

- 每个阶段完成后进行测试验证
- 保留旧代码直到新代码完全稳定
- 使用 Git 分支支持快速回滚

## Open Questions

1. **用户认证**: 当前设计不包含用户认证，如何保护 API？
   - **Decision**: 留待后续实现，当前假设所有请求来自已认证用户

2. **数据库支持**: 当前使用 JSON 文件存储样品定义，是否需要数据库？
   - **Decision**: 先使用 JSON 文件，如果性能成为瓶颈再考虑数据库

3. **并发控制**: 多个用户同时修改同一工作区如何处理？
   - **Decision**: 使用文件锁或最后写入胜（LWW）策略，留待后续优化

4. **大数据文件**: 大文件（如 .raw 文件）如何处理？
   - **Decision**: 保持文件在工作区 `data/` 目录，使用符号链接避免复制
