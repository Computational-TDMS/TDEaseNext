"""
FlowEngine - 轻量级 DAG 调度器

原生 DAG 调度引擎，提供：
- 节点状态管理：PENDING -> READY -> RUNNING -> COMPLETED/FAILED
- DryRun 模式：仅遍历 DAG 验证，不执行
- Resume 模式：检查输出文件存在则跳过
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .graph import NodeState, WorkflowGraph
from .context import ExecutionContext

logger = logging.getLogger(__name__)


async def _noop_execute(node_id: str, node_data: Dict[str, Any], ctx: ExecutionContext) -> None:
    """占位执行函数，实际由 Executor 注入"""
    pass


class FlowEngine:
    """
    流引擎 - 调度层大脑

    职责：遍历 DAG、决定下一批可执行节点、调用 Executor 执行。
    """

    def __init__(
        self,
        workflow_json: Dict[str, Any],
        context: ExecutionContext,
        execute_fn: Optional[Callable] = None,
        output_check_fn: Optional[Callable] = None,
        on_node_state: Optional[Callable[[str, str], None]] = None,
        on_node_skipped: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        nodes = workflow_json.get("nodes", [])
        edges = workflow_json.get("edges", [])
        self.graph = WorkflowGraph(nodes, edges)
        self.context = context
        self._execute_fn = execute_fn or _noop_execute
        self._output_check_fn = output_check_fn or self._default_output_check
        self._on_node_state = on_node_state
        self._on_node_skipped = on_node_skipped
        self._cancelled = False

    def _default_output_check(
        self, node_id: str, node_data: Dict[str, Any], ctx: ExecutionContext
    ) -> bool:
        """默认输出检查：无实现，子类或外部注入"""
        return False

    def set_execute_fn(self, fn: Callable) -> None:
        self._execute_fn = fn

    def set_output_check_fn(self, fn: Callable) -> None:
        self._output_check_fn = fn

    def cancel(self) -> None:
        self._cancelled = True

    def _mark_ready(self) -> None:
        for nid in self.graph.get_ready_nodes():
            node = self.graph.get_node(nid)
            if node and node.state == NodeState.PENDING:
                self.graph.set_state(nid, NodeState.READY)

    async def run(self) -> Dict[str, Any]:
        """
        执行工作流调度循环。

        Returns:
            {"status": "completed"|"failed", "nodes": {node_id: state}, "error": ...}
        """
        if self.graph.has_cycle():
            return {"status": "failed", "nodes": {}, "error": "Workflow contains cycles"}
        if self.context.dryrun:
            return await self._dry_run()
        return await self._execute_loop()

    async def _dry_run(self) -> Dict[str, Any]:
        """DryRun：遍历 DAG，验证参数和依赖"""
        order = self.graph.topological_order()
        node_states = {nid: self.graph.get_node(nid).state for nid in order}
        return {"status": "dryrun", "nodes": {k: v.value for k, v in node_states.items()}}

    def _should_skip_node(self, nid: str, node) -> tuple[bool, str]:
        """
        Check if a node should be skipped during execution.

        Returns:
            tuple[bool, str]: (should_skip, skip_reason)
        """
        # Check if node has executionMode: "interactive"
        node_data = node.data if node else {}
        execution_mode = node_data.get("executionMode") or \
                       node_data.get("nodeConfig", {}).get("executionMode")

        if execution_mode == "interactive":
            return True, "interactive node"

        # Check resume mode and output existence
        if self.context.resume and self._output_check_fn(nid, node_data, self.context):
            return True, "output exists"

        return False, ""

    async def _execute_loop(self) -> Dict[str, Any]:
        """主执行循环"""
        while not self._cancelled and not self.graph.all_done():
            self._mark_ready()
            ready = self.graph.get_ready_nodes()
            if not ready:
                if self.graph.all_done():
                    break
                logger.warning("No ready nodes but workflow not done; possible deadlock")
                break
            tasks = []
            for nid in ready:
                node = self.graph.get_node(nid)
                if not node:
                    continue

                # Check if node should be skipped
                should_skip, skip_reason = self._should_skip_node(nid, node)
                if should_skip:
                    self.graph.set_state(nid, NodeState.SKIPPED)
                    logger.info(f"Skipping node {nid}: {skip_reason}")
                    if self._on_node_state:
                        self._on_node_state(nid, "skipped")
                    if self._on_node_skipped:
                        self._on_node_skipped(nid, node.data)
                    continue

                tasks.append(self._run_node(nid, node))
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Exception):
                        logger.exception("Node execution error: %s", r)
        return self._collect_result()

    async def _run_node(self, nid: str, node) -> None:
        self.graph.set_state(nid, NodeState.RUNNING)
        if self._on_node_state:
            self._on_node_state(nid, "running")
        try:
            await self._execute_fn(nid, node.data, self.context)
            self.graph.set_state(nid, NodeState.COMPLETED)
            if self._on_node_state:
                self._on_node_state(nid, "completed")
        except Exception as e:
            self.graph.set_state(nid, NodeState.FAILED, error=str(e))
            if self._on_node_state:
                self._on_node_state(nid, "failed")
            raise

    def _collect_result(self) -> Dict[str, Any]:
        nodes = {nid: n.state.value for nid, n in self.graph.nodes().items()}
        failed = [nid for nid, n in self.graph.nodes().items() if n.state == NodeState.FAILED]
        status = "failed" if failed else "completed"
        err = None
        if failed:
            fn = self.graph.get_node(failed[0])
            err = fn.error_message if fn else "Unknown"
        return {
            "status": status,
            "nodes": nodes,
            "error": err,
            "edge_metadata": self.graph.edges(),
        }
