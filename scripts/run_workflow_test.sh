#!/bin/bash
# 运行 ABC 工作流执行测试
set -e
cd "$(dirname "$0")/.."
echo "=== Initializing DB (if needed) ==="
uv run python -c "from app.database.init_db import initialize_database; initialize_database()"
echo ""
echo "=== Running Workflow ABC Test ==="
uv run python tests/test_workflow_execution.py
