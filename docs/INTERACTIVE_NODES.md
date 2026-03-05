# 交互式可视化节点 - 用户指南

**更新日期**: 2025-03-05
**版本**: 1.0

## 目录

- [快速开始](#快速开始)
- [节点类型](#节点类型)
- [创建交互式工作流](#创建交互式工作流)
- [配置可视化参数](#配置可视化参数)
- [交叉过滤](#交叉过滤)
- [常见问题](#常见问题)

---

## 快速开始

### 什么是交互式可视化节点？

**交互式可视化节点**（Interactive View Nodes）是一类特殊节点，它们：
- ✅ **不在后端执行**，仅在前端渲染数据
- ✅ **支持实时交互**：画刷选择、缩放、过滤
- ✅ **自动跨表过滤**：选择特征 → 质谱/表格自动更新
- ✅ **可视化配置**：X/Y 轴映射、颜色、大小等

### 支持的查看器类型

| 查看器 | 用途 | 输入数据类型 |
|--------|------|--------------|
| **Feature Map Viewer** | MS1 特征散点图 | `.feature`, `.ms1ft` |
| **Spectrum Viewer** | MS2 质谱图 | `.ms2`, `.msalign` |
| **Table Viewer** | 结果表格 | `.tsv`, `.csv`, `.prsm` |
| **HTML Viewer** | PrSM 序列可视化 | `_html` 目录 |

---

## 节点类型

### 计算节点 vs 视图节点

**计算节点**（Compute Nodes）:
- 图标：蓝色背景
- 执行模式：后端实际运行工具
- 示例：TopFD, TopPIC, ProMex, MSPathFinder

**视图节点**（View Nodes）:
- 图标：橙色/绿色边框
- 执行模式：跳过后端执行
- 示例：Feature Map, Spectrum, Table, HTML Viewer

### 如何识别？

在节点编辑器中：
- **实线蓝边** = 数据流（文件传递）
- **虚线橙边** = 状态流（选择事件）

---

## 创建交互式工作流

### 步骤 1: 创建工作流

1. 点击 **"New Workflow"**
2. 输入名称（例如："MS1 分析 + 可视化"）
3. 点击 **"Create"**

### 步骤 2: 添加计算节点

1. 从左侧工具面板拖拽 **TopFD** 到画布
2. 配置参数：
   - Thread Number: `1`
   - Activation: `21.0`
3. 连接输入数据文件

### 步骤 3: 添加交互式查看器

1. 拖拽 **Feature Map Viewer** 到画布
2. 连接 TopFD 的 `ms1feature` 输出 → Feature Map 的 `feature_data` 输入
3. **注意**：这是**数据流**（实线蓝边）

### 步骤 4: 连接状态流（交叉过滤）

1. 添加 **Spectrum Viewer**
2. 连接 TopFD 的 `ms2feature` 输出 → Spectrum 的 `spectrum_data` 输入（数据流）
3. **关键步骤**：连接 Feature Map 的 `selection_out` → Spectrum 的 `selection_in`（状态流，虚线橙边）

### 步骤 5: 执行工作流

1. 点击 **"Execute"** 或 **"Run"**
2. 观察：
   - TopFD 节点状态：`running` → `completed`
   - Feature Map 节点状态：`skipped`（正常！）
   - Spectrum 节点状态：`skipped`（正常！）

### 步骤 6: 交互探索

1. 双击 **Feature Map** 节点打开配置面板
2. 配置轴映射：
   - X 轴：选择 `RT`（保留时间）
   - Y 轴：选择 `MZ`（质荷比）
   - 颜色：选择 `Intensity`（强度）
3. 点击 **"Apply"**
4. 在散点图上**画刷选择**一些点
5. 观察 **Spectrum Viewer** 自动高亮匹配的质谱峰

---

## 配置可视化参数

### 打开配置面板

**方法 1**: 双击交互节点
**方法 2**: 右键点击节点 → "Configure"

### Feature Map Viewer 配置

**轴映射**:
- **X Axis**: 选择数值列（RT, MZ, Mass, Intensity）
- **Y Axis**: 选择数值列
- **Color**: 颜色映射列（可选）
- **Size**: 点大小列（可选）

**外观**:
- **Color Scheme**: Viridis, Plasma, Inferno, Magma
- **Show Labels**: 显示/隐藏标签
- **Max Features**: 最大特征数（性能优化）

### Spectrum Viewer 配置

**自动配置**:
- Spectrum Viewer 会自动从上游节点接收选择事件
- 无需手动配置轴映射

**手动选项**:
- Peak Annotation: 显示峰注释
- Zoom Level: 缩放级别
- Export: 导出 PNG/SVG

### Table Viewer 配置

**列映射**: 自动检测，无需手动配置

**选项**:
- Virtual Scrolling: 虚拟滚动（处理大数据集）
- Sort: 列排序
- Filter: 列过滤
- Export: 导出 CSV

### HTML Viewer 配置

**自动配置**:
- HTML Viewer 会自动从 TopPIC 节点加载 HTML 片段
- 通过 Feature Map 选择触发

**安全**:
- iframe sandbox 隔离
- 防止 XSS 攻击

---

## 交叉过滤

### 什么是交叉过滤？

**交叉过滤**（Cross-Filtering）是一种交互式数据分析技术，通过在一个视图中的选择自动过滤其他连接的视图。

### TDEase 中的实现

**示例 1: MS1 特征 → MS2 质谱**

```
TopFD → FeatureMap --[state: selection]→ SpectrumViewer
         (用户画刷)      (自动高亮匹配峰)
```

**操作流程**:
1. 在 Feature Map 中画刷选择 5 个特征点
2. StateBus 发送 `state/selection_ids` 事件（包含行索引：0, 5, 12, 23, 45）
3. Spectrum Viewer 接收事件
4. 查询 `/api/nodes/{node_id}/data/rows?row_ids=0,5,12,23,45`
5. 高亮显示对应的 5 个质谱峰

**示例 2: 特征 → PrSM HTML**

```
TopPIC → HTMLViewer
         ↑
FeatureMap --[state: selection]--
  (用户点击)
```

**操作流程**:
1. 用户在 Feature Map 点击某个特征点（行索引 12）
2. HTML Viewer 接收选择事件
3. 查询 `/api/nodes/{node_id}/html/12`
4. 显示该特征的 PrSM 序列可视化

### 创建状态连接

**步骤**:
1. 确保两个交互节点都在画布上
2. 从源节点的**状态输出端口**（`selection_out`）拖拽到目标节点的**状态输入端口**（`selection_in`）
3. 边会显示为**虚线橙色**

**验证**:
- 鼠标悬停在边上，应显示 "State" 或 "Selection"
- 边的样式为虚线（`stroke-dasharray: 5,5`）
- 事件触发时，边会有动画流指示器

---

## 常见问题

### Q1: 为什么我的交互节点显示 "Awaiting data"？

**A**: 节点未连接到上游计算节点，或上游节点尚未执行。

**解决方法**:
1. 检查数据流连接（实线蓝边）
2. 执行上游计算节点
3. 刷新页面

### Q2: 配置面板下拉列表为空？

**A**: 上游节点的输出文件不存在，或没有定义 Schema。

**解决方法**:
1. 执行上游计算节点生成文件
2. 检查工具定义是否包含 `schema` 字段
3. 查看 `/api/nodes/{node_id}/data/schema` 是否返回列定义

### Q3: 交叉过滤不工作？

**A**: 状态连接未正确建立，或 StateBus 未订阅。

**解决方法**:
1. 验证是否为**状态流**连接（虚线橙边）
2. 检查端口类型：`selection_out` → `selection_in`
3. 打开浏览器控制台，检查 StateBus 事件日志
4. 刷新页面重试

### Q4: HTML Viewer 显示 "HTML fragment not found"？

**A**: TopPIC 未生成 HTML 文件，或行索引超出范围。

**解决方法**:
1. 检查 TopPIC 是否设置了 `-g` (skip html)
2. 验证 TopPIC 执行成功
3. 确认选择的特征点在数据范围内

### Q5: 性能问题（卡顿、慢）？

**A**: 数据集太大，或缓存未启用。

**优化方法**:
1. 减少 Max Features 限制（默认 1000）
2. 启用 Virtual Scrolling（Table Viewer）
3. 清除浏览器缓存
4. 检查网络请求：`/api/nodes/{node_id}/data/rows`

### Q6: 如何保存配置？

**A**: 配置会自动持久化到工作流文件中。

**操作**:
1. 双击节点打开配置
2. 修改轴映射、外观等
3. 点击 **"Apply"**
4. 保存工作流（自动保存或手动 Save）

**验证**:
- 重新加载工作流
- 双击节点，确认配置保留

---

## 高级技巧

### 技巧 1: 多级交叉过滤

可以创建**级联过滤**：

```
FeatureMap --[state]--> SpectrumViewer --[state]--> TableViewer
     (选10个)            (过滤到5个)              (显示5行)
```

### 技巧 2: 组合视图

在同一工作流中连接多个查看器：

```
TopFD → FeatureMap ┬→ SpectrumViewer
        (散点图)    └→ TableViewer
        (选特征)      (显示表格)
```

### 技巧 3: 自定义默认映射

编辑工具定义文件 `config/tools/featuremap_viewer.json`：

```json
{
  "defaultMapping": {
    "x": "rt",      // 默认 X 轴
    "y": "mz",      // 默认 Y 轴
    "color": "intensity"  // 默认颜色
  }
}
```

### 技巧 4: 键盘快捷键

- **双击节点**: 打开配置
- **ESC**: 关闭配置面板
- **Ctrl+S**: 保存工作流
- **Ctrl+Z**: 撤销（如果实现）

---

## API 参考

### 获取节点数据 Schema

```bash
GET /api/executions/{execution_id}/nodes/{node_id}/data/schema
```

**响应**:
```json
{
  "schema": [
    {"id": "RT", "type": "number", "name": "Retention Time"},
    {"id": "MZ", "type": "number", "name": "Mass-to-Charge"}
  ]
}
```

### 获取数据行（过滤）

```bash
GET /api/executions/{execution_id}/nodes/{node_id}/data/rows?row_ids=0,5,12
```

**响应**:
```json
{
  "rows": [
    {"RT": 45.2, "MZ": 1234.5, "Intensity": 1000000},
    {"RT": 52.1, "MZ": 1456.7, "Intensity": 500000}
  ]
}
```

### 获取 HTML 片段

```bash
GET /api/executions/{execution_id}/nodes/{node_id}/html/{row_id}
```

**响应**:
```json
{
  "row_id": 0,
  "html": "<html>...</html>",
  "exists": true
}
```

---

## 视频教程

### 教程 1: 创建第一个交互式工作流（5 分钟）

1. 创建工作流
2. 添加 TopFD + FeatureMap
3. 执行并探索数据
4. 保存和加载工作流

### 教程 2: 交叉过滤实战（8 分钟）

1. 构建 TopFD → FeatureMap → Spectrum 链条
2. 创建状态连接
3. 测试画刷选择
4. 验证质谱峰高亮

### 教程 3: 高级配置（10 分钟）

1. 自定义轴映射
2. 配置颜色方案
3. 添加多个查看器
4. 性能优化技巧

（视频教程即将添加到文档）

---

## 反馈与支持

**问题反馈**:
- GitHub Issues: [TDEase Issues](https://github.com/your-org/TDEase-Backend/issues)
- 标签: `interactive-viz`, `frontend`

**功能请求**:
- 在 Issues 中使用标签 `enhancement`
- 描述使用场景和期望行为

**文档贡献**:
- 欢迎 PR 改进文档
- 添加更多使用示例
- 翻译成其他语言

---

*最后更新: 2025-03-05*
