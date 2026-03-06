# TOPMSV 可视化系统架构详解

## 一、系统概述

TopMSV (Top-down MS Viewer) 是一个基于 Web 的自上而下质谱数据可视化工具，用于探索 LC-MS/MS 数据、谱图、反卷积结果和蛋白质形式识别结果。

### 技术栈
- **后端**: Node.js + Express.js + C++
- **前端**: JavaScript + D3.js (2D视图) + Three.js (3D视图)
- **数据格式**: mzML, msalign, mzrt.csv, TSV

---

## 二、交互逻辑

### 2.1 四大可视化视图

#### 1. 总离子色谱图 (TIC)
- **X轴**: 保留时间 (分钟)
- **Y轴**: 所有峰强度之和
- **交互**:
  - 鼠标点击选择保留时间
  - 输入扫描号跳转到特定扫描
  - 显示当前选择的扫描位置

#### 2. LC-MS 3D 视图
- **X轴**: m/z 值
- **Y轴**: 保留时间
- **Z轴**: 峰强度
- **交互操作**:
  - **拖拽**: 左键拖动视图
  - **缩放**: 鼠标滚轮 (整体/分别缩放 m/z 或 RT)
  - **强度缩放**: CTRL + 鼠标滚轮
  - **旋转**: 右键拖动
  - **定位**: 输入特定 m/z 和 RT 值
- **视图设置**:
  - 强度截断阈值
  - 自动强度缩放
  - 高亮当前扫描 (粉色线)
- **功能**:
  - 保存图像
  - 调整视图大小
  - 全屏显示
  - 显示特征区域 (虚线矩形)

#### 3. 质谱图 2D 视图
- **上部**: MS1 谱图
- **下部**: MS/MS 谱图
- **交互**:
  - 拖拽移动视图
  - X轴缩放 (鼠标在X轴下方)
  - 峰强度缩放 (鼠标在X轴上方)
  - 前一个/后一个 MS1 谱图
  - 选择 MS/MS 谱图 (点击前体离子 m/z)
- **特征**: 显示理论同位素包络 (彩色圆圈)

#### 4. 单同位素质量图
- **上部**: 识别的蛋白质形式序列和理论碎片质量
- **中部**: MS/MS 谱图的反卷积单同位素质量
- **下部**: 匹配的理论和实验质量间的 m/z 误差图
- **交互**:
  - 拖拽、缩放、强度缩放
  - 编辑蛋白质序列
  - 提交查看谱图与序列的匹配

### 2.2 页面导航逻辑

```
主页面 (proteins.html)
    ↓
蛋白质列表
    ↓
选择蛋白质 → protein.html
    ↓
PRSM 列表 → prsm.html
    ↓
选择 PRSM → inspect/spectrum.html
    ↓
详细检查页面
```

**URL 参数传递**:
- `folder`: 数据文件夹路径
- `protein_Id`: 蛋白质 ID
- `prsm_seq_num`: PRSM 序列号

---

## 三、实现逻辑

### 3.1 HTML 文件夹结构

```
topmsv/
├── visual/              # 主要可视化页面
│   ├── prsm.html       # PRSM 可视化主页面
│   ├── protein.html    # 蛋白质页面
│   ├── proteins.html   # 蛋白质列表页面
│   └── ms.html         # 质谱识别页面
├── inspect/            # 谱图检查页面
│   ├── spectrum.html
│   └── spectrum_no_nav.html
└── common/             # 共享组件和库
    ├── prsm_view/      # PRSM 可视化核心组件
    ├── spectrum_view/  # 谱图可视化组件
    └── lib/            # 第三方库 (D3.js, Three.js)
```

### 3.2 数据加载机制

#### 动态脚本加载
```javascript
let prsm_data_file_name = "../data/" + folder_path + "/prsms/prsm" + prsm_seq_num + ".js";
prsm_data_script.src = prsm_data_file_name;
head.appendChild(prsm_data_script);
```

#### 数据文件格式
数据以 JavaScript 变量形式存储:
```javascript
var prsm_data = [
  // PRSM 对象数组
  {
    spectrum: { /* 谱图数据 */ },
    sequence: { /* 序列数据 */ },
    peaks: [ /* 峰数据 */ ]
  }
];
```

#### 页面间数据传递
使用 HTML5 localStorage:
```javascript
// 存储数据
window.localStorage.setItem('peakAndIntensityList', JSON.stringify(peakAndIntensityList));
window.localStorage.setItem('massAndIntensityList', JSON.stringify(massAndIntensityList));
window.localStorage.setItem('sequence', JSON.stringify(sequence));

// 读取数据
let peaks = JSON.parse(window.localStorage.getItem('peakAndIntensityList'));
```

### 3.3 核心可视化组件

#### PrsmView 类
- **职责**: 绘制 PRSM 序列图谱
- **方法**: `redraw()` - 重新绘制可视化

#### SpectrumView 类
- **职责**: 绘制质谱图
- **方法**: `redraw()` - 更新谱图显示

#### DataTable 类
- **职责**: 创建峰数据表格
- **数据**: 匹配的质量列表

### 3.4 数据渲染流程

```
1. 数据解析
   ParsePrsm 类解析原始 JavaScript 数据

2. HTML 构建
   loadDatafromJson2Html() 填充页面信息

3. 可视化渲染
   调用各组件的 redraw() 方法
```

---

## 四、数据与数据流

### 4.1 数据生成流程 (TopPIC Suite)

```
原始数据 (mzML)
    ↓
TopFD (反卷积)
    ↓
msalign 文件 (MS1/MS2 反卷积结果)
mzrt.csv 文件 (LC-MS 特征)
    ↓
TopPIC (识别)
    ↓
TSV 文件 (PrSM 结果)
    ↓
XML 生成 (XmlGenerator)
    ↓
JSON 转换 (jsonTranslate)
    ↓
JavaScript 文件 (prsm_data = [...])
    ↓
HTML 可视化 (TopMSV)
```

### 4.2 数据文件类型

#### 输入数据
1. **mzML 文件**: LC-MS/MS 原始数据
2. **FASTA 文件**: 蛋白质序列数据库
3. **PTM 文件**: 常见翻译后修饰定义

#### 中间数据
1. **msalign 文件**:
   - `*_ms1.msalign`: MS1 反卷积结果
   - `*_ms2.msalign`: MS/MS 反卷积结果

2. **mzrt.csv 文件**: LC-MS 图中的蛋白质形式特征

3. **TSV 文件**: 蛋白质形式-谱图匹配 (PrSM) 结果

#### 输出数据
1. **JavaScript 文件**: 包含 `prsm_data` 变量
2. **HTML 文件**: 可视化页面
3. **Web 资源**: TopMSV 可视化库

### 4.3 数据结构示例

#### PRSM 数据结构
```javascript
{
  prsm_id: "唯一标识",
  spectrum_id: "谱图ID",
  protein_id: "蛋白质ID",
  sequence: "蛋白质序列",
  modifications: [
    { position: 10, type: "Acetylation", mass: 42.01 }
  ],
  peaks: [
    { mass: 1234.56, intensity: 1000, type: "theoretical" },
    { mass: 1234.58, intensity: 950, type: "experimental" }
  ],
  mass_errors: [
    { mass: 1234.56, error: 0.02 }
  ]
}
```

#### 谱图数据结构
```javascript
{
  scan_num: 12345,
  precursor_mz: 567.89,
  retention_time: 12.34,
  peaks: [
    { mz: 100.0, intensity: 500 },
    { mz: 200.0, intensity: 1000 }
  ]
}
```

### 4.4 数据传输机制

```
C++ 后端
    ↓ 生成
XML 格式结构化数据
    ↓ 转换
JavaScript 对象 (JSON)
    ↓ 加载
前端 JavaScript
    ↓ 渲染
交互式可视化界面
    ↓ 传递
localStorage (页面间通信)
```

---

## 五、复刻 TOPMSV 的建议

### 5.1 最小化文件集

核心必需文件:
```
prsm_view/          # PRSM 可视化核心
spectrum_view/      # 谱图可视化
parse_json/         # 数据解析器
数据类文件:
  - peak.js         # 峰数据类
  - spectrum.js     # 谱图数据类
  - prsm.js         # PRSM 数据类
```

### 5.2 数据适配策略

创建数据适配器将你的数据转换为 TopMSV 格式:

1. **PRSM 数据结构适配**
   - 质谱识别结果
   - 谱图数据
   - 序列和修饰信息

2. **数据转换模块**
   ```javascript
   function adaptToTopMSVFormat(yourData) {
     return {
       prsm_data: [/* 转换后的 PRSM 数据 */],
       spectrum_data: [/* 转换后的谱图数据 */],
       sequence_data: [/* 转换后的序列数据 */]
     };
   }
   ```

### 5.3 独立部署步骤

1. **移除 TopMSV 特定依赖**
   - 导航栏组件
   - 服务器端 API 调用
   - 项目管理功能

2. **简化数据加载**
   - 使用 AJAX/Fetch API 替代动态脚本加载
   - 实现数据适配层

3. **自定义可视化**
   - 保留核心可视化组件 (PrsmView, SpectrumView)
   - 自定义样式和交互
   - 集成到现有系统

### 5.4 集成示例

```javascript
// 在你的 Vue/React 组件中集成
import { PrsmView, SpectrumView } from './topmsv/components';

function YourVisualization({ data }) {
  const adaptedData = adaptToTopMSVFormat(data);

  return (
    <div>
      <PrsmView data={adaptedData.prsm_data} />
      <SpectrumView data={adaptedData.spectrum_data} />
    </div>
  );
}
```

---

## 六、关键要点

### 优势
- ✅ 模块化设计，组件可独立使用
- ✅ 数据文件为 JavaScript 变量，便于直接加载
- ✅ 支持多种页面类型，可根据需求选择
- ✅ localStorage 机制适用于单页面应用

### 注意事项
- ⚠️ 数据格式特定于 TopPIC Suite
- ⚠️ 需要适配层集成自定义数据
- ⚠️ 可视化组件依赖于 D3.js 和 Three.js
- ⚠️ 页面导航依赖 URL 参数

### 扩展可能
- 添加自定义可视化类型
- 集成机器学习辅助分析
- 支持实时数据更新
- 添加协作和注释功能
