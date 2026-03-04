"""
Migrate samples from JSON files to database

This script reads all samples.json files from the file system and migrates
them to the database. It also converts relative paths to absolute paths.

Usage:
    python scripts/migrate_samples_to_db.py
"""
import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.init_db import initialize_database
from app.services.sample_store import sample_store


def backup_samples_file(samples_file: Path) -> Path:
    """
    Backup samples.json file

    Args:
        samples_file: Path to samples.json file

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = samples_file.parent / f"samples.json.bak.{timestamp}"
    shutil.copy2(samples_file, backup_file)
    return backup_file


def migrate_workspace_samples(user_id: str, workspace_id: str, data_root: str = "data") -> dict:
    """
    Migrate samples for a single workspace

    Args:
        user_id: User ID
        workspace_id: Workspace ID
        data_root: Root data directory

    Returns:
        Dictionary with migration results
    """
    samples_file = Path(data_root) / "users" / user_id / "workspaces" / workspace_id / "samples.json"

    if not samples_file.exists():
        return {
            "status": "skipped",
            "reason": "samples.json not found",
            "migrated_count": 0
        }

    try:
        with open(samples_file, 'r', encoding='utf-8') as f:
            samples_data = json.load(f)
    except Exception as e:
        # Log error internally but don't expose details in return
        import sys
        print(f"[ERROR] Failed to read samples.json: {e}", file=sys.stderr)
        return {
            "status": "error",
            "reason": "Failed to read samples.json",
            "migrated_count": 0
        }

    migrated_count = 0
    failed_samples = []

    workspace_path = samples_file.parent.resolve()

    def validate_path_safe(path_str: str, allowed_base: Path) -> Optional[Path]:
        """Validate path is within allowed directory"""
        try:
            path = Path(path_str)
            if path.is_absolute():
                resolved = path.resolve()
            else:
                resolved = (allowed_base / path).resolve()

            # Check if resolved path is within allowed base
            try:
                resolved.relative_to(allowed_base.resolve())
                return resolved
            except ValueError:
                print(f"[WARN] Path traversal attempt detected: {path_str}", file=sys.stderr)
                return None
        except (OSError, RuntimeError) as e:
            print(f"[WARN] Invalid path {path_str}: {e}", file=sys.stderr)
            return None

    for sample_id, sample_def in samples_data.get("samples", {}).items():
        try:
            # Convert data_paths to absolute paths with validation
            absolute_data_paths = {}
            for key, rel_path in sample_def.get("data_paths", {}).items():
                if rel_path:
                    # Validate and resolve path
                    safe_path = validate_path_safe(rel_path, workspace_path)
                    if safe_path:
                        absolute_data_paths[key] = str(safe_path)
                    else:
                        # Skip this path or use empty string
                        absolute_data_paths[key] = ""
                        print(f"  [WARN] Skipping unsafe path for {sample_id}.{key}: {rel_path}")
                else:
                    absolute_data_paths[key] = ""

            sample_data = {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "name": sample_def.get("name", sample_id),
                "description": sample_def.get("description", ""),
                "context": sample_def.get("context", {}),
                "data_paths": absolute_data_paths,
                "metadata": sample_def.get("metadata", {})
            }

            if sample_store.save(sample_id, sample_data):
                migrated_count += 1
                print(f"  [OK] Migrated sample: {sample_id}")
            else:
                failed_samples.append(sample_id)
                print(f"  [X] Failed to migrate sample: {sample_id}")

        except Exception as e:
            failed_samples.append(sample_id)
            print(f"  [X] Error migrating sample {sample_id}: {e}")

    # Backup original samples.json
    try:
        backup_file = backup_samples_file(samples_file)
        backup_info = str(backup_file)
    except Exception as e:
        backup_info = f"Backup failed: {e}"

    return {
        "status": "completed",
        "migrated_count": migrated_count,
        "failed_samples": failed_samples,
        "backup_file": backup_info
    }


def main():
    """Main migration function"""
    print("[*] Starting sample migration to database...")
    print(f"    Timestamp: {datetime.now().isoformat()}")
    print()

    # Initialize database
    print("[*] Initializing database...")
    if not initialize_database():
        print("[X] Database initialization failed")
        sys.exit(1)
    print("[OK] Database initialized")
    print()

    data_root = Path("data/users")
    if not data_root.exists():
        print("❌ No users directory found")
        sys.exit(1)

    total_migrated = 0
    total_workspaces = 0
    total_failed = 0
    migration_results = []

    # Traverse all users and workspaces
    for user_dir in data_root.iterdir():
        if not user_dir.is_dir():
            continue

        user_id = user_dir.name
        workspaces_dir = user_dir / "workspaces"

        if not workspaces_dir.exists():
            continue

        for workspace_dir in workspaces_dir.iterdir():
            if not workspace_dir.is_dir():
                continue

            workspace_id = workspace_dir.name
            print(f"[*] Migrating {user_id}/{workspace_id}...")

            result = migrate_workspace_samples(user_id, workspace_id)
            migration_results.append({
                "user_id": user_id,
                "workspace_id": workspace_id,
                **result
            })

            if result["status"] == "completed":
                migrated = result["migrated_count"]
                failed = len(result.get("failed_samples", []))
                total_migrated += migrated
                total_failed += failed
                total_workspaces += 1
                print(f"    Migrated: {migrated}, Failed: {failed}")
                if result.get("backup_file"):
                    print(f"    Backup: {result['backup_file']}")
            elif result["status"] == "error":
                print(f"    [!] Error: {result['reason']}")
            else:
                print(f"    >> Skipped: {result['reason']}")

            print()

    # Summary
    print("=" * 60)
    print("[OK] Migration complete!")
    print(f"    Workspaces processed: {total_workspaces}")
    print(f"    Samples migrated: {total_migrated}")
    print(f"    Samples failed: {total_failed}")
    print(f"    Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    # Show details if there were failures
    if total_failed > 0:
        print()
        print("[!] Failed samples:")
        for result in migration_results:
            if result.get("failed_samples"):
                print(f"   {result['user_id']}/{result['workspace_id']}:")
                for sample_id in result["failed_samples"]:
                    print(f"     - {sample_id}")

    # Save migration report
    report_file = Path("data") / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "workspaces_processed": total_workspaces,
                    "samples_migrated": total_migrated,
                    "samples_failed": total_failed
                },
                "details": migration_results
            }, f, indent=2)
        print()
        print(f"[INFO] Migration report saved to: {report_file}")
    except Exception as e:
        print(f"[!] Failed to save migration report: {e}")


if __name__ == "__main__":
    main()
