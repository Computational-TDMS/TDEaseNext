# 运行 ABC 工作流执行测试
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot\..
try {
    Write-Host "=== Initializing DB (if needed) ==="
    uv run python -c "from app.database.init_db import initialize_database; initialize_database()"
    Write-Host ""
    Write-Host "=== Running Workflow ABC Test ==="
    uv run python tests/test_workflow_execution.py
} finally {
    Pop-Location
}
