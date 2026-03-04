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
) -> Dict[str, Path]:
    """根据边和上游节点输出解析输入路径，返回 port_id -> Path 的字典。

    支持穿越交互式节点：当上游节点是交互式节点(executionMode=interactive)时，
    会递归向上查找，直到找到非交互式处理节点的输出。
    """
    param_to_path: Dict[str, Path] = {}
    
    logger.info(f"[resolve_input_paths] Called for node {node_id}, tool={target_tool_id}")
    logger.info(f"[resolve_input_paths] edges count: {len(edges)}, completed_outputs keys: {list(completed_outputs.keys())}")

    def find_real_source(interactive_src_id: str, visited: set) -> Optional[str]:
        """递归查找真实的非交互式源节点。

        Args:
            interactive_src_id: 当前检查的节点ID
            visited: 已访问的节点集合，防止循环

        Returns:
            真实源节点的ID，如果没找到则返回None
        """
        if interactive_src_id in visited:
            logger.warning(f"循环检测：节点 {interactive_src_id} 在输入解析中已被访问")
            return None
        visited.add(interactive_src_id)

        # 检查该节点是否已完成执行（有输出）
        if interactive_src_id in completed_outputs:
            return interactive_src_id

        # 检查是否是交互式节点
        src_node = nodes_map.get(interactive_src_id, {})
        src_data = src_node.get("data", {})
        src_tool = src_data.get("type", "")
        src_info = tools_registry.get(src_tool, {})

        # 如果是交互式节点，继续向上游查找
        if src_info.get("executionMode") == "interactive":
            # 找到该交互式节点的所有上游输入边
            for e in edges:
                if e.get("target") != interactive_src_id:
                    continue
                upstream_src_id = e.get("source")
                if upstream_src_id:
                    result = find_real_source(upstream_src_id, visited)
                    if result:
                        return result
            return None
        else:
            # 非交互式节点但还没完成执行，返回None
            return None

    # 获取源节点的输出端口定义（用于数据类型匹配）
    def get_output_data_types(src_info: Dict[str, Any]) -> Dict[str, str]:
        """获取源工具的所有输出端口的 {handle: dataType} 映射"""
        result = {}
        outputs = src_info.get("ports", {}).get("outputs", [])
        for o in outputs:
            if isinstance(o, dict):
                handle = o.get("handle") or o.get("id", "")
                data_type = o.get("dataType", "")
                if handle and data_type:
                    result[handle] = data_type
        return result

    for e in edges:
        if e.get("target") != node_id:
            continue
        src_id = e.get("source")
        src_handle_raw = e.get("sourceHandle") or ""
        src_handle = src_handle_raw.replace("output-", "") if src_handle_raw else ""
        tgt_handle_raw = e.get("targetHandle") or ""
        tgt_handle = tgt_handle_raw.replace("input-", "") if tgt_handle_raw else ""

        logger.info(f"[resolve_input_paths] Edge: source={src_id}, target={node_id}, srcHandle={src_handle_raw} -> {src_handle}, tgtHandle={tgt_handle_raw} -> {tgt_handle}")

        if not src_id:
            continue

        # 查找真实的源节点（穿越交互式节点）
        real_src_id = find_real_source(src_id, set())
        if not real_src_id or real_src_id not in completed_outputs:
            continue

        src_outputs = completed_outputs[real_src_id]
        src_node = nodes_map.get(real_src_id, {})
        src_data = src_node.get("data", {})
        src_tool = src_data.get("type", "")
        src_info = tools_registry.get(src_tool, {})
        patterns = _get_output_patterns(src_info)
        
        if not patterns:
            if tgt_handle and src_outputs:
                param_to_path[tgt_handle] = src_outputs[0]
            continue
        
        # 获取源节点的输出数据类型映射
        output_data_types = get_output_data_types(src_info)
        
        matched_idx = None
        for idx, p in enumerate(patterns):
            h = p.get("handle", "") if isinstance(p, dict) else ""
            
            # 匹配策略 1: handle 精确匹配
            if h and h == src_handle:
                matched_idx = idx
                break
            
            # 匹配策略 2: src_handle 是数据类型，与该端口的 dataType 匹配
            if src_handle:
                port_data_type = output_data_types.get(h, "")
                if port_data_type and port_data_type == src_handle:
                    matched_idx = idx
                    logger.info(f"[resolve_input_paths] Matched by dataType: {src_handle} -> handle={h}")
                    break
            
            # 匹配策略 3: 无 src_handle 时，使用第一个输出
            if not src_handle and idx == 0:
                matched_idx = idx
                break
        
        if matched_idx is not None and matched_idx < len(src_outputs) and tgt_handle:
            param_to_path[tgt_handle] = src_outputs[matched_idx]
    
    logger.info(f"[resolve_input_paths] Final param_to_path for {node_id}: {param_to_path}")
    return param_to_path


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

        def build_task_spec(nid: str, node_data: Dict, c: ExecutionContext) -> Optional[TaskSpec]:
            tool_id = node_data.get("type", "")
            ti = self.tools.get(tool_id, {})

            # 跳过交互式节点 (interactive execution mode)
            if ti.get("executionMode") == "interactive":
                logger.info(f"Skipping interactive node: {nid} (tool: {tool_id})")
                return None

            # 生成 task_id: {execution_id}:{node_id}
            task_id = f"{c.execution_id}:{nid}"
            logger.debug(f"[WorkflowService] Generated task_id={task_id} for node {nid}")

            params_node = node_data.get("params", {})
            out_paths = _resolve_output_paths(nid, tool_id, ti, c.sample_context, c.workspace_path)
            input_files_dict = _resolve_input_paths(
                nid, edges, nodes_map, self.tools, c.sample_context, c.workspace_path, completed_outputs,
                target_tool_id=tool_id,
            )
            logger.info(f"[WorkflowService] Resolved input_files_dict for node {nid}: {input_files_dict}")

            # 保持向后兼容：input_paths 按 positional 顺序排列
            positional_ids = _get_positional_input_ids(ti)
            if positional_ids:
                in_paths = [input_files_dict[pid] for pid in positional_ids if pid in input_files_dict]
            else:
                in_paths = list(input_files_dict.values())

            # 对于 data_loader，统一使用前端/context 传入的 sample 作为输出文件名，不兜底 basename
            if tool_id == "data_loader":
                params_node = {**params_node, "sample_name": c.sample_context.get("sample", "")}

            return TaskSpec(
                node_id=nid,
                tool_id=tool_id,
                params=params_node,
                input_paths=in_paths,
                input_files=input_files_dict,  # 新增：port_id -> Path 映射
                output_paths=out_paths,
                workspace_path=c.workspace_path,
                conda_env=ti.get("conda_env"),
                log_callback=c.log_callback,
                task_id=task_id,  # 新增：用于进程追踪和取消
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