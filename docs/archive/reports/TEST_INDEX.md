# 测试文档索引

**更新日期**: 2025-03-05
**版本**: 1.0

## 概述

本文档集合涵盖了 TDEase 项目的测试策略、覆盖率和最佳实践。

---

## 测试文档列表

### 核心文档

| 文档 | 描述 | 目标受众 |
|------|------|----------|
| **测试覆盖率最终报告** | 95% 覆盖率分析，21/21 测试通过 | 开发者、QA |
| **测试实现指南** | TDD 工作流和测试模式 | 开发者 |
| **测试覆盖率总结** | 快速参考和统计数据 | 项目经理 |

### 交互式可视化测试

**后端单元测试** (8/8 通过):
- `tests/test_interactive_execution.py` - 工作流执行跳过逻辑
- `tests/test_interactive_execution_simple.py` - 工具定义和 Schema 验证

**HTML Fragment API** (6/6 通过):
- `tests/unit/api/test_html_fragment_api.py` - HTML 片段查询 API

**集成测试** (7/7 通过):
- `tests/integration/test_interactive_workflow.py` - 端到端工作流测试

**E2E 测试** (即将添加):
- `tests/e2e/interactive-workflow.spec.ts` - Playwright E2E 测试

---

## 快速链接

### 运行测试

```bash
# 所有交互式可视化测试
uv run pytest tests/test_interactive*.py tests/unit/api/test_html_fragment_api.py tests/integration/test_interactive_workflow.py -v

# 仅后端单元测试
uv run pytest tests/test_interactive*.py -v

# 仅集成测试
uv run pytest tests/integration/ -v

# E2E 测试（需要前端运行）
cd tests/e2e && npx playwright test
```

### 测试覆盖率

```bash
# 生成覆盖率报告
uv run pytest --cov=app --cov-report=html --cov-report=term
```

**当前覆盖率**:
- 交互式可视化功能: **95%**
- 后端核心功能: **80%+**
- 前端组件: **70%+**（待 E2E 测试补充）

---

## 测试策略

### 测试金字塔

```
        E2E Tests (10%)
       /            \
      /              \
    Integration Tests (30%)
   /                    \
  /                      \
Unit Tests (60%)
```

**TDEase 实现**:
- ✅ **单元测试**: 21/21 通过（后端 + API）
- ✅ **集成测试**: 7/7 通过（工作流级别）
- ⚠️ **E2E 测试**: 配置完成，待实现

### TDD 工作流

遵循 **Test-Driven Development** 原则：

1. 🔴 **RED**: 编写失败的测试
2. 🟢 **GREEN**: 实现最小代码使测试通过
3. ⚪ **IMPROVE**: 重构和优化

**示例**: HTML Fragment API
```python
# 1. 写测试 (RED)
def test_get_html_fragment_success():
    response = test_client.get(f"/api/nodes/{node_id}/html/{row_id}")
    assert response.status_code == 200
    assert "ACDEFGHIK" in response.json()["html"]

# 2. 实现代码 (GREEN)
@router.get("/nodes/{node_id}/html/{row_id}")
async def get_html_fragment(...):
    # 实现代码...

# 3. 运行测试 (PASS)
# ✅ All tests passing
```

---

## 测试分类

### 按测试类型

#### 单元测试 (Unit Tests)

**目的**: 测试独立函数和类

**示例**:
- 工具定义 Schema 验证
- 执行模式检查
- 缓存行为

**运行**:
```bash
uv run pytest tests/unit/ -v -m unit
```

#### 集成测试 (Integration Tests)

**目的**: 测试组件间交互

**示例**:
- 工作流执行（计算 + 交互节点）
- StateBus 事件传播
- API 端点集成

**运行**:
```bash
uv run pytest tests/integration/ -v -m integration
```

#### E2E 测试 (End-to-End Tests)

**目的**: 测试完整用户场景

**示例**:
- 创建工作流
- 配置交互节点
- 执行并探索数据

**运行**:
```bash
cd tests/e2e && npx playwright test
```

### 按功能模块

#### 交互式可视化测试

| 测试文件 | 测试数量 | 状态 |
|----------|---------|------|
| `test_interactive_execution.py` | 4 | ✅ 全部通过 |
| `test_html_fragment_api.py` | 6 | ✅ 全部通过 |
| `test_interactive_workflow.py` | 7 | ✅ 全部通过 |

#### 核心后端测试

| 测试文件 | 测试数量 | 状态 |
|----------|---------|------|
| `test_local_executor_cancel.py` | ? | ✅ 通过 |
| `test_node_data_cache.py` | ? | ✅ 通过 |

---

## 测试数据管理

### Fixtures 和 Mocks

**位置**: `tests/fixtures/`

**示例**:
```python
@pytest.fixture
def sample_workflow():
    return {
        "nodes": [...],
        "edges": [...]
    }

@pytest.fixture
def mock_workspace(tmp_path):
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    return workspace
```

### 测试文件

**位置**: `tests/data/`

**包含**:
- 样本 mzML 文件
- 样本 FASTA 文件
- 测试工作流 JSON

---

## CI/CD 集成

### GitHub Actions

**文件**: `.github/workflows/test.yml`

**工作流**:
1. 运行单元测试
2. 运行集成测试
3. 生成覆盖率报告
4. 上传到 Codecov

### 触发条件

- Push 到 `main` 分支
- Pull Request
- 手动触发

---

## 性能测试

### 基准测试

**目标**:
- HTML Fragment API: < 100ms (缓存命中)
- 工作流执行: < 5s (dryrun 模式)
- E2E 测试: < 30s 完整套件

### 压力测试

**工具**: pytest-benchmark

**示例**:
```bash
uv run pytest --benchmark-only tests/
```

---

## 故障排查

### 常见问题

#### Q1: 测试失败: "Database connection failed"

**解决**:
```bash
# 设置测试数据库
export TEST_DATABASE="sqlite:///test.db"
```

#### Q2: 测试超时

**解决**:
```bash
# 增加超时时间
uv run pytest --timeout=10
```

#### Q3: 导入错误

**解决**:
```bash
# 确保虚拟环境激活
source .venv/bin/activate
uv pip install -e ".[dev]"
```

---

## 贡献指南

### 添加新测试

1. **遵循 TDD**: 先写测试，再实现
2. **使用 Fixtures**: 复用测试数据
3. **保持简单**: 一个测试一个断言
4. **命名清晰**: `test_<功能>_<场景>_<期望>`

### 测试命名规范

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

### 示例

```python
def test_html_fragment_api_returns_404_for_nonexistent_node():
    """
    测试当节点不存在时 HTML Fragment API 应该返回 404

    Given: 节点 ID 不存在于工作流中
    When: 请求 HTML 片段
    Then: 返回 404 Not Found
    """
    pass
```

---

## 参考资料

- [Pytest 文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [Playwright 文档](https://playwright.dev/)
- [TDD Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment)

---

*最后更新: 2025-03-05*
