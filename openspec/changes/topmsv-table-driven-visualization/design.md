## Context

当前工作流已具备 TopFD/TopPIC 处理链和基础交互节点（featuremap、spectrum、table）框架，但 TopMSV 的核心 PrSM 检查交互（PrSM 表格 -> MS2 谱图 -> 序列）尚未落地。  
现状中存在两个关键约束：
- TopPIC `*_prsm_single.tsv` 文件前部包含参数区块，现有通用表格解析将首行误判为表头，直接影响 viewer 读取。
- `wf_test_full.json` 目前没有针对 PrSM 的交互分支和稳定 ID 传播链路，无法建立可复现的 TopMSV 交互模式。

## Goals / Non-Goals

**Goals:**
- 基于 TopPIC/TopFD 表格与谱图输出实现 TopMSV 核心交互，不依赖 HTML 产物。
- 定义并实现新的节点类型与端口契约：PrSM 表格、MS2 查看、序列查看。
- 在 `wf_test_full.json` 增加可运行的数据流与状态流拓扑，完成端到端交互链路设计。
- 建立稳定的 PrSM 级主键传播机制，避免按行号选择导致的重排失配。

**Non-Goals:**
- 不复刻 TopMSV 的 TIC 与 LC-MS 3D 视图。
- 不在本变更中引入新的外部可视化框架（沿用现有前端栈）。
- 不在 MVP 阶段实现完整的 fragment annotation 自动计算（可在后续通过 compute-proxy 扩展）。

## Decisions

1. 以“表格驱动”替代“HTML 驱动”
- 决策：TopFD/TopPIC 在本交互链路默认配置 `skip_html_folder=true`，仅依赖 TSV/msalign/feature 输出。
- 原因：减少 I/O 和冗余产物，统一数据入口到 workflow 输出文件。
- 备选：继续消费 `*_html/topmsv` 页面资源。放弃原因是耦合旧页面脚本与 localStorage 机制，难以融入现有节点系统。

2. 引入 `prsm_bundle_builder` 作为数据归一化节点
- 决策：新增一个 compute/script 节点，输入 `toppic.prsm_single` 和 `topfd.ms2_msalign`（可选 `topfd.ms2feature`），输出 viewer 友好的统一表格。
- 输出契约：
  - `prsm_table_clean.tsv`: 去除参数区块并标准化列名，供表格节点直接展示。
  - `prsm_bundle.tsv`: 每行一个 PrSM，包含 `prsm_id`、`spectrum_id`、`scan`、`proteoform_seq`、`modifications_json`、`ms2_peaks_json` 等字段。
  - `ms2_peaks_json` 采用单文件内嵌策略，并默认按强度 TopN 截断（可配置）。
- 原因：将“跨文件 join + 结构清洗”从交互节点剥离，降低前端复杂度并提高可测试性。
- 备选：仅增强 `node_data_access` 解析 TopPIC TSV。放弃原因是无法解决 msalign 关联与统一数据契约问题。

3. 选择传播以 `Prsm ID` 作为稳定键
- 决策：TopMSV 分支复用 `state/selection_ids` 语义类型，载荷保存 `Prsm ID` 列值，不引入新的 `state/prsm_ids`。
- 原因：表格排序、过滤和分页后行号不稳定，容易造成谱图/序列显示错配。
- 备选：保持行号索引。放弃原因是跨组件一致性不可保证。

4. 新增两类交互 viewer，保留 `table_viewer` 复用
- 决策：
  - 新增 `topmsv_ms2_viewer`（interactive）：显示选中 PrSM 的 MS2 峰图，支持峰 hover 与候选标注层。
  - 新增 `topmsv_sequence_viewer`（interactive）：显示蛋白序列、切割位点、修饰位点和匹配覆盖。
  - `topmsv_sequence_viewer` v1 只读，不提供序列编辑和 compute-proxy 重算入口。
  - `prsm_table_viewer` 复用现有 `table_viewer`，通过配置指定主键列 `Prsm ID`。
- 原因：MS2/序列渲染逻辑明显区别于现有 spectrum/featuremap，单独类型更清晰。
- 备选：把 MS2 与序列做成一个复合节点。放弃原因是复用性差、调试边界不清。

5. 扩展 `wf_test_full.json` 的 TopMSV 分支
- 决策：新增节点并接入 TopFD/TopPIC 分支：
  - `prsm_bundle_builder_1`
  - `prsm_table_1`
  - `ms2_viewer_1`
  - `seq_viewer_1`
- 关键连接：
  - 数据边：`toppic_1.prsm_single -> prsm_bundle_builder_1`
  - 数据边：`topfd_1.ms2_msalign -> prsm_bundle_builder_1`
  - 数据边：`prsm_bundle_builder_1.prsm_table_clean -> prsm_table_1`
  - 数据边：`prsm_bundle_builder_1.prsm_bundle -> ms2_viewer_1`
  - 数据边：`prsm_bundle_builder_1.prsm_bundle -> seq_viewer_1`
  - 状态边：`prsm_table_1.selection -> ms2_viewer_1.selection_in`
  - 状态边：`prsm_table_1.selection -> seq_viewer_1.selection_in`
- 同时修正现有交互连接语义：selection 连接应使用 `connectionKind: "state"`。

6. `node_data_access` 增加 TopPIC preamble 容错
- 决策：在通用解析层支持跳过由分隔符和键值参数构成的前导区块，识别真实表头后再解析。
- 原因：不仅服务 TopMSV 分支，也避免其它表格 viewer 对 TopPIC TSV 读取失败。
- 备选：全部依赖 bundle 节点清洗。放弃原因是降低平台通用性，且调试时不便直接查看原始输出。

## Risks / Trade-offs

- [Risk] `prsm_bundle.tsv` 中 `ms2_peaks_json` 体积大，导致前端加载慢  
  -> Mitigation: 默认截断峰数（如按强度 TopN），保留参数可调并支持延迟加载。

- [Risk] TopPIC 与 TopFD 通过 `Spectrum ID`/`Scan` 关联时可能出现缺失映射  
  -> Mitigation: bundle 节点输出 `mapping_status` 字段并记录未匹配统计，viewer 对缺失项给出可见提示。

- [Risk] 在同一语义类型下混用“行号选择”和“主键选择”可能造成歧义  
  -> Mitigation: TopMSV 节点在工具定义中声明 `selection_key_field`，并在文档中明确该分支以主键为准。

- [Risk] 先做 bundle 再解析会增加一个计算节点与维护成本  
  -> Mitigation: 复用现有脚本节点框架，保持输入输出契约稳定并补充单元测试覆盖。

## Migration Plan

1. 新增工具定义：
   - `config/tools/prsm_bundle_builder.json`
   - `config/tools/topmsv_ms2_viewer.json`
   - `config/tools/topmsv_sequence_viewer.json`
2. 实现 bundle 逻辑与输出文件写入，并补充对应测试数据与解析测试。
3. 增强 `node_data_access` 的 TopPIC TSV preamble 处理，确保原始文件可直接浏览。
4. 实现前端 MS2/序列 viewer，并接入 `InteractiveNode` 渲染分发。
5. 更新 `workflows/wf_test_full.json`，加入 TopMSV 分支并设置 `skip_html_folder=true`。
6. 更新 `docs/TOPMSV.md` 和 `docs/TOPMSV_Architecture.md`，同步新数据流与节点契约。
7. 回归验证：执行工作流、检查节点跳过/加载行为、验证三节点联动。

回滚策略：
- 保持新节点独立与可选，不替换现有 featuremap/spectrum 分支；出现问题时可直接移除新增分支并恢复旧 workflow 文件。

## Open Questions

- 当前范围无阻塞性开放问题；其余扩展项（例如序列编辑与重算）放入后续变更。
