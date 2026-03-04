"""
Migration script to add missing user_id and workspace_id columns
Run this if you see 'no such column: user_id' or 'no such column: workspace_id' errors
"""
import sqlite3
import sys
from pathlib import Path
import re

def migrate_table(cursor, table_name: str, required_columns: dict) -> bool:
    """
    Migrate a table to add missing columns

    Args:
        cursor: Database cursor
        table_name: Name of the table to migrate
        required_columns: Dict of {column_name: column_definition}

    Returns:
        True if migration successful, False otherwise
    """
    try:
        # Check current columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}

        missing_columns = {col: defn for col, defn in required_columns.items() if col not in existing_columns}

        if not missing_columns:
            print(f"[OK] {table_name} table already has all required columns")
            return True

        print(f"[INFO] {table_name} table missing columns: {list(missing_columns.keys())}")

        for col_name, col_defn in missing_columns.items():
            print(f"[WARN] Adding {col_name} column to {table_name} table...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_defn}")
            print(f"[OK] Added {col_name} column to {table_name} table")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to migrate {table_name} table: {e}")
        return False

def extract_workspace_id_from_path(workspace_path: str) -> str:
    """Extract workspace_id from workspace_path"""
    if not workspace_path:
        return ""
    # Extract from path like "data/users/default_user/workspaces/workspace_id"
    match = re.search(r'workspaces/([^/]+)', workspace_path)
    if match:
        return match.group(1)
    return ""

def migrate_all_tables():
    """Migrate all tables to add missing columns"""
    db_path = Path("data/tdease.db")

    if not db_path.exists():
        print(f"[ERROR] Database not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Define required columns for each table
        tables_to_migrate = {
            "workflows": {
                "user_id": "TEXT DEFAULT 'default_user'",
                "workspace_id": "TEXT"
            },
            "samples": {
                "user_id": "TEXT DEFAULT 'default_user'",
            },
            "executions": {
                "user_id": "TEXT DEFAULT 'default_user'",
                "workspace_id": "TEXT"
            }
        }

        all_success = True
        for table_name, required_cols in tables_to_migrate.items():
            if not migrate_table(cursor, table_name, required_cols):
                all_success = False

        if all_success:
            # Update existing records with default values
            print("[INFO] Updating existing records with default values...")

            # Update workflows table
            cursor.execute("SELECT id, workspace_path FROM workflows WHERE user_id IS NULL OR user_id = ''")
            for row in cursor.fetchall():
                wf_id, workspace_path = row
                workspace_id = extract_workspace_id_from_path(workspace_path)
                cursor.execute(
                    "UPDATE workflows SET user_id = 'default_user', workspace_id = ? WHERE id = ?",
                    (workspace_id, wf_id)
                )
            print(f"[OK] Updated {cursor.rowcount} workflows records")

            # Update samples table
            cursor.execute("UPDATE samples SET user_id = 'default_user' WHERE user_id IS NULL OR user_id = ''")
            print(f"[OK] Updated {cursor.rowcount} samples records")

            # Update executions table
            cursor.execute("SELECT id, workspace_path FROM executions WHERE user_id IS NULL OR user_id = ''")
            for row in cursor.fetchall():
                exec_id, workspace_path = row
                workspace_id = extract_workspace_id_from_path(workspace_path)
                cursor.execute(
                    "UPDATE executions SET user_id = 'default_user', workspace_id = ? WHERE id = ?",
                    (workspace_id, exec_id)
                )
            print(f"[OK] Updated {cursor.rowcount} executions records")

            conn.commit()
            return True
        else:
            conn.rollback()
            return False

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add user_id and workspace_id columns")
    print("=" * 60)
    print()

    if migrate_all_tables():
        print()
        print("=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("[ERROR] Migration failed!")
        print("=" * 60)
        sys.exit(1)
