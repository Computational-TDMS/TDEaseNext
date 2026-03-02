"""Workflow structure schemas for DAG validation and execution context."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """Workflow node definition"""

    id: str = Field(..., description="Node unique identifier")
    type: str = Field(..., description="Node type (tool, input, output, etc.)")
    name: Optional[str] = Field(None, description="Node display name")
    data: Dict[str, Any] = Field(default_factory=dict, description="Node data/configuration")
    position: Optional[Dict[str, float]] = Field(None, description="Node position in UI")


class WorkflowEdge(BaseModel):
    """Workflow edge/connection definition"""

    id: str = Field(..., description="Edge unique identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: Optional[str] = Field(None, description="Source output handle")
    target_handle: Optional[str] = Field(None, description="Target input handle")
    data: Optional[Dict[str, Any]] = Field(None, description="Edge metadata")


class WorkflowStructure(BaseModel):
    """Complete workflow structure validation schema"""

    nodes: List[WorkflowNode] = Field(default_factory=list, description="Workflow nodes")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="Workflow connections")
    viewport: Optional[Dict[str, Any]] = Field(None, description="UI viewport state")

    def validate_dag(self) -> List[str]:
        """Validate that the workflow forms a valid DAG"""
        errors = []

        # Check for cycles using simple DFS
        graph = {edge.source: [] for edge in self.edges}
        for edge in self.edges:
            graph[edge.source].append(edge.target)

        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    cycle_path = path + [neighbor, node]
                    errors.append(f"Cycle detected: {' -> '.join(cycle_path)}")
                    return True

            rec_stack.remove(node)
            return False

        for node_id in graph.keys():
            if node_id not in visited:
                dfs(node_id, [node_id])

        # Check for disconnected nodes
        node_ids = {node.id for node in self.nodes}
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)

        disconnected = node_ids - connected_nodes
        if disconnected:
            errors.append(f"Disconnected nodes found: {', '.join(disconnected)}")

        return errors


class ExecutionContext(BaseModel):
    """Execution context for workflow runtime"""

    workflow_id: str = Field(..., description="Workflow identifier")
    execution_id: str = Field(..., description="Execution identifier")
    workspace_path: str = Field(..., description="Working directory path")
    samples: Optional[List[str]] = Field(None, description="Sample list")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution parameters")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")

