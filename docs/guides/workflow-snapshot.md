# 工作流结构快照机制

## 概述

TDEase 实现了 **workflow_snapshot** 机制，用于区分「结构变更」和「参数变更」，仅在结构变更时保存快照。

## 核心概念

### 结构变更 vs 参数变更

| 变更类型 | 示例 | 是否保存快照 |
|---------|------|------------|
| **结构变更** | 增删节点、修改连接关系、改变节点类型 | ✅ 保存 |
| **参数变更** | 仅修改节点参数值（如阈值、文件路径等） | ❌ 不保存 |

### 结构定义

**结构**包括：
- `nodes`：节点列表（id、type、position）
- `edges`：连接关系（source、target、sourceHandle、targetHandle）
- `format_version`：格式版本

**结构不包括**：
- `params`：节点参数值（这些是运行时数据，不是结构）

## 实现细节

### 1. 结构提取

`app/services/workflow_diff.py` 中的 `extract_structure()` 函数：

```python
def extract_structure(workflow_json):
    """提取结构部分，忽略参数"""
    nodes = [
        {"id": n["id"], "type": n["type"], "position": n["position"]}
        for n in workflow_json.get("nodes", [])
    ]
    edges = [
        {"source": e["source"], "target": e["target"], ...}
        for e in workflow_json.get("edges", [])
    ]
    return {"nodes": nodes, "edges": edges, "format_version": ...}
```

### 2. 变更检测

```python
def has_structure_changed(old_workflow, new_workflow) -> bool:
    """比较结构是否变化"""
    old_struct = extract_structure(old_workflow)
    new_struct = extract_structure(new_workflow)
    return old_struct != new_struct
```

### 3. 执行时快照保存

执行流程（`app/api/workflow.py`）：

```python
# 1. 获取上次执行的快照
last_exec_id, last_snapshot = get_last_execution_snapshot(db, workflow_id)

# 2. 检测结构变更
if last_snapshot:
    if has_structure_changed(last_snapshot, current_workflow):
        workflow_snapshot = json.dumps(current_workflow)  # 保存
else:
    workflow_snapshot = json.dumps(current_workflow)  # 首次执行，保存

# 3. 创建 execution 记录
execution_store.create(execution_id, workflow_id, workspace_path, workflow_snapshot)
```

## 使用场景

### 场景 1：参数调整（不保存快照）

```
运行 1: 节点 A 参数 threshold=0.5
  → execution_1, workflow_snapshot = {...}  (首次，保存)

用户修改: 节点 A 参数 threshold=0.8  (仅参数变更)

运行 2: 节点 A 参数 threshold=0.8
  → execution_2, workflow_snapshot = NULL  (结构未变，不保存)
```

### 场景 2：结构变更（保存快照）

```
运行 1: 节点 A → B → C
  → execution_1, workflow_snapshot = {nodes: [A,B,C], edges: [...]}

用户修改: 添加节点 D，连接 B → D → C  (结构变更)

运行 2: 节点 A → B → D → C
  → execution_2, workflow_snapshot = {nodes: [A,B,C,D], edges: [...]}  (保存)
```

## 数据库设计

### executions 表

```sql
CREATE TABLE executions (
    ...
    workflow_snapshot TEXT,  -- JSON 字符串，仅在结构变更时保存
    ...
);
```

### 查询示例

```sql
-- 获取某次执行的结构快照
SELECT workflow_snapshot FROM executions WHERE id = 'exec_xxx';

-- 获取工作流最后一次结构变更的快照
SELECT workflow_snapshot FROM executions
WHERE workflow_id = 'wf_xxx' AND workflow_snapshot IS NOT NULL
ORDER BY start_time DESC LIMIT 1;
```

## 优势

1. **历史追溯**：可查看每次执行使用的确切结构
2. **断点续传**：基于快照恢复执行状态
3. **性能优化**：参数调整不产生冗余快照
4. **调试友好**：区分结构问题 vs 参数问题

## 注意事项

- **首次执行**：总是保存快照（无历史可比较）
- **批量执行**：第一个样本检测结构变更，后续样本复用相同快照
- **直接执行**（不通过 workflow_id）：总是保存快照

## 相关代码

- `app/services/workflow_diff.py`：结构变更检测
- `app/services/execution_store.py`：快照存储
- `app/api/workflow.py`：执行时快照逻辑
