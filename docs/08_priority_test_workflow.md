# Section 8: 优先测试工作流架构 (Priority Test Workflow)

## 8.1 核心测试工作流说明
`wf_test_full.json` 是本架构 v2.1 版本的基准测试用例，旨在验证全链路数据转发与交叉过滤逻辑。

- **工作流 ID**: `wf_test_full`
- **目标场景**：从原始 mzML 到 TopFD 处理，最终在两个不同的 Viewer 中并行审阅同一节点的多个输出。

## 8.2 节点拓扑与数据流
1.  **data_loader_1**: 挂载 mzML 原始文件。
2.  **topfd_1**:
    - **输入**：`data_loader_1`
    - **输出**：`ms1feature` (CSV), `peaks` (Binary/Text)。
3.  **featuremap_1**:
    - **数据输入**：连接 `topfd_1` 的 `ms1feature` 端口。
    - **职责**：渲染特征散点图。
4.  **spectrum_1**:
    - **数据输入**：连接 `topfd_1` 的 `peaks` 端口。
    - **职责**：渲染质谱峰。

## 8.3 状态流 (Interaction) 逻辑
- **Feature Selection**: `featuremap_1` (output-selection) -> `spectrum_1` (input-selection)。
- **验证点**：当用户在 `featuremap_1` 中画刷选中数个特征时，`spectrum_1` 必须通过 `StateBus` 接收 ID 列表，并自动加载对应的 Peaks 数据进行高亮。

## 8.4 验证方法
1.  **Port-Aware API**: 检查后端日志，确认 `featuremap_1` 请求数据时携带了 `port_id=ms1feature`，而 `spectrum_1` 请求时携带了 `port_id=peaks`。
2.  **StateBus Trace**: 在前端控制台开启 `StateBus` 调试模式，确认 `state/selection_ids` 事件在节点间准确流转。
