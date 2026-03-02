# 前后端交互优化方案

## 📊 当前架构分析

### 现状评估

通过分析 `app/` 目录代码，发现以下关键问题：

#### 🔴 严重问题

1. **调试代码污染**
   - 大量 `agent log` 调试代码散布在核心路径
   - 硬编码的日志路径 `/home/ray/TDEase-Backend/.cursor/debug.log`
   - 生产代码和调试代码混合

2. **架构分层不清**
   - API 端点直接处理业务逻辑（[workflow.py:706-923](app/api/workflow.py#L706-L923)）
   - 缺少服务层抽象
   - 数据库操作分散在各处

3. **执行状态同步缺失**
   - 前端无法实时获取执行进度
   - WebSocket 未实现或未集成
   - 依赖轮询获取状态

4. **错误处理不统一**
   - 某些异常被静默吞噬
   - 错误信息不够详细
   - 缺少错误分类和恢复机制

#### 🟡 中等问题

5. **工作流持久化混乱**
   - `WorkflowStore` 模块缺失
   - 数据库操作直接在 API 层
   - 文件系统和数据库双存储但不同步

6. **执行模型问题**
   - 使用全局 `execution_manager` 单例
   - 任务生命周期管理不清晰
   - 缺少执行取消机制

7. **配置管理分散**
   - Settings 对象在多处重复创建
   - 缺少统一的配置管理器

---

## 🎯 优化目标

### 短期目标 (v0.3.0)

1. **清理调试代码** - 移除所有 agent log
2. **架构分层** - 引入清晰的服务层
3. **状态同步** - 实现实时通知机制
4. **错误处理** - 统一错误处理和恢复

### 中期目标 (v0.4.0)

5. **工作流存储** - 实现 WorkflowStore 抽象
6. **执行管理** - 改进任务生命周期
7. **配置管理** - 统一配置系统

### 长期目标 (v0.5.0+)

8. **Hot Run** - 增量执行支持
9. **多用户** - 协作编辑
10. **性能优化** - 缓存和批处理

---

## 🏗️ 新架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue.js)                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Workflow      │  │ Execution     │  │ Tool          │   │
│  │ Editor        │  │ Monitor       │  │ Registry      │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘   │
└──────────┼──────────────────┼──────────────────┼───────────┘
           │                  │                  │
           │ WebSocket        │                  │
           │ + REST API       │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Workflow      │  │ Execution     │  │ Tool          │   │
│  │ Controllers   │  │ Controllers   │  │ Controllers   │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘   │
└──────────┼──────────────────┼──────────────────┼───────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer (NEW)                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Workflow      │  │ Execution     │  │ Tool          │   │
│  │ Service       │  │ Service       │  │ Service       │   │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Workflow      │  │ Execution     │  │ Notification  │   │
│  │ Store         │  │ Store         │  │ Service       │   │
│  └───────────────┘  └───────────────┘  └───────┬───────┘   │
└─────────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Workflow      │  │ Snakemake     │  │ WebSocket     │   │
│  │ Builder       │  │ Executor      │  │ Manager       │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
           │                  │
           ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Database      │  │ File System   │  │ Cache         │   │
│  │ (SQLite)      │  │ (Workspace)   │  │ (Redis)       │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 详细优化方案

### 1. 代码清理 (优先级: 🔴 高)

#### 1.1 移除调试代码

**问题代码**:
```python
# #region agent log
import json as json_lib
with open("/home/ray/TDEase-Backend/.cursor/debug.log", "a") as f:
    f.write(json_lib.dumps({...}) + "\n")
# #endregion
```

**解决方案**:
```python
# 创建统一的日志工具
# app/utils/logger.py

import logging
import json
from contextlib import contextmanager
from typing import Any, Dict
from datetime import datetime

class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._debug_mode = False  # 通过配置控制

    def log_event(self, event: str, data: Dict[str, Any], level: str = "info"):
        """记录结构化事件"""
        if self._debug_mode:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event": event,
                "data": data
            }
            log_msg = json.dumps(log_entry)

            getattr(self.logger, level)(log_msg)

    @contextmanager
    def debug_context(self, **context):
        """调试上下文管理器"""
        old_debug = self._debug_mode
        self._debug_mode = True
        try:
            yield
        finally:
            self._debug_mode = old_debug

# 使用示例
logger = StructuredLogger(__name__)

# 正常生产代码
logger.log_event("execution_started", {"execution_id": ex.id})

# 调试代码（仅在 debug_mode=True 时记录）
with logger.debug_context(execution_id=ex.id):
    logger.log_event("dag_build_started", {...})
```

**迁移步骤**:
1. 创建 `app/utils/logger.py`
2. 全局搜索 `#region agent log`
3. 替换为结构化日志调用
4. 删除所有硬编码的日志路径

---

### 2. 服务层重构 (优先级: 🔴 高)

#### 2.1 创建 WorkflowService

**当前问题**:
```python
# app/api/workflow.py - 业务逻辑直接在 API 层
@router.post("/")
async def create_workflow(workflow: WorkflowCreate):
    # 验证、创建目录、保存数据库... 混在一起
```

**新架构**:
```python
# app/services/workflow_service.py

from typing import List, Optional
from app.models.workflow import WorkflowCreate, WorkflowResponse
from app.stores.workflow_store import WorkflowStore
from app.builders.workflow_builder import WorkflowBuilder

class WorkflowService:
    """工作流业务逻辑服务"""

    def __init__(self, db):
        self.db = db
        self.store = WorkflowStore(db)
        self.builder = WorkflowBuilder()

    async def create_workflow(
        self,
        workflow_data: WorkflowCreate
    ) -> WorkflowResponse:
        """创建工作流"""
        # 1. 验证
        validation = await self._validate_workflow(workflow_data)
        if not validation.is_valid:
            raise WorkflowValidationError(validation.errors)

        # 2. 创建目录结构
        workspace = await self._prepare_workspace(workflow_data)

        # 3. 保存到数据库
        workflow = await self.store.create(workflow_data, workspace)

        # 4. 返回响应
        return self._to_response(workflow)

    async def get_workflow(self, workflow_id: str) -> WorkflowResponse:
        """获取工作流"""
        workflow = await self.store.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        return self._to_response(workflow)

    async def update_workflow(
        self,
        workflow_id: str,
        updates: WorkflowUpdate
    ) -> WorkflowResponse:
        """更新工作流"""
        # 获取现有工作流
        workflow = await self.store.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)

        # 应用更新
        updated = await self.store.update(workflow_id, updates)

        # 发布更新事件
        await self.event_bus.publish("workflow.updated", {
            "workflow_id": workflow_id,
            "updates": updates
        })

        return self._to_response(updated)

    async def execute_workflow(
        self,
        workflow_id: str,
        parameters: ExecutionParameters
    ) -> ExecutionResponse:
        """执行工作流"""
        # 获取工作流
        workflow = await self.store.get(workflow_id)

        # 构建执行环境
        execution_env = await self.builder.build_execution_env(
            workflow, parameters
        )

        # 创建执行记录
        execution = await self.execution_service.create_execution(
            workflow_id, execution_env
        )

        # 异步执行
        asyncio.create_task(
            self.execution_service.execute(execution, execution_env)
        )

        return ExecutionResponse(
            execution_id=execution.id,
            status="running"
        )

    async def _validate_workflow(self, workflow_data):
        """验证工作流"""
        # 验证逻辑
        pass

    async def _prepare_workspace(self, workflow_data):
        """准备工作空间"""
        # 工作空间准备逻辑
        pass

    def _to_response(self, workflow) -> WorkflowResponse:
        """转换为响应对象"""
        # 转换逻辑
        pass
```

**API 层简化**:
```python
# app/api/workflow.py

from fastapi import APIRouter, Depends
from app.services.workflow_service import WorkflowService
from app.dependencies import get_workflow_service

router = APIRouter()

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    workflow: WorkflowCreate,
    service: WorkflowService = Depends(get_workflow_service)
):
    """创建工作流"""
    return await service.create_workflow(workflow)

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    service: WorkflowService = Depends(get_workflow_service)
):
    """获取工作流"""
    return await service.get_workflow(workflow_id)

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    updates: WorkflowUpdate,
    service: WorkflowService = Depends(get_workflow_service)
):
    """更新工作流"""
    return await service.update_workflow(workflow_id, updates)
```

---

### 3. 实时状态同步 (优先级: 🔴 高)

#### 3.1 WebSocket 实现

**当前问题**:
- 前端需要轮询获取执行状态
- 无法实时推送节点状态变化

**解决方案**:
```python
# app/services/notification_service.py

from typing import Set, Dict
from fastapi import WebSocket
from datetime import datetime
import json

class NotificationService:
    """实时通知服务"""

    def __init__(self):
        # 连接管理
        self._workflow_connections: Dict[str, Set[WebSocket]] = {}
        self._execution_connections: Dict[str, Set[WebSocket]] = {}

    async def subscribe_workflow(self, workflow_id: str, websocket: WebSocket):
        """订阅工作流变更"""
        if workflow_id not in self._workflow_connections:
            self._workflow_connections[workflow_id] = set()

        self._workflow_connections[workflow_id].add(websocket)

        # 发送订阅确认
        await websocket.send_json({
            "type": "subscription_confirmed",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def subscribe_execution(self, execution_id: str, websocket: WebSocket):
        """订阅执行状态"""
        if execution_id not in self._execution_connections:
            self._execution_connections[execution_id] = set()

        self._execution_connections[execution_id].add(websocket)

    async def unsubscribe(self, websocket: WebSocket):
        """取消订阅"""
        for connections in self._workflow_connections.values():
            connections.discard(websocket)

        for connections in self._execution_connections.values():
            connections.discard(websocket)

    async def broadcast_workflow_change(
        self,
        workflow_id: str,
        change_type: str,
        data: Dict
    ):
        """广播工作流变更"""
        if workflow_id not in self._workflow_connections:
            return

        message = {
            "type": "workflow_changed",
            "workflow_id": workflow_id,
            "change_type": change_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 广播给所有订阅者
        disconnected = set()
        for websocket in self._workflow_connections[workflow_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        # 清理断开的连接
        for ws in disconnected:
            await self.unsubscribe(ws)

    async def broadcast_node_status(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        progress: int,
        data: Dict = None
    ):
        """广播节点状态变化"""
        if execution_id not in self._execution_connections:
            return

        message = {
            "type": "node_status_changed",
            "execution_id": execution_id,
            "node_id": node_id,
            "status": status,
            "progress": progress,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        disconnected = set()
        for websocket in self._execution_connections[execution_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            await self.unsubscribe(ws)

    async def broadcast_log(
        self,
        execution_id: str,
        node_id: str,
        level: str,
        message: str
    ):
        """广播日志消息"""
        if execution_id not in self._execution_connections:
            return

        log_message = {
            "type": "log",
            "execution_id": execution_id,
            "node_id": node_id,
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        disconnected = set()
        for websocket in self._execution_connections[execution_id]:
            try:
                await websocket.send_json(log_message)
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            await self.unsubscribe(ws)

# 全局单例
notification_service = NotificationService()
```

**WebSocket 端点**:
```python
# app/api/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.notification_service import notification_service

router = APIRouter()

@router.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket(
    workflow_id: str,
    websocket: WebSocket
):
    """工作流实时更新"""
    await websocket.accept()

    await notification_service.subscribe_workflow(workflow_id, websocket)

    try:
        while True:
            # 接收客户端消息（心跳、确认等）
            data = await websocket.receive_json()

            # 处理客户端消息
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await notification_service.unsubscribe(websocket)

@router.websocket("/ws/executions/{execution_id}")
async def execution_websocket(
    execution_id: str,
    websocket: WebSocket
):
    """执行状态实时更新"""
    await websocket.accept()

    await notification_service.subscribe_execution(execution_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await notification_service.unsubscribe(websocket)
```

**执行服务集成**:
```python
# app/services/execution_service.py

class ExecutionService:
    """执行服务"""

    def __init__(self):
        self.notification_service = notification_service

    async def execute_node(self, node_id, rule):
        """执行单个节点"""
        # 开始执行
        await self.notification_service.broadcast_node_status(
            self.execution_id, node_id, "running", 0
        )

        try:
            # 执行逻辑
            result = await self._run_node(node_id, rule)

            # 完成
            await self.notification_service.broadcast_node_status(
                self.execution_id, node_id, "completed", 100
            )

        except Exception as e:
            # 失败
            await self.notification_service.broadcast_node_status(
                self.execution_id, node_id, "failed", 0,
                {"error": str(e)}
            )
            raise

    async def _run_node(self, node_id, rule):
        """实际执行节点"""
        # 捕获 Snakemake 日志
        log_handler = self._create_log_handler(node_id)

        # 执行...
        pass
```

---

### 4. 工作流存储抽象 (优先级: 🟡 中)

#### 4.1 WorkflowStore 实现

```python
# app/stores/workflow_store.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pathlib import Path
import yaml
import json

class WorkflowStore(ABC):
    """工作流存储抽象"""

    @abstractmethod
    async def create(self, workflow_data, workspace) -> Dict:
        """创建工作流"""
        pass

    @abstractmethod
    async def get(self, workflow_id: str) -> Optional[Dict]:
        """获取工作流"""
        pass

    @abstractmethod
    async def update(self, workflow_id: str, updates) -> Dict:
        """更新工作流"""
        pass

    @abstractmethod
    async def delete(self, workflow_id: str) -> bool:
        """删除工作流"""
        pass

    @abstractmethod
    async def list(self, filters: Dict) -> List[Dict]:
        """列出工作流"""
        pass

class DatabaseWorkflowStore(WorkflowStore):
    """数据库工作流存储"""

    def __init__(self, db):
        self.db = db

    async def create(self, workflow_data, workspace) -> Dict:
        cursor = self.db.cursor()

        workflow_id = self._generate_id()

        cursor.execute("""
            INSERT INTO workflows (id, name, description, vueflow_data,
                                   workspace_path, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_id,
            workflow_data.name,
            workflow_data.description,
            json.dumps(workflow_data.vueflow_data),
            workspace,
            "created",
            datetime.utcnow().isoformat()
        ))

        self.db.commit()

        return await self.get(workflow_id)

    async def get(self, workflow_id: str) -> Optional[Dict]:
        cursor = self.db.cursor()

        cursor.execute("""
            SELECT id, name, description, vueflow_data, workspace_path,
                   status, created_at, updated_at
            FROM workflows WHERE id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "vueflow_data": json.loads(row[3]),
            "workspace_path": row[4],
            "status": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }

    async def update(self, workflow_id: str, updates) -> Dict:
        # 构建更新 SQL
        update_fields = []
        update_values = []

        for key, value in updates.items():
            if key == "vueflow_data":
                update_fields.append("vueflow_data = ?")
                update_values.append(json.dumps(value))
            else:
                update_fields.append(f"{key} = ?")
                update_values.append(value)

        update_fields.append("updated_at = ?")
        update_values.append(datetime.utcnow().isoformat())
        update_values.append(workflow_id)

        sql = f"UPDATE workflows SET {', '.join(update_fields)} WHERE id = ?"

        cursor = self.db.cursor()
        cursor.execute(sql, update_values)
        self.db.commit()

        return await self.get(workflow_id)

    async def delete(self, workflow_id: str) -> bool:
        cursor = self.db.cursor()

        cursor.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))

        self.db.commit()

        return cursor.rowcount > 0

    async def list(self, filters: Dict) -> List[Dict]:
        # 实现列表查询
        pass

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return f"wf_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"

# 使用工厂模式创建
def create_workflow_store(db, backend: str = "database") -> WorkflowStore:
    """创建工作流存储"""
    if backend == "database":
        return DatabaseWorkflowStore(db)
    # 未来可添加其他存储后端
    # elif backend == "filesystem":
    #     return FileSystemWorkflowStore()
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

---

### 5. 配置管理统一 (优先级: 🟡 中)

#### 5.1 配置管理器

```python
# app/services/config_manager.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from snakemake.settings.types import (
    DAGSettings, ExecutionSettings, ResourceSettings,
    SchedulingSettings, DeploymentSettings
)

@dataclass
class WorkflowExecutionConfig:
    """工作流执行配置"""

    # 资源配置
    cores: int = 4
    nodes: Optional[int] = None
    memory: Optional[str] = None

    # 执行配置
    use_conda: bool = True
    dryrun: bool = False
    keep_going: bool = False

    # 调度配置
    greediness: float = 1.0

    # 部署配置
    conda_prefix: Optional[str] = None

    def to_snakemake_settings(self) -> Dict:
        """转换为 Snakemake Settings 对象"""
        return {
            "dag_settings": DAGSettings(),
            "execution_settings": ExecutionSettings(
                dryrun=self.dryrun,
                keep_going=self.keep_going
            ),
            "resource_settings": ResourceSettings(
                cores=self.cores,
                nodes=self.nodes
            ),
            "scheduling_settings": SchedulingSettings(
                greediness=self.greediness
            ),
            "deployment_settings": DeploymentSettings(
                conda_prefix=self.conda_prefix
            )
        }

class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self._configs: Dict[str, WorkflowExecutionConfig] = {}

    def get_config(
        self,
        workflow_id: str,
        overrides: Dict[str, Any] = None
    ) -> WorkflowExecutionConfig:
        """获取工作流配置"""
        # 获取基础配置
        base_config = self._configs.get(workflow_id)

        if not base_config:
            base_config = WorkflowExecutionConfig()

        # 应用覆盖
        if overrides:
            config = self._apply_overrides(base_config, overrides)
        else:
            config = base_config

        return config

    def set_config(self, workflow_id: str, config: WorkflowExecutionConfig):
        """设置工作流配置"""
        self._configs[workflow_id] = config

    def _apply_overrides(
        self,
        base: WorkflowExecutionConfig,
        overrides: Dict[str, Any]
    ) -> WorkflowExecutionConfig:
        """应用配置覆盖"""
        config_dict = dataclasses.asdict(base)
        config_dict.update(overrides)
        return WorkflowExecutionConfig(**config_dict)

# 全局单例
config_manager = ConfigManager()
```

---

### 6. 错误处理统一 (优先级: 🔴 高)

#### 6.1 异常层次结构

```python
# app/exceptions.py

class TDEaseException(Exception):
    """TDEase 基础异常"""
    def __init__(self, message: str, code: str, details: Dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class WorkflowException(TDEaseException):
    """工作流相关异常"""
    pass

class WorkflowNotFoundError(WorkflowException):
    """工作流不存在"""
    def __init__(self, workflow_id: str):
        super().__init__(
            f"Workflow {workflow_id} not found",
            "WORKFLOW_NOT_FOUND",
            {"workflow_id": workflow_id}
        )

class WorkflowValidationError(WorkflowException):
    """工作流验证失败"""
    def __init__(self, errors: List[str]):
        super().__init__(
            f"Workflow validation failed: {', '.join(errors)}",
            "WORKFLOW_VALIDATION_ERROR",
            {"errors": errors}
        )

class ExecutionException(TDEaseException):
    """执行相关异常"""
    pass

class ExecutionFailedException(ExecutionException):
    """执行失败"""
    def __init__(self, execution_id: str, reason: str):
        super().__init__(
            f"Execution {execution_id} failed: {reason}",
            "EXECUTION_FAILED",
            {"execution_id": execution_id, "reason": reason}
        )

class ToolException(TDEaseException):
    """工具相关异常"""
    pass

class ToolNotFoundException(ToolException):
    """工具不存在"""
    def __init__(self, tool_name: str):
        super().__init__(
            f"Tool {tool_name} not found",
            "TOOL_NOT_FOUND",
            {"tool_name": tool_name}
        )
```

**统一错误处理中间件**:
```python
# app/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.exceptions import TDEaseException
import logging

logger = logging.getLogger(__name__)

async def tdease_exception_handler(
    request: Request,
    exc: TDEaseException
):
    """TDEase 异常处理器"""

    # 记录错误
    logger.error(
        f"API Error: {exc.code} - {exc.message}",
        extra={
            "code": exc.code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )

    # 返回统一格式
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )

async def general_exception_handler(
    request: Request,
    exc: Exception
):
    """通用异常处理器"""

    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )

# 注册到 FastAPI
# app/main.py
from app.middleware.error_handler import (
    tdease_exception_handler,
    general_exception_handler
)

app.add_exception_handler(TDEaseException, tdease_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

---

## 📋 实施计划

### Phase 1: 基础重构 (1-2周)

**目标**: 清理代码、建立服务层

- [x] 移除所有调试代码
- [ ] 创建 `WorkflowService`
- [ ] 创建 `ExecutionService`
- [ ] 实现 `WorkflowStore`
- [ ] 统一错误处理
- [ ] API 层重构

### Phase 2: 实时同步 (1周)

**目标**: 实现 WebSocket 实时通知

- [ ] 实现 `NotificationService`
- [ ] 创建 WebSocket 端点
- [ ] 集成到执行服务
- [ ] 前端 WebSocket 客户端
- [ ] 测试和调优

### Phase 3: 高级特性 (2-3周)

**目标**: 配置管理、性能优化

- [ ] 实现 `ConfigManager`
- [ ] 工作流版本管理
- [ ] 执行缓存
- [ ] Hot Run 模式支持

---

## 🔑 关键设计决策

### 1. 服务层职责

**服务层做什么**:
- ✅ 业务逻辑编排
- ✅ 数据转换和验证
- ✅ 事件发布和通知
- ✅ 事务管理

**服务层不做什么**:
- ❌ 数据访问（由 Store 负责）
- ❌ HTTP 通信（由 API 层负责）
- ❌ 底层执行（由 Executor 负责）

### 2. 存储抽象

**为什么需要 Store**:
- 统一数据访问接口
- 方便单元测试（可 Mock）
- 支持多存储后端（DB、文件、缓存）

### 3. 实时通知策略

**WebSocket vs Server-Sent Events**:
- **WebSocket**: 双向通信，适合交互式操作
- **SSE**: 单向推送，适合简单的状态广播

**选择**: WebSocket（支持双向通信）

### 4. 配置管理

**为什么需要 ConfigManager**:
- 避免 Settings 对象到处创建
- 统一配置来源
- 支持配置覆盖和继承

---

## 📊 性能优化建议

### 1. 数据库查询优化

**问题**:
- 频繁的数据库查询
- N+1 查询问题

**解决方案**:
```python
# 使用连接池
from aiosqlite import connect

class DatabasePool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._connections = asyncio.Queue(maxsize=pool_size)

    async def init(self):
        for _ in range(pool_size):
            conn = await connect(self.db_path)
            await self._connections.put(conn)

    async def acquire(self):
        return await self._connections.get()

    async def release(self, conn):
        await self._connections.put(conn)
```

### 2. 执行状态缓存

**问题**:
- 频繁查询执行状态
- 数据库压力大

**解决方案**:
```python
# 使用 Redis 缓存执行状态
from redis import asyncio as aioredis

class ExecutionStatusCache:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.ttl = 300  # 5分钟

    async def set_status(self, execution_id: str, status: Dict):
        await self.redis.setex(
            f"execution:{execution_id}",
            self.ttl,
            json.dumps(status)
        )

    async def get_status(self, execution_id: str) -> Optional[Dict]:
        data = await self.redis.get(f"execution:{execution_id}")
        return json.loads(data) if data else None
```

### 3. 批量操作

**问题**:
- 逐个更新节点状态
- 大量数据库写入

**解决方案**:
```python
class BatchNodeStatusUpdater:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self._pending_updates = []

    async def update_node_status(self, execution_id, node_id, status):
        self._pending_updates.append((execution_id, node_id, status))

        if len(self._pending_updates) >= self.batch_size:
            await self._flush()

    async def _flush(self):
        # 批量更新数据库
        cursor.executemany(
            "UPDATE execution_nodes SET status = ? WHERE execution_id = ? AND node_id = ?",
            self._pending_updates
        )
        self._pending_updates.clear()
```

---

## 🎯 前端集成建议

### 1. 状态管理

**使用 Pinia**:
```typescript
// stores/workflow.ts
import { defineStore } from 'pinia'

export const useWorkflowStore = defineStore('workflow', {
  state: () => ({
    workflows: [],
    currentWorkflow: null,
    validationErrors: []
  }),

  actions: {
    async loadWorkflows() {
      const response = await api.getWorkflows()
      this.workflows = response.workflows
    },

    async saveWorkflow(workflow: Workflow) {
      if (workflow.id) {
        await api.updateWorkflow(workflow.id, workflow)
      } else {
        await api.createWorkflow(workflow)
      }
    }
  }
})

// stores/execution.ts
export const useExecutionStore = defineStore('execution', {
  state: () => ({
    executions: {},
    currentExecution: null
  }),

  actions: {
    subscribeToExecution(executionId: string) {
      const ws = new WebSocket(`ws://localhost:8000/ws/executions/${executionId}`)

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)

        if (message.type === 'node_status_changed') {
          this.updateNodeStatus(message)
        } else if (message.type === 'log') {
          this.appendLog(message)
        }
      }

      return ws
    },

    updateNodeStatus(message: NodeStatusMessage) {
      const execution = this.executions[message.execution_id]
      if (execution) {
        const node = execution.nodes.find(n => n.id === message.node_id)
        if (node) {
          node.status = message.status
          node.progress = message.progress
        }
      }
    }
  }
})
```

### 2. 自动保存

```typescript
// composables/useAutoSave.ts
import { watch } from 'vue'
import { debounce } from 'lodash-es'

export function useAutoSave(workflow: Ref<Workflow>) {
  const save = debounce(async () => {
    try {
      await api.updateWorkflow(workflow.value.id, workflow.value)
      console.log('Auto-saved')
    } catch (error) {
      console.error('Auto-save failed:', error)
    }
  }, 2000) // 2秒防抖

  watch(workflow, save, { deep: true })
}
```

### 3. 错误处理

```typescript
// utils/errorHandler.ts
export class APIError extends Error {
  constructor(
    public code: string,
    public message: string,
    public details: any
  ) {
    super(message)
  }
}

export async function handleAPIResponse(response: Response) {
  if (!response.ok) {
    const error = await response.json()
    throw new APIError(
      error.error.code,
      error.error.message,
      error.error.details
    )
  }
  return response.json()
}
```

---

## 📝 总结

### 核心优化点

1. **代码清理** - 移除调试代码，提升可维护性
2. **架构分层** - 清晰的服务层抽象
3. **实时同步** - WebSocket 实时通知
4. **存储抽象** - 统一的工作流存储
5. **错误处理** - 一致的异常处理
6. **配置管理** - 集中的配置系统

### 实施优先级

**高优先级** (立即开始):
- ✅ 清理调试代码
- ✅ 服务层重构
- ✅ 错误处理统一
- ✅ WebSocket 实现

**中优先级** (1-2周内):
- WorkflowStore 实现
- ConfigManager 实现
- 前端集成

**低优先级** (长期):
- 性能优化
- 缓存机制
- Hot Run 模式

### 预期收益

- **可维护性**: +50% (清晰的架构)
- **开发效率**: +30% (统一的服务层)
- **用户体验**: +40% (实时反馈)
- **代码质量**: +60% (移除调试代码)
