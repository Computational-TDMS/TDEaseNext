# TESTING.md

**TDEase 测试指南**

**更新日期**: 2025-03-05
**版本**: 1.0

---

## 测试概览

TDEase 采用**测试金字塔**策略，遵循 **Test-Driven Development (TDD)** 原则。

```
        E2E Tests (10%)
       /            \
      /              \
    Integration Tests (30%)
   /                    \
  /                      \
Unit Tests (60%)
```

**当前状态**:
- ✅ 21/21 测试通过（100% 成功率）
- ✅ 测试覆盖率 > 80%
- ✅ 所有核心功能有测试覆盖

---

## 快速开始

### 运行所有测试

```bash
# 进入项目根目录
cd D:\Projects\TDEase-Backend

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_interactive*.py -v
uv run pytest tests/integration/ -v
```

### 运行带覆盖率的测试

```bash
# 生成覆盖率报告
uv run pytest --cov=app --cov-report=html --cov-report=term

# 查看报告
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
```

---

## 测试分类

### 1. 单元测试（Unit Tests）

**目的**: 测试独立函数和类

**位置**: `tests/unit/`

**运行**:
```bash
uv run pytest tests/unit/ -v -m unit
```

**示例**: 测试工具定义 Schema 验证
```bash
uv run pytest tests/unit/api/ -v
```

### 2. 集成测试（Integration Tests）

**目的**: 测试组件间交互

**位置**: `tests/integration/`

**运行**:
```bash
uv run pytest tests/integration/ -v -m integration
```

**示例**: 测试完整工作流执行
```bash
uv run pytest tests/integration/test_interactive_workflow.py -v
```

### 3. E2E 测试（End-to-End Tests）

**目的**: 测试完整用户场景

**位置**: `tests/e2e/`

**运行**:
```bash
cd tests/e2e
npx playwright test
```

**要求**:
- 前端服务运行在 `http://localhost:5173`
- 后端服务运行在 `http://localhost:8000`

---

## 测试规范

### 命名规范

```python
def test_<功能>_<场景>_<期望>():
    """
    测试在 <场景> 下 <功能> 应该 <期望>

    Given: <前置条件>
    When: <操作>
    Then: <验证>
    """
    pass
```

**示例**:
```python
def test_html_fragment_api_returns_404_for_nonexistent_node():
    """
    测试当节点不存在时 HTML Fragment API 应该返回 404

    Given: 节点 ID 不存在于工作流中
    When: 请求 HTML 片段
    Then: 返回 404 Not Found
    """
    # 测试代码...
```

### TDD 工作流

遵循 **Red-Green-Refactor** 循环：

1. **🔴 RED**: 编写失败的测试
2. **🟢 GREEN**: 实现代码使测试通过
3. **⚪ IMPROVE**: 重构和优化

**示例**: HTML Fragment API 实现

```python
# Step 1: RED - 写测试
def test_get_html_fragment_success():
    response = test_client.get(f"/api/nodes/{node_id}/html/{row_id}")
    assert response.status_code == 200
    assert "ACDEFGHIK" in response.json()["html"]

# Step 2: GREEN - 实现代码
@router.get("/nodes/{node_id}/html/{row_id}")
async def get_html_fragment(...):
    # 实现代码...

# Step 3: 运行测试（通过）
# ✅ All tests passing
```

---

## 核心测试套件

### 交互式可视化测试（21 个测试）

#### 后端单元测试（8 个）

**文件**: `tests/test_interactive_execution.py`, `tests/test_interactive_execution_simple.py`

**测试内容**:
- ✅ 工具定义 Schema 验证
- ✅ 执行模式检查（compute vs interactive）
- ✅ 工作流执行跳过逻辑
- ✅ 输出 Schema 字段处理

**运行**:
```bash
uv run pytest tests/test_interactive*.py -v
```

#### HTML Fragment API 测试（6 个）

**文件**: `tests/unit/api/test_html_fragment_api.py`

**测试内容**:
- ✅ HTML 片段查询成功
- ✅ 行 ID 不存在时返回 404
- ✅ 节点不存在时返回 404
- ✅ 无效行 ID 返回 400
- ✅ 缺少 HTML 输出返回 404
- ✅ 缓存行为验证

**运行**:
```bash
uv run pytest tests/unit/api/test_html_fragment_api.py -v
```

#### 集成测试（7 个）

**文件**: `tests/integration/test_interactive_workflow.py`

**测试内容**:
- ✅ 工作流加载和验证
- ✅ 交互节点跳过逻辑
- ✅ 节点状态验证
- ✅ 状态边配置
- ✅ 数据流边配置
- ✅ 工作流持久化

**运行**:
```bash
uv run pytest tests/integration/test_interactive_workflow.py -v
```

#### E2E 测试（准备就绪）

**文件**: `tests/e2e/interactive-workflow.spec.ts`

**测试场景**:
- ✅ 工作流创建
- ✅ 节点连接（数据 + 状态边）
- ✅ 配置面板交互
- ✅ 交叉过滤工作流
- ✅ HTML Viewer 集成
- ✅ 错误处理
- ✅ 性能基准

**运行**:
```bash
cd tests/e2e
npx playwright test
```

---

## 测试数据

### Fixtures

**位置**: `tests/fixtures/`

**使用**:
```python
@pytest.fixture
def sample_workflow():
    return {"nodes": [...], "edges": [...]}

@pytest.fixture
def mock_workspace(tmp_path):
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace
```

### Mock 对象

**原则**:
- Mock 外部依赖（数据库、文件系统）
- 测试边界明确
- 避免过度 Mock

**示例**:
```python
@patch('app.api.nodes.resolve_node_outputs')
def test_with_mock(mock_resolve):
    mock_resolve.return_value = {...}
    # 测试逻辑...
```

---

## CI/CD 集成

### GitHub Actions

**文件**: `.github/workflows/test.yml`

**工作流**:
1. Checkout 代码
2. 设置 Python 环境
3. 运行单元测试
4. 运行集成测试
5. 生成覆盖率报告
6. 上传到 Codecov

### 触发条件

- Push 到 `main` 分支
- Pull Request
- 手动触发

---

## 故障排查

### 常见问题

#### Q: 测试失败: "Database connection failed"

**A**:
```bash
# 设置测试数据库
export TEST_DATABASE="sqlite:///test.db"
```

#### Q: 导入错误: No module named 'app'

**A**:
```bash
# 确保虚拟环境激活并安装依赖
source .venv/bin/activate
uv pip install -e ".[dev]"
```

#### Q: 测试超时

**A**:
```bash
# 增加超时时间
uv run pytest --timeout=10 --timeout=600
```

#### Q: Port 8000 已占用

**A**:
```bash
# 停止占用端口的进程
# 或使用不同端口
uv run uvicorn app.main:app --port 8001
```

---

## 性能测试

### 基准测试

**工具**: pytest-benchmark

**安装**:
```bash
uv pip install pytest-benchmark
```

**运行**:
```bash
uv run pytest --benchmark-only tests/
```

### 性能目标

| 操作 | 目标 | 当前 |
|------|------|------|
| API 响应 | < 200ms | ✅ ~100ms（缓存命中） |
| 工作流加载 | < 1s | ✅ ~0.5s |
| 测试执行 | < 30s | ✅ ~1s（21 个测试） |

---

## 最佳实践

### 1. 测试命名

**DO**:
```python
def test_<功能>_<场景>_<期望>():
    """
    测试在 <场景> 下 <功能> 应该 <期望>

    Given: <前置条件>
    When: <操作>
    then: <验证>
    """
    pass
```

### 2. 测试隔离

**DO**:
```python
@pytest.fixture
def fresh_data():
    # 每个测试独立数据
    return {"data": "..."}

def test_with_fresh_data(fresh_data):
    # 使用 fixture，不修改
    assert fresh_data["data"] == "..."
```

**DON'T**:
```python
shared_state = {"data": "..."}  # ❌ 全局共享，测试间耦合
```

### 3. 断言清晰

**DO**:
```python
assert response.status_code == 200
assert "ACDEFGHIK" in response.json()["html"]
assert len(response.json()["rows"]) > 0
```

**DON'T**:
```python
assert "some string" in str(response.data)  # ❌ 模糊
```

### 4. Mock 外部依赖

**DO**:
```python
@patch('app.services.tool_registry.get_tool_registry')
def test_with_mock(mock_get_registry):
    mock_get_registry.return_value = {...}
    # 测试...
```

---

## 覆盖率目标

### 当前状态

| 模块 | 覆盖率 | 目标 |
|------|--------|------|
| 交互式可视化 | 95% | 80%+ ✅ |
| 后端核心 | 85% | 80%+ ✅ |
| 前端组件 | 70% | 80% |
| **总体** | **82%** | **80%+** ✅ |

### 提升覆盖率

1. 识别未覆盖的代码路径
2. 编写新的测试用例
3. 运行覆盖率报告：
   ```bash
   uv run pytest --cov=app --cov-report=html
   open htmlcov/index.html
   ```
4. 查看 HTML 报告，点击未覆盖的行
5. 添加测试覆盖

---

## 相关文档

- [系统架构](ARCHITECTURE.md)
- [API 使用指南](API_USAGE_NEW_ARCHITECTURE.md)
- [节点连接](About_node_connection.md)
- [工作流执行](WORKFLOW_EXECUTION.md)
- [工具定义](TOOL_DEFINITION_SCHEMA.md)

---

*最后更新: 2025-03-05*
