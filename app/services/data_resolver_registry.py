"""
Data Resolver Registry - 通用交互式数据解析器注册中心

根据选择状态加载详细数据的 resolver（如 topmsv_prsm）在此注册，
从工具定义的 subResources 等配置读取路径与行为，避免硬编码。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from app.services.node_data_service import (
    _get_output_patterns,
    _resolve_output_paths,
    resolve_node_outputs,
)
from app.services.topmsv_data_service import build_topmsv_prsm_payload
from app.services.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)


def _resolve_node_tool_id(node_data: Dict[str, Any]) -> str:
    return (
        node_data.get("type")
        or (node_data.get("data") or {}).get("type")
        or (node_data.get("nodeConfig") or {}).get("toolId")
        or ""
    )


def _get_tool_info_and_sub_resources_from_snapshot(
    workflow_snapshot: Dict[str, Any],
    node_id: str,
    port_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    nodes = workflow_snapshot.get("nodes", []) if isinstance(workflow_snapshot, dict) else []
    node_data = next((n for n in nodes if n.get("id") == node_id), None)
    if not node_data:
        return None, None

    tool_id = _resolve_node_tool_id(node_data)
    if not tool_id:
        return None, None

    registry = get_tool_registry()
    tool_info = registry.get(tool_id)
    if not tool_info:
        return None, None

    outputs = tool_info.get("ports", {}).get("outputs", [])
    port_id_lower = (port_id or "").strip().lower()
    sub_resources = None
    for out in outputs:
        if not isinstance(out, dict):
            continue
        oid = (out.get("id") or out.get("handle") or "").strip().lower()
        if oid == port_id_lower:
            sub_resources = out.get("subResources")
            break

    return tool_info, sub_resources


def _get_node_tool_info_and_sub_resources(
    db,
    execution_id: str,
    node_id: str,
    port_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Load workflow snapshot for execution, resolve node's tool_id, return tool_info and
    subResources for the given output port (if any).
    """
    cursor = db.cursor()
    cursor.execute(
        "SELECT workflow_snapshot FROM executions WHERE id = ?",
        (execution_id,),
    )
    row = cursor.fetchone()
    if not row or not row[0]:
        return None, None

    try:
        snapshot = json.loads(row[0]) if isinstance(row[0], str) else row[0]
    except (TypeError, json.JSONDecodeError):
        return None, None

    return _get_tool_info_and_sub_resources_from_snapshot(snapshot, node_id, port_id)


def _load_workflow_snapshot_and_workspace(
    db,
    workflow_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    cursor = db.cursor()
    cursor.execute(
        "SELECT vueflow_data, workspace_path FROM workflows WHERE id = ?",
        (workflow_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None, None

    snapshot_raw = row[0]
    workspace_raw = row[1]

    try:
        snapshot = json.loads(snapshot_raw) if isinstance(snapshot_raw, str) else snapshot_raw
    except (TypeError, json.JSONDecodeError):
        return None, None
    if not isinstance(snapshot, dict):
        return None, None

    workspace_path = Path(str(workspace_raw)) if workspace_raw else None
    return snapshot, workspace_path


def _resolve_sample_context_for_workflow(
    workflow_snapshot: Dict[str, Any],
    workspace_path: Optional[Path],
    explicit_sample: Optional[str] = None,
) -> Tuple[Dict[str, str], str]:
    metadata = workflow_snapshot.get("metadata", {}) if isinstance(workflow_snapshot, dict) else {}
    sample_context: Dict[str, str] = {}
    source = "default"

    metadata_ctx = metadata.get("sample_context")
    if isinstance(metadata_ctx, dict):
        sample_context.update({k: str(v) for k, v in metadata_ctx.items() if isinstance(v, (str, int, float))})
        if sample_context:
            source = "workflow_metadata.sample_context"

    if explicit_sample:
        sample_context["sample"] = explicit_sample
        source = "query.sample"

    if not sample_context.get("sample"):
        samples_field = metadata.get("samples")
        if isinstance(samples_field, list) and samples_field:
            sample_context["sample"] = str(samples_field[0])
            source = "workflow_metadata.samples[0]"
        else:
            sample_field = metadata.get("sample")
            if isinstance(sample_field, str) and sample_field.strip():
                sample_context["sample"] = sample_field.strip()
                source = "workflow_metadata.sample"

    if (not sample_context or not sample_context.get("sample")) and workspace_path:
        samples_file = workspace_path / "samples.json"
        if samples_file.exists():
            try:
                with open(samples_file, "r", encoding="utf-8") as fp:
                    payload = json.load(fp)
                samples_map = payload.get("samples", {})
                if isinstance(samples_map, dict) and samples_map:
                    first_sample = next(iter(samples_map.values()))
                    if isinstance(first_sample, dict):
                        first_ctx = first_sample.get("context", {}) or {}
                        if isinstance(first_ctx, dict):
                            for key, value in first_ctx.items():
                                if key not in sample_context and isinstance(value, (str, int, float)):
                                    sample_context[key] = str(value)
                            source = "workspace.samples_json.first_context"
            except Exception:
                logger.warning(
                    "[data_resolver_registry] Failed reading samples.json for workflow-level context fallback",
                    exc_info=True,
                )

    if not sample_context:
        sample_context = {"sample": "default"}
        source = "default"
    elif not sample_context.get("sample"):
        sample_context["sample"] = "default"
        source = f"{source}+default.sample"

    return sample_context, source


def _discover_html_root_fallback(workspace_path: Optional[Path]) -> Optional[Path]:
    if not workspace_path or not workspace_path.exists():
        return None

    candidates = [p for p in workspace_path.glob("*_html") if p.is_dir()]
    if not candidates:
        try:
            candidates = [p for p in workspace_path.rglob("*_html") if p.is_dir()]
        except Exception:
            candidates = []
    if not candidates:
        return None
    candidates.sort(key=lambda p: (len(p.parts), str(p)))
    return candidates[0]


def _resolve_outputs_for_workflow(
    workflow_snapshot: Dict[str, Any],
    workspace_path: Optional[Path],
    node_id: str,
    tool_info: Dict[str, Any],
    requested_port_id: str,
    explicit_sample: Optional[str],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    sample_context, context_source = _resolve_sample_context_for_workflow(
        workflow_snapshot=workflow_snapshot,
        workspace_path=workspace_path,
        explicit_sample=explicit_sample,
    )
    resolution: Dict[str, Any] = {
        "mode": "workflow",
        "sample_context_source": context_source,
        "sample_context": sample_context,
    }

    if not workspace_path:
        return {"outputs": []}, resolution

    try:
        output_paths = _resolve_output_paths(
            node_id=node_id,
            tool_id=_resolve_node_tool_id(
                next((n for n in workflow_snapshot.get("nodes", []) if n.get("id") == node_id), {}) or {}
            ),
            tool_info=tool_info,
            sample_ctx=sample_context,
            workspace=workspace_path,
        )
        resolution["output_path_resolution"] = "pattern"
    except Exception as exc:
        logger.warning(
            "[data_resolver_registry] Workflow-level output path resolution failed for node=%s: %s",
            node_id,
            exc,
        )
        output_paths = []
        resolution["output_path_resolution"] = "pattern_failed"

    patterns = _get_output_patterns(tool_info)
    outputs = []
    for idx, file_path in enumerate(output_paths):
        pattern_info = patterns[idx] if idx < len(patterns) else {}
        output_port_id = pattern_info.get("handle", pattern_info.get("id", f"port_{idx}"))
        if requested_port_id and output_port_id != requested_port_id:
            continue
        outputs.append(
            {
                "port_id": output_port_id,
                "file_path": str(file_path),
                "file_name": file_path.name,
                "exists": file_path.exists(),
                "is_directory": file_path.exists() and file_path.is_dir(),
            }
        )

    if not outputs:
        fallback_root = _discover_html_root_fallback(workspace_path)
        if fallback_root:
            outputs = [
                {
                    "port_id": requested_port_id or "html_folder",
                    "file_path": str(fallback_root),
                    "file_name": fallback_root.name,
                    "exists": True,
                    "is_directory": True,
                }
            ]
            resolution["output_path_resolution"] = "workspace_glob_fallback"

    return {"outputs": outputs}, resolution


def _resolve_html_root_from_outputs(
    output_result: Dict[str, Any],
    port_id: str,
) -> Optional[Path]:
    """Pick HTML root path from resolve_node_outputs result; support port_id or _html dir heuristic."""
    outputs = output_result.get("outputs", [])
    resolved_port = (port_id or "html_folder").strip()
    for output in outputs:
        path_str = output.get("file_path")
        if not isinstance(path_str, str) or not path_str:
            continue
        path = Path(path_str)
        is_port = (output.get("port_id") or "").strip() == resolved_port
        looks_like_html = (
            path.exists()
            and path.is_dir()
            and str(path.name).lower().endswith("_html")
        )
        if is_port or looks_like_html:
            return path if path.exists() and path.is_dir() else None
    return None


def _topmsv_prsm_resolver(
    node_id: str,
    selection_key: str,
    db,
    execution_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    sample: Optional[str] = None,
    port_id: Optional[str] = None,
    spectrum_id: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Resolve TopMSV PrSM payload for a given PrSM ID (selection_key).
    Supports both execution-level and workflow-level addressing.
    """
    del kwargs
    port_id = port_id or "html_folder"
    try:
        prsm_id = int(selection_key)
    except (TypeError, ValueError):
        raise ValueError(f"selection_key must be an integer PrSM ID, got: {selection_key!r}")
    if prsm_id < 0:
        raise ValueError("prsm_id must be non-negative")

    html_root: Optional[Path] = None
    sub_resources: Optional[Dict[str, Any]] = None
    resolution: Dict[str, Any] = {}

    if execution_id:
        output_result = resolve_node_outputs(
            execution_id=execution_id,
            node_id=node_id,
            db=db,
            port_id=port_id,
            include_data=False,
        )
        html_root = _resolve_html_root_from_outputs(output_result, port_id)
        _, sub_resources = _get_node_tool_info_and_sub_resources(
            db, execution_id, node_id, port_id
        )
        resolution = {"mode": "execution", "output_path_resolution": "execution_outputs"}

    elif workflow_id:
        workflow_snapshot, workspace_path = _load_workflow_snapshot_and_workspace(db, workflow_id)
        if not workflow_snapshot:
            raise ValueError(f"Workflow not found or invalid: {workflow_id}")
        tool_info, sub_resources = _get_tool_info_and_sub_resources_from_snapshot(
            workflow_snapshot, node_id, port_id
        )
        if not tool_info:
            raise ValueError(f"Node '{node_id}' not found or tool not registered in workflow '{workflow_id}'")
        output_result, resolution = _resolve_outputs_for_workflow(
            workflow_snapshot=workflow_snapshot,
            workspace_path=workspace_path,
            node_id=node_id,
            tool_info=tool_info,
            requested_port_id=port_id,
            explicit_sample=sample,
        )
        html_root = _resolve_html_root_from_outputs(output_result, port_id)
        if not html_root:
            fallback_root = _discover_html_root_fallback(workspace_path)
            if fallback_root:
                html_root = fallback_root
                resolution["output_path_resolution"] = "workspace_glob_fallback"

    else:
        raise ValueError("Either execution_id or workflow_id must be provided")

    if not html_root:
        scope_id = execution_id or workflow_id or "<unknown>"
        raise FileNotFoundError(
            f"No HTML output found on node '{node_id}' (port '{port_id}') in scope '{scope_id}'."
        )

    payload = build_topmsv_prsm_payload(
        html_root=html_root,
        prsm_id=prsm_id,
        spectrum_id=spectrum_id,
        sub_resources=sub_resources,
    )
    result: Dict[str, Any] = {
        "node_id": node_id,
        "port_id": port_id,
        "prsm_id": prsm_id,
        "resolution": resolution,
        **payload,
    }
    if execution_id:
        result["execution_id"] = execution_id
    if workflow_id:
        result["workflow_id"] = workflow_id
    return result


def _legacy_topmsv_prsm_resolver(
    execution_id: str,
    node_id: str,
    selection_key: str,
    db,
    port_id: Optional[str] = None,
    spectrum_id: Optional[int] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Backward-compatible adapter kept for older internal call-sites.
    """
    return _topmsv_prsm_resolver(
        execution_id=execution_id,
        node_id=node_id,
        selection_key=selection_key,
        db=db,
        port_id=port_id,
        spectrum_id=spectrum_id,
        **kwargs,
    )


class DataResolverRegistry:
    """Registry of named resolvers for interactive selection-driven data loading."""

    def __init__(self) -> None:
        self._resolvers: Dict[str, Callable[..., Dict[str, Any]]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.register("topmsv_prsm", _topmsv_prsm_resolver)

    def register(self, name: str, resolver_fn: Callable[..., Dict[str, Any]]) -> None:
        """Register a resolver callable. Signature: (execution_id, node_id, selection_key, db, **kwargs) -> dict."""
        self._resolvers[name] = resolver_fn
        logger.debug("Registered data resolver: %s", name)

    def get(self, name: str) -> Optional[Callable[..., Dict[str, Any]]]:
        return self._resolvers.get(name)

    def resolve(
        self,
        name: str,
        node_id: str,
        selection_key: str,
        db,
        execution_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        **query_params: Any,
    ) -> Dict[str, Any]:
        """
        Invoke a resolver by name. Raises ValueError if unknown resolver or resolver raises.
        """
        resolver = self._resolvers.get(name)
        if not resolver:
            raise ValueError(f"Unknown data resolver: {name}")
        return resolver(
            execution_id=execution_id,
            workflow_id=workflow_id,
            node_id=node_id,
            selection_key=selection_key,
            db=db,
            **query_params,
        )

    def list_resolvers(self) -> list[str]:
        return list(self._resolvers.keys())


_registry: Optional[DataResolverRegistry] = None


def get_data_resolver_registry() -> DataResolverRegistry:
    global _registry
    if _registry is None:
        _registry = DataResolverRegistry()
    return _registry
