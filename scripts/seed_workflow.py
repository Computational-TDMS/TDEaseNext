"""
Seed workflow JSON files into SQLite workflows table.

Supports:
- Single workflow file
- Batch import from a directory
- Optional user/workspace inference from path:
  data/users/<user_id>/workspaces/<workspace_id>/workflows/<file>.json
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Tuple

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.init_db import initialize_database
from app.services.unified_workspace_manager import get_unified_workspace_manager

DB_PATH = "data/tdease.db"
DEFAULT_USER_ID = "test_user"
DEFAULT_WORKSPACE_ID = "test_workspace"
DEFAULT_WORKFLOW_PATH = Path(__file__).parent.parent / "tests" / "test.json"
SAMPLES_FIXTURE_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "samples_test_workspace.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed workflow JSON(s) into workflows table")
    parser.add_argument(
        "--workflow",
        type=str,
        default=str(DEFAULT_WORKFLOW_PATH),
        help="Single workflow JSON path (kept for backward compatibility)",
    )
    parser.add_argument(
        "--workflow-dir",
        type=str,
        help="Directory containing workflow JSON files to import in batch",
    )
    parser.add_argument(
        "--glob",
        type=str,
        default="*.json",
        help="Glob pattern for --workflow-dir (default: *.json)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search under --workflow-dir",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=DEFAULT_USER_ID,
        help="Fallback user ID when path inference is unavailable",
    )
    parser.add_argument(
        "--workspace-id",
        type=str,
        default=DEFAULT_WORKSPACE_ID,
        help="Fallback workspace ID when path inference is unavailable",
    )
    parser.add_argument(
        "--infer-workspace",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Infer user_id/workspace_id from workflow path when possible",
    )
    parser.add_argument(
        "--continue-on-error",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Continue processing remaining files if one fails",
    )
    parser.add_argument(
        "--ensure-samples-fixture",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Ensure samples.json exists (or is not empty) using tests fixture",
    )
    return parser.parse_args()


def _load_workflow(workflow_path: Path) -> dict:
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _infer_user_workspace(workflow_path: Path) -> Optional[Tuple[str, str]]:
    # Expected pattern: .../data/users/<user_id>/workspaces/<workspace_id>/workflows/<file>.json
    parts = workflow_path.resolve().parts
    try:
        users_idx = parts.index("users")
        if parts[users_idx + 2] != "workspaces":
            return None
        user_id = parts[users_idx + 1]
        workspace_id = parts[users_idx + 3]
        return user_id, workspace_id
    except (ValueError, IndexError):
        return None


def _discover_workflow_files(args: argparse.Namespace) -> list[Path]:
    if args.workflow_dir:
        root = Path(args.workflow_dir)
        if not root.exists():
            raise FileNotFoundError(f"Workflow directory not found: {root}")
        iterator: Iterable[Path]
        if args.recursive:
            iterator = root.rglob(args.glob)
        else:
            iterator = root.glob(args.glob)
        files = sorted(p for p in iterator if p.is_file())
        if not files:
            raise FileNotFoundError(f"No workflow files found in {root} with pattern {args.glob}")
        return files
    return [Path(args.workflow)]


def _ensure_workspace_layout(
    manager,
    user_id: str,
    workspace_id: str,
    ensure_samples_fixture: bool,
) -> Path:
    workspace_path = manager.get_workspace_path(user_id, workspace_id)
    (workspace_path / "workflows").mkdir(parents=True, exist_ok=True)
    (workspace_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (workspace_path / "data" / "fasta").mkdir(parents=True, exist_ok=True)

    if ensure_samples_fixture and SAMPLES_FIXTURE_PATH.exists():
        samples_file = workspace_path / "samples.json"
        needs_write = not samples_file.exists()
        if not needs_write:
            try:
                samples_data = json.loads(samples_file.read_text(encoding="utf-8"))
                needs_write = not bool(samples_data.get("samples"))
            except Exception:
                needs_write = True
        if needs_write:
            fixture_data = json.loads(SAMPLES_FIXTURE_PATH.read_text(encoding="utf-8"))
            fixture_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            fixture_data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
            samples_file.write_text(json.dumps(fixture_data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  [workspace:{workspace_id}] seeded samples.json from fixture")

    return workspace_path


def _extract_workflow_identity(wf_data: dict) -> Tuple[str, str, str, dict]:
    metadata_obj = wf_data.get("metadata", {})
    wf_id = metadata_obj.get("id") or wf_data.get("workflow_id")
    if not wf_id:
        raise ValueError("Workflow must contain metadata.id or workflow_id")
    name = metadata_obj.get("name") or wf_data.get("name") or wf_id
    description = metadata_obj.get("description") or wf_data.get("description", "")
    return wf_id, name, description, metadata_obj


def _upsert_workflow(
    cursor: sqlite3.Cursor,
    wf_data: dict,
    workspace_path: Path,
    now: str,
) -> Tuple[str, str, bool]:
    wf_id, name, description, metadata_obj = _extract_workflow_identity(wf_data)
    workspace_path_str = str(workspace_path.resolve())

    vueflow_data = json.dumps(wf_data, ensure_ascii=False)
    workflow_document = vueflow_data
    metadata = json.dumps(metadata_obj, ensure_ascii=False)

    cursor.execute("SELECT id FROM workflows WHERE id=?", (wf_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE workflows
            SET name=?, description=?, vueflow_data=?, workspace_path=?,
                updated_at=?, metadata=?, status='created',
                workflow_format='vueflow', workflow_document=?
            WHERE id=?
            """,
            (name, description, vueflow_data, workspace_path_str, now, metadata, workflow_document, wf_id),
        )
        inserted = False
    else:
        cursor.execute(
            """
            INSERT INTO workflows (
                id, name, description, vueflow_data, workspace_path,
                status, created_at, updated_at, metadata,
                workflow_format, workflow_document
            )
            VALUES (?, ?, ?, ?, ?, 'created', ?, ?, ?, 'vueflow', ?)
            """,
            (wf_id, name, description, vueflow_data, workspace_path_str, now, now, metadata, workflow_document),
        )
        inserted = True

    # Keep a readable copy in workspace
    workflows_dir = workspace_path / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    wf_file = workflows_dir / f"{wf_id}.json"
    wf_file.write_text(json.dumps(wf_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return wf_id, name, inserted


def seed(args: argparse.Namespace) -> bool:
    print("Initializing database if needed...")
    initialize_database()

    manager = get_unified_workspace_manager()
    workflow_files = _discover_workflow_files(args)
    print(f"Discovered {len(workflow_files)} workflow file(s)")

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    ensured_workspaces: set[tuple[str, str]] = set()
    succeeded = 0
    failed = 0

    try:
        for workflow_path in workflow_files:
            try:
                inferred = _infer_user_workspace(workflow_path) if args.infer_workspace else None
                user_id = inferred[0] if inferred else args.user_id
                workspace_id = inferred[1] if inferred else args.workspace_id

                workspace_key = (user_id, workspace_id)
                if workspace_key not in ensured_workspaces:
                    _ensure_workspace_layout(
                        manager,
                        user_id=user_id,
                        workspace_id=workspace_id,
                        ensure_samples_fixture=args.ensure_samples_fixture,
                    )
                    ensured_workspaces.add(workspace_key)

                wf_data = _load_workflow(workflow_path)
                now = datetime.now(timezone.utc).isoformat()
                workspace_path = manager.get_workspace_path(user_id, workspace_id)
                wf_id, name, inserted = _upsert_workflow(
                    cursor=cursor,
                    wf_data=wf_data,
                    workspace_path=workspace_path,
                    now=now,
                )
                conn.commit()

                action = "inserted" if inserted else "updated"
                print(
                    f"[OK] {action}: {wf_id} | "
                    f"user={user_id} workspace={workspace_id} | "
                    f"nodes={len(wf_data.get('nodes', []))} edges={len(wf_data.get('edges', []))}"
                )
                succeeded += 1
            except Exception as exc:
                conn.rollback()
                failed += 1
                print(f"[ERROR] {workflow_path}: {exc}")
                if not args.continue_on_error:
                    return False

        print(f"Done. success={succeeded}, failed={failed}, total={len(workflow_files)}")
        return failed == 0
    finally:
        conn.close()


if __name__ == "__main__":
    cli_args = _parse_args()
    ok = seed(cli_args)
    sys.exit(0 if ok else 1)
