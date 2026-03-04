"""
Node Data Service - 节点输出数据推导与解析服务

从 workflow_service.py 提取的路径推导逻辑，供执行引擎和数据查询两处复用。
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.workflow.validator import validate_placeholders

logger = logging.getLogger(__name__)


# Supported tabular file extensions
TABULAR_EXTENSIONS = {
    '.tsv', '.txt', '.ms1ft', '.feature', '.csv'
}

# Binary file extensions (for file type detection)
BINARY_EXTENSIONS = {
    '.pbf', '.raw', '.mzml', '.png', '.jpg', '.jpeg', '.exe', '.dll'
}


def _get_output_patterns(tool_info: Dict[str, Any]) -> List[Dict[str, str]]:
    """从工具定义获取输出模式：优先 output_patterns，否则从 ports.outputs 推导（新 Schema）"""
    patterns = tool_info.get("output_patterns", [])
    if patterns:
        return patterns
    outputs = tool_info.get("ports", {}).get("outputs", [])
    for o in outputs:
        if isinstance(o, dict) and o.get("pattern"):
            patterns.append({
                "pattern": o["pattern"],
                "handle": o.get("handle") or o.get("id", "output"),
            })
    if not patterns and tool_info.get("outputs"):
        for o in tool_info["outputs"]:
            if isinstance(o, dict) and o.get("pattern"):
                patterns.append({
                    "pattern": o["pattern"],
                    "handle": o.get("handle") or o.get("id", "output"),
                })
    return patterns


def _resolve_output_paths(
    node_id: str,
    tool_id: str,
    tool_info: Dict[str, Any],
    sample_ctx: Dict[str, str],
    workspace: Path,
) -> List[Path]:
    """根据 output_patterns / ports.outputs 和 sample_ctx 解析输出路径"""
    patterns = _get_output_patterns(tool_info)
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


def parse_tabular_file(file_path: Path, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """
    解析表格文件（TSV/CSV/TXT等）

    Args:
        file_path: 文件路径
        max_rows: 最大读取行数（None表示全量读取）

    Returns:
        {
            "columns": [str],      # 列名
            "rows": [dict],        # 行数据（每行是列名->值的字典）
            "total_rows": int      # 总行数
        }
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # 根据扩展名选择分隔符
    extension = file_path.suffix.lower()
    delimiter = ',' if extension == '.csv' else '\t'

    columns = []
    rows = []
    total_rows = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        # 读取列名
        header_line = f.readline().strip()
        if header_line:
            columns = header_line.split(delimiter)

        # 读取数据行
        for line in f:
            total_rows += 1
            if max_rows is not None and len(rows) >= max_rows:
                # 继续计数以获取 total_rows，但不存储数据
                continue

            values = line.strip().split(delimiter)
            if len(values) == len(columns):
                row_data = dict(zip(columns, values))
                rows.append(row_data)
            elif values:  # 处理列数不匹配的情况
                # 用索引作为键
                row_data = {f"col_{i}": v for i, v in enumerate(values)}
                rows.append(row_data)

    return {
        "columns": columns,
        "rows": rows,
        "total_rows": total_rows
    }


def resolve_node_outputs(
    execution_id: str,
    node_id: str,
    db,
    include_data: bool = False,
    max_rows: Optional[int] = None
) -> Dict[str, Any]:
    """
    解析节点输出文件路径并返回文件元信息

    Args:
        execution_id: 执行ID
        node_id: 节点ID
        db: 数据库连接
        include_data: 是否内联解析数据
        max_rows: 最大读取行数（仅当 include_data=True 时生效）

    Returns:
        {
            "execution_id": str,
            "node_id": str,
            "outputs": [
                {
                    "port_id": str,
                    "data_type": str,
                    "file_name": str,
                    "file_path": str,
                    "file_size": int,
                    "exists": bool,
                    "parseable": bool,
                    "data": {...} | None
                }
            ]
        }
    """
    from app.services.tool_registry import get_tool_registry
    from app.services.sample_store import SampleStore

    # 1. 查询 executions 表获取 workflow_snapshot, workspace_path, sample_id
    cursor = db.cursor()
    cursor.execute(
        "SELECT workflow_snapshot, workspace_path, sample_id FROM executions WHERE id = ?",
        (execution_id,)
    )
    row = cursor.fetchone()

    if not row:
        raise ValueError(f"Execution not found: {execution_id}")

    workflow_snapshot_json, workspace_path_str, sample_id = row
    workspace_path = Path(workspace_path_str)

    # 2. 解析 workflow_snapshot 找到节点的 tool_id
    if not workflow_snapshot_json:
        raise ValueError(f"Workflow snapshot is empty for execution: {execution_id}")

    try:
        workflow_snapshot = json.loads(workflow_snapshot_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid workflow snapshot JSON: {e}")

    nodes = workflow_snapshot.get("nodes", [])
    node_data = None
    for node in nodes:
        if node.get("id") == node_id:
            node_data = node
            break

    if not node_data:
        raise ValueError(f"Node not found in workflow snapshot: {node_id}")

    tool_id = node_data.get("type", "")
    if not tool_id:
        raise ValueError(f"Node has no tool_id: {node_id}")

    # 3. 查询 tool_registry 获取工具定义
    tool_registry = get_tool_registry()
    tool_info = tool_registry.get_tool(tool_id)
    if not tool_info:
        raise ValueError(f"Tool not found in registry: {tool_id}")

    # 4. 查询 sample_context
    sample_context = {}
    if sample_id:
        sample_store = SampleStore()
        sample = sample_store.get(sample_id)
        if sample:
            sample_context = sample.get("context", {})

    # 如果没有 sample_context，使用默认值
    if not sample_context:
        sample_context = {"sample": "default"}

    # 5. 解析输出路径
    output_paths = _resolve_output_paths(
        node_id=node_id,
        tool_id=tool_id,
        tool_info=tool_info,
        sample_ctx=sample_context,
        workspace=workspace_path
    )

    # 6. 获取输出端口定义
    patterns = _get_output_patterns(tool_info)
    outputs = []

    for idx, file_path in enumerate(output_paths):
        file_exists = file_path.exists()
        file_size = file_path.stat().st_size if file_exists else 0
        file_name = file_path.name

        # 获取端口信息
        pattern_info = patterns[idx] if idx < len(patterns) else {}
        port_id = pattern_info.get("handle", pattern_info.get("id", f"port_{idx}"))
        data_type = pattern_info.get("pattern", "").split(".")[-1] if pattern_info.get("pattern") else ""

        # 判断是否可解析
        extension = file_path.suffix.lower()
        parseable = extension in TABULAR_EXTENSIONS and file_exists

        output_entry = {
            "port_id": port_id,
            "data_type": data_type,
            "file_name": file_name,
            "file_path": str(file_path.relative_to(workspace_path)) if file_exists else str(file_path),
            "file_size": file_size,
            "exists": file_exists,
            "parseable": parseable,
            "data": None
        }

        # 如果需要内联数据且文件可解析
        if include_data and file_exists and parseable:
            try:
                table_data = parse_tabular_file(file_path, max_rows)
                output_entry["data"] = table_data
            except Exception as e:
                logger.warning(f"Failed to parse file {file_path}: {e}")
                output_entry["parseable"] = False

        outputs.append(output_entry)

    return {
        "execution_id": execution_id,
        "node_id": node_id,
        "outputs": outputs
    }
