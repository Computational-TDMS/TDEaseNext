"""
WorkflowService - 工作流编排服务

基于 FlowEngine + ToolRegistry + LocalExecutor 的原生工作流执行引擎。
支持 dryrun、resume（断点续传）模式。
"""
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.engine import FlowEngine, WorkflowGraph, NodeState
from app.core.engine.context import ExecutionContext
from app.core.executor import LocalExecutor, MockExecutor, TaskSpec
from app.services.tool_registry import get_tool_registry
from src.workflow.validator import validate_placeholders

logger = logging.getLogger(__name__)


def _resolve_output_paths(
    node_id: str,
    tool_id: str,
    tool_info: Dict[str, Any],
    sample_ctx: Dict[str, str],
    workspace: Path,
) -> List[Path]:
    """根据 output_patterns 和 sample_ctx 解析输出路径"""
    patterns = tool_info.get("output_patterns", [])
    if not patterns and tool_info.get("outputs"):
        for o in tool_info["outputs"]:
            if isinstance(o, dict) and o.get("pattern"):
                patterns.append({
                    "pattern": o["pattern"],
                    "handle": o.get("handle") or o.get("id", "output"),
                })
    if not patterns:
        return []
    result = []
    for p in patterns:
        pat = p.get("pattern", "") if isinstance(p, dict) else str(p)

        # Validate all placeholders are present before formatting
        required = set(re.findall(r"\{(\w+)\}", pat))
        if required:
            validate_placeholders(required, sample_ctx, pattern_hint=pat)

        # Now format with confidence
        resolved = pat.format(**sample_ctx)
        result.append(workspace / resolved)

    return result


def _resolve_input_paths(
    node_id: str,
    edges: List[Dict],
    nodes_map: Dict[str, Dict],
    tools_registry: Dict[str, Dict],
    sample_ctx: Dict[str, str],
    workspace: Path,
    completed_outputs: Dict[str, List[Path]],
    target_tool_id: str = "",
) -> List[Path]:
    """根据边和上游节点输出解析输入路径。若有 positional_params 则按该顺序排列。"""
    param_to_path: Dict[str, Path] = {}
    for e in edges:
        if e.get("target") != node_id:
            continue
        src_id = e.get("source")
        src_handle = (e.get("sourceHandle") or "").replace("output-", "")
        tgt_handle = (e.get("targetHandle") or "").replace("input-", "")
        if not src_id or src_id not in completed_outputs:
            continue
        src_outputs = completed_outputs[src_id]
        src_node = nodes_map.get(src_id, {})
        src_data = src_node.get("data", {})
        src_tool = src_data.get("type", "")
        src_info = tools_registry.get(src_tool, {})
        patterns = src_info.get("output_patterns", [])
        if not patterns:
            if tgt_handle and src_outputs:
                param_to_path[tgt_handle] = src_outputs[0]
            continue
        for p in patterns:
            h = p.get("handle", "") if isinstance(p, dict) else ""
            if not src_handle or h == src_handle:
                idx = patterns.index(p) if isinstance(patterns[0], dict) else 0
                if idx < len(src_outputs) and tgt_handle:
                    param_to_path[tgt_handle] = src_outputs[idx]
                break
    positional = tools_registry.get(target_tool_id, {}).get("positional_params", [])
    if positional:
        return [param_to_path[p] for p in positional if p in param_to_path]
    return list(param_to_path.values())


class WorkflowService:
    """工作流编排服务 - 使用新架构"""

    def __init__(
        self,
        tool_registry=None,
        execution_store=None,
        executor=None,
    ):
        self.tool_registry = tool_registry or get_tool_registry()
        self.tools = self.tool_registry.list_tools()
        self.executor = executor or LocalExecutor(self.tools)
        self.execution_store = execution_store

    async def execute_workflow(
        self,
        workflow_json: Dict[str, Any],
        workspace_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        dryrun: bool = False,
        resume: bool = False,
        simulate: bool = False,
        execution_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        log_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        执行工作流（同步入口，供后台任务调用）

        Returns:
            {"status": "completed"|"failed", "execution_id": str, "nodes": {...}, "error": ...}
        """
        from src.workflow.normalizer import WorkflowNormalizer
        from src.workflow.validator import WorkflowValidator

        wf = WorkflowNormalizer().normalize(workflow_json)
        vres = WorkflowValidator().validate(wf)
        if vres.get("errors"):
            return {"status": "failed", "error": "; ".join(e.get("message", "") for e in vres["errors"])}

        params = parameters or {}
        sample_ctx = params.get("sample_context", {}) or {"sample": params.get("sample", "default")}

        ex_id = execution_id or str(uuid.uuid4())
        executor = MockExecutor(self.tools) if simulate else self.executor
        ctx = ExecutionContext(
            workspace_path=Path(workspace_path),
            sample_context=sample_ctx,
            config_overrides=params,
            dryrun=dryrun,
            resume=resume,
            execution_id=ex_id,
            workflow_id=workflow_id,
            log_callback=log_callback,
        )

        nodes_map = {n["id"]: n for n in wf.get("nodes", [])}
        edges = wf.get("edges", [])
        completed_outputs: Dict[str, List[Path]] = {}

        def output_check(node_id: str, node_data: Dict, c: ExecutionContext) -> bool:
            tool_id = node_data.get("type", "")
            ti = self.tools.get(tool_id, {})
            paths = _resolve_output_paths(node_id, tool_id, ti, c.sample_context, c.workspace_path)
            if not paths:
                return False
            return all(p.exists() for p in paths)

        def build_task_spec(nid: str, node_data: Dict, c: ExecutionContext) -> TaskSpec:
            tool_id = node_data.get("type", "")
            params_node = node_data.get("params", {})
            ti = self.tools.get(tool_id, {})
            out_paths = _resolve_output_paths(nid, tool_id, ti, c.sample_context, c.workspace_path)
            in_paths = _resolve_input_paths(
                nid, edges, nodes_map, self.tools, c.sample_context, c.workspace_path, completed_outputs,
                target_tool_id=tool_id,
            )
            return TaskSpec(
                node_id=nid,
                tool_id=tool_id,
                params=params_node,
                input_paths=in_paths,
                output_paths=out_paths,
                workspace_path=c.workspace_path,
                conda_env=ti.get("conda_env"),
                log_callback=c.log_callback,
            )

        async def execute_fn(nid: str, node_data: Dict, c: ExecutionContext) -> None:
            spec = build_task_spec(nid, node_data, c)
            await executor.execute(spec)
            tool_id = node_data.get("type", "")
            ti = self.tools.get(tool_id, {})
            completed_outputs[nid] = _resolve_output_paths(nid, tool_id, ti, c.sample_context, c.workspace_path)

        def on_node_state(nid: str, state: str) -> None:
            if self.execution_store and ctx.execution_id:
                try:
                    self.execution_store.update_node_status(
                        ctx.execution_id, nid, state,
                        progress=100 if state in ("completed", "skipped") else 0,
                    )
                except Exception as e:
                    logger.warning("Update node status failed: %s", e)

        def on_node_skipped(nid: str, node_data: Dict[str, Any]) -> None:
            """Resume 模式下节点被跳过时，仍需将其输出路径写入 completed_outputs，供下游解析输入"""
            tool_id = node_data.get("type", "")
            ti = self.tools.get(tool_id, {})
            paths = _resolve_output_paths(nid, tool_id, ti, ctx.sample_context, ctx.workspace_path)
            if paths:
                completed_outputs[nid] = paths

        engine = FlowEngine(
            wf, ctx,
            execute_fn=execute_fn,
            output_check_fn=output_check,
            on_node_state=on_node_state,
            on_node_skipped=on_node_skipped,
        )

        result = await engine.run()
        result["execution_id"] = ex_id
        if simulate and isinstance(executor, MockExecutor):
            result["simulated_tasks"] = executor.executed_tasks
        return result
