"""
Workflow Graph - DAG 图结构与节点状态管理

从前端 JSON (nodes + edges) 构建内存图，支持：
- 循环依赖检测
- 拓扑排序
- 节点状态 (PENDING/READY/RUNNING/COMPLETED/FAILED/SKIPPED)
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class NodeState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class GraphNode:
    id: str
    data: Dict[str, Any]
    state: NodeState = NodeState.PENDING
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    error_message: Optional[str] = None


@dataclass
class GraphEdge:
    id: str
    source: str
    target: str
    source_handle: Optional[str]
    target_handle: Optional[str]
    connection_kind: str
    semantic_type: Optional[str]
    dependency: bool


class WorkflowGraph:
    """
    工作流 DAG 图

    从 VueFlow JSON 构建，支持拓扑遍历和断点续传检查。
    """

    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._build(nodes, edges)

    def _build(self, nodes: List[Dict], edges: List[Dict]) -> None:
        for n in nodes:
            nid = n.get("id")
            if not nid:
                continue
            self._nodes[nid] = GraphNode(id=nid, data=n.get("data", {}))
        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            if not src or not tgt or src not in self._nodes or tgt not in self._nodes:
                continue
            connection_kind = str(e.get("connectionKind") or "data").lower()
            semantic_type = e.get("semanticType")
            is_dependency = connection_kind in {"data", "control"}
            self._edges.append(
                GraphEdge(
                    id=str(e.get("id") or ""),
                    source=src,
                    target=tgt,
                    source_handle=e.get("sourceHandle"),
                    target_handle=e.get("targetHandle"),
                    connection_kind=connection_kind,
                    semantic_type=semantic_type,
                    dependency=is_dependency,
                )
            )
            if is_dependency:
                self._nodes[tgt].predecessors.add(src)
                self._nodes[src].successors.add(tgt)

    def has_cycle(self) -> bool:
        """检测是否存在环"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def visit(nid: str) -> bool:
            visited.add(nid)
            rec_stack.add(nid)
            for succ in self._nodes[nid].successors:
                if succ not in visited:
                    if visit(succ):
                        return True
                elif succ in rec_stack:
                    return True
            rec_stack.remove(nid)
            return False

        for nid in self._nodes:
            if nid not in visited and visit(nid):
                return True
        return False

    def topological_order(self) -> List[str]:
        """返回拓扑排序的节点 ID 列表"""
        in_degree: Dict[str, int] = {nid: 0 for nid in self._nodes}
        for n in self._nodes.values():
            for s in n.successors:
                in_degree[s] = in_degree.get(s, 0) + 1
        zero = [nid for nid, d in in_degree.items() if d == 0]
        order = []
        while zero:
            nid = zero.pop()
            order.append(nid)
            for s in self._nodes[nid].successors:
                in_degree[s] -= 1
                if in_degree[s] == 0:
                    zero.append(s)
        return order

    def get_ready_nodes(self) -> List[str]:
        """获取所有依赖已满足且未完成的节点"""
        ready = []
        for nid, node in self._nodes.items():
            if node.state not in (NodeState.COMPLETED, NodeState.FAILED, NodeState.SKIPPED):
                deps_ok = all(
                    self._nodes[p].state in (NodeState.COMPLETED, NodeState.SKIPPED)
                    for p in node.predecessors
                )
                if deps_ok and node.state != NodeState.RUNNING:
                    ready.append(nid)
        return ready

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def set_state(self, node_id: str, state: NodeState, error: Optional[str] = None) -> None:
        n = self._nodes.get(node_id)
        if n:
            n.state = state
            n.error_message = error

    def all_done(self) -> bool:
        """是否所有节点均已完成（成功或跳过）或失败"""
        for n in self._nodes.values():
            if n.state in (NodeState.PENDING, NodeState.READY, NodeState.RUNNING):
                return False
        return True

    def nodes(self) -> Dict[str, GraphNode]:
        return self._nodes

    def node_ids(self) -> List[str]:
        return list(self._nodes.keys())

    def edges(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "sourceHandle": edge.source_handle,
                "targetHandle": edge.target_handle,
                "connectionKind": edge.connection_kind,
                "semanticType": edge.semantic_type,
                "dependency": edge.dependency,
            }
            for edge in self._edges
        ]
