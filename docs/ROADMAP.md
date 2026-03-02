# TDEase 开发路线图

## 📋 目录

- [项目状态](#项目状态)
- [已完成功能](#已完成功能)
- [进行中的工作](#进行中的工作)
- [短期计划](#短期计划)
- [中期计划](#中期计划)
- [长期愿景](#长期愿景)

---

## 项目状态

**当前版本**: v0.2.0-beta
**最后更新**: 2025-02-02
**架构状态**: 已完成从编译器模式到直接 API 模式的重构

### 核心里程碑

- ✅ **Phase 1**: 环境搭建和基础架构
- ✅ **Phase 2**: FastAPI 后端和数据库集成


- 🔄 **Phase 3**: 前端集成和用户界面
- 📋 **Phase 4**: 高级功能和优化

---

## 已完成功能

### ✅ 核心架构 (Phase 1-2)

- [x] FastAPI 后端框架搭建
- [x] SQLite 数据库设计和实现
- [x] Snakemake API 直接执行模式
- [x] 工作流规范化 (WorkflowNormalizer)
- [x] 节点到 Snakemake Rule 转换 (RuleBuilder)
- [x] 程序化工作流构建 (WorkflowBuilder)
- [x] 节点级别执行跟踪 (ExecutionStore)
- [x] 日志捕获和存储 (LogHandler)

### ✅ 工具管理

- [x] 工具注册系统
- [x] 工具发现机制
- [x] Docker 工具支持 (MSConvert, TopPIC)
- [x] 跨平台工具路径管理
- [x] 工具参数映射

### ✅ 文件管理

- [x] 文件上传/下载 API
- [x] 工作空间管理
- [x] 跨平台权限处理
- [x] 文件路径路由

### ✅ 测试工具链

- [x] data_loader - 数据文件加载
- [x] fasta_loader - FASTA 文件加载
- [x] msconvert_docker - 质谱格式转换
- [x] topfd - TopPIC 前端工具
- [x] toppic - TopPIC 主工具

---

## 进行中的工作

### 🔄 JSON 编译兼容性改进

**状态**: 进行中

**问题**:
- 文件格式限制过于严格
- Loader 中存在不必要的格式验证

**解决方案**:
- [ ] 移除不必要的文件格式验证
- [ ] 改进工具注册的灵活性
- [ ] 增强错误提示

---

## 短期计划 (v0.3.0)

### 🎯 核心 Bug 修复

#### 1. 创建缺失的 WorkflowStore 模块

**优先级**: 高

**问题**: 代码引用 `app.services.workflow_store` 但模块不存在

**解决方案**:
```python
# app/services/workflow_store.py
class WorkflowStore:
    """统一工作流持久化操作"""

    def create_workflow(self, workflow_data: dict) -> str
    def get_workflow(self, workflow_id: str) -> dict
    def update_workflow(self, workflow_id: str, workflow_data: dict)
    def delete_workflow(self, workflow_id: str)
    def list_workflows(self, filters: dict) -> list
```

**预期收益**: 统一工作流存储机制，修复 API 不一致问题

#### 2. 修复前端保存重复创建问题

**优先级**: 高

**问题**: Frontend `saveWorkflow()` 总是调用 `createWorkflow` API

**解决方案**:
```typescript
// 前端修复
async saveWorkflow(workflow: WorkflowJSON, silent: boolean = false) {
    const workflowId = workflow.metadata.id

    // 检查工作流是否存在
    const exists = await workflowApi.getWorkflow(workflowId).catch(() => false)

    if (exists) {
        // 更新现有工作流
        return await workflowApi.updateWorkflow(workflowId, payload)
    } else {
        // 创建新工作流
        return await workflowApi.createWorkflow(payload)
    }
}
```

**预期收益**: 测试工作流不会每次保存都创建新版本

#### 3. data_loader 执行问题修复

**优先级**: 中

**问题**: 规则构建或执行环境问题导致执行失败

**解决方案**:
- 添加详细日志记录
- 验证工作目录设置
- 修复 shell 命令构建逻辑

**预期收益**: 测试工作流可以完整执行

### 🔧 架构改进

#### 4. 统一 API 响应格式

**优先级**: 中

**目标**:
- 统一成功响应格式
- 统一错误响应格式
- 添加请求 ID 追踪

#### 5. 增强错误处理

**优先级**: 中

**目标**:
- 详细的错误信息
- 错误分类和编码
- 错误恢复建议

---

## 中期计划 (v0.4.0 - v0.5.0)

### 🎨 前端集成

#### 1. VueFlow 工作流编辑器

**功能**:
- [-] 节点拖拽和连接
- [-] 参数配置面板
- [ ] 实时验证
- [-] 工具搜索和添加

如何实现



#### 2. 状态管理

**方案**: 使用 Pinia 进行状态管理

**模块**:
- workflows - 工作流状态
- executions - 执行状态
- tools - 工具列表
- files - 文件管理

#### 3. 执行监控界面

**功能**:
- 实时进度显示
- 节点状态可视化
- 日志实时更新
- 错误提示和定位

### ⚡ Hot Run 模式

**目标**: 前端修改节点后立即执行该节点

**实现步骤**:

1. **工作流版本管理**
   - 每次修改创建新版本
   - 支持版本回滚
   - 版本差异对比

2. **增量 DAG 构建**
   - 只构建变化的节点
   - 自动识别依赖关系
   - 智能缓存复用

3. **节点级执行 API**
   ```python
   @router.post("/{workflow_id}/execute-node")
   async def execute_node(workflow_id: str, node_id: str):
       """执行单个节点及其依赖"""
       dag_settings = DAGSettings(
           targets=frozenset([f"node_{node_id}"]),
           forcetargets=True
       )
       # 执行逻辑
   ```

4. **前端集成**
   - 节点修改时自动触发执行
   - 显示执行进度
   - 错误实时反馈

### 📡 WebSocket 实时同步

**功能**:
- 工作流变更广播
- 执行状态推送
- 多用户协作支持

**API 设计**:
```python
@router.websocket("/ws/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """工作流实时同步"""
    await manager.connect(websocket, workflow_id)

    # 订阅工作流变更
    await manager.subscribe_workflow_changes(workflow_id)

    # 接收和广播消息
    while True:
        data = await websocket.receive_text()
        await manager.broadcast(workflow_id, data)
```

---

## 长期愿景 (v1.0.0+)

### 🤖 AI Agent 集成

**目标**: 智能 AI 助手辅助工作流设计

**功能**:
- [ ] 自然语言生成工作流
- [ ] 智能推荐工具组合
- [ ] 参数优化建议
- [ ] 错误诊断和修复

### 🔌 工作流导入导出

**支持格式**:
- [ ] CWL (Common Workflow Language)
- [ ] Snakemake 工作流格式
- [ ] Nextflow
- [ ] 自定义 JSON 格式

### 📦 批量处理增强

**功能**:
- [ ] 多样品批量执行
- [ ] 参数扫描
- [ ] 并行执行控制
- [ ] 结果汇总和比较

### 🌐 多用户协作

**功能**:
- [ ] 用户认证和授权
- [ ] 工作流共享
- [ ] 团队工作空间
- [ ] 审计日志

### ⚙️ 工作流模板

**功能**:
- [ ] 预定义工作流模板
- [ ] 社区模板市场
- [ ] 自定义模板创建
- [ ] 模板版本管理

### 📊 可视化增强

**功能**:
- [ ] DAG 可视化
- [ ] 执行时间线
- [ ] 资源使用监控
- [ ] 结果可视化

### 🔧 高级执行特性

**功能**:
- [ ] 检查点 (Checkpoints)
- [ ] 条件执行
- [ ] 循环和迭代
- [ ] 子工作流

---

## 技术债务清单

### 高优先级

- [ ] 创建 WorkflowStore 类
- [ ] 修复 execute 端点的模块导入问题
- [ ] 统一工作流存储机制
- [ ] 完善单元测试覆盖

### 中优先级

- [ ] 重构 RuleBuilder 以提高可读性
- [ ] 优化数据库查询性能
- [ ] 添加性能监控
- [ ] 改进日志系统

### 低优先级

- [ ] 迁移到 PostgreSQL (如需要)
- [ ] 实现缓存机制
- [ ] 添加 API 速率限制
- [ ] 实现分布式执行

---

## 发布计划

### v0.2.1 (Bug Fix Release)
- 预计发布: 2025-02-15
- 重点: JSON 兼容性修复

### v0.3.0 (Stability Release)
- 预计发布: 2025-03-01
- 重点: 核心 Bug 修复和架构改进

### v0.4.0 (Frontend Integration)
- 预计发布: 2025-04-01
- 重点: 完整的前端界面和基础功能

### v0.5.0 (Advanced Features)
- 预计发布: 2025-05-15
- 重点: Hot Run 模式和 WebSocket 实时同步

### v1.0.0 (Production Ready)
- 预计发布: 2025-07-01
- 重点: 生产级稳定性和完整功能集

---

