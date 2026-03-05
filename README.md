# TDEase Backend

质谱数据分析工作流平台后端服务 - Mass Spectrometry Data Analysis Workflow Platform Backend

## 功能特性

- **工作流管理**: 创建、编辑、编译和执行VueFlow工作流
- **执行监控**: 实时监控工作流执行状态和进度
- **工具集成**: 跨平台工具发现和管理系统
- **文件管理**: 文件上传、下载和目录管理
- **权限控制**: 跨平台文件权限和用户工作空间管理
- **实时通信**: WebSocket实时状态更新和日志监控

## 技术栈

- **FastAPI**: 现代异步Web框架
- **FlowEngine**: 自研轻量级DAG调度器
- **LocalExecutor**: 本地命令执行器
- **ShellRunner**: Shell命令执行（支持Conda环境）
- **Pydantic**: 数据验证和序列化
- **SQLite**: 轻量级数据库
- **WebSocket**: 实时双向通信
- **YAML**: 配置文件格式

## 项目结构

```
TDEase-Backend/
├── app/                        # FastAPI应用主目录
│   ├── api/                    # API端点模块
│   │   ├── workflows.py        # 工作流管理API
│   │   ├── executions.py       # 执行管理API
│   │   ├── tools.py            # 工具管理API
│   │   └── files.py            # 文件管理API
│   ├── core/                   # 核心功能模块
│   │   ├── engine/             # FlowEngine调度器
│   │   ├── executor/           # 命令执行器
│   │   ├── platform_manager.py # 平台管理器
│   │   ├── permission_manager.py # 权限管理器
│   │   └── websocket.py        # WebSocket实时通信
│   ├── models/                 # Pydantic数据模型
│   ├── services/               # 业务逻辑服务
│   │   ├── workflow_service.py # 工作流编排服务
│   │   ├── tool_registry.py    # 工具注册表
│   │   └── execution_store.py  # 执行状态存储
│   ├── database/               # 数据库初始化
│   ├── schemas/                # Pydantic schemas
│   ├── core/                   # 配置常量
│   └── dependencies.py         # 依赖注入
├── src/                        # 原有TDEase代码
├── config/                     # 配置文件
├── data/                       # 运行时数据
├── docs/                       # 文档目录
├── tests/                      # 测试脚本
├── requirements.txt            # Python依赖
└── start_fastapi.py           # 启动脚本
```


## API端点

### 工作流管理
- `POST /api/workflows/` - 创建工作流
- `GET /api/workflows/{workflow_id}` - 获取工作流详情
- `PUT /api/workflows/{workflow_id}` - 更新工作流
- `DELETE /api/workflows/{workflow_id}` - 删除工作流
- `POST /api/workflows/{workflow_id}/compile` - 编译工作流
- `GET /api/workflows/{workflow_id}/status` - 获取工作流状态

### 执行管理
- `POST /api/execution/{workflow_id}/execute` - 开始执行工作流
- `GET /api/execution/{execution_id}` - 获取执行详情
- `GET /api/execution/{execution_id}/status` - 获取执行状态
- `POST /api/execution/{execution_id}/control` - 控制执行(暂停/恢复/取消)
- `GET /api/execution/{execution_id}/logs` - 获取执行日志

### 工具管理
- `GET /api/tools/discovery` - 发现可用工具
- `GET /api/tools/registered` - 获取已注册工具
- `POST /api/tools/register` - 注册新工具
- `PUT /api/tools/{tool_name}` - 更新工具信息
- `DELETE /api/tools/{tool_name}` - 删除工具注册

### 文件管理
- `POST /api/files/upload` - 上传文件
- `POST /api/files/download` - 下载文件
- `GET /api/files/list/{workspace_path}` - 列出目录内容
- `GET /api/files/workspace/{workspace_path}` - 获取工作空间信息
- `POST /api/files/operation` - 文件操作(复制/移动/删除)

### WebSocket
- `WS /ws/{workflow_id}` - 工作流实时监控

## 开发指南

### 运行测试

```bash
# Phase 1 基础功能测试
python test_fastapi_setup.py

# Phase 2 API功能测试
python test_phase2_api.py
```

### 代码规范

- 使用Python 3.8+语法
- 遵循PEP 8代码风格
- 使用类型注解
- 完善的文档字符串

### 跨平台支持

项目支持Windows和Linux平台：

- Windows: 支持Win32 API和文件属性
- Linux: 支持Unix权限和管理命令
- 工具发现: 自动适配平台特定的可执行文件格式
- 路径处理: 使用标准库确保跨平台兼容


## 故障排除

### 常见问题

1. **数据库初始化失败**
   - 检查数据目录权限
   - 确保SQLite可用

2. **工具发现失败**
   - 检查PATH环境变量
   - 验证工具可执行权限

3. **WebSocket连接失败**
   - 检查防火墙设置
   - 确认WebSocket支持

4. **文件操作失败**
   - 检查工作空间权限
   - 验证磁盘空间

### 日志查看

```bash
# 应用日志
tail -f logs/app.log

# FlowEngine执行日志
tail -f data/workflows/{workflow_id}/logs/engine.log
```

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件