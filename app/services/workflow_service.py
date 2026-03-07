"""
WorkflowService - 工作流编排服务

基于 FlowEngine + ToolRegistry + LocalExecutor 的原生工作流执行引擎。
支持 dryrun、resume（断点续传）模式。
"""
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.core.engine import FlowEngine
from app.core.engine.context import ExecutionContext
from app.core.executor import LocalExecutor, MockExecutor, TaskSpec
from app.services.input_binding_planner import (
    BindingDecision,
    InputBindingContractError,
    plan_input_bindings,
)
from app.services.tool_registry import get_tool_registry
# 从 node_data_service 导入路径推导函数（保持向后兼容）
from app.services.node_data_service import _get_output_patterns, _resolve_output_paths


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
    *,
    enforce_contracts: bool = False,
    return_diagnostics: bool = False,
) -> Dict[str, Path] | tuple[Dict[str, Path], List[BindingDecision]]:
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
        enforce_contracts=enforce_contracts,
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
    if return_diagnostics:
        return param_to_path, decisions
    return param_to_path


def _get_nested(node_data: Dict[str, Any], path: str) -> Any:
    """Resolve path like 'params.input_sources[0]' from node data (data.params.input_sources[0])."""
    if not path.strip():
        return None
    parts = re.split(r"\.|\[|\]", path)
    parts = [p.strip() for p in parts if p.strip()]
    obj = node_data
    for part in parts:
        if obj is None:
            return None
        if part.isdigit():
            idx = int(part)
            if isinstance(obj, list) and 0 <= idx < len(obj):
                obj = obj[idx]
            else:
                return None
        else:
            obj = obj.get(part) if isinstance(obj, dict) else None
    return obj


def _enrich_sample_context_from_hooks(
    nodes: List[Dict[str, Any]],
    sample_ctx: Dict[str, str],
    tools_registry: Dict[str, Dict[str, Any]],
) -> None:
    """Apply contextHooks.enrichSampleContext from tool definitions to fill sample_ctx."""
    if not isinstance(sample_ctx, dict):
        return

    def _set_if_missing(key: str, value: Optional[str]) -> None:
        if value is not None and key not in sample_ctx:
            sample_ctx[key] = value

    for node in nodes:
        data = node.get("data", {}) or {}
        tool_id = data.get("type", "")
        if not tool_id:
            continue
        ti = tools_registry.get(tool_id, {})
        hooks = ti.get("contextHooks") or {}
        enrich = hooks.get("enrichSampleContext")
        if not isinstance(enrich, dict):
            continue
        extract_from = enrich.get("extractFrom")
        provide = enrich.get("provide")
        if not extract_from or not isinstance(provide, dict):
            continue
        value = _get_nested({"params": data.get("params", {})}, extract_from)
        if value is None:
            first_list = data.get("params", {}).get("input_sources") or data.get("params", {}).get("input_source")
            if isinstance(first_list, str):
                first_list = [first_list]
            if isinstance(first_list, list) and first_list:
                value = first_list[0]
        if value is None or not str(value).strip():
            continue
        try:
            first = Path(str(value))
        except Exception:
            continue
        repl = {
            "value": str(first),
            "parent": str(first.parent),
            "stem": first.stem,
            "suffix": first.suffix.lstrip("."),
            "name": first.name,
        }
        for ctx_key, tpl in provide.items():
            if not isinstance(tpl, str):
                continue
            resolved = tpl
            for k, v in repl.items():
                resolved = resolved.replace("{" + k + "}", str(v))
            _set_if_missing(ctx_key, resolved if resolved != tpl else resolved)


def _apply_inject_params(
    tool_info: Dict[str, Any],
    params_node: Dict[str, Any],
    sample_context: Dict[str, str],
) -> Dict[str, Any]:
    """Apply contextHooks.injectParams from tool definition; substitute {sample_context.*}."""
    inject = (tool_info.get("contextHooks") or {}).get("injectParams")
    if not isinstance(inject, dict):
        return params_node
    out = dict(params_node)
    for key, tpl in inject.items():
        if not isinstance(tpl, str):
            continue
        resolved = tpl
        for k, v in (sample_context or {}).items():
            resolved = resolved.replace("{sample_context." + k + "}", str(v))
        if resolved != tpl or key not in out:
            out[key] = resolved
    return out


def _node_resume_manifest_path(workspace: Path, node_id: str) -> Path:
    return workspace / ".tdease_resume" / f"{node_id}.json"


def _resolve_required_output_paths(tool_info: Dict[str, Any], output_paths: List[Path]) -> List[Path]:
    if not output_paths:
        return []

    outputs = tool_info.get("ports", {}).get("outputs", [])
    by_handle: Dict[str, Dict[str, Any]] = {}
    for out in outputs:
        if not isinstance(out, dict):
            continue
        key = str(out.get("handle") or out.get("id") or "").strip().lower()
        if key:
            by_handle[key] = out

    patterns = _get_output_patterns(tool_info)
    required_paths: List[Path] = []
    for idx, path in enumerate(output_paths):
        pattern_item = patterns[idx] if idx < len(patterns) else {}
        handle = str((pattern_item or {}).get("handle") or (pattern_item or {}).get("id") or "").strip().lower()
        output_def = by_handle.get(handle) if handle else None
        is_required = True if output_def is None else bool(output_def.get("required", True))
        if is_required:
            required_paths.append(path)

    return required_paths or list(output_paths)


def _write_resume_manifest(
    manifest_path: Path,
    *,
    node_id: str,
    required_outputs: List[Path],
    all_outputs: List[Path],
) -> None:
    payload = {
        "node_id": node_id,
        "completed": True,
        "required_outputs": [str(p) for p in required_outputs],
        "all_outputs": [str(p) for p in all_outputs],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False)


def _should_skip_node_on_resume(
    output_paths: List[Path],
    *,
    required_output_paths: Optional[List[Path]] = None,
    completion_manifest: Optional[Path] = None,
) -> bool:
    """
    Resume skip policy:
    - manifest present + required outputs complete: skip
    - otherwise require all required outputs to exist
    """
    required_paths = list(required_output_paths or output_paths)
    if not required_paths:
        return False

    if completion_manifest and completion_manifest.exists():
        try:
            with open(completion_manifest, "r", encoding="utf-8") as fp:
                payload = json.load(fp)
            if payload.get("completed") is True:
                manifest_required = payload.get("required_outputs") or [str(p) for p in required_paths]
                return all(Path(p).exists() for p in manifest_required)
        except Exception:
            logger.warning("Invalid resume manifest at %s", completion_manifest)

    return all(p.exists() for p in required_paths)


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

    def _serialize_binding_decisions(self, decisions: List[BindingDecision]) -> List[Dict[str, Any]]:
        return [
            {
                "edge_id": decision.edge_id,
                "source_node_id": decision.source_node_id,
                "resolved_source_node_id": decision.resolved_source_node_id,
                "target_port_id": decision.target_port_id,
                "source_handle": decision.source_handle,
                "target_handle": decision.target_handle,
                "selected_output_index": decision.selected_output_index,
                "selected_output_path": decision.selected_output_path,
                "score": decision.score,
                "reason": decision.reason,
                "status": decision.status,
            }
            for decision in decisions
        ]

    def _persist_binding_trace(
        self,
        *,
        execution_id: Optional[str],
        node_id: str,
        tool_id: str,
        decisions: List[BindingDecision],
        contract_error: Optional[InputBindingContractError] = None,
    ) -> None:
        if not self.execution_store or not execution_id:
            return

        payload: Dict[str, Any] = {
            "node_id": node_id,
            "tool_id": tool_id,
            "input_binding": {
                "status": "ok" if contract_error is None else "failed",
                "decisions": self._serialize_binding_decisions(decisions),
            },
        }
        if contract_error is not None:
            payload["input_binding"]["error"] = contract_error.to_dict()

        try:
            self.execution_store.update_node_command_trace(execution_id, node_id, payload)
        except Exception as exc:
            logger.warning("Persist binding diagnostics failed for node %s: %s", node_id, exc)

    def _persist_node_failure(self, execution_id: Optional[str], node_id: str, error_message: str) -> None:
        if not self.execution_store or not execution_id:
            return
        try:
            self.execution_store.update_node_status(
                execution_id,
                node_id,
                "failed",
                progress=0,
                error_message=error_message,
            )
        except Exception as exc:
            logger.warning("Persist node failure failed for node %s: %s", node_id, exc)

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
        try:
            input_files_dict, binding_decisions = _resolve_input_paths(
                nid,
                edges or [],
                nodes_map or {},
                self.tools,
                c.sample_context,
                c.workspace_path,
                completed_outputs or {},
                target_tool_id=tool_id,
                enforce_contracts=True,
                return_diagnostics=True,
            )
            self._persist_binding_trace(
                execution_id=c.execution_id,
                node_id=nid,
                tool_id=tool_id,
                decisions=binding_decisions,
            )
        except InputBindingContractError as contract_error:
            self._persist_binding_trace(
                execution_id=c.execution_id,
                node_id=nid,
                tool_id=tool_id,
                decisions=contract_error.decisions,
                contract_error=contract_error,
            )
            raise
        logger.info(f"[WorkflowService] Resolved input_files_dict for node {nid}: {input_files_dict}")

        positional_ids = _get_positional_input_ids(ti)
        if positional_ids:
            in_paths = [input_files_dict[pid] for pid in positional_ids if pid in input_files_dict]
        else:
            in_paths = list(input_files_dict.values())

        params_node = _apply_inject_params(ti, params_node, c.sample_context)

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
        _enrich_sample_context_from_hooks(wf.get("nodes", []), sample_ctx, self.tools)

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
            required_paths = _resolve_required_output_paths(ti, paths)
            manifest = _node_resume_manifest_path(c.workspace_path, node_id)
            return _should_skip_node_on_resume(
                paths,
                required_output_paths=required_paths,
                completion_manifest=manifest,
            )

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
            try:
                spec = build_task_spec(nid, node_data, c)
            except Exception as exc:
                self._persist_node_failure(c.execution_id, nid, str(exc))
                raise

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
                output_paths = _resolve_output_paths(nid, tool_id, ti, c.sample_context, c.workspace_path)
                completed_outputs[nid] = output_paths
                required_paths = _resolve_required_output_paths(ti, output_paths)
                manifest_path = _node_resume_manifest_path(c.workspace_path, nid)
                _write_resume_manifest(
                    manifest_path,
                    node_id=nid,
                    required_outputs=required_paths,
                    all_outputs=output_paths,
                )
            except Exception as exc:
                self._persist_node_failure(c.execution_id, nid, str(exc))
                raise
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
