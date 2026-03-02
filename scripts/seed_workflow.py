"""
Seed test workflow into database
Loads the test workflow from TDEase-FrontEnd/workflows/test.json and saves it to the database
"""

import sqlite3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.init_db import initialize_database

# Paths
db_path = "data/tdease.db"
test_workflow_path = Path(__file__).parent.parent / "tests" / "test.json"

def load_test_workflow():
    """Load test workflow from JSON file"""
    if not test_workflow_path.exists():
        raise FileNotFoundError(f"Test workflow file not found: {test_workflow_path}")
    
    with open(test_workflow_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def seed():
    """Seed test workflow into database"""
    # Ensure database is initialized
    print("Initializing database if needed...")
    initialize_database()
    
    # Load test workflow
    print(f"Loading test workflow from: {test_workflow_path}")
    wf_data = load_test_workflow()
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    wf_id = wf_data["metadata"]["id"]
    name = wf_data["metadata"]["name"]
    description = wf_data["metadata"].get("description", "")
    workspace_path = f"data/workflows/{wf_id}"
    
    # Prepare vueflow_data (the entire workflow structure)
    vueflow_data = json.dumps(wf_data, ensure_ascii=False)
    
    # Prepare metadata (just the metadata section)
    metadata = json.dumps(wf_data["metadata"], ensure_ascii=False)
    
    try:
        # Check if workflow exists
        cursor.execute("SELECT id FROM workflows WHERE id=?", (wf_id,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"Updating existing workflow: {wf_id}")
            cursor.execute("""
                UPDATE workflows 
                SET name=?, 
                    description=?, 
                    vueflow_data=?, 
                    workspace_path=?,
                    updated_at=?, 
                    metadata=?,
                    status='created'
                WHERE id=?
            """, (name, description, vueflow_data, workspace_path, now, metadata, wf_id))
        else:
            print(f"Inserting new workflow: {wf_id}")
            cursor.execute("""
                INSERT INTO workflows (
                    id, name, description, vueflow_data, workspace_path, 
                    status, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, 'created', ?, ?, ?)
            """, (wf_id, name, description, vueflow_data, workspace_path, now, now, metadata))
        
        conn.commit()
        print(f"✓ Successfully saved workflow '{name}' (ID: {wf_id}) to database")
        print(f"  Workspace path: {workspace_path}")
        print(f"  Nodes: {len(wf_data.get('nodes', []))}")
        print(f"  Edges: {len(wf_data.get('edges', []))}")
        
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
