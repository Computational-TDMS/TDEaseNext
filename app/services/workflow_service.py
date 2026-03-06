"""
WorkflowService - 工作流编排服务

基于 FlowEngine + ToolRegistry + LocalExecutor 的原生工作流执行引擎。
支持 dryrun、resume（断点续传）模式。
"""
import logging
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.engine import FlowEngine
from app.core.engine.context import ExecutionContext
from app.core.executor import LocalExecutor, MockExecutor, TaskSpec
from app.services.input_binding_planner import plan_input_bindings
from app.services.tool_registry import get_tool_registry
# 从 node_data_service 导入路径推导函数（保持向后兼容）
from app.services.node_data_service import _resolve_output_paths


logger = logging.getLogger(__name__)


def _get_positional_input_ids(tool_info: Dict[str, Any]) -> List[str]:
    """获取位置参数的端口 ID 顺序：优先 positional_params，否则从 ports.inputs 推导（新 Schema）"""
    positional = tool_info.get("positional_params", [])
    if positional:
        return positional
    inputs = tool_info.get("ports", {}).get("inputs", [])
    pos_inputs = [i for i in inputs if isinstance(i, dict) and i.get("positional", False)]
    pos_inputs.sort(key=lambda x: x.get("positionalOrder", 0))
    return [i.get("id", "") for i in pos_inputs if i.get("id")]


def _resolve_input_paths(
    node_id: str,
    edges: List[Dict],
    nodes_map: Dict[str, Dict],
    tools_registry: Dict[str, Dict],
    sample_ctx: Dict[str, str],
    workspace: Path,
    completed_outputs: Dict[str, List[Path]],
    target_tool_id: str = "",
) -> Dict[str, Path]:
    """兼容包装：委托 InputBindingPlanner 解析输入绑定。"""
    _ = sample_ctx, workspace  # 保留签名兼容；规划器当前仅依赖结构化连接与已完成输出
    logger.info("[resolve_input_paths] Called for node=%s tool=%s", node_id, target_tool_id)
    param_to_path, decisions = plan_input_bindings(
        node_id=node_id,
        edges=edges,
        nodes_map=nodes_map,
        tools_registry=tools_registry,
        completed_outputs=completed_outputs,
        target_tool_id=target_tool_id,
    )
    for decision in decisions:
        logger.info(
            "[resolve_input_paths] edge=%s status=%s src=%s real_src=%s target_port=%s idx=%s score=%s reason=%s path=%s",
            decision.edge_id,
            decision.status,
            decision.source_node_id,
            decision.resolved_source_node_id,
            decision.target_port_id,
            decision.selected_output_index,
            decision.score,
            decision.reason,
            decision.selected_output_path,
        )
    logger.info("[resolve_input_paths] Final param_to_path for %s: %s", node_id, param_to_path)
    return param_to_path


def _enrich_sample_context_for_input_nodes(nodes: List[Dict[str, Any]], sample_ctx: Dict[str, str]) -> None:
    """从 data_loader 等节点推导占位符，补全 sample_context."""
    if not isinstance(sample_ctx, dict):
        return

    def _set_if_missing(key: str, value: Optional[str]) -> None:
        if value and key not in sample_ctx:
            sample_ctx[key] = value

    for node in nodes:
        data = node.get("data", {}) or {}
        if data.get("type") != "data_loader":
            continue
        params = data.get("params", {}) or {}
        input_sources = params.get("input_sources") or params.get("input_source") or []
        if isinstance(input_sources, str):
            input_sources = [input_sources]
        if not input_sources:
            continue
        first = Path(input_sources[0])
        _set_if_missing("raw_path", str(first))
        _set_if_missing("input_dir", str(first.parent))
        _set_if_missing("input_basename", first.stem)
        _set_if_missing("input_ext", first.suffix.lstrip("."))  # expect without dot
        _set_if_missing("input_file", first.name)


def _should_skip_node_on_resume(output_paths: List[Path]) -> bool:
    """
    Resume skip policy:
    - no resolved outputs: cannot skip
    - at least one resolved output exists: treat node as already done

    Why "any" instead of "all":
    Some tools (e.g. MSPathFinderT) declare multiple conditional outputs, and
    only a subset is produced in a normal run. Requiring all outputs would
    incorrectly re-run already completed nodes.
    """
    if not output_paths:
        return False
    return any(p.exists() for p in output_paths)


class WorkflowService:
    """工作流编排服务 - 使用新架构"""

    def __init__(
        self,
        tool_registry=None,
        execution_store=None,
        executor=None,
        execution_manager=None,
    ):
        self.tool_registry = tool_registry or get_tool_registry()
        self.tools = self.tool_registry.list_tools()
        self.executor = executor or LocalExecutor(self.tools)
        self.execution_store = execution_store
        self.execution_manager = execution_manager  # 用于注册节点状态以支持取消操作

    def __build_task_spec(
        self,
        nid: str,
        node_data: Dict[str, Any],
        c: ExecutionContext,
        *,
        edges: Optional[List[Dict[str, Any]]] = None,
        nodes_map: Optional[Dict[str, Dict[str, Any]]] = None,
        completed_outputs: Optional[Dict[str, List[Path]]] = None,
    ) -> Optional[TaskSpec]:
        """Build TaskSpec for a node; return None for interactive nodes."""
        tool_id = node_data.get("type", "")
        ti = self.tools.get(tool_id, {})

        if ti.get("executionMode") == "interactive":
            logger.info(f"Skipping interactive node: {nid} (tool: {tool_id})")
            return None

        task_id = f"{c.execution_id}:{nid}"
        logger.debug(f"[WorkflowService] Generated task_id={task_id} for node {nid}")

        params_node = node_data.get("params", {})
        out_paths = _resolve_output_paths(nid, tool_id, ti, c.sample_context, c.workspace_path)
        input_files_dict = _resolve_input_paths(
            nid,
            edges or [],
            nodes_map or {},
            self.tools,
            c.sample_context,
            c.workspace_path,
            completed_outputs or {},
            target_tool_id=tool_id,
        )
        logger.info(f"[WorkflowService] Resolved input_files_dict for node {nid}: {input_files_dict}")

        positional_ids = _get_positional_input_ids(ti)
        if positional_ids:
            in_paths = [input_files_dict[pid] for pid in positional_ids if pid in input_files_dict]
        else:
            in_paths = list(input_files_dict.values())

        if tool_id == "data_loader":
            params_node = {**params_node, "sample_name": c.sample_context.get("sample", "")}

        return TaskSpec(
            node_id=nid,
            tool_id=tool_id,
            params=params_node,
            input_paths=in_paths,
            input_files=input_files_dict,
            output_paths=out_paths,
            workspace_path=c.workspace_path,
            conda_env=ti.get("conda_env"),
            log_callback=c.log_callback,
            task_id=task_id,
        )

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
        skip_path_check = dryrun or simulate
        vres = WorkflowValidator().validate(wf, skip_path_exists=skip_path_check)
        if vres.get("errors"):
            return {"status": "failed", "error": "; ".join(e.get("message", "") for e in vres["errors"])}

        params = parameters or {}
        sample_ctx = params.get("sample_context", {}) or {"sample": params.get("sample", "default")}
        _enrich_sample_context_for_input_nodes(wf.get("nodes", []), sample_ctx)

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
            return _should_skip_node_on_resume(paths)

        def build_task_spec(nid: str, node_data: Dict, c: ExecutionContext) -> Optional[TaskSpec]:
            return self.__build_task_spec(
                nid,
                node_data,
                c,
                edges=edges,
                nodes_map=nodes_map,
                completed_outputs=completed_outputs,
            )

        async def execute_fn(nid: str, node_data: Dict, c: ExecutionContext) -> None:
            spec = build_task_spec(nid, node_data, c)

            # 跳过交互式节点 (返回 None 的 spec)
            if spec is None:
                on_node_state(nid, "skipped")
                return

            # 注册节点开始执行（用于取消操作）
            if self.execution_manager and c.execution_id:
                self.execution_manager.register_node_start(c.execution_id, nid)

            try:
                await executor.execute(spec)
                tool_id = node_data.get("type", "")
                ti = self.tools.get(tool_id, {})
                completed_outputs[nid] = _resolve_output_paths(nid, tool_id, ti, c.sample_context, c.workspace_path)
            finally:
                # 注册节点完成（用于取消操作）
                if self.execution_manager and c.execution_id:
                    self.execution_manager.register_node_complete(c.execution_id, nid)

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
