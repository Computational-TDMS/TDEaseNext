## Context

**当前状态**: workflow.vue 使用单层 flex 横向布局，所有面板（节点工具箱、画布、属性面板、日志面板）平铺在同一行。固定宽度导致窄屏下画布空间被挤压，无折叠或响应式机制。

**约束条件**:
- 使用现有 Vue 3 Composition API 和 Element Plus 组件
- 不引入新的外部依赖
- 保持现有功能（节点选择、属性编辑、日志查看）不受影响
- 确保 Tauri 桌面应用兼容性

**利益相关者**: 前端用户（需要可用工作区）、开发者（维护布局代码）

## Goals / Non-Goals

**Goals:**
- 实现 VS Code 风格的三层 flex 布局结构（toolbar → workspace → editor-row + panel）
- 支持侧边栏和底部面板的折叠/展开，状态持久化到 localStorage
- 实现拖拽调节面板尺寸功能（侧边栏宽度、底部面板高度）
- 添加响应式断点（1024px、768px）自动折叠侧边栏
- 移除 PropertyPanel 的过时拖拽移动逻辑，适配侧边栏嵌入

**Non-Goals:**
- 不实现 VS Code 风格的活动栏（Activity Bar，最左侧的窄图标栏）
- 不支持 Panel 位置切换（底部 ↔ 右侧）
- 不改变现有业务逻辑（节点连接、属性编辑、日志输出）
- 不涉及后端 API 变更

## Decisions

### 1. 布局层级结构

**决策**: 采用三层嵌套 flex 容器

```
workflow-page (flex column, 100vh)
├── toolbar (fixed height)
└── workspace (flex: 1, flex column, overflow: hidden)
    ├── editor-row (flex: 1, flex row, overflow: hidden)
    │   ├── primary-sidebar (节点工具箱, 可折叠)
    │   ├── canvas-container (flex: 1, min-width: 300px)
    │   └── secondary-sidebar (属性面板, 可折叠)
    └── panel-container (底部 Panel, 可折叠, 可调高度)
```

**理由**:
- 分离关注点：toolbar 控制操作、workspace 承载编辑区、panel-container 承载输出区
- flex: 1 确保画布自动填充剩余空间
- overflow: hidden 防止滚动条出现在错误位置

**替代方案**: 单层 grid 布局
- **不采用**: Grid 布局难以实现动态的折叠/展开动画，且不支持 flex: 1 的自动填充

### 2. 状态管理方案

**决策**: 使用 Vue 3 ref + localStorage 持久化

```typescript
const primarySidebarVisible = ref(true)
const secondarySidebarVisible = ref(true)
const panelVisible = ref(true)
const panelHeight = ref(300)
```

**理由**:
- 轻量级，无需引入 Pinia 等状态管理库
- localStorage 持久化简单直接
- 响应式 API 与 Vue 3 深度集成

**替代方案**: Pinia 全局状态
- **不采用**: 布局状态仅 workflow 页面使用，无需全局共享

### 3. 拖拽调节实现

**决策**: 使用原生 mouse 事件 + 状态更新

```typescript
// resizer 逻辑
function onResizerMouseDown(e: MouseEvent, type: 'sidebar' | 'panel') {
  // 记录初始位置和尺寸
  // 添加 window.mousemove 和 window.mouseup 监听
  // 更新对应的状态（sidebarWidth 或 panelHeight）
}
```

**理由**:
- 不依赖第三方拖拽库，减少依赖
- 精确控制拖拽行为（最小/最大尺寸限制）
- 与 Element Plus resizer 组件行为一致

**替代方案**: vue-resizer 等第三方库
- **不采用**: 增加依赖，功能可自行实现

### 4. 响应式断点策略

**决策**: CSS media query + Vue ref 联动

```css
@media (max-width: 1024px) {
  /* 默认折叠右侧属性面板 */
}
@media (max-width: 768px) {
  /* 默认折叠左侧节点工具箱 */
}
```

```typescript
// 监听窗口尺寸，自动更新折叠状态
watch(windowWidth, (newWidth) => {
  if (newWidth < 1024) secondarySidebarVisible.value = false
  if (newWidth < 768) primarySidebarVisible.value = false
})
```

**理由**:
- CSS media query 保证初始加载时布局正确
- Vue ref 监听确保动态调整窗口时状态同步

**替代方案**: 纯 CSS 隐藏/显示
- **不采用**: 无法持久化用户手动展开的状态

### 5. 侧边栏折叠显示策略

**决策**: 折叠时宽度为 0，通过 toolbar 按钮重新展开

```css
.sidebar {
  width: 280px;
  transition: width 0.2s ease;
}
.sidebar.collapsed {
  width: 0;
  overflow: hidden;
}
```

**理由**:
- 完全隐藏节省空间
- 简化实现，无需额外的窄条逻辑
- toolbar 按钮始终可访问

**替代方案**: 折叠时显示 48px 窄条（类似 VS Code）
- **不采用**: 增加复杂度，当前需求不高

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 拖拽调节时性能问题 | 使用 requestAnimationFrame 节流更新 |
| localStorage 存储失败（隐私模式） | 添加 try-catch，降级为内存状态 |
| 响应式断点与用户手动折叠冲突 | 用户手动操作优先，断点仅在初始加载时生效 |
| 画布内容在布局调整时重排 | 使用 CSS will-change 属性优化重排性能 |
| 不同屏幕 DPI 下拖拽位置不准 | 使用 clientX/clientY 而非 screenX/screenY |

## Migration Plan

**部署步骤**:
1. 创建新分支 `feat/vscode-layout`
2. 重构 workflow.vue 模板结构（先结构，后样式）
3. 添加响应式状态和 localStorage 逻辑
4. 实现拖拽调节功能
5. 添加响应式断点和 media query
6. 简化 PropertyPanel 组件
7. 测试各屏幕尺寸下的布局表现
8. 提交 PR 并合并

**回滚策略**:
- 使用 Git 分支隔离，可随时回退到重构前
- localStorage 新增前缀（如 `vscode-layout-`），不影响旧存储

## Open Questions

1. **侧边栏最小/最大宽度限制** - 建议最小 200px，最大 500px
2. **底部面板高度范围** - 建议最小 150px，最大 60% 视口高度
3. **是否需要"重置布局"按钮** - 可选增强，建议第二期实现
