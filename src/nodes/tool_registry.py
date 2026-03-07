"""
Legacy ToolRegistry compatibility shim.

Deprecated path:
    src.nodes.tool_registry.ToolRegistry

Authoritative path:
    app.services.tool_registry.ToolRegistry
"""
from __future__ import annotations

import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas.tool import ToolDefinition
from app.services.tool_registry import ToolRegistry as _AuthoritativeToolRegistry

logger = logging.getLogger(__name__)


class ToolRegistry(_AuthoritativeToolRegistry):
    """
    Backward-compatible wrapper over the authoritative ToolRegistry.

    Notes:
    - `registry_file` is treated as a one-time local override layer.
    - New code should import from `app.services.tool_registry`.
    """

    def __init__(self, registry_file: Optional[str] = None):
        warnings.warn(
            "src.nodes.tool_registry.ToolRegistry is deprecated; "
            "use app.services.tool_registry.ToolRegistry instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__()
        if registry_file:
            self._load_legacy_registry_file(Path(registry_file))

    def _load_legacy_registry_file(self, registry_file: Path) -> None:
        if not registry_file.exists():
            logger.warning("Legacy registry file not found: %s", registry_file)
            return

        try:
            with open(registry_file, "r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception as exc:
            logger.warning("Failed loading legacy registry file %s: %s", registry_file, exc)
            return

        if not isinstance(payload, dict):
            logger.warning("Invalid legacy registry payload in %s: expected object", registry_file)
            return

        for tool_id, tool_data in payload.items():
            if not isinstance(tool_data, dict):
                continue
            merged = dict(tool_data)
            merged.setdefault("id", tool_id)
            self._registry[tool_id] = merged
            try:
                self._definitions[tool_id] = ToolDefinition(**merged)
            except Exception as exc:
                # Keep raw compatibility behavior even if pydantic parsing fails.
                logger.warning("Legacy ToolDefinition parse skipped for %s: %s", tool_id, exc)

    # Legacy API aliases
    def get_tool_info(self, tool_type: str) -> Optional[Dict[str, Any]]:
        return self.get(tool_type)

    def register_tool(
        self,
        tool_type: str,
        script_path: str,
        input_params: Optional[List[str]] = None,
        output_patterns: Optional[List[Dict[str, str]]] = None,
        conda_env: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        legacy_outputs = output_patterns or [{"id": "output", "pattern": "{sample}_output"}]
        normalized_outputs: List[Dict[str, str]] = []
        for idx, item in enumerate(legacy_outputs):
            if isinstance(item, dict):
                out = dict(item)
                out.setdefault("id", str(out.get("handle") or f"output_{idx}"))
                normalized_outputs.append(out)
        if not normalized_outputs:
            normalized_outputs = [{"id": "output", "pattern": "{sample}_output"}]
        self._registry[tool_type] = {
            "id": tool_type,
            "name": tool_type,
            "description": description or f"Legacy tool {tool_type}",
            "executionMode": "script",
            "command": {
                "executable": script_path,
                "interpreter": "python",
            },
            "ports": {
                "inputs": [
                    {"id": p, "required": False} for p in (input_params or ["input_files"])
                ],
                "outputs": normalized_outputs,
            },
            "parameters": {},
            "conda_env": conda_env,
        }

    def save_to_file(self, registry_file: str) -> None:
        with open(registry_file, "w", encoding="utf-8") as fp:
            json.dump(self.list_tools(), fp, indent=2, ensure_ascii=False)
