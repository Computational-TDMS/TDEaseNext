## 工作流格式概述

Galaxy支持多种工作流格式，主要包括传统的JSON格式（`.ga`）和现代的YAML格式（`.gxwf.yml`） [1](#1-0) 。

我们目前采用混合格式规范，结合Galaxy格式的结构化特点，同时保留VueFlow的UI信息，以便前端渲染。

## TDEase工作流格式（混合格式）

### 格式结构

TDEase工作流采用混合格式，既支持Galaxy格式的执行语义，又保留VueFlow的UI信息：

```json
{
  "metadata": {
    "id": "workflow_id",
    "name": "工作流名称",
    "version": "1.0.0",
    "description": "工作流描述",
    "author": "作者",
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-01T00:00:00Z",
    "tags": ["tag1", "tag2"],
    "uuid": "optional-uuid",
    "license": "optional-license"
  },
  "format_version": "2.0",
  "nodes": [
    // VueFlow节点定义（用于UI渲染）
  ],
  "connections": [
    // VueFlow连接定义（用于UI渲染）
  ],
  "steps": {
    // Galaxy格式步骤定义（用于执行）
    "step_id": {
      "id": "step_id",
      "type": "tool",
      "tool_id": "tool_name",
      "tool_state": {},
      "inputs": {},
      "outputs": {}
    }
  },
  "inputs": {
    // Galaxy格式工作流输入
  },
  "outputs": {
    // Galaxy格式工作流输出
  },
  "projectSettings": {}
}
```

### 关键字段说明

- **metadata**: Galaxy格式的元数据，包含id、name、version、tags等
- **format_version**: 格式版本号，默认为"2.0"
- **nodes**: VueFlow节点定义，保留UI渲染所需的位置、样式等信息
- **connections**: VueFlow连接定义，保留节点间的连接关系
- **steps**: Galaxy格式的步骤定义，由normalizer从nodes/connections自动生成，用于执行
- **inputs**: Galaxy格式的工作流输入定义
- **outputs**: Galaxy格式的工作流输出定义
- **projectSettings**: 项目设置（保留现有字段）

## 批量处理配置

批量处理通过JSON格式的配置表格实现，支持多样品批量执行（类似Snakemake的config.yaml功能）。

### 主要格式类型

1. **传统JSON格式（.ga）** - Galaxy原生格式，使用`format-version: "0.1"` [2](#1-1) 
2. **现代YAML格式（.gxwf.yml）** - 基于Format2规范，使用`class: GalaxyWorkflow` [3](#1-2) 
3. **CWL格式（.abstract.cwl）** - 抽象工作流语言格式 [4](#1-3) 

## 格式结构详解

### 1. 传统JSON格式结构

```json
{
    "a_galaxy_workflow": "true",
    "format-version": "0.1",
    "name": "工作流名称",
    "annotation": "工作流描述",
    "steps": {
        "0": {
            "id": 0,
            "type": "data_input",
            "tool_state": "{}",
            "inputs": [],
            "outputs": []
        }
    }
}
``` [5](#1-4) 

### 2. 现代YAML格式结构

```yaml
class: GalaxyWorkflow
name: 工作流名称
inputs:
  input1: data
outputs:
  wf_output_1:
    outputSource: step_name/output_name
steps:
  step_name:
    tool_id: tool_identifier
    in:
      input1: input1
``` [6](#1-5) 

## 格式转换与导出

### 导出样式

工作流可以通过API以不同样式导出 [7](#1-6) ：

- **export** - 标准导出格式，用于工作流导入
- **format** - 现代YAML格式
- **editor** - 编辑器格式，包含UI渲染信息
- **run** - 运行时格式

### 格式转换逻辑

在`WorkflowContentsManager`中，格式转换通过以下方法实现 [8](#1-7) ：

1. 检测输入格式类型
2. 使用`python_to_workflow`转换Format2格式
3. 通过`from_galaxy_native`转换为YAML格式

## 具体格式示例

### 简单工作流示例

```yaml
class: GalaxyWorkflow
inputs:
  input1: data
steps:
  first_cat:
    tool_id: cat1
    in:
      input1: input1
``` [9](#1-8) 

### 嵌套工作流示例

```yaml
class: GalaxyWorkflow
inputs:
  outer_input: data
steps:
  nested_workflow:
    run:
      class: GalaxyWorkflow
      inputs:
        inner_input: data
      steps:
        random:
          tool_id: random_lines1
    in:
      inner_input: outer_input
``` [10](#1-9) 

## Notes

工作流格式的设计考虑了向后兼容性和扩展性。传统JSON格式保持稳定，而现代YAML格式提供了更好的可读性和扩展性。格式转换机制确保了不同版本间的互操作性。

Wiki pages you might want to explore:
- [Histories and Datasets (galaxyproject/galaxy)](/wiki/galaxyproject/galaxy#2.1)

### Citations

**File:** lib/galaxy/managers/workflows.py (L628-660)
```python
    def normalize_workflow_format(self, trans, as_dict):
        """Process incoming workflow descriptions for consumption by other methods.

        Currently this mostly means converting format 2 workflows into standard Galaxy
        workflow JSON for consumption for the rest of this module. In the future we will
        want to be a lot more precise about this - preserve the original description along
        side the data model and apply updates in a way that largely preserves YAML structure
        so workflows can be extracted.
        """
        workflow_directory = None
        workflow_path = None

        if as_dict.get("src", None) == "from_path":
            if not trans.user_is_admin:
                raise exceptions.AdminRequiredException()

            workflow_path = as_dict.get("path")
            workflow_directory = os.path.normpath(os.path.dirname(workflow_path))

        workflow_class, as_dict, object_id = artifact_class(trans, as_dict)
        if workflow_class == "GalaxyWorkflow" or "yaml_content" in as_dict:
            # Format 2 Galaxy workflow.
            galaxy_interface = Format2ConverterGalaxyInterface()
            import_options = ImportOptions()
            import_options.deduplicate_subworkflows = True
            try:
                as_dict = python_to_workflow(
                    as_dict, galaxy_interface, workflow_directory=workflow_directory, import_options=import_options
                )
            except yaml.scanner.ScannerError as e:
                raise exceptions.MalformedContents(str(e))

        return RawWorkflowDescription(as_dict, workflow_path)
```

**File:** lib/galaxy/managers/workflows.py (L975-1005)
```python
    def store_workflow_artifacts(self, directory, filename_base, workflow, **kwd):
        modern_workflow_path = os.path.join(directory, f"{filename_base}.gxwf.yml")
        legacy_workflow_path = os.path.join(directory, f"{filename_base}.ga")
        abstract_cwl_workflow_path = os.path.join(directory, f"{filename_base}.abstract.cwl")
        for path in [legacy_workflow_path, modern_workflow_path, abstract_cwl_workflow_path]:
            self.app.workflow_contents_manager.store_workflow_to_path(path, workflow.stored_workflow, workflow, **kwd)
        try:
            cytoscape_path = os.path.join(directory, f"{filename_base}.html")
            to_cytoscape(modern_workflow_path, cytoscape_path)
        except Exception:
            # completely optional and currently broken so ignore...
            pass

    def store_workflow_to_path(self, workflow_path, stored_workflow, workflow, **kwd):
        trans = kwd.get("trans")
        if trans is None:
            trans = WorkRequestContext(app=self.app, user=kwd.get("user"), history=kwd.get("history"))

        workflow = stored_workflow.latest_workflow
        with open(workflow_path, "w") as f:
            if workflow_path.endswith(".ga"):
                wf_dict = self._workflow_to_dict_export(trans, stored_workflow, workflow=workflow)
                json.dump(wf_dict, f, indent=4)
            elif workflow_path.endswith(".abstract.cwl"):
                wf_dict = self._workflow_to_dict_export(trans, stored_workflow, workflow=workflow)
                abstract_dict = from_dict(wf_dict)
                ordered_dump(abstract_dict, f)
            else:
                wf_dict = self._workflow_to_dict_export(trans, stored_workflow, workflow=workflow)
                wf_dict = from_galaxy_native(wf_dict, None, json_wrapper=True)
                f.write(wf_dict["yaml_content"])
```

**File:** lib/galaxy/schema/schema.py (L2682-2713)
```python
class WorkflowToExport(Model):
    a_galaxy_workflow: str = Field(  # Is this meant to be a bool instead?
        "true", title="Galaxy Workflow", description="Whether this workflow is a Galaxy Workflow."
    )
    format_version: str = Field(
        "0.1",
        alias="format-version",  # why this field uses `-` instead of `_`?
        title="Galaxy Workflow",
        description="Whether this workflow is a Galaxy Workflow.",
    )
    name: str = Field(..., title="Name", description="The name of the workflow.")
    annotation: Optional[str] = AnnotationField
    tags: TagCollection
    uuid: Optional[UUID4] = Field(
        None,
        title="UUID",
        description="Universal unique identifier of the workflow.",
    )
    creator: Optional[List[Union[Person, Organization]]] = Field(
        None,
        title="Creator",
        description=("Additional information about the creator (or multiple creators) of this workflow."),
    )
    license: Optional[str] = Field(
        None, title="License", description="SPDX Identifier of the license associated with this workflow."
    )
    version: int = Field(
        ..., title="Version", description="The version of the workflow represented by an incremental number."
    )
    steps: Dict[int, Union[SubworkflowStepToExport, WorkflowToolStepToExport, WorkflowStepToExport]] = Field(
        {}, title="Steps", description="A dictionary with information about all the steps of the workflow."
    )
```

**File:** lib/galaxy_test/base/workflow_fixtures.py (L34-44)
```python
WORKFLOW_SIMPLE_CAT_TWICE = """
class: GalaxyWorkflow
inputs:
  input1: data
steps:
  first_cat:
    tool_id: cat
    in:
      input1: input1
      queries_0|input2: input1
"""
```

**File:** lib/galaxy_test/base/workflow_fixtures.py (L332-369)
```python
WORKFLOW_NESTED_SIMPLE = """
class: GalaxyWorkflow
inputs:
  outer_input: data
outputs:
  outer_output:
    outputSource: second_cat/out_file1
steps:
  first_cat:
    tool_id: cat1
    in:
      input1: outer_input
  nested_workflow:
    run:
      class: GalaxyWorkflow
      inputs:
        inner_input: data
      outputs:
        workflow_output:
          outputSource: random_lines/out_file1
      steps:
        random_lines:
          tool_id: random_lines1
          state:
            num_lines: 1
            input:
              $link: inner_input
            seed_source:
              seed_source_selector: set_seed
              seed: asdf
    in:
      inner_input: first_cat/out_file1
  second_cat:
    tool_id: cat1
    in:
      input1: nested_workflow/workflow_output
      queries_0|input2: nested_workflow/workflow_output
"""
```

**File:** lib/galaxy_test/base/workflow_fixtures.py (L866-879)
```python
WORKFLOW_WITH_OUTPUTS = """
class: GalaxyWorkflow
inputs:
  input1: data
outputs:
  wf_output_1:
    outputSource: first_cat/out_file1
steps:
  first_cat:
    tool_id: cat1
    in:
      input1: input1
      queries_0|input2: input1
"""
```

**File:** lib/galaxy/webapps/galaxy/api/workflows.py (L339-365)
```python
        style = kwd.get("style", "export")
        download_format = kwd.get("format")
        version = kwd.get("version")
        history = None
        if history_id := kwd.get("history_id"):
            history = self.history_manager.get_accessible(
                self.decode_id(history_id), trans.user, current_history=trans.history
            )
        ret_dict = self.workflow_contents_manager.workflow_to_dict(
            trans, stored_workflow, style=style, version=version, history=history
        )
        if download_format == "json-download":
            sname = stored_workflow.name
            sname = "".join(c in util.FILENAME_VALID_CHARS and c or "_" for c in sname)[0:150]
            if ret_dict.get("format-version", None) == "0.1":
                extension = "ga"
            else:
                extension = "gxwf.json"
            trans.response.headers["Content-Disposition"] = (
                f'attachment; filename="Galaxy-Workflow-{sname}.{extension}"'
            )
            trans.response.set_content_type("application/galaxy-archive")

        if style == "format2" and download_format != "json-download":
            return ordered_dump(ret_dict)
        else:
            return format_return_as_json(ret_dict, pretty=True)
```

**File:** lib/galaxy_test/api/test_workflows.py (L74-87)
```python
WORKFLOW_SIMPLE = """
class: GalaxyWorkflow
name: Simple Workflow
inputs:
  input1: data
outputs:
  wf_output_1:
    outputSource: first_cat/out_file1
steps:
  first_cat:
    tool_id: cat1
    in:
      input1: input1
"""
```
