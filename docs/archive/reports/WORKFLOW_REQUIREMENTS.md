# TDEase 交互式工作流需求

**文档目的**: 清晰描述用户的工作流交互目标，为架构设计提供需求输入

---

## 核心交互流程

### 流程 1: MS1 特征探索

**输入**: MS1 特征文件（ms1feature）

**步骤**:
1. 在 FeatureMap 节点中展示数据
   - 数据维度: mass, intensity, start_time, end_time
   - 可视化: 二维散点/热力图
   - 映射关系:
     - X轴: start_time / end_time (保留时间)
     - Y轴: mass (质荷比)
     - 颜色: intensity (强度)

2. 用户框选感兴趣的区域

3. 框选结果投影到 Spectrum 节点
   - 映射关系:
     - mass → m/z (X轴)
     - intensity → intensity (Y轴)
   - 注: 不同点的质量一般不重叠，直接映射即可，无需积分

---

### 流程 2: 修饰识别与标注

**输入**: FeatureMap + Spectrum 的选择状态

**步骤**:
1. 用户在 Spectrum 节点中进一步框选特定的峰

2. Table 节点基于选中的峰进行修饰匹配
   - 数据源: ms1feature 中的其他峰
   - 参考信息: 用户提供的修饰库（Unimod 或其他格式）
   - 匹配规则:
     - ppm (质量误差)
     - isotopic shift (同位素位移)

   - 在 Spectrum 上标注识别出的修饰
   - 在 Table 中展示匹配结果详情

---

### 流程 3: MS2 数据关联

**输入**: TOPPIC MS2 分析结果

**数据文件**:
- `sample_ms2_toppic_proteoform.tsv`
- `sample_ms2_toppic_prsm.tsv`
- 对应的 `_html` 文件（包含二级图谱和修饰序列）

**步骤**:
1. 通过 featureID 找到对应的 PrSM ID

2. 从 HTML 文件中提取:
   - 二级谱图（MS2 spectrum）
   - 修饰序列信息

3. 在可视化节点中展示:
   - MS2 谱图
   - 肽段序列和修饰位置

4. 用户交互:
   - 点击或框选 MS1 特征
   - 自动关联并展示对应的 MS2 信息

---

## 参考工具设计

### LCMS-Spectator 的功能

**处理 ProMex 输出**:
- 读取 `.ms1ft` 特征文件
- 必需字段: MonoMass, Abundance, Envelope, MinCharge, MaxCharge, MinScan, MaxScan
- 将特征组织成特征点，关联到 MS/MS 谱图

**处理 MSPathFinder 输出**:
- 读取 TSV 或 ZIP 格式结果文件
- 必需字段: #MatchedFragments, ProteinName, Modifications, Sequence, Scan, Charge, QValue
- 目标/诱饵库结果（IcTarget.tsv, IcDecoy.tsv, IcTda.tsv）

**数据关联**:
- ProMex 特征通过 MinScan/MaxScan 关联到 MS/MS 谱图
- MSPathFinder 的肽段识别通过质量容差匹配到特征
- 可视化: XIC 图、误差图、序列图

**交互能力**:
- 点击特征查看详细信息
- 框选区域批量操作
- 关联 MS/MS 谱图自动显示

### Informed Proteomics 工具链

**PBFGen**:
- 输入: 原始质谱文件（.raw, .mzML, etc.）
- 输出: .pbf 文件（优化访问速度的二进制格式）
- 功能: 提取 MS1 和 MSn 的 Full XIC（提取离子色谱图）

**ProMex**:
- 输入: .pbf 文件
- 输出: .ms1ft 文件（MS1 特征）
- 功能: 检测蛋白质离子的同位素包络

**MSPathFinder**:
- 输入: .pbf + .ms1ft + 蛋白质数据库
- 输出: PrSM 结果（.tsv + .mzid）
- 功能: 蛋白质级别的数据库搜索

---

## 已大致实现的基础能力

根据 `openspec/changes/interactive-visualization/`，项目已完成:

✅ **三种基础可视化节点**:
- FeatureMapViewer: 散点图显示
- SpectrumViewer: 质谱图显示
- TableViewer: 表格显示

✅ **交互能力**:
- 框选、点击选择
- 节点间状态传递（前端零延迟）
- 数据导出

✅ **数据流**:
- 处理节点 → 交互式节点: API 加载文件数据
- 交互式节点 → 交互式节点: 前端状态传播

---

## 待实现的核心功能

### 1. 修饰匹配系统
- 修饰库加载（Unimod 格式）
- ppm / isotopic shift 匹配算法
- Spectrum 上的修饰标注
- 匹配结果展示

### 2. MS2 数据支持
- PrSM 数据解析
- MS2 谱图加载和展示
- featureID ↔ PrSM ID 关联
- HTML 文件解析（序列和修饰）

### 3. 质谱特定格式支持
- `.ms1ft` 文件解析
- MSPathFinder TSV 解析
- 特征 ↔ 谱图关联逻辑

### 4. 高级可视化
- XIC 图（提取离子色谱图）
- 误差图（质量误差分布）
- 序列图（肽段序列覆盖）

- ? 这中间细节的交互该如何进行设计?


---

## 设计参考点

### 数据流设计

**ProMex → MSPathFinder → 可视化**:
```
ProMex 特征 (.ms1ft)
  ↓ (通过 MinScan/MaxScan)
MS/MS 谱图
  ↓ (MSPathFinder 搜索)
PrSM 结果
  ↓ (质量容差匹配)
特征-肽段关联
  ↓
可视化展示
```

**节点间交互**:
```
[FeatureMap] --框选--> [Spectrum] --框选峰--> [修饰匹配] --> [Table + 标注]
     ↓                                                      ↓
  选择状态                                            匹配结果
```

### 用户交互模式

1. **探索模式**: 在 FeatureMap 中浏览特征分布
2. **精确选择**: 框选区域缩小到感兴趣的谱图
3. **修饰识别**: 在 Spectrum 中选择峰，自动匹配修饰
4. **结果验证**: 查看 Table 中的匹配详情和标注
5. **MS2 关联**: 点击 MS1 特征，查看对应的 MS2 谱图和序列
6. 更加高级的交互: 给一个序列,然后自动匹配二级原始谱图中的碎片峰(该如何设计我们的架构才能实现?)

---

## 技术约束和考虑

我们处理后的数据在后端, 如何提供用户查看? 

### 数据规模
- MS1 特征数量: 可能达到数万到数十万
- MS2 谱图数量: 取决于实验设计
- 实时交互需求: 框选等操作需要低延迟响应

### 数据格式
- 已支持: TSV, CSV（基础表格）
- 待支持: .ms1ft, PrSM TSV, HTML（质谱特定格式）
- 修饰库: Unimod 或自定义格式

### 性能目标
- 数据加载: 合理的等待时间（用户可接受）
- 交互响应: 框选、点击等操作实时反馈
- 可视化渲染: 大数据集下保持流畅


---

## 当前项目状态

**已完成** (interactive-visualization OpenSpec):
- ✅ 基础可视化节点框架
- ✅ 前端状态管理
- ✅ 简单的节点联动

**缺失**:
- ❌ 修饰匹配逻辑
- ❌ MS2 数据支持
- ❌ 质谱特定格式解析
- ❌ 高级可视化图表（XIC、误差图、序列图）
- ❌ 文件编辑能力（fasta 等）

---

**用途**: 本文档提供给架构设计师，用于理解用户的工作流交互目标和技术约束。
