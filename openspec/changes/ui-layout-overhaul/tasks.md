## 0. 前置安装

- [ ] 0.1 安装 `splitpanes` 前端布局库：`npm install splitpanes`（在 `TDEase-FrontEnd` 目录）

---

## 1. 全局设计 Token 系统

- [ ] 1.1 创建 `src/assets/design-tokens.css`，定义以下 CSS 变量：
  - 背景：`--bg-workspace: #F8FAFC`，`--bg-panel: #FFFFFF`，`--bg-surface: #F1F5F9`
  - 边框：`--border-subtle: #E2E8F0`，`--border-default: #CBD5E1`
  - 强调色：`--accent-primary: #3B82F6`，`--accent-primary-hover: #2563EB`
  - 节点类型色（色条）：`--node-tool: #3B82F6`，`--node-interactive: #8B5CF6`，`--node-input: #10B981`，`--node-output: #F59E0B`
  - 文字：`--text-primary: #0F172A`，`--text-secondary: #475569`，`--text-muted: #94A3B8`
  - 圆角：`--radius-sm: 6px`，`--radius-md: 12px`，`--radius-lg: 16px`
  - 阴影：`--shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)`，`--shadow-card-hover: 0 4px 12px rgba(0,0,0,0.10)`
- [ ] 1.2 在 `src/main.ts` 中于最顶部引入 `import './assets/design-tokens.css'`

---

## 2. 布局 Composable — useWorkflowLayout

- [ ] 2.1 创建 `src/composables/useWorkflowLayout.ts`，将 `workflow.vue` 中的以下状态迁移至此：
  - `primarySidebarWidth`，`secondarySidebarWidth`，`panelHeight`
  - `primarySidebarVisible`，`secondarySidebarVisible`，`panelVisible`
  - 新增 `activePrimaryTab: Ref<'palette' | 'files' | 'visualizations' | null>`（默认 `'palette'`）
  - `primarySidebarOpen: ComputedRef<boolean>`（= `activePrimaryTab !== null`）
- [ ] 2.2 在 Composable 中实现 `togglePrimaryTab(tab)` 函数（点击已激活 tab → 折叠；点击其他 → 切换）
- [ ] 2.3 将 localStorage 持久化逻辑（`saveLayoutState` / `loadLayoutState`）从 `workflow.vue` 迁移到此 Composable，保留原有 key 前缀 `tdease-workflow.`，新增 `tdease-workflow.activePrimaryTab` key

---

## 3. 顶层布局组件 — WorkflowLayout

- [ ] 3.1 创建 `src/components/layout/WorkflowLayout.vue`：
  - 使用 `<Splitpanes>` 包裹水平方向的三栏（Primary Sidebar | Canvas | Secondary Sidebar）
  - 使用嵌套 `<Splitpanes horizontal>` 包裹垂直方向的（Canvas Row | Bottom Panel）
  - 从 `useWorkflowLayout()` 获取初始 `size` prop 传入各 `<Pane>`
  - 监听 `@pane-resized` 事件，保存宽高并触发 `emitCanvasResized` 事件
- [ ] 3.2 创建 `src/components/layout/ActivityBar.vue`：
  - 固定宽度 48px，`position: relative`，竖排图标按钮
  - 三个图标：Operation（palette）、Folder（files）、DataAnalysis（visualizations）
  - 高亮激活状态（`--accent-primary` 色）；调用 `useWorkflowLayout().togglePrimaryTab()`
- [ ] 3.3 创建 `src/components/layout/PrimarySidebar.vue`：
  - 接受 `activePrimaryTab` prop
  - 通过 `v-if` / `v-show` 切换显示三个面板内容的插槽（`palette`，`files`，`visualizations`）

---

## 4. 重构 workflow.vue

- [ ] 4.1 将 `workflow.vue` 中的所有布局状态、Resizer handler、window resize 监听代码移除（迁移到 `useWorkflowLayout` 和 `WorkflowLayout`）
- [ ] 4.2 `workflow.vue` 改为：顶层 `<div class="workflow-page">` 包含 `WorkflowToolbar` + `WorkflowLayout`，`WorkflowLayout` 通过具名插槽接收 `NodePalette`、`FileBrowser`、`VueFlowCanvas`、`PropertyPanel`、日志底部面板
- [ ] 4.3 保留 `workflow.vue` 中的业务逻辑（`executeWorkflow`, `saveWorkflow`, `createNewWorkflow`, `onContextMenu` 等），通过 `provide` 或 props 传入子组件

---

## 5. VueFlowCanvas — ResizeObserver 修复

- [ ] 5.1 在 `VueFlowCanvas.vue` 中，去除 `.vue-flow-container` 的 `position: absolute; top: 0; left: 0; right: 0; bottom: 0`，改为 `width: 100%; height: 100%`
- [ ] 5.2 去除外层 `.canvas-container` 的 `margin: 16px`（在 `WorkflowLayout` 中通过 padding 或 gap 控制间距）
- [ ] 5.3 在 `VueFlowCanvas.vue` 的 `onMounted` 中挂载 `ResizeObserver`：
  - 观察根 div 元素
  - 回调中通过 `requestAnimationFrame` 调用 `fitView({ padding: 0.05, duration: 0 })`（防抖：同一帧内只执行一次）
- [ ] 5.4 在 `VueFlowCanvas.vue` 的 `onUnmounted` 中调用 `observer.disconnect()`

---

## 6. ToolNode 视觉重设

- [ ] 6.1 修改 `src/components/node/ToolNode.vue` 样式：
  - 替换全包围 `border: 2px solid color` 为 `border: 1px solid var(--border-subtle); border-left: 4px solid var(--node-color, #3B82F6)`
  - 圆角从 `8px` 改为 `var(--radius-md, 12px)`
  - 阴影改为 `var(--shadow-card)`，hover 时改为 `var(--shadow-card-hover)` + `translateY(-1px)`
  - 节点头部背景色改为 `color-mix(in srgb, var(--node-color) 8%, white)`（不再写死 `background-color: node.data.color`）
- [ ] 6.2 在 `VueFlowCanvas.vue` 的节点数据映射（`nodes computed`）中 根据节点类型（`input/output/tool/interactive`）给 `data` 附加 `nodeColor` 字段，`ToolNode` 通过 `:style="{'--node-color': data.nodeColor}"` 消费
- [ ] 6.3 修改 `NodePalette.vue` 中工具项（`.tool-item`）的左侧色条，统一用 CSS 变量替代 inline style

---

## 7. PropertyPanel 节点类型分支

- [ ] 7.1 创建 `src/components/workflow/InteractivePropertyView.vue`：
  - 接受 `node: NodeDefinition` prop
  - 展示：节点类型徽章（FeatureMap / Spectrum / Table）、数据加载状态（通过 `useVisualizationStore()` 获取 `loadingStates[node.id]`）、当前选中点/行数（`nodeSelections[node.id]?.selectedIndices.size`）、"导出 CSV" 按钮（发出 `export` 事件，由父级或 Viewer 处理）
- [ ] 7.2 修改 `PropertyPanel.vue`：顶层增加 `v-if="selectedNode?.executionMode === 'interactive'"` 分支渲染 `InteractivePropertyView`；将现有参数配置部分提取为 `ToolPropertyView`（内部逻辑不变）

---

## 8. FileBrowser 组件

- [ ] 8.1 创建 `src/components/workflow/FileBrowser.vue`：
  - 组件挂载时调用 `WorkflowService.listWorkspaceFiles(userId, workspaceId)` 获取目录树（userId/workspaceId 从 Pinia store 或 inject 获取）
  - 使用 Element Plus `<el-tree>` 展示目录结构，`node-key="path"`
  - 请求失败时显示占位提示："文件浏览需要后端 API 支持，请确保 backend-workspace-access 已部署"
- [ ] 8.2 在 `FileBrowser.vue` 中处理文件点击：调用 `WorkflowService.getFileContent(userId, workspaceId, path, 100)` 获取预览，通过 `provide/inject` 或 emit 将预览内容传递到底部 Panel
- [ ] 8.3 在 `src/services/workflow.ts`（或新增 `src/services/api/workspace-data.ts`）中添加两个 API 方法：
  - `listWorkspaceFiles(userId, workspaceId)` → `GET /api/users/{userId}/workspaces/{workspaceId}/files`
  - `getFileContent(userId, workspaceId, path, maxRows?)` → `GET /api/users/{userId}/workspaces/{workspaceId}/file-content?path=...&max_rows=...`
  - （这两个方法在 backend-workspace-access 完成后才正常工作，组件内需处理请求失败的情况）

---

## 9. 底部面板扩展

- [ ] 9.1 修改底部 Panel（`logs-panel`）：增加 tab 切换机制（"执行日志" / "文件预览"），通过 `provide` 接收 FileBrowser 发来的文件预览内容，切换到"文件预览" tab 展示
- [ ] 9.2 底部 Panel 标题栏统一视觉（高度 36px，背景 `var(--bg-surface)`，边框 `var(--border-subtle)`）

---

## 10. 响应式断点

- [ ] 10.1 在 `useWorkflowLayout.ts` 中恢复 `window.addEventListener('resize', ...)` 逻辑：
  - 宽度 < 1280px 时 Secondary Sidebar（PropertyPanel）自动折叠
  - 宽度 < 1024px 时 Primary Sidebar 折叠（仅保留 ActivityBar）
  - 宽度恢复时还原用户偏好设置
