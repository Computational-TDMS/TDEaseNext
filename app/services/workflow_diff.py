"""
Workflow Diff - 检测工作流结构变更 vs 参数变更

区分「结构变更」（nodes/edges 变化）和「参数变更」（仅 params 变化）。
结构变更时需要保存 workflow_snapshot，参数变更时不需要。
"""
import json
import logging
from typing import Dict, Any, Set, Tuple, Optional

logger = logging.getLogger(__name__)


def extract_structure(workflow_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    提取工作流的结构部分（忽略参数值）
    
    Args:
        workflow_json: 完整的工作流 JSON
        
    Returns:
        仅包含结构信息的字典（nodes 的 id/type/position，edges，但不包含 params）
    """
    nodes = []
    for node in workflow_json.get("nodes", []):
        node_structure = {
            "id": node.get("id"),
            "type": node.get("type") or (node.get("data", {}).get("type")),
            "position": node.get("position", {}),
        }
        nodes.append(node_structure)
    
    edges = []
    for edge in workflow_json.get("edges", []):
        edge_structure = {
            "id": edge.get("id"),
            "source": edge.get("source"),
            "target": edge.get("target"),
            "sourceHandle": edge.get("sourceHandle"),
            "targetHandle": edge.get("targetHandle"),
        }
        edges.append(edge_structure)
    
    return {
        "nodes": sorted(nodes, key=lambda n: n.get("id", "")),
        "edges": sorted(edges, key=lambda e: (e.get("source", ""), e.get("target", ""))),
        "format_version": workflow_json.get("format_version"),
    }


def has_structure_changed(
    old_workflow: Dict[str, Any],
    new_workflow: Dict[str, Any]
) -> bool:
    """
    检测工作流结构是否发生变化
    
    Args:
        old_workflow: 旧的工作流 JSON
        new_workflow: 新的工作流 JSON
        
    Returns:
        True 如果结构发生变化（nodes/edges 变化），False 如果只是参数变化
    """
    old_struct = extract_structure(old_workflow)
    new_struct = extract_structure(new_workflow)
    
    # 比较结构（忽略顺序）
    old_nodes_set = {json.dumps(n, sort_keys=True) for n in old_struct["nodes"]}
    new_nodes_set = {json.dumps(n, sort_keys=True) for n in new_struct["nodes"]}
    
    old_edges_set = {json.dumps(e, sort_keys=True) for e in old_struct["edges"]}
    new_edges_set = {json.dumps(e, sort_keys=True) for e in new_struct["edges"]}
    
    # 节点数量或内容变化
    if old_nodes_set != new_nodes_set:
        return True
    
    # 边连接关系变化
    if old_edges_set != new_edges_set:
        return True
    
    # format_version 变化也算结构变更
    if old_struct.get("format_version") != new_struct.get("format_version"):
        return True
    
    return False


def get_last_execution_snapshot(
    db,
    workflow_id: str
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    获取工作流最后一次执行的 snapshot
    
    Args:
        db: 数据库连接
        workflow_id: 工作流 ID
        
    Returns:
        (execution_id, workflow_snapshot_dict) 或 (None, None)
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, workflow_snapshot
            FROM executions
            WHERE workflow_id = ? AND workflow_snapshot IS NOT NULL
            ORDER BY start_time DESC
            LIMIT 1
        """, (workflow_id,))
        
        row = cursor.fetchone()
        if row and row[1]:
            snapshot_json = json.loads(row[1])
            return row[0], snapshot_json
        return None, None
    except Exception as e:
        logger.warning(f"Failed to get last execution snapshot: {e}")
        return None, None
