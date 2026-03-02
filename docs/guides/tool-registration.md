# 工具注册指南

## 📋 概述

TDEase 采用 JSON 配置文件的方式注册和管理质谱数据处理工具。本文档详细说明如何创建和注册新工具。

---

## 工具定义格式

### 基本结构

```json
{
  "id": "tool_id",
  "name": "工具名称",
  "kind": "command",
  "toolPath": "/path/to/tool",
  "description": "工具描述",
  "category": "工具分类",
  "inputs": [...],
  "outputs": [...],
  "positional_params": [...],
  "param_mapping": {...},
  "input_flag": "--input",
  "output_flag": "--output",
  "output_flag_supported": true
}
```

### 字段说明

#### 基本信息字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 工具唯一标识符 |
| `name` | string | ✅ | 工具显示名称 |
| `kind` | string | ✅ | 工具类型: `command` 或 `script` |
| `toolPath` | string | ✅ | 可执行文件路径 |
| `description` | string | ❌ | 工具描述 |
| `category` | string | ❌ | 工具分类（如：转换、分析、可视化） |

#### 输入输出端口

**inputs** - 输入端口定义

```json
{
  "inputs": [
    {
      "id": "input_file",
      "type": "file",
      "dataType": "mzml",
      "label": "输入文件",
      "description": "质谱数据文件",
      "accept": [".mzML", ".raw"],
      "required": true
    }
  ]
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 端口唯一标识符 |
| `type` | string | ✅ | 端口类型: `file`, `directory`, `string` |
| `dataType` | string | ✅ | 数据类型: `mzml`, `msalign`, `fasta`, `raw` 等 |
| `label` | string | ❌ | 显示标签 |
| `description` | string | ❌ | 端口描述 |
| `accept` | array | ❌ | 接受的文件扩展名 |
| `required` | boolean | ❌ | 是否必需 |

**outputs** - 输出端口定义

```json
{
  "outputs": [
    {
      "id": "output_file",
      "type": "file",
      "dataType": "msalign",
      "pattern": "{sample}.msalign",
      "label": "输出文件",
      "description": "转换后的数据文件"
    }
  ]
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 端口唯一标识符 |
| `type` | string | ✅ | 端口类型: `file`, `directory` |
| `dataType` | string | ✅ | 数据类型 |
| `pattern` | string | ✅ | 输出文件名模板（支持通配符） |
| `label` | string | ❌ | 显示标签 |
| `description` | string | ❌ | 端口描述 |
| `provides` | string | ❌ | 提供的数据标识符 |

#### 参数映射

**param_mapping** - 参数到命令行标志的映射

```json
{
  "param_mapping": {
    "precursor_mass_error": {
      "flag": "-e",
      "type": "value",
      "default": "0.02",
      "label": "前体质量误差",
      "description": "前体离子质量误差容忍度"
    },
    "use_top_fd": {
      "flag": "--use-topfd",
      "type": "boolean",
      "default": false,
      "label": "使用Top-FD",
      "description": "是否使用Top-FD数据"
    },
    "algorithm": {
      "flag": "--algorithm",
      "type": "choice",
      "options": ["exact", "fuzzy", "hybrid"],
      "default": "exact",
      "label": "算法选择",
      "description": "选择匹配算法"
    }
  }
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `flag` | string | ✅ | 命令行标志 |
| `type` | string | ✅ | 参数类型: `value`, `boolean`, `choice` |
| `default` | any | ❌ | 默认值 |
| `options` | array | ❌ | 选择项（type=choice 时必需） |
| `label` | string | ❌ | 显示标签 |
| `description` | string | ❌ | 参数描述 |

#### 位置参数

**positional_params** - 命令行位置参数

```json
{
  "positional_params": [
    {
      "name": "fasta_file",
      "source": "input.fasta_file",
      "label": "FASTA文件",
      "description": "蛋白质序列数据库文件"
    }
  ]
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 参数名称 |
| `source` | string | ✅ | 值来源（引用输入端口） |
| `label` | string | ❌ | 显示标签 |
| `description` | string | ❌ | 参数描述 |

#### 输入输出标志

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `input_flag` | string | ❌ | 输入文件命令行标志 |
| `output_flag` | string | ❌ | 输出文件命令行标志 |
| `output_flag_supported` | boolean | ❌ | 是否支持输出标志（默认 true） |

---

## 命令行占位符

### Snakemake 占位符规则

在工具定义中，可以使用以下占位符：

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{input}` | 输入文件 | `{input}` |
| `{input.<id>}` | 命名输入 | `{input.input_file}` |
| `{output}` | 输出文件 | `{output}` |
| `{output.<id>}` | 命名输出 | `{output.output_file}` |
| `{params.<key>}` | 参数值 | `{params.precursor_mass_error}` |
| `{sample}` | 样品名 | `{sample}` |
| `{fasta_filename}` | FASTA文件名 | `{fasta_filename}` |

### 命令构建示例

**简单命令**:
```bash
# 工具定义
{
  "toolPath": "/usr/bin/msconvert",
  "input_flag": "-i",
  "output_flag": "-o"
}

# 生成的命令
{toolPath} {input_flag} {input} {output_flag} {output_dir}
# 实际执行
/usr/bin/msconvert -i input.mzML -o output_dir
```

**带参数的命令**:
```bash
# 工具定义
{
  "toolPath": "/usr/bin/toppic",
  "param_mapping": {
    "precursor_mass_error": {
      "flag": "-e",
      "type": "value"
    }
  }
}

# 生成的命令
{toolPath} -e {params.precursor_mass_error} {input} {output}
# 实际执行（假设 precursor_mass_error = 0.02）
/usr/bin/toppic -e 0.02 input.mzML output.msalign
```

**带位置参数的命令**:
```bash
# 工具定义
{
  "toolPath": "/usr/bin/toppic",
  "positional_params": [
    {
      "name": "fasta_file",
      "source": "input.fasta_file"
    }
  ]
}

# 生成的命令
{toolPath} {input} {positional_params.fasta_file} {output}
# 实际执行
/usr/bin/toppic input.msalign database.fasta output.msalign
```

---

## 路径管理与输出行为

### 输出行为类型

#### 1. 支持输出标志的工具 (默认)

**特征**: 工具支持 `--output` 标志指定输出位置

```json
{
  "output_flag_supported": true,
  "output_flag": "--output"
}
```

**处理**: 直接使用 Snakemake 的 `{output}` 占位符

#### 2. 不支持输出标志的工具

**特征**: 工具将输出文件生成在输入文件所在目录

```json
{
  "output_flag_supported": false,
  "output_behavior": "input_dir"
}
```

**处理**:
1. 在输入目录执行工具
2. 执行完成后移动输出文件到工作目录

### 路由配置

对于不支持输出标志的工具，需要配置路由规则：

```json
{
  "routing": {
    "output_files": [
      {
        "pattern": "{sample}_ms1.txt",
        "source": "input_dir",
        "move_to": "workdir"
      }
    ]
  }
}
```

---

## 工具注册流程

### 1. 创建工具配置文件

在 `TDEase-FrontEnd/config/tools/` 目录下创建工具 JSON 文件：

```bash
TDEase-FrontEnd/config/tools/my_tool.json
```

### 2. 填写工具定义

参考以下模板：

```json
{
  "id": "my_tool",
  "name": "My Analysis Tool",
  "kind": "command",
  "toolPath": "/usr/bin/my_tool",
  "description": "A tool for analyzing mass spectrometry data",
  "category": "analysis",

  "inputs": [
    {
      "id": "input_file",
      "type": "file",
      "dataType": "mzml",
      "label": "Input File",
      "description": "Mass spectrometry data file",
      "accept": [".mzML"],
      "required": true
    }
  ],

  "outputs": [
    {
      "id": "output_file",
      "type": "file",
      "dataType": "txt",
      "pattern": "{sample}_result.txt",
      "label": "Output File",
      "description": "Analysis results"
    }
  ],

  "param_mapping": {
    "tolerance": {
      "flag": "-t",
      "type": "value",
      "default": "0.02",
      "label": "Mass Tolerance",
      "description": "Mass tolerance in Da"
    },
    "verbose": {
      "flag": "--verbose",
      "type": "boolean",
      "default": false,
      "label": "Verbose Output",
      "description": "Enable verbose logging"
    }
  },

  "input_flag": "--input",
  "output_flag": "--output",
  "output_flag_supported": true
}
```

### 3. 通过 API 注册工具

```bash
curl -X POST http://localhost:8000/api/tools/register \
  -H "Content-Type: application/json" \
  -d @TDEase-FrontEnd/config/tools/my_tool.json
```

### 4. 验证工具注册

```bash
# 查看已注册工具
curl http://localhost:8000/api/tools/registered

# 查看特定工具详情
curl http://localhost:8000/api/tools/my_tool
```

---

## 工具示例

### MSConvert (Docker)

```json
{
  "id": "msconvert_docker",
  "name": "MSConvert (Docker)",
  "kind": "command",
  "toolPath": "docker run --rm -v {workdir}:/data chambm/pwiz-msconvert:latest",
  "description": "Convert mass spectrometry data files using MSConvert in Docker",
  "category": "conversion",

  "inputs": [
    {
      "id": "input_file",
      "type": "file",
      "dataType": "raw",
      "label": "Input File",
      "description": "Raw mass spectrometry data file",
      "accept": [".raw"],
      "required": true
    }
  ],

  "outputs": [
    {
      "id": "output_file",
      "type": "file",
      "dataType": "mzml",
      "pattern": "{sample}.mzML",
      "label": "Output File",
      "description": "Converted mzML file"
    }
  ],

  "param_mapping": {
    "mzML": {
      "flag": "--mzML",
      "type": "boolean",
      "default": true,
      "label": "mzML Format",
      "description": "Output in mzML format"
    },
    "zlib": {
      "flag": "--zlib",
      "type": "boolean",
      "default": false,
      "label": "zlib Compression",
      "description": "Use zlib compression"
    },
    "filter": {
      "flag": "--filter",
      "type": "value",
      "default": "peakPicking true 1-",
      "label": "Peak Picking",
      "description": "Apply peak picking filter"
    }
  },

  "input_flag": "-i",
  "output_flag": "-o",
  "output_flag_supported": true
}
```

### TopPIC

```json
{
  "id": "toppic",
  "name": "TopPIC",
  "kind": "command",
  "toolPath": "/path/to/toppic",
  "description": "Proteoform identification using top-down mass spectrometry",
  "category": "analysis",

  "inputs": [
    {
      "id": "input_file",
      "type": "file",
      "dataType": "msalign",
      "label": "Input File",
      "description": "MSAlign format data file",
      "accept": [".msalign"],
      "required": true
    },
    {
      "id": "fasta_file",
      "type": "file",
      "dataType": "fasta",
      "label": "Database File",
      "description": "Protein sequence database",
      "accept": [".fasta"],
      "required": true
    }
  ],

  "outputs": [
    {
      "id": "output_file",
      "type": "file",
      "dataType": "tsv",
      "pattern": "{sample}_proteoforms.tsv",
      "label": "Proteoforms File",
      "description": "Identified proteoforms"
    }
  ],

  "positional_params": [
    {
      "name": "fasta_file",
      "source": "input.fasta_file",
      "label": "FASTA Database",
      "description": "Protein sequence database file"
    }
  ],

  "param_mapping": {
    "precursor_mass_error": {
      "flag": "-e",
      "type": "value",
      "default": "15.0",
      "label": "Precursor Mass Error",
      "description": "Precursor mass error tolerance (ppm)"
    },
    "mass_error": {
      "flag": "-m",
      "type": "value",
      "default": "10.0",
      "label": "Mass Error",
      "description": "Fragment mass error tolerance (ppm)"
    },
    "variable_ptm": {
      "flag": "--variable-ptm",
      "type": "choice",
      "options": ["Acetylation", "Oxidation", "Phosphorylation"],
      "default": "Acetylation",
      "label": "Variable PTM",
      "description": "Variable post-translational modification"
    }
  },

  "input_flag": "-i",
  "output_flag_supported": true
}
```

### Data Loader

```json
{
  "id": "data_loader",
  "name": "Data Loader",
  "kind": "command",
  "toolPath": "cp",
  "description": "Load data files into workflow directory",
  "category": "data_management",

  "inputs": [
    {
      "id": "input_sources",
      "type": "array",
      "dataType": "file",
      "label": "Input Files",
      "description": "External data files to load",
      "required": true
    }
  ],

  "outputs": [
    {
      "id": "output_files",
      "type": "file",
      "dataType": "any",
      "pattern": "{sample}.{ext}",
      "label": "Copied Files",
      "description": "Files copied to workflow directory"
    }
  ],

  "input_flag": "",
  "output_flag": "",
  "output_flag_supported": true
}
```

---

## 工具测试

### 测试流程

1. **注册工具**
   ```bash
   curl -X POST http://localhost:8000/api/tools/register \
     -H "Content-Type: application/json" \
     -d @config/tools/my_tool.json
   ```

2. **验证工具可用性**
   ```bash
   curl http://localhost:8000/api/tools/my_tool
   ```

3. **创建测试工作流**
   ```python
   test_workflow = {
       "metadata": {"name": "Test My Tool"},
       "nodes": [
           {
               "id": "node_1",
               "type": "my_tool",
               "data": {
                   "params": {
                       "tolerance": "0.02",
                       "verbose": true
                   }
               }
           }
       ],
       "edges": []
   }
   ```

4. **执行工作流**
   ```bash
   curl -X POST http://localhost:8000/api/workflows/execute \
     -H "Content-Type: application/json" \
     -d '{"workflow": ...}'
   ```

5. **检查执行结果**
   ```bash
   curl http://localhost:8000/api/executions/{execution_id}
   ```

---

## 常见问题

### Q1: 工具路径如何配置？

**A**: 工具路径可以是：
- **绝对路径**: `/usr/bin/tool`
- **相对路径**: `./tools/tool` (相对于工作目录)
- **环境变量**: `$HOME/tools/tool`
- **Docker命令**: `docker run ...`

### Q2: 如何处理依赖关系？

**A**: 依赖关系通过工作流的 edges 定义：
```json
{
  "edges": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "sourceHandle": "output_file",
      "targetHandle": "input_file"
    }
  ]
}
```

### Q3: 如何指定工作目录？

**A**: 工作目录由 Snakemake 自动管理，可通过 `{workdir}` 占位符引用。

### Q4: 如何处理复杂的多输入工具？

**A**: 使用数组类型的输入端口：
```json
{
  "inputs": [
    {
      "id": "input_files",
      "type": "array",
      "dataType": "mzml",
      "label": "Input Files"
    }
  ]
}
```

---

## 相关文档

- [工作流格式说明](workflow-format.md)
- [工作空间管理](workspace-management.md)
- [API 端点文档](../api/endpoints.md)
