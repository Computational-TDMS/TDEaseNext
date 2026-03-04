# Proposal: UI Layout Overhaul — Unified Sidebar & Modern Workflow Canvas

## Why

当前前端工作流编辑器存在以下核心体验问题：

1. **布局架构混乱**：`workflow.vue` 超过 1000 行，同时处理布局状态、持久化、事件绑定和业务逻辑，手动实现的 Resizer（`document.mousemove` 监听）在面板伸缩时频繁导致画布坐标偏移和缩放计算错误。
2. **侧边栏功能割裂**：左侧节点工具箱（NodePalette）和右侧属性面板（PropertyPanel）是独立存在的抽屉，"后端工作区文件浏览器"作为新功能没有预定位置。随着交互式可视化节点的加入，属性面板也需要区分处理节点（参数配置）和可视化节点（数据状态/导出），侧边栏管理将失控。
3. **VSCode 模式缺失**：用户希望像 VSCode 一样通过图标栏点击切换左侧面板内容（工具箱 / 文件浏览器 / 可视化节点列表），而不是固定宽度的单一面板。
4. **节点视觉陈旧**：节点使用全包围彩色边框（`border: 2px solid color`）、偏小圆角和平淡阴影，缺乏专业 SaaS 工具风格。画布背景为纯白，与整页背景区分不明显。
5. **缩放/坐标问题根源**：`canvas-container` 的 `margin: 16px` + 内部 `position: absolute` 的 VueFlow 容器组合，导致面板拖拽时画布宽度计算错误，VueFlow 无法感知容器尺寸变化。

此变更旨在彻底重构前端布局骨架，为当前的工作流编辑能力以及即将落地的交互式可视化节点提供一个清晰、高性能、视觉专业的基础。

## What Changes

### 1. VSCode 式三区布局替换扁平 Flex 布局

```
┌────────────────────────────────────────────────────────────┐
│ Toolbar (固定高度 48px)                                     │
├──────┬─── Activity Bar ──┬──────────────────────┬──────────┤
│      │ [工具箱图标]      │                      │          │
│ L    │ [文件浏览图标]    │    Vue Flow Canvas   │ Property │
│ e    │ [可视化节点图标]  │    (flex: 1, 无margin)│  Panel   │
│ f    ├───────────────────┤    (ResizeObserver   │(按节点类型│
│ t    │                   │     自动触发 fitView) │ 切换内容) │
│      │  Primary Sidebar  │                      │          │
│ S    │  (按点击切换内容) │                      │          │
│ i    │  - NodePalette    ├──────────────────────┘          │
│ d    │  - FileBrowser    │  Bottom Panel (Logs/Terminal)   │
│ e    │  - VisualizList   │  (splitpanes 驱动)              │
│      │                   │                                 │
└──────┴───────────────────┴─────────────────────────────────┘
```

- **Activity Bar（最左侧图标栏）**: 宽 48px 固定，仅含图标，点击切换左侧面板内容
- **Primary Sidebar（左侧内容面板）**: 可折叠，内容视激活图标显示不同组件
- **Canvas（中心）**: 取消 `margin`，直接 flex 充满，配合 `ResizeObserver` 确保 VueFlow 感知尺寸变化
- **Property Panel（右侧）**: 保持可折叠，内容根据选中节点类型自动切换（`ToolNode` → 参数面板；`InteractiveNode` → 可视化状态/导出面板）

### 2. Splitpanes 替换手搓 Resizer

引入 `splitpanes` 库（~12KB），替换现有约 200 行的手动 `document.mousemove` Resizer 代码。

- 主轴（水平）：Left Sidebar | Canvas | Property Panel
- 次轴（垂直）：Canvas Row | Bottom Panel
- Splitpanes 的 `pane-resized` 事件触发 `ResizeObserver`，通知 VueFlow 重新计算

### 3. 修复画布缩放根本原因

- 去除 `.canvas-container` 的 `margin: 16px`
- `.vue-flow-container` 改为 `width: 100%; height: 100%`（去掉 `position: absolute`）
- 挂载 `ResizeObserver` 于 `.canvas-container`，回调中调用 VueFlow 的 `fitView()` 或重置视口原点

### 4. 全局设计 Token & 节点视觉重设

引入 CSS 变量设计系统（不引入 Tailwind），统一颜色规范：

- **全局背景**: `--bg-workspace: #F8FAFC`
- **面板背景**: `--bg-panel: #FFFFFF`
- **边框**: `--border-subtle: #E2E8F0`
- **强调色**: `--accent-primary: #3B82F6`（蓝）
- **节点类型色条**（左侧 border-left 4px 替代全包围 border）：
  - 处理工具节点: `--node-tool: #3B82F6`
  - 交互式可视化节点: `--node-interactive: #8B5CF6`
  - 输入节点: `--node-input: #10B981`
  - 输出节点: `--node-output: #F59E0B`
- **节点样式**: 白底卡片，`border-radius: 12px`，轻弥散阴影，左侧 4px 彩色条

### 5. 右侧属性面板：区分节点类型

`PropertyPanel.vue` 内部通过 `selectedNode.executionMode` 决定渲染哪个子视图：
- `executionMode !== 'interactive'` → 现有的参数配置表单（保留）
- `executionMode === 'interactive'` → 新的 `InteractivePropertyView.vue`（数据加载状态 + 导出按钮 + 选择统计）

## Capabilities

### New Capabilities

- **`workflow-layout-engine`**: VSCode 式布局管理
  - Activity Bar + Primary Sidebar 多面板切换
  - splitpanes 驱动的自适应布局
  - ResizeObserver 感知画布尺寸变化并通知 VueFlow

- **`file-browser-sidebar`**: 工作区文件浏览面板
  - 集成到 Primary Sidebar 的"文件浏览"标签页
  - 调用 `workspace-file-browser` 能力获取目录树
  - 点击文件可在底部 Panel 或弹窗预览

- **`design-token-system`**: 全局设计变量
  - CSS 变量统一颜色、间距、圆角
  - 节点类型色彩系统

### Modified Capabilities

- **`interactive-visualization-nodes`**: 交互式节点属性面板适配
  - 右侧 PropertyPanel 对 interactive 节点展示独立的 `InteractivePropertyView`

## Impact

### 前端代码（新增）
- `src/components/layout/WorkflowLayout.vue` — 顶层布局容器
- `src/components/layout/ActivityBar.vue` — 左侧图标导航栏
- `src/components/layout/PrimarySidebar.vue` — 左侧滑动面板（内含插槽）
- `src/components/workflow/FileBrowser.vue` — 工作区文件浏览组件
- `src/components/workflow/InteractivePropertyView.vue` — 交互式节点属性视图
- `src/composables/useWorkflowLayout.ts` — 布局状态 Composable（宽高 + 折叠 + 持久化）
- `src/assets/design-tokens.css` — 全局 CSS 变量Token

### 前端代码（修改）
- `src/pages/workflow.vue` — 拆解为薄层容器，布局逻辑委托给 WorkflowLayout
- `src/components/workflow/VueFlowCanvas.vue` — 去除 `position:absolute`，挂载 ResizeObserver
- `src/components/workflow/ToolNode.vue` — 重设节点视觉（左侧色条 + 轻阴影 + 12px 圆角）
- `src/components/workflow/NodePalette.vue` — 迁移到 PrimarySidebar 插槽
- `src/components/workflow/PropertyPanel.vue` — 增加节点类型判断分支
- `src/main.ts` — 引入 design-tokens.css

### 依赖
- 新增 `splitpanes` (布局分割)
- 依赖 `backend-workspace-access` 变更的文件浏览 API（FileBrowser 组件）
- 与 `interactive-visualization` 变更并行（PropertyPanel 分支可先占位）
