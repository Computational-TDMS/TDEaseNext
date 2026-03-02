"""
Tool JSON Schema - 工具定义规范

用于定义工具的 JSON 结构，支持前端动态渲染（表单、按钮、下拉框）。
工具配置由后端运行环境决定，存储在 data/tools/ 和 config/tools/。
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ToolParamDef(BaseModel):
    """单个参数的 UI 配置，供前端渲染输入框/按钮/下拉框"""

    flag: str = Field(..., description="命令行标志，如 -a, --format")
    type: str = Field(
        default="value",
        description="参数类型: value(输入框), boolean(开关), choice(下拉选择)",
    )
    choices: Optional[List[str]] = Field(None, description="choice 类型时的可选值")
    default: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(False, description="是否必填")
    description: Optional[str] = Field(None, description="参数说明")
    short: Optional[bool] = Field(None, description="是否为短标志（如 -a）")


class ToolInputDef(BaseModel):
    """工具输入定义"""

    id: str = Field(..., description="输入句柄 ID")
    name: Optional[str] = Field(None, description="显示名称")
    type: str = Field(default="file", description="类型: file, string 等")
    dataType: Optional[str] = Field(None, description="数据类型，如 raw, mzml, fasta")
    required: Optional[bool] = Field(True, description="是否必填")
    accept: Optional[List[str]] = Field(None, description="接受的文件扩展名")


class ToolOutputDef(BaseModel):
    """工具输出定义"""

    id: Optional[str] = Field(None, description="输出句柄 ID")
    name: Optional[str] = Field(None, description="显示名称")
    type: str = Field(default="file", description="类型")
    dataType: Optional[str] = Field(None, description="数据类型")
    pattern: str = Field(..., description="输出文件模式，如 {sample}.mzML")
    handle: Optional[str] = Field(None, description="句柄，用于连线匹配")
    provides: Optional[List[str]] = Field(None, description="提供的数据类型列表")

    @property
    def effective_handle(self) -> str:
        return self.handle or self.id or "output"


class ToolDefinition(BaseModel):
    """
    工具完整定义 (JSON Schema)

    支持两种格式的兼容：
    - 扁平结构: id, name, kind, toolPath, params, param_mapping, ...
    - 与现有 config/tools/*.json 格式兼容
    """

    id: str = Field(..., description="工具唯一 ID")
    name: str = Field(..., description="工具显示名称")
    kind: str = Field(default="command", description="command | script")
    description: Optional[str] = Field(None, description="工具描述")

    # 执行相关
    toolPath: Optional[str] = Field(None, description="可执行路径或脚本路径")
    executionMode: Optional[str] = Field(None, description="native | docker")
    conda_env: Optional[str] = Field(None, description="Conda 环境路径")

    # 输入输出
    inputs: List[Union[ToolInputDef, Dict[str, Any]]] = Field(default_factory=list)
    outputs: List[Union[ToolOutputDef, Dict[str, Any]]] = Field(default_factory=list)
    input_params: List[str] = Field(default_factory=list, description="输入参数名列表")
    input_param_flags: Dict[str, str] = Field(default_factory=dict, description="参数名到标志的映射")
    input_flag: Optional[str] = Field(None, description="输入总标志")
    output_flag: Optional[str] = Field(None, description="输出总标志")
    output_flag_supported: bool = Field(True, description="是否支持输出目录标志")
    output_patterns: Optional[List[Dict[str, str]]] = Field(
        None,
        description="输出模式 [{pattern, handle}]，与 outputs 二选一",
    )
    positional_params: Optional[List[str]] = Field(None, description="位置参数顺序")

    # 参数配置（前端渲染用）
    params: List[Dict[str, Any]] = Field(default_factory=list, description="参数 UI 定义")
    param_mapping: Dict[str, Union[ToolParamDef, Dict[str, Any]]] = Field(
        default_factory=dict,
        description="参数名 -> 命令行标志映射，含 type/choices 等 UI 配置",
    )
    use_params_json: Optional[bool] = Field(None, description="是否通过 JSON 传参")

    class Config:
        extra = "allow"
        populate_by_name = True

    def get_tool_path(self) -> str:
        return (self.toolPath or getattr(self, "tool_path", None) or "").strip()

    def get_output_patterns(self) -> List[Dict[str, str]]:
        """获取输出模式列表，兼容 outputs 与 output_patterns"""
        if self.output_patterns:
            return self.output_patterns
        result = []
        for out in self.outputs:
            if isinstance(out, dict):
                pat = out.get("pattern")
                handle = out.get("handle") or out.get("id", "output")
            else:
                pat = getattr(out, "pattern", None)
                handle = getattr(out, "effective_handle", "output")
            if pat:
                result.append({"pattern": pat, "handle": handle})
        return result

    def get_input_params(self) -> List[str]:
        if self.input_params:
            return self.input_params
        return [inp.get("id", "input") for inp in self.inputs if isinstance(inp, dict)]
