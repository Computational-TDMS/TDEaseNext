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
    logger.info(f"[parse_tabular_file] Starting to parse file: {file_path}")
    logger.info(f"[parse_tabular_file] File exists: {file_path.exists()}")

    if not file_path.exists():
        logger.error(f"[parse_tabular_file] File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # 根据扩展名选择分隔符
    extension = file_path.suffix.lower()
    delimiter = ',' if extension == '.csv' else '\t'

    logger.info(f"[parse_tabular_file] File extension: {extension}, delimiter: '{delimiter}'")
    logger.info(f"[parse_tabular_file] Max rows: {max_rows}")

    columns = []
    rows = []
    total_rows = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 读取列名
            header_line = f.readline().strip()
            if header_line:
                columns = header_line.split(delimiter)
                logger.info(f"[parse_tabular_file] Found {len(columns)} columns: {columns}")
            else:
                logger.warning(f"[parse_tabular_file] Empty header line in file: {file_path}")

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

        logger.info(f"[parse_tabular_file] Successfully parsed {len(rows)} rows (total: {total_rows})")
    except OSError as exc:
        logger.error(f"[parse_tabular_file] Failed to read file {file_path}: {exc}")
        raise ValueError(f"Failed to read file: {file_path}") from exc
    except Exception as exc:
        logger.error(f"[parse_tabular_file] Unexpected error parsing {file_path}: {exc}")
        raise

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

    # 1. 查询 executions 表获取 workflow_snapshot, workspace_path, sample_id, workflow_id
    cursor = db.cursor()
    cursor.execute(
        "SELECT workflow_snapshot, workspace_path, sample_id, workflow_id FROM executions WHERE id = ?",
        (execution_id,)
    )
    row = cursor.fetchone()

    if not row:
        raise ValueError(f"Execution not found: {execution_id}")

    workflow_snapshot_json, workspace_path_str, sample_id = row[0], row[1], row[2]
    workflow_id = row[3] if len(row) > 3 else None
    workspace_path = Path(workspace_path_str)

    # 2. 解析 workflow_snapshot 找到节点的 tool_id（无 snapshot 时从 workflows 表或上次执行回退）
    if not workflow_snapshot_json and workflow_id:
        try:
            cursor.execute("SELECT vueflow_data FROM workflows WHERE id = ?", (workflow_id,))
            wf_row = cursor.fetchone()
            if wf_row and wf_row[0]:
                workflow_snapshot_json = wf_row[0] if isinstance(wf_row[0], str) else json.dumps(wf_row[0])
        except Exception:
            pass
        if not workflow_snapshot_json:
            try:
                from app.services.workflow_diff import get_last_execution_snapshot
                _, last_snapshot = get_last_execution_snapshot(db, workflow_id)
                if last_snapshot:
                    workflow_snapshot_json = json.dumps(last_snapshot)
            except Exception:
                pass

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

    # Support both VueFlow format (type at top) and WorkflowNormalizer format (type in data)
    tool_id = (
        node_data.get("type")
        or (node_data.get("data") or {}).get("type")
        or (node_data.get("nodeConfig") or {}).get("toolId")
        or ""
    )
    if not tool_id:
        raise ValueError(f"Node has no tool_id: {node_id}")

    # 3. 查询 tool_registry 获取工具定义
    tool_registry = get_tool_registry()
    tool_info = tool_registry.get(tool_id)
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
    logger.info(f"[resolve_node_outputs] Resolving output paths for node {node_id}")
    logger.info(f"[resolve_node_outputs] Sample context: {sample_context}")
    logger.info(f"[resolve_node_outputs] Workspace: {workspace_path}")

    output_paths = _resolve_output_paths(
        node_id=node_id,
        tool_id=tool_id,
        tool_info=tool_info,
        sample_ctx=sample_context,
        workspace=workspace_path
    )

    logger.info(f"[resolve_node_outputs] Resolved {len(output_paths)} output paths:")
    for idx, path in enumerate(output_paths):
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        logger.info(f"  [{idx}] {path} - exists: {exists}, size: {size} bytes")

    # 6. 获取输出端口定义
    patterns = _get_output_patterns(tool_info)
    logger.info(f"[resolve_node_outputs] Found {len(patterns)} output patterns")
    outputs = []

    for idx, file_path in enumerate(output_paths):
        file_exists = file_path.exists()
        file_size = file_path.stat().st_size if file_exists else 0
        file_name = file_path.name

        logger.info(f"[resolve_node_outputs] Processing output {idx}: {file_name}")
        logger.info(f"  - Full path: {file_path}")
        logger.info(f"  - Exists: {file_exists}")
        logger.info(f"  - Size: {file_size} bytes")

        # 获取端口信息
        pattern_info = patterns[idx] if idx < len(patterns) else {}
        port_id = pattern_info.get("handle", pattern_info.get("id", f"port_{idx}"))
        data_type = pattern_info.get("pattern", "").split(".")[-1] if pattern_info.get("pattern") else ""

        logger.info(f"  - Port ID: {port_id}")
        logger.info(f"  - Data type: {data_type}")

        # 判断是否可解析
        extension = file_path.suffix.lower()
        parseable = extension in TABULAR_EXTENSIONS and file_exists

        logger.info(f"  - Extension: {extension}")
        logger.info(f"  - Parseable: {parseable} (in TABULAR_EXTENSIONS: {extension in TABULAR_EXTENSIONS})")

        output_entry = {
            "port_id": port_id,
            "data_type": data_type,
            "file_name": file_name,
            "file_path": str(file_path),
            "relative_path": str(file_path.relative_to(workspace_path)) if file_exists else str(file_path),
            "file_size": file_size,
            "exists": file_exists,
            "parseable": parseable,
            "data": None
        }

        # 如果需要内联数据且文件可解析
        if include_data and file_exists and parseable:
            try:
                logger.info(f"  - Parsing file with max_rows={max_rows}...")
                table_data = parse_tabular_file(file_path, max_rows)
                logger.info(f"  - Successfully parsed {len(table_data['rows'])} rows")
                logger.info(f"  - Columns: {table_data['columns']}")
                output_entry["data"] = table_data
            except Exception as e:
                logger.error(f"  - Failed to parse file {file_path}: {e}", exc_info=True)
                output_entry["parseable"] = False

        outputs.append(output_entry)

    return {
        "execution_id": execution_id,
        "node_id": node_id,
        "outputs": outputs
    }
