"""
Seed default workflow into database

Loads tests/test.json and saves to database.
Uses new architecture: workspace_path = data/users/{user_id}/workspaces/{workspace_id}/
"""

import sqlite3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.init_db import initialize_database
from app.services.unified_workspace_manager import get_unified_workspace_manager

# Paths
db_path = "data/tdease.db"
test_workflow_path = Path(__file__).parent.parent / "tests" / "test.json"

# Default workspace for seeded workflow (matches test_user/test_workspace in samples.json)
DEFAULT_USER_ID = "test_user"
DEFAULT_WORKSPACE_ID = "test_workspace"

# Fixture: samples.json for test workspace（统一使用 sample 名，由前端/context 保证）
SAMPLES_FIXTURE_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "samples_test_workspace.json"


def load_test_workflow():
    """Load test workflow from JSON file"""
    if not test_workflow_path.exists():
        raise FileNotFoundError(f"Test workflow file not found: {test_workflow_path}")
    
    with open(test_workflow_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def seed():
    """Seed default workflow into database"""
    # Ensure database is initialized
    print("Initializing database if needed...")
    initialize_database()
    
    # Use workspace path (new architecture); ensure dirs exist
    manager = get_unified_workspace_manager()
    workspace_path = manager.get_workspace_path(DEFAULT_USER_ID, DEFAULT_WORKSPACE_ID)
    (workspace_path / "workflows").mkdir(parents=True, exist_ok=True)
    (workspace_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (workspace_path / "data" / "fasta").mkdir(parents=True, exist_ok=True)
    # 若测试工作区尚无 samples.json 或 samples 为空，写入 fixture（统一使用 sample 名）
    samples_file = workspace_path / "samples.json"
    if SAMPLES_FIXTURE_PATH.exists():
        if not samples_file.exists():
            with open(SAMPLES_FIXTURE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
            with open(samples_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Created {samples_file} from fixture")
        else:
            samples_data = json.loads(samples_file.read_text(encoding="utf-8"))
            if not samples_data.get("samples"):
                with open(SAMPLES_FIXTURE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
                with open(samples_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  Filled empty samples.json from fixture")
    workspace_path = str(workspace_path.resolve()) if hasattr(workspace_path, 'resolve') else str(workspace_path)
    
    # Load test workflow
    print(f"Loading test workflow from: {test_workflow_path}")
    wf_data = load_test_workflow()
    
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    wf_id = wf_data["metadata"]["id"]
    name = wf_data["metadata"]["name"]
    description = wf_data["metadata"].get("description", "")
    
    # Prepare vueflow_data and workflow_document
    vueflow_data = json.dumps(wf_data, ensure_ascii=False)
    workflow_document = vueflow_data
    metadata = json.dumps(wf_data["metadata"], ensure_ascii=False)
    
    # Save workflow JSON to workspace/workflows/ (optional, for consistency)
    workflows_dir = Path(workspace_path) / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    wf_file = workflows_dir / f"{wf_id}.json"
    wf_file.write_text(vueflow_data, encoding='utf-8')
    print(f"  Saved to workspace: {wf_file}")
    
    try:
        cursor.execute("SELECT id FROM workflows WHERE id=?", (wf_id,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"Updating existing workflow: {wf_id}")
            cursor.execute("""
                UPDATE workflows 
                SET name=?, description=?, vueflow_data=?, workspace_path=?,
                    updated_at=?, metadata=?, status='created',
                    workflow_format='vueflow', workflow_document=?
                WHERE id=?
            """, (name, description, vueflow_data, workspace_path, now, metadata, workflow_document, wf_id))
        else:
            print(f"Inserting new workflow: {wf_id}")
            cursor.execute("""
                INSERT INTO workflows (
                    id, name, description, vueflow_data, workspace_path, 
                    status, created_at, updated_at, metadata,
                    workflow_format, workflow_document
                )
                VALUES (?, ?, ?, ?, ?, 'created', ?, ?, ?, 'vueflow', ?)
            """, (wf_id, name, description, vueflow_data, workspace_path, now, now, metadata, workflow_document))
        
        conn.commit()
        print(f"✓ Successfully saved workflow '{name}' (ID: {wf_id}) to database")
        print(f"  Workspace: {workspace_path}")
        print(f"  Nodes: {len(wf_data.get('nodes', []))}, Edges: {len(wf_data.get('edges', []))}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    success = seed()
    sys.exit(0 if success else 1)
