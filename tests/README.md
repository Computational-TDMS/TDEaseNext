# 测试指南 / Testing Guide

## 推荐测试车道（Mock 回归 vs 生产烟雾）

```bash
# 1) 快速回归（默认本地开发）
uv run pytest -m "not prod_smoke" -v

# 2) 生产烟雾（真实 TopFD/TopPIC 链路）
uv run pytest tests/smoke/test_real_tool_compute_chain.py -m prod_smoke -v -rs
```

生产烟雾测试默认会检查前置条件，不满足时会 `skip` 并给出明确原因。  
可通过环境变量提供夹具路径：

```bash
$env:TDEASE_SMOKE_MZML="D:\\fixtures\\prod\\sample.mzML"
$env:TDEASE_SMOKE_FASTA="D:\\fixtures\\prod\\sample.fasta"
```

工具可执行路径采用“共享可移植 + 本地覆盖”策略：

- `config/tools/*.json` 保持可移植命令名（不提交机器绝对路径）。
- 如需本机绝对路径，写入 `data/tools/<tool_id>.json`（`data/` 不入库）。
- 可选 profile 叠加通过 `TDEASE_TOOL_PROFILE` / `TDEASE_TOOL_PROFILES` 指定。

## ABC 工作流执行测试 (Mock 工具链)

用于验证后端 FlowEngine + LocalExecutor 的真实执行路径，使用 A -> B -> C 三个 Python 脚本模拟工具链。

### 运行方式

```bash
# 使用 uv（推荐）
uv run python tests/test_workflow_execution.py

# 或使用 pytest
uv run pytest tests/test_workflow_execution.py -v
```

**无需启动 API 服务器**：测试通过 `TestClient` 在进程内调用后端，真实执行 Shell 命令。

## 命令行拼装 E2E（Command Composition）

用于验证工作流执行系统最终拼装出的命令行参数（不是只测中间函数）。

### 覆盖场景

- `pbfgen` 风格：输入端口通过 `flag`（如 `-i`）传参，且 edge `sourceHandle` 与上游输出 handle 不一致时仍能正确解析并拼装。
- `toppic` 风格：多输入位置参数的顺序稳定（`positionalOrder` 生效）。
- 运行日志链路：工具 stdout 能通过 `log_callback` 被捕获（前端日志展示链路的后端入口）。
- 命令拼装追踪：执行前会输出 `[command_trace] {...}` 结构化日志，包含 `cmd_parts/input_flags/positional_args`。
- API 可直接读取节点 trace：`GET /api/executions/{execution_id}/nodes/{node_id}/trace`。

### 运行方式

```bash
uv run python -m pytest tests/test_cmdline_composition_e2e.py -q
uv run python -m pytest tests/test_input_binding_planner.py -q
uv run python -m pytest tests/test_command_pipeline_trace.py -q
uv run python -m pytest tests/test_execution_store_command_trace.py tests/test_execution_api_command_trace.py -q
```

相关文件：

- `tests/test_cmdline_composition_e2e.py`
- `tests/fixtures/tools/mock_source_tool.py`
- `tests/fixtures/tools/mock_pbfgen_tool.py`
- `tests/fixtures/tools/mock_echo_argv_tool.py`

### 必填输入严格校验（Fail-Fast）

当前执行路径会在命令组装前校验 required 输入端口：

- required 端口无绑定：节点直接失败（不会执行命令）。
- required 单输入端口出现多候选绑定：节点以歧义错误失败（不会隐式挑选）。
- 绑定决策与失败原因会写入节点 `command_trace.input_binding`，可通过  
  `GET /api/executions/{execution_id}/nodes/{node_id}/trace` 查询。

对旧工作流迁移建议：

- 为每个 required 输入补齐明确 edge（尤其是 `targetHandle`）。
- 避免同一 required 单输入端口挂多条并行上游边。
- 对历史“模糊匹配才可运行”的流程，先在测试环境修正连接再升级到新规则。

### 依赖与结构

| 文件 | 说明 |
|------|------|
| `tests/fixtures/tools/tool_a.py` | Mock 工具 A：无输入，输出 `{sample}_a.txt` |
| `tests/fixtures/tools/tool_b.py` | Mock 工具 B：读取 A 输出，输出 `{sample}_b.txt` |
| `tests/fixtures/tools/tool_c.py` | Mock 工具 C：读取 B 输出，输出 `{sample}_c.txt` |
| `config/tools/tool_a.json` | 工具 A 注册定义 |
| `config/tools/tool_b.json` | 工具 B 注册定义 |
| `config/tools/tool_c.json` | 工具 C 注册定义 |
| `tests/fixtures/workflow_abc.json` | Data Loader -> A -> B -> C 工作流 |
| `tests/fixtures/dummy.raw` | 占位输入文件（满足 validator） |

### 文件命名规范

- 上游输出：`{sample}_a.txt`、`{sample}_b.txt`
- 下游接收：通过 edges 的 sourceHandle/targetHandle 关联
- 日志：各工具向 stderr 输出模拟日志，可被 Shell 捕获

### 验证内容

- 执行完成 (status=completed)
- 输出文件 `dummy_a.txt`、`dummy_b.txt`、`dummy_c.txt` 存在
- **内容验证**：A 输出 `TOOL_A_SIGNATURE=`；B 必须读到 A 的输出（含该签名）才继续，并输出 `TOOL_B_SIGNATURE=`；C 必须读到 B 的输出（含该签名）才继续。任一验证失败则工具返回非 0 退出码。

### 是否直接通过 API 调用后端？

**是**。测试使用 `TestClient(app)` 发送 `POST /api/workflows/execute`，请求经 FastAPI 路由进入 `workflow_service.execute_workflow()`，最终由 FlowEngine + LocalExecutor + ShellRunner 实际执行 Shell 命令。即：**直接通过 HTTP API 调用后端**，不启动单独服务（TestClient 在进程内模拟 HTTP）。

---

## 测试工作流执行 / Testing Workflow Execution

### 方法1: 使用 ABC 测试（推荐，真实执行）

```bash
uv run python tests/test_workflow_execution.py
```

通过 TestClient 在进程内调用 API，**无需单独启动服务器**。

### 方法2: 使用测试脚本（需先启动 API）

```bash
# 1. 确保API服务器正在运行
uv run python -m app.main

# 2. 在另一个终端运行测试脚本
uv run python tests/test_workflow_execution.py
```

### 方法2: 使用前端界面

1. 启动后端API:
   ```bash
   python -m app.main
   ```

2. 启动前端应用 (在TDEase-FrontEnd目录):
   ```bash
   npm run dev  # 或相应的启动命令
   ```

3. 在前端界面中:
   - 导入 `tests/flattened_workspace_test.json` 文件
   - 或者手动创建相同的工作流
   - 点击执行按钮

### 方法3: 使用curl或Postman

```bash
# 1. 准备请求数据 (从测试JSON转换)
# 2. 调用API端点

curl -X POST http://localhost:8000/api/workflows/execute \
  -H "Content-Type: application/json" \
  -d @tests/test_execute_request.json
```

### 测试文件说明

- `flattened_workspace_test.json`: 测试工作流定义
  - 包含 data_loader, fasta_loader, topfd, toppic 节点
  - 测试扁平化工作空间设计

- `test_workflow_execution.py`: 自动化测试脚本
  - 可以直接运行，无需前端
  - 包含完整的执行流程测试

### 验证执行结果

执行完成后，检查：

1. **执行状态**: 通过 `/api/executions/{execution_id}` 查看状态
2. **工作空间**: 检查 `data/workflows/{workflow_id}/` 目录
3. **日志文件**: 查看 `data/workflows/{workflow_id}/logs/` 目录
4. **结果文件**: 查看 `data/workflows/{workflow_id}/results/` 目录

### 调试提示

如果测试失败：

1. **检查API是否运行**: `curl http://localhost:8000/health`
2. **查看API日志**: 检查终端输出的日志
3. **检查数据库**: SQLite数据库在 `data/database.db`
4. **查看执行日志**: 通过 `/api/executions/{execution_id}/logs` 端点
5. **生产烟雾被跳过**: 使用 `-rs` 查看 skip 原因，补齐 TopFD/TopPIC 可执行文件和 `TDEASE_SMOKE_MZML` / `TDEASE_SMOKE_FASTA`
6. **pytest 收集失败（权限拒绝）**: 清理或避免遍历临时目录（如 `tests/fixtures/tmp_pytest`、`pytest-cache-files-*`）

### 示例：快速测试

```bash
# 终端1: 启动API
python -m app.main

# 终端2: 运行测试
python tests/test_workflow_execution.py

# 终端3: 查看执行状态 (可选)
curl http://localhost:8000/api/executions/{execution_id}
```
