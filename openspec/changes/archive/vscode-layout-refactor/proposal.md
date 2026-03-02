## Why

当前 workflow.vue 采用单层 flex 横向布局，固定宽度的侧边栏（节点工具箱 280px、属性面板 260-600px、日志面板 340px）在窄屏下严重挤压画布空间，导致几乎无可用工作区域。缺乏折叠和响应式逻辑，无法适配小屏幕设备，影响用户体验和工作效率。

## What Changes

重构 workflow 页面布局为 VS Code 风格的多层 flex 结构：

- **新增 workspace 容器** - 包裹主内容区域，支持垂直 flex 布局
- **新增 editor-row 容器** - 包裹画布和两侧边栏，支持水平 flex 布局
- **重构侧边栏结构** - 将属性面板从 main-content 移出，作为 secondary-sidebar 入驻 editor-row
- **新增 panel-container** - 底部可折叠、可调高度的日志面板容器
- **添加折叠状态管理** - primarySidebarVisible、secondarySidebarVisible、panelVisible 响应式状态
- **实现拖拽调节功能** - 侧边栏宽度拖拽、底部面板高度拖拽
- **添加响应式断点** - 1024px/768px 断点自动折叠侧边栏
- **移除过时的拖拽移动逻辑** - 简化 PropertyPanel 组件，适配侧边栏嵌入

## Capabilities

### New Capabilities
- `collapsible-sidebars`: 左右两侧边栏的折叠/展开功能，支持状态持久化和响应式自动折叠
- `resizable-panels`: 侧边栏宽度和底部面板高度的拖拽调节功能
- `responsive-layout`: 基于屏幕尺寸断点的响应式布局自动调整
- `layout-persistence`: 布局状态（折叠状态、面板尺寸）的本地存储持久化

### Modified Capabilities
*(无现有规范需要修改)*

## Impact

**受影响的文件**:
- `TDEase-Frontend/src/views/workflow.vue` - 模板结构重构、样式重写、状态管理新增
- `TDEase-Frontend/src/components/PropertyPanel.vue` - 移除拖拽移动逻辑，适配侧边栏展示

**新增依赖**:
- 无新增外部依赖（使用现有 Element Plus 图标和 Vue 3 响应式 API）

**用户体验变更**:
- 画布在窄屏下获得更多可用空间
- 侧边栏和面板可按需折叠，提升工作区灵活性
- 布局状态持久化，刷新后保持用户偏好
