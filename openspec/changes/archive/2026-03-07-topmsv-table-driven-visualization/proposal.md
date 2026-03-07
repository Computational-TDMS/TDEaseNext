## Why

TopPIC/TopFD 已经输出了实现 TopMSV 核心交互所需的结构化文件（TSV、msalign、feature），但当前 TDEase 交互节点还不能直接基于这些文件完成 PrSM 表格、MS2 谱图和序列联动。现在推进这项改造，可以在不依赖 HTML 产物的前提下，把 TopMSV 的关键交互模式纳入现有工作流体系。

## What Changes

- 新增一个面向 TopPIC/TopFD 输出的 PrSM 数据打包能力，将多源文件整理为可视化可直接消费的统一表格数据。
- 扩展交互可视化节点类型，新增 TopMSV 风格的 MS2 谱图查看节点与序列查看节点，并与 PrSM 表格联动。
- 扩展现有节点数据访问行为，使其可稳定读取包含参数前导区块的 TopPIC TSV 文件。
- 扩展 `workflows/wf_test_full.json`，增加 TopMSV 交互分支与状态连接，明确 `Prsm ID` 驱动的状态传播链路。
- 将 TopFD/TopPIC 的 HTML 生成参数在该工作流中默认关闭（`skip_html_folder=true`），避免冗余输出。

## Capabilities

### New Capabilities
- `topmsv-prsm-bundle`: 将 TopPIC PrSM 结果与 TopFD MS2 数据清洗并打包为统一的可视化输入契约，供表格、谱图、序列节点复用。

### Modified Capabilities
- `interactive-visualization`: 增加 TopMSV 交互节点能力（PrSM 表格、MS2 谱图、序列联动）及基于 `Prsm ID` 的跨节点状态同步行为。
- `node-data-access`: 增强表格解析逻辑以支持 TopPIC TSV 参数前导区块，保证交互节点稳定读取 TopPIC 结果文件。

## Impact

- 受影响后端模块：`app/services/node_data_service.py`、工具定义加载与交互节点输出解析链路、`config/tools/*.json`。
- 受影响前端模块：交互节点容器与新 viewer 组件、状态总线订阅映射、节点面板与端口配置。
- 受影响工作流资产：`workflows/wf_test_full.json` 及对应测试夹具。
- 受影响文档：`docs/TOPMSV.md`、`docs/TOPMSV_Architecture.md` 需要同步为表格驱动实现路径。
