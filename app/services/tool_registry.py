"""
Tool Registry - 工具注册中心

从 config/tools/、config/tools/profiles/<profile>/ 和 data/tools/ 加载 JSON 定义，
提供统一查询接口。支持环境 profile 覆盖与本地 data 覆盖。
"""
import json
import logging
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from app.schemas.tool import ToolDefinition
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

_ENV_PROFILE_KEYS: Tuple[str, ...] = ("TDEASE_TOOL_PROFILES", "TDEASE_TOOL_PROFILE")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|\\\\\?\\)")


class NonPortableToolConfigError(ValueError):
    """Raised when shared config contains machine-local absolute executable paths."""


def _is_absolute_machine_path(value: str) -> bool:
    literal = value.strip()
    if not literal:
        return False

    # Environment-variable based indirection is allowed in shared config.
    if literal.startswith(("${", "$", "%", "{")):
        return False
    # Relative references are portable.
    if literal.startswith(("./", "../", ".\\", "..\\")):
        return False

    if _WINDOWS_ABSOLUTE_RE.match(literal):
        return True
    return literal.startswith("/")


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _extract_executable(tool_data: Dict[str, Any]) -> str:
    command = tool_data.get("command")
    if isinstance(command, dict):
        executable = command.get("executable")
        if isinstance(executable, str):
            return executable
    tool_path = tool_data.get("toolPath") or tool_data.get("tool_path")
    return str(tool_path) if isinstance(tool_path, str) else ""


def _validate_portable_shared_tool(tool_data: Dict[str, Any], *, source: str) -> None:
    executable = _extract_executable(tool_data)
    if executable and _is_absolute_machine_path(executable):
        tool_id = tool_data.get("id") or "<unknown>"
        raise NonPortableToolConfigError(
            f"Tool '{tool_id}' in {source} uses non-portable absolute executable path: {executable}. "
            "Use command names in shared config and put machine-specific absolute overrides in data/tools/*.json."
        )


def _parse_profiles(profile: Optional[str | Sequence[str]]) -> List[str]:
    raw: List[str] = []
    if profile is None:
        for env_key in _ENV_PROFILE_KEYS:
            env_value = os.environ.get(env_key, "")
            if env_value:
                raw.extend(env_value.split(","))
    elif isinstance(profile, str):
        raw.extend(profile.split(","))
    else:
        for item in profile:
            raw.extend(str(item).split(","))

    ordered: List[str] = []
    seen = set()
    for item in raw:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        ordered.append(normalized)
        seen.add(normalized)
    return ordered


def _parse_tool_entries(file_path: Path, payload: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    # 兼容单工具格式：{ "id": "...", ... }
    if "id" in payload:
        tool_id = str(payload["id"])
        normalized = dict(payload)
        normalized["id"] = tool_id
        yield tool_id, normalized
        return

    # 兼容文件名同名嵌套格式：{ "<file_stem>": { ... } }
    if file_path.stem in payload and isinstance(payload[file_path.stem], dict):
        tool_id = file_path.stem
        nested = dict(payload[file_path.stem])
        nested.setdefault("id", tool_id)
        yield tool_id, nested
        return

    # 兜底：将当前对象视作工具定义，ID 取文件名
    fallback = dict(payload)
    fallback.setdefault("id", file_path.stem)
    yield str(fallback["id"]), fallback


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _load_validation_schema() -> Dict[str, Any]:
    """Load JSON schema for tool definition validation"""
    schema_path = Path(__file__).parent.parent / "schemas" / "validation" / "tool_definition_schema.json"
    if schema_path.exists():
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load validation schema: {e}")
    return {}


def _validate_tool_definition(tool_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate tool definition against JSON schema

    Returns:
        True if valid or schema not available, False if validation fails
    """
    if not schema:
        return True  # Skip validation if schema not available

    try:
        validate(instance=tool_data, schema=schema)
        return True
    except ValidationError as e:
        logger.warning(f"Tool '{tool_data.get('id')}' failed validation: {e.message}")
        return False


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

    加载顺序（优先级从低到高）：
    1. config/tools/*.json
    2. config/tools/profiles/<profile>/*.json（按 profile 列表顺序叠加）
    3. data/tools/*.json
    """

    def __init__(
        self,
        config_tools_dir: Optional[Path] = None,
        data_tools_dir: Optional[Path] = None,
        profiles: Optional[str | Sequence[str]] = None,
        config_profiles_dir: Optional[Path] = None,
    ):
        root = _project_root()
        self._config_tools = config_tools_dir or (root / "config" / "tools")
        self._config_profiles = config_profiles_dir or (self._config_tools / "profiles")
        self._data_tools = data_tools_dir or (root / "data" / "tools")
        self._profiles = _parse_profiles(profiles)
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        self._validation_schema = _load_validation_schema()
        self.reload()

    @property
    def active_profiles(self) -> List[str]:
        return list(self._profiles)

    def _load_tool_layer(
        self,
        dir_path: Path,
        *,
        source_label: str,
        validate_portability: bool,
    ) -> Dict[str, Dict[str, Any]]:
        loaded: Dict[str, Dict[str, Any]] = {}
        if not dir_path.exists() or not dir_path.is_dir():
            return loaded

        for fp in sorted(dir_path.glob("*.json")):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    logger.warning("Load tool file %s failed: root JSON must be object", fp)
                    continue

                for tool_id, raw_tool in _parse_tool_entries(fp, data):
                    if validate_portability:
                        _validate_portable_shared_tool(raw_tool, source=f"{source_label}/{fp.name}")
                    loaded[tool_id] = raw_tool
            except NonPortableToolConfigError as e:
                logger.warning(str(e))
            except Exception as e:
                logger.warning("Load tool file %s failed: %s", fp, e)
        return loaded

    def reload(self) -> None:
        """重新加载所有工具定义"""
        self._registry.clear()
        self._definitions.clear()

        # Layer 1: shared base config (portable by design)
        merged = self._load_tool_layer(
            self._config_tools,
            source_label="config/tools",
            validate_portability=True,
        )

        # Layer 2: shared profile overrides (also must stay portable in repo)
        for profile in self._profiles:
            profile_dir = self._config_profiles / profile
            if not profile_dir.exists():
                logger.warning("Tool profile '%s' not found at %s", profile, profile_dir)
                continue
            overrides = self._load_tool_layer(
                profile_dir,
                source_label=f"config/tools/profiles/{profile}",
                validate_portability=True,
            )
            for tool_id, override_tool in overrides.items():
                if tool_id in merged:
                    merged[tool_id] = _deep_merge_dict(merged[tool_id], override_tool)
                else:
                    merged[tool_id] = override_tool

        # Layer 3: local data overrides (machine-specific paths are allowed)
        local_overrides = self._load_tool_layer(
            self._data_tools,
            source_label="data/tools",
            validate_portability=False,
        )
        for tool_id, override_tool in local_overrides.items():
            if tool_id in merged:
                merged[tool_id] = _deep_merge_dict(merged[tool_id], override_tool)
            else:
                merged[tool_id] = override_tool

        for tool_id, raw_tool in merged.items():
            try:
                normalized = _normalize_tool_data(raw_tool)
                normalized["id"] = tool_id
                if not _validate_tool_definition(normalized, self._validation_schema):
                    logger.warning("Skipping tool '%s' due to validation errors", tool_id)
                    continue
                self._registry[tool_id] = normalized
                try:
                    self._definitions[tool_id] = ToolDefinition(**normalized)
                except Exception as e:
                    logger.warning("ToolDefinition parse skip %s: %s", tool_id, e)
            except Exception as e:
                logger.warning("Normalize tool '%s' failed: %s", tool_id, e)

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
        # Include schema in outputs
        outputs_with_schema = []
        for o in (d.get_output_patterns() or d.outputs):
            if isinstance(o, dict):
                output_data = {
                    "pattern": o.get("pattern", ""),
                    "handle": o.get("handle") or o.get("id", "output")
                }
                if "schema" in o:
                    output_data["schema"] = o["schema"]
            else:
                output_data = {
                    "pattern": getattr(o, "pattern", ""),
                    "handle": getattr(o, "effective_handle", "output")
                }
                if hasattr(o, 'schema') and o.schema:
                    output_data["schema"] = o.schema
            outputs_with_schema.append(output_data)

        return {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "executionMode": d.executionMode,
            "params": params_ui,
            "inputs": [i if isinstance(i, dict) else i.model_dump() for i in d.inputs],
            "outputs": outputs_with_schema,
            "param_mapping": {k: (v if isinstance(v, dict) else v.model_dump())
                             for k, v in d.param_mapping.items()},
            "defaultMapping": d.defaultMapping if hasattr(d, 'defaultMapping') else None,
        }


# 单例，供依赖注入使用
_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
