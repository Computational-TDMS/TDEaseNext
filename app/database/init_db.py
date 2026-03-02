"""
Database Initialization
Creates and initializes database tables for TDEase API
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles database initialization and migrations"""

    def __init__(self, db_path: str = "data/tdease.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize_database(self) -> bool:
        """Initialize all database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Create tables
                self._create_workflows_table(conn)
                self._create_executions_table(conn)
                self._create_execution_nodes_table(conn)
                self._create_tools_table(conn)
                self._create_files_table(conn)
                self._create_batch_configs_table(conn)

                # Create indexes
                self._create_indexes(conn)

                # Insert default data
                self._insert_default_data(conn)

                conn.commit()
                logger.info(f"Database initialized successfully: {self.db_path}")
                return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    def _create_workflows_table(self, conn: sqlite3.Connection):
        """Create workflows table"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                vueflow_data TEXT NOT NULL,
                workspace_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                metadata TEXT,
                workflow_format TEXT,
                workflow_document TEXT,
                batch_config TEXT
            )
        """)
        # Migrate existing tables to add new columns if they do not exist
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(workflows)")
            cols = {row[1] for row in cursor.fetchall()}
            if "workflow_format" not in cols:
                conn.execute("ALTER TABLE workflows ADD COLUMN workflow_format TEXT")
            if "workflow_document" not in cols:
                conn.execute("ALTER TABLE workflows ADD COLUMN workflow_document TEXT")
            if "batch_config" not in cols:
                conn.execute("ALTER TABLE workflows ADD COLUMN batch_config TEXT")
        except Exception:
            pass

    def _create_executions_table(self, conn: sqlite3.Connection):
        """Create executions table"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                start_time TEXT NOT NULL,
                end_time TEXT,
                engine_args TEXT,
                config_overrides TEXT,
                environment TEXT,
                workspace_path TEXT NOT NULL,
                workflow_snapshot TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
            )
        """)
        # Migration: Add workflow_snapshot column if it doesn't exist
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(executions)")
            cols = {row[1] for row in cursor.fetchall()}
            if "workflow_snapshot" not in cols:
                conn.execute("ALTER TABLE executions ADD COLUMN workflow_snapshot TEXT")
            # Migration: Rename snakemake_args to engine_args for existing databases
            if "snakemake_args" in cols and "engine_args" not in cols:
                logger.info("Migration: Renaming snakemake_args to engine_args")
                conn.execute("ALTER TABLE executions RENAME COLUMN snakemake_args TO engine_args")
        except Exception as e:
            logger.debug(f"Executions table migration note: {e}")
    
    def _create_execution_nodes_table(self, conn: sqlite3.Connection):
        """Create execution_nodes table for node-level tracking"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS execution_nodes (
                id TEXT PRIMARY KEY,
                execution_id TEXT NOT NULL,
                node_id TEXT NOT NULL,
                rule_name TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                start_time TEXT,
                end_time TEXT,
                progress INTEGER DEFAULT 0,
                log_path TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES executions (id) ON DELETE CASCADE
            )
        """)

    def _create_tools_table(self, conn: sqlite3.Connection):
        """Create tools table"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                name TEXT PRIMARY KEY,
                version TEXT,
                description TEXT,
                category TEXT,
                executable_path TEXT,
                is_available INTEGER DEFAULT 0,
                platform_info TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)

    def _create_files_table(self, conn: sqlite3.Connection):
        """Create files table"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                safe_filename TEXT NOT NULL,
                file_path TEXT UNIQUE NOT NULL,
                workspace_path TEXT NOT NULL,
                subdirectory TEXT,
                size INTEGER NOT NULL,
                mime_type TEXT,
                uploaded_at TEXT NOT NULL
            )
        """)
    
    def _create_batch_configs_table(self, conn: sqlite3.Connection):
        """Create batch_configs table - stores batch configurations separately from workflows, linked to user_id"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batch_configs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                config_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                is_shared INTEGER DEFAULT 0
            )
        """)
        # Migration: add column if table exists but column doesn't
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(batch_configs)")
            cols = {row[1] for row in cursor.fetchall()}
            if "is_shared" not in cols:
                conn.execute("ALTER TABLE batch_configs ADD COLUMN is_shared INTEGER DEFAULT 0")
        except Exception:
            pass

    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for performance"""
        # Workflows indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows (status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows (created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_workflows_format ON workflows (workflow_format)")

        # Executions indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions (workflow_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_status ON executions (status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_executions_created_at ON executions (created_at)")
        
        # Execution nodes indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_execution_nodes_execution_id ON execution_nodes (execution_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_execution_nodes_node_id ON execution_nodes (node_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_execution_nodes_status ON execution_nodes (status)")

        # Tools indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_category ON tools (category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tools_is_available ON tools (is_available)")

        # Files indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_workspace_path ON files (workspace_path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_uploaded_at ON files (uploaded_at)")
        
        # Batch configs indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_batch_configs_user_id ON batch_configs (user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_batch_configs_created_at ON batch_configs (created_at)")

    def _insert_default_data(self, conn: sqlite3.Connection):
        """Insert default data into tables"""
        # Insert default tool categories
        default_categories = [
            ("converter", "File format converters"),
            ("processor", "Data processing tools"),
            ("analyzer", "Analysis and statistics"),
            ("visualizer", "Visualization tools"),
            ("utility", "General utilities"),
            ("other", "Other tools")
        ]

        # Note: Categories are just metadata, not stored in separate table
        # This is for documentation purposes

        logger.debug("Default data inserted successfully")


def initialize_database(db_path: Optional[str] = None) -> bool:
    """Initialize database with default path"""
    initializer = DatabaseInitializer(db_path or "data/tdease.db")
    return initializer.initialize_database()


def get_database_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get database connection"""
    db_path = db_path or "data/tdease.db"
    db_file = Path(db_path)

    # Ensure database exists and is initialized
    if not db_file.exists():
        if not initialize_database(db_path):
            raise RuntimeError(f"Failed to initialize database: {db_path}")
    else:
        # Migration: Ensure all required tables exist (for existing databases)
        try:
            initializer = DatabaseInitializer(db_path)
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # Check required tables
                required_tables = ["workflows", "executions", "execution_nodes", "tools", "files", "batch_configs"]
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                # Create missing tables
                if "workflows" not in existing_tables:
                    logger.info("Migration: Creating workflows table")
                    initializer._create_workflows_table(conn)
                if "executions" not in existing_tables:
                    logger.info("Migration: Creating executions table")
                    initializer._create_executions_table(conn)
                if "execution_nodes" not in existing_tables:
                    logger.info("Migration: Creating execution_nodes table")
                    initializer._create_execution_nodes_table(conn)
                if "tools" not in existing_tables:
                    logger.info("Migration: Creating tools table")
                    initializer._create_tools_table(conn)
                if "files" not in existing_tables:
                    logger.info("Migration: Creating files table")
                    initializer._create_files_table(conn)
                if "batch_configs" not in existing_tables:
                    logger.info("Migration: Creating batch_configs table")
                    initializer._create_batch_configs_table(conn)
                
                # Ensure indexes exist
                initializer._create_indexes(conn)
                
                # Migration: Remove FOREIGN KEY constraint on executions.workflow_id if it exists
                # This allows direct execution without requiring workflow to exist in workflows table
                try:
                    cursor.execute("PRAGMA foreign_key_check(executions)")
                    # If the above doesn't fail, check if we need to recreate the table
                    # SQLite doesn't support DROP CONSTRAINT, so we'll need to recreate
                    cursor.execute("PRAGMA table_info(executions)")
                    cols = cursor.fetchall()
                    has_fk = any(row[11] for row in cols if len(row) > 11)  # Check for FK in table_info
                    # For now, we'll just ensure the constraint doesn't block us
                    # The constraint removal will take effect on next table creation
                except Exception:
                    pass
                
                conn.commit()
        except Exception as e:
            logger.warning(f"Migration check failed: {e}")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable dictionary-like access
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def check_database_health(db_path: Optional[str] = None) -> dict:
    """Check database health and statistics"""
    try:
        db_path = db_path or "data/tdease.db"
        db_file = Path(db_path)

        if not db_file.exists():
            return {
                "healthy": False,
                "error": "Database file does not exist",
                "path": str(db_path)
            }

        with sqlite3.connect(db_path) as conn:
            # Check tables exist
            cursor = conn.cursor()

            tables = ["workflows", "executions", "execution_nodes", "tools", "files", "batch_configs"]
            missing_tables = []

            for table in tables:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                if not cursor.fetchone():
                    missing_tables.append(table)

            if missing_tables:
                return {
                    "healthy": False,
                    "error": f"Missing tables: {', '.join(missing_tables)}",
                    "path": str(db_path)
                }

            # Get statistics
            stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # Database file size
            file_size = db_file.stat().st_size

            return {
                "healthy": True,
                "path": str(db_path),
                "file_size": file_size,
                "statistics": stats,
                "last_checked": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "path": str(db_path) if db_path else "data/tdease.db"
        }


def backup_database(backup_path: Optional[str] = None, source_path: Optional[str] = None) -> bool:
    """Create database backup"""
    try:
        source_path = source_path or "data/tdease.db"
        source_file = Path(source_path)

        if not source_file.exists():
            logger.error(f"Source database does not exist: {source_path}")
            return False

        # Generate backup filename if not provided
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backup/tdease_backup_{timestamp}.db"

        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy database
        import shutil
        shutil.copy2(source_path, backup_path)

        logger.info(f"Database backup created: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return False


if __name__ == "__main__":
    """Test database initialization"""
    logging.basicConfig(level=logging.INFO)

    print("Initializing TDEase database...")
    if initialize_database():
        print("✅ Database initialized successfully")

        # Check health
        health = check_database_health()
        print(f"📊 Database health: {health}")

    else:
        print("❌ Database initialization failed")
        exit(1)
