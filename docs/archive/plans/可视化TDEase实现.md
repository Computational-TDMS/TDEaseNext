## 1. 修改后端
<!-- 
1. 我们要将后端生成的文件, 能够让前端看到我们的工作目录
    1. 后端识别文件列表给前端查看(应当有相应的插件) 
    2. 

2. csv, tsv等基本的表格形式需要能够展示即可 --> (已经完成)

我们可以对表格进行针对性的优化

而对于fasta等基本文件, 需要可以直接从前端进行编辑?

3. 之后我们会自行搭建框架来实现质谱实际数据的传输!(基于MSQL)


## 关于前端:

1. 前端能够看到我们对应工作目录, 并且点开查看, 然后我们能够正确用aggrid来渲染表格(这是最基本的)

2. 添置featuremap工具

3. 可以设计前端的简单数据处理流程, 并且将可视化组件堆叠在一个页面, 从而让用户自定义一个数据人工筛选工作流!


## 关于TDEase 完整功能的阐述:


1. 用featuremap来展示我们的ms1feature文件

mass intensity start_time end_time  从而可以构成一个二维, 每个数据点产生一条trace的热力图!(intensity为颜色, start_time为x轴, end_time为x轴, mass为y轴)

2. 框选的区域, 这高维数据会进行投影, 从而在我们的spectrum节点进行显示

mass-->x

intensity --> y

虽然可以进行积分, 强度累加, 但是普遍来说不同的点的质量是不会重叠的, 映射即可


3. spectrum节点中如果我们进一步进行框选, 那么就是选中对应的峰

我们的另一个表格节点, 会基于这个峰, 筛选ms1feature中的其他峰, 根据其差异, 然后对照用户所传入的unimod或者其他形式的修饰列表去进行比对, 根据ppm, isotopic shift来确定修饰, 然后再在spectrum上进行标注

(当然匹配结果表格也是要展示的, 给用户一个交代!)

4. 因为toppic还产生了二级结果, 那么我们接着就要在 
_ms2_toppic_proteoform.tsv
[text](../../data/users/test_user/workspaces/test_workspace/sample1_ms2_toppic_proteoform_single.tsv)
sample1_ms2_toppic_prsm_single.tsv

test_workspace/sample1_ms2_toppic_prsm.tsv

中根据其featureID去对应到相应地prsm ID, 然后就可以从 _html中找到对应的 二级图谱以及其所对应的修饰序列, 然后进行展示, 以便于用户交互式地找到二级图谱的信息



## pbfgen:

这里的可视化流程就需要去参考 lcms spectator!

支持的 InformedProteomics 工具输出
1. ProMex 特征文件
ProMex 输出的 MS1 特征文件可通过 
FeatureReaderL30-L62 读取，要求包含以下字段：

MonoMass, Abundance, LikelihoodRatio/Probability, Envelope,
MinCharge, MaxCharge, MinScan, MaxScan
这些特征数据在 
ProMexModelL25-L225 中被组织成特征点，并关联到 MS/MS 谱图。

2. MSPathFinder 结果文件
MSPathFinder 输出的 TSV 或 ZIP 文件通过 
IcFileReaderL23-L205 读取，包含：

Zip 格式：Dataset_IcTsv.zip，内部包含 IcTarget.tsv、IcDecoy.tsv、IcTda.tsv（见 
IdFileReaderFactory.cs#L29-L36L29-L36）
TSV 格式：包含 #MatchedFragments、ProteinName、Modifications、Sequence、Scan、Charge、ProteinDesc、QValue 等字段（见 
IcFileReader.cs#L83-L97L83-L97）
3. MSPathFinder 参数文件
.param 文件通过 
MsPfParameters.ReadFromFileL133-L142 解析，用于重现搜索设置：

SpecFile, DatabaseFile, FeatureFile, SearchMode, Tda,
PrecursorIonTolerancePpm, ProductIonTolerancePpm,
Modification (composition, amino acid, fixed, location, name)
pbfgen 输出文件
虽然代码中没有明确提到 pbfgen，但从支持的文件格式推断：

如果 pbfgen 输出标准的 MS1 特征文件（包含 MonoMass、Abundance、Envelope 等字段），可以直接通过 FeatureReader 读取
如果输出的是 MSPathFinder 兼容的 TSV 格式，可以通过 IcFileReader 读取
关键：需要确认文件头是否匹配预期的字段名（见 
FeatureReader.cs#L73-L84L73-L84）
数据流整合
ProMex 和 MSPathFinder 的输出可以在 LCMS-Spectator 中进行关联：

ProMex 特征通过 MinScan 和 MaxScan 关联到 MS/MS 谱图
MSPathFinder 的肽段识别（PrSm）通过质量容差匹配到特征（见 
ProMexModel.SetIdsL108-L155）
可视化时可以同时显示 XIC 图、误差图和序列图
---

在参照这两个工具之后,我们就能够明确我们之后可视化节点的设计范式与 相应的, 我们所需要的功能了!


