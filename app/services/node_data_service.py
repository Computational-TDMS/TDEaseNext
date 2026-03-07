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


def _get_output_patterns(tool_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从工具定义获取输出模式并保留端口元信息（schema/dataType 等）"""
    output_patterns = tool_info.get("output_patterns", [])
    normalized: List[Dict[str, Any]] = []

    # Legacy schema: output_patterns
    if output_patterns:
        for idx, pattern_info in enumerate(output_patterns):
            if isinstance(pattern_info, dict):
                port_id = pattern_info.get("handle") or pattern_info.get("id") or f"output_{idx}"
                normalized.append({
                    "pattern": pattern_info.get("pattern", ""),
                    "handle": port_id,
                    "id": pattern_info.get("id", port_id),
                    "data_type": pattern_info.get("dataType", ""),
                    "schema": pattern_info.get("schema", []),
                })
            else:
                normalized.append({
                    "pattern": str(pattern_info),
                    "handle": f"output_{idx}",
                    "id": f"output_{idx}",
                    "data_type": "",
                    "schema": [],
                })
        return normalized

    # New schema: ports.outputs
    outputs = tool_info.get("ports", {}).get("outputs", [])
    for idx, output in enumerate(outputs):
        if not isinstance(output, dict):
            continue
        pattern = output.get("pattern")
        if not pattern:
            continue
        port_id = output.get("handle") or output.get("id", f"output_{idx}")
        normalized.append({
            "pattern": pattern,
            "handle": port_id,
            "id": output.get("id", port_id),
            "data_type": output.get("dataType", ""),
            "schema": output.get("schema", []),
        })

    # Compatibility: old outputs list
    if not normalized and tool_info.get("outputs"):
        for idx, output in enumerate(tool_info["outputs"]):
            if not isinstance(output, dict):
                continue
            pattern = output.get("pattern")
            if not pattern:
                continue
            port_id = output.get("handle") or output.get("id", f"output_{idx}")
            normalized.append({
                "pattern": pattern,
                "handle": port_id,
                "id": output.get("id", port_id),
                "data_type": output.get("dataType", ""),
                "schema": output.get("schema", []),
            })

    return normalized


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


def _read_text_lines(file_path: Path) -> List[str]:
    with open(file_path, "r", encoding="utf-8", errors="replace") as fp:
        return fp.read().splitlines()


def _looks_like_key_value_preamble(fields: List[str]) -> bool:
    """
    Detect if a TSV row looks like a key-value preamble line (e.g. "Key: value").
    Used to skip non-header lines when detecting tabular header. Port-level
    fileFormat.preambleStyle (key_value | comment | none) can override behavior in future.
    """
    non_empty = [field.strip() for field in fields if field.strip()]
    if not non_empty:
        return True
    if non_empty[0].endswith(":"):
        return True
    if len(non_empty) <= 2 and any(field.endswith(":") for field in non_empty):
        return True
    return False


def _find_tabular_header(
    lines: List[str],
    delimiter: str,
    preamble_style: str = "key_value",
) -> tuple[Optional[int], List[str]]:
    """
    Detect header row and return (line_index, columns).

    TSV: skips comment lines (#, *) and key-value preamble when preamble_style is "key_value".
    CSV: uses first non-empty line as header. preamble_style can be "key_value" | "comment" | "none".
    """
    skip_preamble = preamble_style == "key_value"

    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped:
            continue

        if delimiter == ",":
            return idx, [part.strip() for part in stripped.split(delimiter)]

        if stripped.startswith("#") or stripped.startswith("*"):
            continue
        if "\t" not in stripped:
            continue

        columns = [part.strip() for part in stripped.split("\t")]
        non_empty = [part for part in columns if part]
        if len(non_empty) < 2:
            continue
        if skip_preamble and _looks_like_key_value_preamble(columns):
            continue

        has_nonempty_after = False
        has_data_like_after = False
        for follow_raw in lines[idx + 1 :]:
            follow = follow_raw.strip()
            if not follow:
                continue
            has_nonempty_after = True
            if follow.startswith("#") or follow.startswith("*"):
                continue
            if "\t" not in follow:
                continue
            follow_fields = [part.strip() for part in follow.split("\t")]
            follow_non_empty = [part for part in follow_fields if part]
            if len(follow_non_empty) < 2:
                continue
            if skip_preamble and _looks_like_key_value_preamble(follow_fields):
                continue
            has_data_like_after = True
            break

        if has_data_like_after or not has_nonempty_after:
            return idx, columns

    return None, []


def _is_tabular_parseable(file_path: Path) -> bool:
    extension = file_path.suffix.lower()
    if extension not in TABULAR_EXTENSIONS:
        return False
    if not file_path.exists():
        return False
    try:
        lines = _read_text_lines(file_path)
    except OSError:
        return False
    if not lines:
        return False
    delimiter = "," if extension == ".csv" else "\t"
    header_idx, _ = _find_tabular_header(lines, delimiter)
    return header_idx is not None


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

    columns: List[str] = []
    rows: List[Dict[str, str]] = []
    total_rows = 0

    try:
        lines = _read_text_lines(file_path)
        if not lines:
            return {"columns": [], "rows": [], "total_rows": 0}

        header_idx, columns = _find_tabular_header(lines, delimiter)
        if header_idx is None:
            raise ValueError(f"No tabular header detected in file: {file_path}")

        logger.info(f"[parse_tabular_file] Found {len(columns)} columns: {columns}")

        # 读取数据行
        for line in lines[header_idx + 1 :]:
            if not line.strip():
                continue

            total_rows += 1
            if max_rows is not None and len(rows) >= max_rows:
                # 继续计数以获取 total_rows，但不存储数据
                continue

            values = line.strip().split(delimiter)
            if len(values) == len(columns):
                row_data = dict(zip(columns, values))
                rows.append(row_data)
            elif any(values):  # 处理列数不匹配的情况
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
    port_id: Optional[str] = None,
    include_data: bool = False,
    max_rows: Optional[int] = None
) -> Dict[str, Any]:
    """
    解析节点输出文件路径并返回文件元信息

    Args:
        execution_id: 执行ID
        node_id: 节点ID
        db: 数据库连接
        port_id: 可选的端口ID，用于过滤多输出工具的特定端口
        include_data: 是否内联解析数据
        max_rows: 最大读取行数（仅当 include_data=True 时生效）

    Returns:
        {
            "execution_id": str,
            "node_id": str,
            "port_id": str | None,
            "outputs": [
                {
                    "port_id": str,
                    "data_type": str,
                    "schema": list,
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

    requested_port_id = port_id

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

    def _execution_has_node(execution: str, target_node: str) -> Optional[bool]:
        """Check whether execution_nodes table records this node for the execution.

        Returns:
            True/False when table exists, None when table is unavailable.
        """
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='execution_nodes'"
            )
            if not cursor.fetchone():
                return None
            cursor.execute(
                "SELECT 1 FROM execution_nodes WHERE execution_id = ? AND node_id = ? LIMIT 1",
                (execution, target_node),
            )
            return cursor.fetchone() is not None
        except Exception:
            return None

    # 2. 解析 workflow_snapshot 找到节点的 tool_id（无 snapshot 时从 workflows 表或上次执行回退）
    if not workflow_snapshot_json and workflow_id:
        execution_has_node = _execution_has_node(execution_id, node_id)
        if execution_has_node is False:
            raise ValueError(
                f"Node '{node_id}' is not part of execution '{execution_id}'. "
                "This execution may belong to an older workflow revision; please run the latest workflow again."
            )
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
    metadata = workflow_snapshot.get("metadata", {}) or {}
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

    # 如果 sample_context 为空或缺少 sample，占位符，先尝试从 workspace/samples.json 推断
    if not sample_context or not sample_context.get("sample"):
        samples_file = workspace_path / "samples.json"
        if samples_file.exists():
            try:
                with open(samples_file, "r", encoding="utf-8") as fp:
                    samples_payload = json.load(fp)
                samples_map = samples_payload.get("samples", {})
                if isinstance(samples_map, dict) and samples_map:
                    first_sample = next(iter(samples_map.values()))
                    if isinstance(first_sample, dict):
                        first_ctx = first_sample.get("context", {}) or {}
                        if isinstance(first_ctx, dict):
                            sample_context = {**sample_context, **first_ctx}
            except Exception:
                logger.debug(
                    "[resolve_node_outputs] Failed to read samples.json for sample context fallback",
                    exc_info=True,
                )

    # 如果 sample_context 为空或缺少 sample，占位符，尝试从 workflow_snapshot.metadata 中推断
    if not sample_context or not sample_context.get("sample"):
        sample_name = None
        samples_field = metadata.get("samples")
        if isinstance(samples_field, list) and samples_field:
            sample_name = str(samples_field[0])
        else:
            single_sample = metadata.get("sample")
            if isinstance(single_sample, str) and single_sample:
                sample_name = single_sample
        if sample_name:
            sample_context = {**sample_context, "sample": sample_name}

    # 如果仍然没有 sample_context，使用默认值
    if not sample_context:
        sample_context = {"sample": "default"}

    # 5. 解析输出路径
    logger.debug(f"[resolve_node_outputs] Resolving output paths for node {node_id}")
    logger.debug(f"[resolve_node_outputs] Sample context: {sample_context}")
    logger.debug(f"[resolve_node_outputs] Workspace: {workspace_path}")

    output_paths = _resolve_output_paths(
        node_id=node_id,
        tool_id=tool_id,
        tool_info=tool_info,
        sample_ctx=sample_context,
        workspace=workspace_path
    )

    logger.debug(f"[resolve_node_outputs] Resolved {len(output_paths)} output paths:")
    for idx, path in enumerate(output_paths):
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        logger.debug(f"  [{idx}] {path} - exists: {exists}, size: {size} bytes")

    # 6. 获取输出端口定义
    patterns = _get_output_patterns(tool_info)
    logger.debug(f"[resolve_node_outputs] Found {len(patterns)} output patterns")
    outputs = []

    for idx, file_path in enumerate(output_paths):
        file_exists = file_path.exists()
        is_directory = file_exists and file_path.is_dir()
        file_size = file_path.stat().st_size if file_exists and not is_directory else 0
        file_name = file_path.name

        logger.debug(f"[resolve_node_outputs] Processing output {idx}: {file_name}")
        logger.debug(f"  - Full path: {file_path}")
        logger.debug(f"  - Exists: {file_exists}")
        logger.debug(f"  - Size: {file_size} bytes")

        # 获取端口信息
        pattern_info = patterns[idx] if idx < len(patterns) else {}
        output_port_id = pattern_info.get("handle", pattern_info.get("id", f"port_{idx}"))
        data_type = pattern_info.get("data_type") or (
            pattern_info.get("pattern", "").split(".")[-1] if pattern_info.get("pattern") else ""
        )
        output_schema = pattern_info.get("schema", [])

        logger.debug(f"  - Port ID: {output_port_id}")
        logger.debug(f"  - Data type: {data_type}")

        # 判断是否可解析
        extension = file_path.suffix.lower()
        parseable = extension in TABULAR_EXTENSIONS and file_exists and _is_tabular_parseable(file_path)

        logger.debug(f"  - Extension: {extension}")
        logger.debug(f"  - Parseable: {parseable} (in TABULAR_EXTENSIONS: {extension in TABULAR_EXTENSIONS})")

        output_entry = {
            "port_id": output_port_id,
            "data_type": data_type,
            "schema": output_schema,
            "file_name": file_name,
            "file_path": str(file_path),
            "relative_path": str(file_path.relative_to(workspace_path)) if file_exists else str(file_path),
            "file_size": file_size,
            "exists": file_exists,
            "is_directory": is_directory,
            "parseable": parseable,
            "data": None
        }

        # 如果需要内联数据且文件可解析
        if include_data and file_exists and parseable:
            try:
                logger.debug(f"  - Parsing file with max_rows={max_rows}...")
                table_data = parse_tabular_file(file_path, max_rows)
                logger.debug(f"  - Successfully parsed {len(table_data['rows'])} rows")
                logger.debug(f"  - Columns: {table_data['columns']}")
                output_entry["data"] = table_data
            except Exception as e:
                logger.error(f"  - Failed to parse file {file_path}: {e}", exc_info=True)
                output_entry["parseable"] = False

        outputs.append(output_entry)

    # Filter by port_id if specified
    if requested_port_id:
        outputs = [o for o in outputs if o["port_id"] == requested_port_id]

    return {
        "execution_id": execution_id,
        "node_id": node_id,
        "port_id": requested_port_id,
        "outputs": outputs
    }
