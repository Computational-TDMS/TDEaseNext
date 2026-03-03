#!/usr/bin/env python3
"""
Database Migration Script for New Architecture

This script handles:
1. Backing up existing database
2. Cleaning old batch_configs (now using samples.json)
3. Updating workflow formats if needed
4. Providing a fresh start option

Run: python scripts/migrate_database.py --help
"""
import sys
import sqlite3
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.init_db import backup_database, check_database_health


def backup_existing_db(db_path: str = "data/tdease.db") -> bool:
    """Backup existing database"""
    print(f"[*] Backing up database: {db_path}")
    if backup_database(source_path=db_path):
        print("[OK] Database backed up successfully")
        return True
    print("[FAIL] Database backup failed")
    return False


def clean_batch_configs(db_path: str = "data/tdease.db") -> int:
    """
    Clean batch_configs table - no longer needed with samples.json approach
    Returns: number of rows deleted
    """
    print(f"[*] Cleaning batch_configs table (deprecated in new architecture)")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count before
        cursor.execute("SELECT COUNT(*) FROM batch_configs")
        before_count = cursor.fetchone()[0]

        # Delete all batch configs
        cursor.execute("DELETE FROM batch_configs")

        conn.commit()
        conn.close()

        print(f"[OK] Deleted {before_count} batch config(s)")
        return before_count

    except Exception as e:
        print(f"[FAIL] Error cleaning batch_configs: {e}")
        return 0


def analyze_workflows(db_path: str = "data/tdease.db") -> dict:
    """Analyze workflows in database for compatibility issues"""
    print(f"[*] Analyzing workflows in database")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, vueflow_data FROM workflows")
        rows = cursor.fetchall()

        analysis = {
            "total": len(rows),
            "has_sample_context": 0,
            "needs_migration": 0,
            "compatible": 0,
            "samples": []
        }

        for row in rows:
            wf_id, name, vueflow_data = row
            try:
                if vueflow_data:
                    wf = json.loads(vueflow_data)
                    metadata = wf.get("metadata", {})

                    # Check for old sample_context in metadata
                    if "sample_context" in metadata:
                        analysis["has_sample_context"] += 1
                        analysis["needs_migration"] += 1
                        analysis["samples"].append({
                            "id": wf_id,
                            "name": name,
                            "issue": "Contains inline sample_context (deprecated)"
                        })
                    else:
                        analysis["compatible"] += 1
            except:
                analysis["samples"].append({
                    "id": wf_id,
                    "name": name,
                    "issue": "Invalid JSON"
                })

        conn.close()

        print(f"[OK] Analysis complete:")
        print(f"  Total workflows: {analysis['total']}")
        print(f"  Compatible: {analysis['compatible']}")
        print(f"  Needs migration: {analysis['needs_migration']} (contain sample_context)")

        return analysis

    except Exception as e:
        print(f"[FAIL] Error analyzing workflows: {e}")
        return {"total": 0, "has_sample_context": 0, "needs_migration": 0, "compatible": 0}


def migrate_workflow(workflow_id: str, db_path: str = "data/tdease.db") -> bool:
    """
    Migrate a single workflow to new format
    Removes sample_context from metadata
    """
    print(f"[*] Migrating workflow: {workflow_id}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT vueflow_data FROM workflows WHERE id = ?", (workflow_id,))
        row = cursor.fetchone()
        if not row:
            print(f"[FAIL] Workflow not found: {workflow_id}")
            return False

        vueflow_data = json.loads(row[0])

        # Remove sample_context from metadata
        if "metadata" in vueflow_data and "sample_context" in vueflow_data["metadata"]:
            del vueflow_data["metadata"]["sample_context"]
            print(f"  - Removed sample_context from metadata")

        # Update modified timestamp
        vueflow_data["metadata"]["modified"] = datetime.now().isoformat() + "Z"

        # Save back
        cursor.execute(
            "UPDATE workflows SET vueflow_data = ?, updated_at = ? WHERE id = ?",
            (json.dumps(vueflow_data), datetime.now().isoformat() + "Z", workflow_id)
        )

        conn.commit()
        conn.close()

        print(f"[OK] Workflow migrated: {workflow_id}")
        return True

    except Exception as e:
        print(f"[FAIL] Error migrating workflow: {e}")
        return False


def reset_database(db_path: str = "data/tdease.db") -> bool:
    """
    Complete database reset - DESTRUCTIVE
    Removes all workflows and executions
    Keeps table structure
    """
    print(f"[!] WARNING: This will DELETE ALL workflows and executions!")

    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("[CANCEL] Database reset cancelled")
        return False

    print(f"[*] Resetting database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Delete all data but keep tables
        cursor.execute("DELETE FROM execution_nodes")
        cursor.execute("DELETE FROM executions")
        cursor.execute("DELETE FROM workflows")
        cursor.execute("DELETE FROM batch_configs")
        cursor.execute("DELETE FROM files")

        conn.commit()
        conn.close()

        print("[OK] Database reset complete")
        print("     - All workflows deleted")
        print("     - All executions deleted")
        print("     - All batch configs deleted")
        print("     - Table structure preserved")

        return True

    except Exception as e:
        print(f"[FAIL] Error resetting database: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Database migration tool for new architecture")
    parser.add_argument("--backup", action="store_true", help="Backup database before migration")
    parser.add_argument("--clean-batch", action="store_true", help="Clean deprecated batch_configs")
    parser.add_argument("--analyze", action="store_true", help="Analyze workflows for compatibility")
    parser.add_argument("--migrate", type=str, metavar="ID", help="Migrate specific workflow by ID")
    parser.add_argument("--reset", action="store_true", help="Complete database reset (DESTRUCTIVE)")
    parser.add_argument("--db", type=str, default="data/tdease.db", help="Database path")

    args = parser.parse_args()

    print("=" * 60)
    print("Database Migration Tool - New Architecture")
    print("=" * 60)
    print()

    db_path = args.db

    # Check if database exists
    if not Path(db_path).exists():
        print(f"[INFO] Database not found: {db_path}")
        print(f"[INFO] Database will be created on first run")
        return 0

    # Backup if requested
    if args.backup:
        if not backup_existing_db(db_path):
            return 1
        print()

    # Analyze workflows
    if args.analyze:
        analysis = analyze_workflows(db_path)
        print()

        if analysis["needs_migration"] > 0:
            print("Workflows needing migration:")
            for s in analysis["samples"]:
                if "Contains inline sample_context" in s.get("issue", ""):
                    print(f"  - {s['id']}: {s['name']}")
        print()
        return 0

    # Migrate specific workflow
    if args.migrate:
        if not migrate_workflow(args.migrate, db_path):
            return 1
        print()
        return 0

    # Clean batch configs
    if args.clean_batch:
        clean_batch_configs(db_path)
        print()

    # Reset database
    if args.reset:
        if not reset_database(db_path):
            return 1
        print()

    # If no action specified, show status
    if not (args.backup or args.clean_batch or args.analyze or args.migrate or args.reset):
        health = check_database_health(db_path)
        print(f"Database Status:")
        print(f"  Path: {health.get('path')}")
        print(f"  Healthy: {health.get('healthy')}")
        if health.get('statistics'):
            print(f"  Statistics:")
            for key, value in health.get('statistics', {}).items():
                print(f"    - {key}: {value}")
        print()
        print("Recommended actions:")
        print("  1. --analyze: Check workflow compatibility")
        print("  2. --clean-batch: Remove deprecated batch_configs")
        print("  3. --backup: Backup before changes")
        print("  4. --reset: Fresh start (DESTRUCTIVE)")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
