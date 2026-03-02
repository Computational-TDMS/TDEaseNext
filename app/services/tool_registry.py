"""
Tool Registry - 工具注册中心

从 data/tools/ 和 config/tools/ 加载 JSON 定义，提供统一查询接口。
工具配置由后端运行环境决定，支持用户自定义工具。
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas.tool import ToolDefinition

logger = logging.getLogger(__name__)


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _normalize_tool_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    标准化工具数据 - 仅支持新 JSON Schema 格式。

    新格式 (Opus redesign):
    - executionMode, command, ports, parameters, output

    不再支持旧格式字段 (tool_type, param_mapping, output_flag_supported, etc.)
    """
    data = dict(raw)

    # 仅保留最小兼容性：大小写变体
    if "tool_path" in data and "toolPath" not in data:
        data["toolPath"] = data["tool_path"]
    if "toolType" in data and "executionMode" not in data:
        data["executionMode"] = data["toolType"]

    # 验证必需字段
    if "id" not in data:
        raise ValueError("Tool definition missing required field: 'id'")
    if "executionMode" not in data:
        raise ValueError(f"Tool '{data.get('id')}' missing required field: 'executionMode'")
    if "ports" not in data:
        raise ValueError(f"Tool '{data.get('id')}' missing required field: 'ports'")
    if "parameters" not in data:
        # parameters 可以为空对象，但必须存在
        data["parameters"] = {}

    return data


class ToolRegistry:
    """
    工具注册中心

    加载顺序：config/tools/*.json -> data/tools/*.json
    后者覆盖前者（同 id 时）。
    """

    def __init__(
        self,
        config_tools_dir: Optional[Path] = None,
        data_tools_dir: Optional[Path] = None,
    ):
        root = _project_root()
        self._config_tools = config_tools_dir or (root / "config" / "tools")
        self._data_tools = data_tools_dir or (root / "data" / "tools")
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        self.reload()

    def reload(self) -> None:
        """重新加载所有工具定义"""
        self._registry.clear()
        self._definitions.clear()

        for dir_path in (self._config_tools, self._data_tools):
            if not dir_path.exists() or not dir_path.is_dir():
                continue
            for fp in dir_path.glob("*.json"):
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if not isinstance(data, dict):
                        continue
                    # 支持单工具 { "id": "x", ... } 或多工具 { "tool_id": { ... } }
                    if "id" in data:
                        tool_id = data["id"]
                        normalized = _normalize_tool_data(data)
                        self._registry[tool_id] = normalized
                        try:
                            self._definitions[tool_id] = ToolDefinition(**normalized)
                        except Exception as e:
                            logger.warning("ToolDefinition parse skip %s: %s", tool_id, e)
                    elif fp.stem in data and isinstance(data[fp.stem], dict):
                        tool_id = fp.stem
                        normalized = _normalize_tool_data(data[fp.stem])
                        normalized.setdefault("id", tool_id)
                        self._registry[tool_id] = normalized
                        try:
                            self._definitions[tool_id] = ToolDefinition(**normalized)
                        except Exception as e:
                            logger.warning("ToolDefinition parse skip %s: %s", tool_id, e)
                except Exception as e:
                    logger.warning("Load tool file %s failed: %s", fp, e)

    def get(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """获取工具原始数据（兼容旧代码）"""
        return self._registry.get(tool_id)

    def get_definition(self, tool_id: str) -> Optional[ToolDefinition]:
        """获取工具 Pydantic 定义"""
        return self._definitions.get(tool_id)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """列出所有工具（原始格式，兼容 ToolRegistry.list_tools）"""
        return self._registry.copy()

    def list_definitions(self) -> Dict[str, ToolDefinition]:
        """列出所有工具定义"""
        return self._definitions.copy()

    def get_ui_schema(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工具的 UI 配置，供前端渲染表单/按钮/下拉框。

        Returns:
            {
                "id": "...",
                "name": "...",
                "params": [ { "id", "name", "type", "choices", "default", ... } ],
                "inputs": [...],
                "outputs": [...],
                "param_mapping": { ... }
            }
        """
        d = self.get_definition(tool_id)
        if not d:
            return None
        params_ui = []
        for p in d.params:
            if isinstance(p, dict):
                params_ui.append(p)
        if not params_ui and d.param_mapping:
            for name, m in d.param_mapping.items():
                pm = m if isinstance(m, dict) else m.model_dump()
                params_ui.append({
                    "id": name,
                    "name": name,
                    "type": pm.get("type", "value"),
                    "flag": pm.get("flag"),
                    "choices": pm.get("choices"),
                    "default": pm.get("default"),
                    "required": pm.get("required", False),
                })
        return {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "params": params_ui,
            "inputs": [i if isinstance(i, dict) else i.model_dump() for i in d.inputs],
            "outputs": [
                {"pattern": o.get("pattern") if isinstance(o, dict) else getattr(o, "pattern", ""),
                 "handle": (o.get("handle") or o.get("id")) if isinstance(o, dict) else getattr(o, "effective_handle", "output")}
                for o in (d.get_output_patterns() or d.outputs)
            ],
            "param_mapping": {k: (v if isinstance(v, dict) else v.model_dump())
                             for k, v in d.param_mapping.items()},
        }


# 单例，供依赖注入使用
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
