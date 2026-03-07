# Section 6: 测试指南 (End-to-End Testing)

## 6.1 全局测试策略：金字塔模型
TDEase 遵循 TDD (Test-Driven Development) 原则，确保每一项架构变更（无论是重型后端还是实时前端）都有可靠的自动化验证。

- **Unit Tests (60%)**：验证独立算法（如 `fragment_matcher`）、Schema 逻辑及 `path_router`。
- **Integration Tests (30%)**：验证 API 端点（Workflow, Execution, Compute Proxy）、数据库持久化与流程调度逻辑。
- **E2E Tests (10%)**：验证完整用户场景，如批量执行触发、画布连接与 Dashboard 渲染。

## 6.2 核心测试模块 (Core Test Suites)
### 6.2.1 引擎与管道测试 (`tests/workflow/`)
验证 `CommandPipeline` 是否能正确注入占位符、处理物理路径并生成预期的 CLI 命令。
### 6.2.2 实时代理测试 (`tests/unit/api/compute_proxy/`)
验证 `/fragment-match` 与 `/modification-search` 在高并发下的响应性能与准确性。
### 6.2.3 交互式架构测试 (`tests/test_interactive*.py`)
验证后端是否正确识别并跳过 `executionMode: "interactive"` 的节点，同时通过 Port-Aware 接口转发输出。

## 6.3 开发工作流：TDD 实战
1.  **Red (红)**：针对新功能（如新的工具定义）编写失败的单元测试。
2.  **Green (绿)**：实现代码（修改 `tool_registry` 或 `command_pipeline`）使测试通过。
3.  **Refactor (重构)**：优化逻辑并确保全量集成测试（Integration Tests）依然通过。

## 6.4 运行指南
```bash
# 快速回归（不含真实工具烟雾）
uv run pytest -m "not prod_smoke" -v

# 真实工具生产烟雾（TopFD -> TopPIC 最小链路）
uv run pytest tests/smoke/test_real_tool_compute_chain.py -m prod_smoke -v -rs

# 指定模块回归
uv run pytest tests/test_workflow_execution.py tests/test_cmdline_composition_e2e.py -v
```

## 6.5 CI/CD 与质量控制
- **自动化网控**：所有 PR 必须通过 GitHub Actions 的全量测试。
- **性能基准**：交互式 API (Compute Proxy) 的 P99 响应时间必须保持在 200ms 以内。
- **烟雾车道命令**：在已配置真实工具与夹具的 runner 上执行  
  `uv run pytest tests/smoke/test_real_tool_compute_chain.py -m prod_smoke -v -rs`

## 6.6 生产烟雾前置条件与排障

- `config/tools/*.json` 默认使用可移植命令名（如 `topfd` / `toppic`），不再提交机器绝对路径。
- 如需本机绝对路径，请在 `data/tools/<tool_id>.json` 覆盖 `command.executable`（`data/` 默认不纳入版本控制）。
- 可选 profile 叠加：通过 `TDEASE_TOOL_PROFILE` 或 `TDEASE_TOOL_PROFILES` 指定 `config/tools/profiles/<profile>/`。
- 需要可执行的最小夹具：`mzML` 与 `FASTA`。
- 可通过环境变量指定夹具路径：
  - `TDEASE_SMOKE_MZML`
  - `TDEASE_SMOKE_FASTA`
- 若测试被跳过，使用 `-rs` 查看具体缺失项并补齐环境。
- 若出现 pytest 收集权限错误，优先检查临时目录（如 `tests/fixtures/tmp_pytest`、`pytest-cache-files-*`）是否被隔离在收集范围外。
