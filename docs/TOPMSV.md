TopMSV is a web-based tool for top-down MS data visualization. It provides various 2D and 3D views for top-down MS data. Researchers can use TopMSV to explore LC profiles, LC–MS maps, MS and MS/MS spectra, and spectral deconvolution and proteoform identification results. Developers can also use JavaScript libraries provided by TopMSV to implement their interfaces for MS data visualization.

The server side of TopMSV was developed using Node.js, Express.js, and C++. Node.js is an open-source, cross-platform, JavaScript runtime environment, and Express.js is an open-source web application framework for Node.js. The tools for MS data format conversion were implemented in C++. Visualization functions at the web browser side were developed using Java Script, in which 2D views of mass spectra and identified PrSMs were implemented using the D3.js library and 3D views of LC–MS data using the three.js library.


在Toppic勾选HTML输出之后:

D:\Projects\TDEase-Backend\data\users\test_user\workspaces\test_workspace\sample1_html 输出文件夹, 我们通常访问其中的的
data/users/test_user/workspaces/test_workspace/sample1_html/topmsv/index.html来打开其本地的网页服务



1. The total ion current chromotogram


This view shows the total ion current chromatogram of an LC-MS/MS data. The x axis represents retention time in minutes and the y axis represents the sum of all peak intensities being detected at a time point.

Operations:
Select retention time: move the mouse pointer to a retention time and click the left button of the mouse.
Change the current scan: input a scan number in the text box above the chromotogram and click "request."
2. A 3D view of LC-MS data


In the 3D view of LC-MS data, the x axis represents the m/z value, the y axis represents the retention time, and the z axis represents the peak intensity. This view provides visualization functions of zooming, dragging, and intensity scaling.

Basic operations
Dragging: hold the left-button of the mouse down and move the mouse to drag the view.
Zooming of the m/z value and retention time: place the mouse pointer in the view and use the mouse wheel to zoom in and out the view.
Zooming of the m/z value: place the mouse pointer below or above the view and use the mouse wheel to zoom in and out the m/z value of the view.
Zooming of the retention time: place the mouse pointer left to or right to the view and use the mouse wheel to zoom in and out the retention time of the view.
Intensity scaling: press a CTRL key in the keyboard and use the mouse wheel to scale peak intensities.
Rotating: hold the right button of the mouse and move the mouse to rotate the view.
Going to a specific position: input the specific m/z value and retention time in the text boxes above the view and click the "request" button.
View settings
Intensity cutoff threshold: input an intensity cutoff value in the text box "Intensity cutoff value."
Intensity auto scaling: when checked, the peak intensities of the view will be automatically adjusted based on the highest peak in the view.
Highlight current scan: when checked, a pink line will be drawn on the view, horizontal to the x axis. It highlights the retention time of the currently selected scan.
Other functions
Save Graph: save the 3D view to an image file.
Adjust view size: use the "+" and "-" buttons to increase or decrease the view size.
Full Screen: use the "Full screen" button to show the view in full screen.
3. 2D views of mass spectra


The top view shows peaks in an MS1 spectrum and the bottom view shows peaks in an MS/MS spectrum. When spectral deconvolution results are available, circles in the views represent the positions of peaks in theoretical isotopic envelopes and circles for one envelope are shown with the same color.

Operations
Dragging: hold the left-button of the mouse down and move the mouse to drag the view.
Zooming of the x axis: place the mouse pointer below the x-axis and use the mouse wheel to zoom in and out the x axis.
Scaling peak intensities: place the mouse pointer above the x-axis and use the mouse wheel to scale peak intensities.
Previous or next MS1 spectrum: click the "previous" or "next" button to show the previous or next MS1 spectrum.
Select an MS/MS spectrum: When several precursor ions in the current MS1 spectrum are selected for MS/MS analyses, click a precursor m/z value (above the bottom view) to show its corresponding MS/MS spectrum.
4. A view of monoisotopic mass graphs


This view shows deconvoluted monoisotopic masses in an MS/MS spectrum and its matched proteoform.

At the top, the identified proteoform sequence and its theoretical fragment masses are displayed; in the middle, the deconvoluted monoisotopic masses of the MS/MS spectrum are plotted; at the bottom, the m/z errors between matched theoretical and experimental masses are drawn in an error plot.

Operations
Dragging: hold the left-button of the mouse down and move the mouse to drag the view.
Zooming of the x axis: place the mouse pointer below the x-axis and use the mouse wheel to zoom in and out the x axis.
Scaling peak intensities: place the mouse pointer above the x-axis and use the mouse wheel to scale peak intensities.


1. Downloading TopMSV
Go to the Download web page.
Choose the download type "Windows 64-bit zip file."
Fill out the registration form, and click "I accept license agreement and download TopMSV" to download TopMSV.
Create a new folder C:\topmsv\server, save the zip file to the folder, and unzip the downloaded zip file to the folder C:\topmsv\server.
2. Starting a TopMSV server
Double click the batch file startServer.bat in the folder C:\topmsv\server\scripts\windows to start the server.

3. LC-MS/MS data visualization
3.1 Data
3.1.1 A top-down MS/MS Data set
In the MS experiment, the protein extract of S. typhimurium was reduced with dithiothreitol and alkylated with iodoacetamide. The protein mixture was first separated by gas-phase fractionation, resulting in 7 fractions. Each fraction was separated by an HPLC system coupled to an LTQ-Orbitrap mass spectrometer (Thermo Fisher Scientific). MS and MS/MS spectra were collected at a resolution of 60,000 and 30,000, respectively. In this tutorial, we use only the LC-MS/MS data file of the first fraction. The raw file was converted to an mzML file (st_1.mzML) using msconvert in ProteoWizard.

Click here to download the data set, save it into the folder C:\topmsv\data, and unzip it.

3.1.2 A protein sequence database
A S. typhimurium proteome database of 1,799 proteins was downloaded from the UniProt database.

Click here to download the protein database and save it into the folder C:\topmsv\data.

3.1.3 A text file of common post-translational modifications (PTMs)
Click here to download a text file containing common PTMs and save it into the folder C:\topmsv\data.

3.2 Uploading data
If not opened yet, open the Google Chrome web browser, type in the web server address http://localhost:8443/ in the address bar, and click the "Enter" button in the keyboard to go to the main webpage of the TopMSV server.
Click the "Sign in" button in the top right corner to sign in as a guest.


Click the "Upload" tab.


Type in "st_1" as the project name, click the "Select mzML file" button to select the data file C:\topmsv\data\st_1.mzML, and click the "Submit" button to update the data file.


3.3 Data visualization
Click the "My project" tab to show all projects.


Click "Link" in the "Project link" column to visualize the LC-MS/MS data. A manual for data visualization can be found at the manual webpage. After the data file is uploaded, it takes several minutes for the server to store peak information into a database. if the "Project link" column shows "processing," please wait for several minutes until a link is available.


3.4 Adding deconvolution results
Spectral deconvolution results can be added to the LC-MS/MS data by (1) running TopFD at the server or (2) runing TopFD locally and uploading deconvolution result files to the server. When spectral deconvolution results are available, theoretical isotopic envelopes will be shown in 2D views of MS1 and MS/MS spectra.

3.4.1 Running TopFD at the server
Click the "TopFD" button in the top right corner of the visualization webpage.


Select parameter settings of TopFD and and click the "Submit" button. A manual of parameter settings of TopFD can be found here.


After the task is submitted, the progress of the task can be found in the "Tasks" tab. When the task is finished, spectral deconvolution results reported by TopFD will be added to the database of the data set.
3.4.2 Uploading deconvolution results
Run TopFD to perform spectral deconvolution of the data file st_1.mzML. A tutorial for runing TopFD can be found here. Spectral deconvolution result files reported by TopFD include:
C:\topmsv\data\st_1_file\st_1_ms1.msalign: deconvolution results of MS1 spectra.
C:\topmsv\data\st_1_ms2.msalign: deconvolution results of MS/MS spectra.
C:\topmsv\data\st_1_file\st_1_frac.mzrt.csv: proteoform features in the LC-MS map.
Click the "Upload" button in the top right corner of the visualization webpage.


Click "Choose file" to choose the files C:\topmsv\data\st_1_file\st_1_ms1.msalign and C:\topmsv\data\st_2_ms2.msalign, and click the "upload" button.


Click "Choose file" to choose the file C:\topmsv\data\st_1_file\st_1_frac.mzrt.csv, and click "upload" button.


3.4.3 Visualization of deconvolution results
When deconvolution results are avaiable, theoretical isotopic envelopes will be added to 2D views of MS1 and MS/MS spectra. In addition, a table of deconvoluted monoisotopic masses will be added to the visualization webpage.


The file st_1_fract.mzrt.csv contains features reported from the LC-MS map. When feature information is available, features will be shown as dotted rectangles in the 3D view of the LC-MS map. When a CTRL key is pressed in the keyboard and a mouse pointer hovers over a rectangle, information of the feature will be shown.


3.5 Uploading spectral identfication results
Spectral identification results can be added to the LC-MS/MS data by (1) running TopPIC at the server or (2) runing TopPIC locally and uploading identification result files to the server. When spectral identification results are available, identified proteoform-spectrum-matches of MS/MS spectra can be shown and inspected.

3.5.1 Running TopPIC
Click the "TopPIC" button in the top right corner of the visualization webpage.


Click the first "Browse" button to choose the protein database file C:\topmsv\data\uniprot-st.fasta, and upload it. If PTM charaterization is needed, click the third "Browse" button to choose the text file C:\topmsv\data\common_mods.txt, and upload it. Choose parameter settings of TopPIC and click the "Submit" button to submit a task to the server. A manual of parameter settings of TopPIC can be found here.


After the task is submitted, the progress of the task can be found in the "Tasks" tab. When the task is finished, spectral identification results reported by TopPIC will be added to the database of the data set.
3.5.2 Uploading spectral identification results
Run TopPIC to perform spectral identification of the data file st_1_ms2.msalign reported by TopFD. A tutorial for runing TopPIC can be found here. Spectral identification result files reported by TopPIC include:
C:\topmsv\data\st_1_ms2_toppic_prsm_single.tsv: proteoform-spectrum-matches (PrSMs) reported from the file st_1_ms2.msalign.
Click the "Upload" button in the top right corner of the visualization webpage.


Click the "Choose file" button to select the file C:\topmsv\data\st_1_ms2_toppic_prsm_single.tsv and upload it.


3.5.3 Inspecting PrSMs
PrSMs identified by TopPIC can be shown and inspected.
In the visualization webpage of an MS/MS spectrum with an identified PrSM, click the "Inspect" button to inspect the PrSM.


In the inspection webpage, the user can edit the protein sequence and then click the "Submit" button to inspect the match between the spectrum and the protein sequence.


After the "Submit" button is clicked, a 2D view of the spectrum, a 2D view of the monoisotopic masses, and a table of matched masses will be shown. A manual for the operations of the views can be found at the manual webpage.





我现在关注其所生成的_HTML文件夹的结构, 数据存储的逻辑,以及我们可以如何调用? 以及其所展示的逻辑, 以便于我去进行复刻! 
Fast
View as codemap
HTML文件夹结构与数据存储逻辑
文件夹结构
TopMSV的HTML文件组织在server/public/resources/topview/目录下，采用分层结构：

topview/  
├── visual/           # 主要可视化页面  
│   ├── prsm.html     # PRSM可视化主页面  
│   ├── protein.html  # 蛋白质页面  
│   ├── proteins.html # 蛋白质列表页面  
│   └── ms.html       # 质谱识别页面  
├── inspect/          # 谱图检查页面  
│   ├── spectrum.html  
│   └── spectrum_no_nav.html  
└── common/           # 共享组件和库  
    ├── prsm_view/    # PRSM可视化核心  
    ├── spectrum_view/ # 谱图可视化  
    └── lib/          # 第三方库  
数据存储逻辑
1. 动态数据加载
系统通过动态创建<script>标签加载JavaScript数据文件：

let prsm_data_file_name = "../data/" + folder_path + "/prsms/prsm" + prsm_seq_num + ".js";  
prsm_data_script.src = prsm_data_file_name;  
head.appendChild(prsm_data_script);
2. 数据文件格式
数据以JavaScript变量形式存储，例如PRSM数据文件包含：

prsm_data - PRSM对象数组
谱图数据 - MS1/MS2谱图信息
序列数据 - 蛋白质序列和修饰信息
3. 页面间数据传递
使用localStorage在页面间传递数据：

window.localStorage.setItem('peakAndIntensityList', JSON.stringify(peakAndIntensityList));  
window.localStorage.setItem('massAndIntensityList', JSON.stringify(massAndIntensityList));  
window.localStorage.setItem('sequence', JSON.stringify(sequence));
调用方式
1. URL参数解析
页面通过URL参数获取数据路径和ID：

let folder_path = path_and_value[0].split("=")[1];  
let prsm_seq_num = path_and_value[1].split("=")[1];
2. 页面导航
各页面间通过URL链接导航：

let l_allproteins_url = "proteins.html?folder=" + folderpath;  
proteinUrl.href = "protein.html?folder=" + folderpath + "&protein_Id=" + proteoformObj.getSeqId();
展示逻辑
1. PRSM可视化流程










2. 核心可视化组件
PrsmView - 绘制PRSM序列图谱
SpectrumView - 绘制质谱图
DataTable - 创建峰数据表格
3. 数据渲染过程
数据解析 - ParsePrsm类解析原始数据
HTML构建 - loadDatafromJson2Html填充页面信息
可视化渲染 - 调用各组件的redraw()方法
复刻建议
1. 最小化文件集
核心文件：

prsm_view/ - PRSM可视化核心
spectrum_view/ - 谱图可视化
parse_json/ - 数据解析器
数据类文件 - peak.js, spectrum.js, prsm.js等
2. 数据适配
创建数据适配器将你的数据转换为TopMSV格式，重点关注：

PRSM数据结构
谱图数据格式
序列和修饰信息
3. 独立部署
移除TopMSV特定依赖：

导航栏组件
服务器端API调用
项目管理功能
Notes
TopMSV使用模块化设计，各可视化组件可独立使用
数据文件格式为JavaScript变量，便于直接加载
系统支持多种页面类型，可根据需求选择复刻
localStorage机制适用于单页面应用的数据传递
Wiki pages you might want to explore:

Overview (toppic-suite/topmsv)



TopPIC HTML结构与可视化流程
TopPIC Suite通过一个完整的数据处理链路实现质谱数据的可视化，包括XML生成、JSON转换和HTML展示三个主要阶段。

HTML生成流程
TopPIC在处理完成后会生成HTML可视化文件，这个过程在TopPIC_post函数中实现 toppic_process.cpp:535-548 ：

if (arguments["geneHTMLFolder"] == "true"){  
  // 生成proteoform XML文件  
  xml_gene = std::make_shared<XmlGenerator>(prsm_para_ptr, resource_dir,   
                                          "toppic_form_cutoff",   
                                          "toppic_proteoform_cutoff");  
  xml_gene->process();  
    
  // 将XML转换为HTML文件  
  jsonTranslate(arguments, "toppic_proteoform_cutoff");  
}
数据存储与转换过程
XML生成阶段：XmlGenerator类负责将分析结果转换为XML格式 xml_generator.hpp:35-42

JSON转换阶段：jsonTranslate函数将XML文件转换为JavaScript可读的JSON格式 json_transformer.cpp:46-80 ：

读取XML文件列表
逐个转换为JSON格式
输出为prsm_data =开头的JavaScript文件
TopMSV资源复制：copyTopMSV函数将可视化所需的Web资源复制到输出目录 console_util.cpp:23-39

HTML目录结构
生成的HTML文件具有以下结构 toppic_manual.md:33-39 ：

spectra_html/  
├── toppic_prsm_cutoff/     # 谱图级别 cutoff 的JavaScript文件  
├── toppic_proteoform_cutoff/ # 蛋白质形式级别 cutoff 的JavaScript文件  
└── topmsv/                 # HTML可视化文件  
    ├── index.html          # 主入口页面  
    ├── proteins.html       # 蛋白质识别页面  
    └── inspect/            # 详细检查页面  
TopMSV可视化实现
TopMSV是一个基于JavaScript的可视化框架，主要组件包括：

主页面结构：proteins.html提供了TopPIC和TopMG结果的入口界面 proteins.html:25-72

数据交互：通过localStorage在页面间传递数据 topview.js.html:35-52 ：

// 存储谱图数据到本地存储  
window.localStorage.setItem('peakAndIntensityList', JSON.stringify(peakAndIntensityList));  
window.localStorage.setItem('massAndIntensityList', JSON.stringify(massAndIntensityList));
可视化组件：包括谱图显示、蛋白质序列标注、PTM位点标记等功能

数据传输机制
数据传输采用以下流程：

C++后端生成XML格式的结构化数据
XML2JSON转换器将XML转换为JavaScript对象
前端JavaScript读取JSON数据并渲染可视化界面
页面间通信通过HTML5 localStorage实现
这种架构实现了计算密集型的质谱分析（C++）与交互式可视化（JavaScript）的分离，确保了系统的性能和可维护性。

Notes
TopMG使用相同的可视化架构，只是输出文件名前缀为topmg而非toppic topmg_process.cpp:370-418
HTML生成可以通过--skip-html-folder参数禁用 toppic_manual.md:174-176
可视化系统在版本1.3.0中引入 RELEASE_NOTE:19-22
Wiki pages you might want to explore:

Overview (toppic-suite/toppic-suite)




如果不启动HTML输出的选项, 那么其输出的数据也足够完成 TOPMSV的可视化吗? 我打算自己实现
Fast
View as codemap
数据充分性分析
如果不启动HTML输出选项，TopPIC输出的数据足够完成TopMSV可视化，但需要你自己实现数据转换和前端渲染部分。

可用的核心数据
当geneHTMLFolder设为"false"时，TopPIC仍会输出以下关键文件 toppic_process.cpp:535-548 ：

TSV表格文件：
_toppic_prsm.tsv - PrSM级别结果
_toppic_proteoform.tsv - proteoform级别结果
XML文件（包含完整可视化数据）：
XmlGenerator类会生成详细的XML文件，包含所有可视化所需的结构化数据 xml_generator.cpp:428-450
XML数据结构
XmlGenerator::process()生成的XML包含以下关键信息 xml_generator.cpp:50-125 ：

PrSM数据：谱图匹配信息、评分、质量数据
质谱峰数据：m/z、强度、电荷状态 anno_prsm.cpp:135-190
蛋白质序列信息：序列、修饰、质量偏移
谱图头信息：扫描号、前体质量等
需要自己实现的部分
要完成完整的可视化流程，你需要实现：

XML到JSON转换：
// 类似jsonConvert函数的功能  
void jsonConvert(const std::string &xml_file_name,   
                 const std::string &json_file_name) {  
  // 读取XML并转换为JavaScript对象格式  
  const auto json_str = xml2json(xml_content);  
  // 输出为prsm_data = {...}格式  
}
json_transformer.cpp:32-43

前端可视化界面：
数据加载逻辑
谱图可视化组件
蛋白质序列标注
交互功能
TopMSV资源文件：
需要从resources/topmsv/目录复制HTML/CSS/JS文件
或自行开发可视化组件
数据访问示例
XML文件中的数据结构示例（从anno_prsm.cpp可见） anno_prsm.cpp:192-215 ：

<prsm>  
  <ms_header>  
    <scans>扫描号信息</scans>  
    <precursor_mono_mass>前体质量</precursor_mono_mass>  
  </ms_header>  
  <ms>  
    <peaks>  
      <peak>  
        <monoisotopic_mass>质量</monoisotopic_mass>  
        <intensity>强度</intensity>  
        <charge>电荷</charge>  
        <matched_ions>匹配离子信息</matched_ions>  
      </peak>  
    </peaks>  
  </ms>  
  <proteoform>蛋白质形式信息</proteoform>  
</prsm>
实现建议
保留XML生成：确保XmlGenerator正常运行，这是数据的核心来源
实现转换器：基于xml2json库实现XML到JavaScript对象的转换
开发前端：参考TopMSV的resources/topmsv/目录中的实现
数据加载：实现类似TopMSV的数据加载和localStorage机制
Notes
TopMG使用相同的数据结构和流程 topmg_process.cpp:370-418
XML文件包含所有必要的元数据和谱图信息，是可视化的唯一数据源
可以通过--skip-html-folder参数禁用HTML生成来测试你的实现 toppic_manual.md:174-176
Wiki pages you might want to explore:

Overview (toppic-suite/toppic-suite)