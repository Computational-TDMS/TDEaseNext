"""
Node Mapper - Map FlowEngine tasks to frontend node IDs

Maps between frontend workflow node IDs and FlowEngine task IDs.
Uses naming convention: task_name = "node_{node_id}"
"""

from typing import Dict, Optional


class NodeMapper:
    """Maps FlowEngine Tasks to frontend node IDs."""

    PREFIX = "node_"

    @classmethod
    def task_name_to_node_id(cls, task_name: str) -> Optional[str]:
        """
        Extract node ID from task name.

        Args:
            task_name: FlowEngine task name (format: "node_{node_id}")

        Returns:
            Node ID or None if format doesn't match
        """
        if task_name.startswith(cls.PREFIX):
            return task_name[len(cls.PREFIX):]
        return None

    @classmethod
    def node_id_to_task_name(cls, node_id: str) -> str:
        """
        Convert node ID to task name.

        Args:
            node_id: Frontend node ID

        Returns:
            FlowEngine task name
        """
        return f"{cls.PREFIX}{node_id}"

    def __init__(self):
        """Initialize mapper with tracking."""
        self.task_to_node: Dict[str, str] = {}
        self.node_to_task: Dict[str, str] = {}
        self.job_to_node: Dict[str, str] = {}  # job_id -> node_id

    def register_task_node(self, task_name: str, node_id: str):
        """
        Register mapping between task and node.

        Args:
            task_name: FlowEngine task name
            node_id: Frontend node ID
        """
        self.task_to_node[task_name] = node_id
        self.node_to_task[node_id] = task_name

    def register_job_node(self, job_id: str, node_id: str):
        """
        Register mapping between job and node.

        Args:
            job_id: FlowEngine job ID
            node_id: Frontend node ID
        """
        self.job_to_node[job_id] = node_id

    def get_node_id_from_task(self, task_name: str) -> Optional[str]:
        """Get node ID from task name."""
        # First check explicit mapping
        if task_name in self.task_to_node:
            return self.task_to_node[task_name]
        # Then try naming convention
        return self.task_name_to_node_id(task_name)

    def get_node_id_from_job(self, job_id: str) -> Optional[str]:
        """Get node ID from job ID."""
        return self.job_to_node.get(job_id)

    def get_task_name_from_node(self, node_id: str) -> Optional[str]:
        """Get task name from node ID."""
        # First check explicit mapping
        if node_id in self.node_to_task:
            return self.node_to_task[node_id]
        # Then use naming convention
        return self.node_id_to_task_name(node_id)


