## Context

当前前端工作流编辑器状态：

- **`src/pages/workflow.vue`** (~1076行): 承担顶层布局、Toolbar、手动 Resizer、工作流业务逻辑，所有耦合于单文件
- **布局实现**: 手动监听 `document.mousemove` 调整侧边栏宽度，逻辑约 200 行；`canvas-container` 有 `margin: 16px`，内部 `vue-flow-container` 使用 `position: absolute`，Flex 伸缩时 VueFlow 无法感知尺寸变化
- **侧边栏**: 左固定 `NodePalette`（280px），右固定 `PropertyPanel`（260px）；无文件浏览器的容纳位置
- **组件注册**: `VueFlowCanvas.vue` 用 `nodeTypes: { tool: ToolNode, interactive: InteractiveNode }` — interactive 节点已注册但属性面板无对应分支
- **设计系统**: 无全局 CSS 变量，Component 散落各处直写 `#f5f7fa`, `#409eff`, `#e4e7ed`

已有可复用的基础设施：
- `splitpanes` 库（或可快速安装）
- `useWorkflowStore`（工作流状态）、`useVisualizationStore`（可视化状态 — interactive-visualization 产出）
- `WorkflowService.filesystem*` API（backend-workspace-access 产出）
- `@vue-flow/core` 的 `useVueFlow` 暴露 `fitView`, `setViewport` 用于重置视口

## Goals / Non-Goals

**Goals:**

1. 用 splitpanes + ResizeObserver 取代 `document.mousemove` Resizer，从根本上修复画布偏移问题
2. 实现 VSCode 式 Activity Bar（左图标栏），点击切换 Primary Sidebar 内容（节点工具箱 / 文件浏览器 / 可视化节点列表）
3. 将 `workflow.vue` 拆解为薄层容器，布局逻辑委托给 `WorkflowLayout.vue` + `useWorkflowLayout.ts`
4. 建立全局 CSS 变量设计系统（`design-tokens.css`），统一颜色、圆角、阴影
5. 重设 `ToolNode.vue` 视觉风格（左侧色条 + 12px 圆角 + 轻阴影）
6. `PropertyPanel` 增加节点类型分支，对 interactive 节点渲染 `InteractivePropertyView.vue`
7. 集成后端文件浏览 API，在 Primary Sidebar 中提供 `FileBrowser.vue` 面板

**Non-Goals:**

- 不引入 Tailwind CSS（保持 Vanilla CSS + CSS 变量）
- 不实现暗色模式（设计 Token 预留 CSS 变量但不实现切换逻辑）
- 不重写 `NodePalette` 的搜索/过滤逻辑（视觉更新即可）
- 不改变 VueFlow 核心的节点连接逻辑和数据流（仅改视觉层）
- 不实现 FileBrowser 与画布节点的拖拽联动（第一阶段仅浏览和预览）

## Decisions

### Decision 1: splitpanes 替代 document.mousemove Resizer

**选择**：安装 `splitpanes`（或功能等价的 `vue-resizable-panels`），改造 `editor-row` 水平分割和 `panel-container` 垂直分割

**替代方案**：保留手写 Resizer，修复边界条件

**理由**：
- 手写 Resizer 代码约 200 行（`onPrimaryResizerMouseDown`, `onSecondaryResizerMouseDown`, `onPanelResizerMouseDown`, `onResizerMouseMove`, `onResizerMouseUp`）维护成本高
- splitpanes 体积约 12KB，无额外依赖，原生支持嵌套（水平 + 垂直）
- `pane-resized` 事件触发时机精确，可精准触发 ResizeObserver 回调
- 历史布局尺寸仍通过 `useWorkflowLayout.ts` 持久化到 localStorage（splitpanes 支持初始 `size` prop）

### Decision 2: ResizeObserver 修复 VueFlow 缩放问题

**选择**：在 `VueFlowCanvas.vue` 的 `onMounted` 中，对 `.vue-flow-container` 挂载 `ResizeObserver`，回调中调用 `useVueFlow().fitView({ padding: 0.1 })`

**具体做法**：
```typescript
const containerRef = ref<HTMLElement | null>(null)
const { fitView } = useVueFlow()
let observer: ResizeObserver

onMounted(() => {
  if (containerRef.value) {
    observer = new ResizeObserver(() => {
      nextTick(() => fitView({ padding: 0.1, duration: 0 }))
    })
    observer.observe(containerRef.value)
  }
})

onUnmounted(() => observer?.disconnect())
```

**理由**：
- 根本原因是 VueFlow 内部缓存了初始容器尺寸，flex 伸缩后宽度变化但未通知 VueFlow 更新 viewport matrix
- `fitView` 是最轻量的重计算方式（不会 reset zoom level，只更新原点）
- `duration: 0` 避免动画加剧视觉抖动

### Decision 3: Activity Bar + Primary Sidebar 架构

**选择**：`ActivityBar.vue`（48px 图标栏）+ `PrimarySidebar.vue`（内容面板，宽度可调）

```typescript
// useWorkflowLayout.ts 中的状态
const activePrimaryTab = ref<'palette' | 'files' | 'visualizations' | null>('palette')
const primarySidebarOpen = computed(() => activePrimaryTab.value !== null)

function toggleTab(tab: 'palette' | 'files' | 'visualizations') {
  activePrimaryTab.value = activePrimaryTab.value === tab ? null : tab
}
```

Activity Bar 图标：
| 图标 | tab ID | 面板内容 |
|------|--------|---------|
| ⬡ (Operation) | `palette` | 节点工具箱（NodePalette） |
| 📁 (Folder) | `files` | 工作区文件浏览（FileBrowser） |
| 📊 (DataAnalysis) | `visualizations` | 交互式节点列表（VisualizationList — 后续扩展） |

**替代方案**：两个独立 toggle 按钮（当前方案）

**理由**：
- 符合用户 VSCode 式操作习惯
- 为未来新增面板（如运行历史、调试控制台）提供扩展点，不需改动布局
- `null` 状态表示整个 Primary Sidebar 收起，图标栏依然可见

### Decision 4: ToolNode.vue 视觉重设策略

**选择**：保留 `ToolNode.vue` 组件结构，仅修改 CSS；使用 `--node-color` CSS 变量驱动左侧色条

```css
/* 新的节点卡片基础样式 */
.tool-node {
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--border-subtle, #E2E8F0);
  border-left: 4px solid var(--node-color, #3B82F6);
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}

.tool-node:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  transform: translateY(-1px);
}
```

节点头部：使用 `--node-color` 的 `alpha(0.08)` 透明版本作为头部背景（不再用 `node.data.color` 写死）

**理由**：
- 避免全包围粗边框（视觉笨重）
- 左侧 4px 色条 + 轻阴影是 Linear/Notion/Vercel 等 Modern SaaS 产品的标准节点风格
- 通过 CSS 变量而非内联 style 设置颜色，便于统一管理和后续暗色模式

### Decision 5: PropertyPanel 节点类型分支

**选择**：在 `PropertyPanel.vue` 顶层通过 `executionMode` 路由到两个子视图

```vue
<template>
  <div class="property-panel">
    <template v-if="selectedNode">
      <!-- interactive 节点 → 可视化状态面板 -->
      <InteractivePropertyView
        v-if="selectedNode.executionMode === 'interactive'"
        :node="selectedNode"
      />
      <!-- 处理节点 → 现有参数配置面板 -->
      <ToolPropertyView
        v-else
        :node="selectedNode"
      />
    </template>
    <div v-else class="empty-state">...</div>
  </div>
</template>
```

`InteractivePropertyView.vue` 展示：
- 节点类型徽章（FeatureMap / Spectrum / Table）
- 数据加载状态（loading / error / ready + 行数 / 点数统计）
- 当前选择状态（已选 N 个点/行）
- 导出按钮（触发对应 Viewer 的导出方法）

### Decision 6: FileBrowser 集成

**选择**：`FileBrowser.vue` 作为 PrimarySidebar 的一个面板，通过 `WorkflowService.listWorkspaceFiles()` 加载目录树

目录树使用 Element Plus `<el-tree>` 组件，点击文件触发 `file-preview` 事件，在底部 Panel 区域展示预览内容。

FileBrowser 所需 API 来自 `backend-workspace-access` 变更（`workspace-file-browser` 能力），如该变更未完成则 FileBrowser 显示占位状态（"文件浏览功能需要后端 API 支持"）。

## Risks / Trade-offs

### [Risk] splitpanes 与 VueFlow Controls 定位冲突
- **场景**：VueFlow 内置 Controls（缩放按钮）和 MiniMap 使用 `position: absolute` 相对于 `.vue-flow-container`，切换 splitpanes 可能引起定位异常
- **缓解**：保留 `.vue-flow-container` 的 `position: relative`，移除 `position: absolute` 即可；Controls 和 MiniMap 的 `bottom/left` 定位不受影响

### [Risk] ResizeObserver 回调频率过高
- **场景**：用户快速拖动 splitpanes 分隔线时，每帧触发 `fitView()`
- **缓解**：对 ResizeObserver 回调加 `requestAnimationFrame` 防抖（单帧内最多触发一次），或仅在 `splitpanes` 的 `pane-resized` 事件（拖拽释放时）触发，而非 `ResizeObserver` 持续触发

### [Risk] ActivityBar 宽度占用画布空间
- **场景**：低分辨率屏幕（1280px 以下）时 ActivityBar（48px）+ PrimarySidebar（280px）+ Canvas + PropertyPanel（260px）总宽超出视口
- **缓解**：小于 1280px 时 Secondary（PropertyPanel）默认折叠；小于 1024px 时 PrimarySidebar 默认折叠（仅显示 ActivityBar）

### [Risk] localStorage 持久化 key 继承
- **场景**：当前 `useWorkflowLayout.ts` 需要兼容原有 `tdease-workflow.*` key
- **缓解**：保留相同的 key 前缀，仅新增 `activePrimaryTab` key；迁移时现有宽高数据不丢失
