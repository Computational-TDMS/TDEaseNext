"""
Unit tests for LocalExecutor.cancel() method

Tests workflow cancellation through executor.
"""
import pytest
import asyncio
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
from app.core.executor.local import LocalExecutor
from app.core.executor.base import TaskSpec


def _make_workspace_dir() -> Path:
    base = Path("data") / "test_tmp_dirs"
    base.mkdir(parents=True, exist_ok=True)
    path = (base / f"local_executor_{uuid4().hex}").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


class TestLocalExecutorCancel:
    """Test suite for LocalExecutor.cancel()"""

    @pytest.fixture
    def executor(self):
        """Create LocalExecutor instance"""
        tools_registry = {
            "test-tool": {
                "id": "test-tool",
                "executionMode": "native",
                "command": {"executable": sys.executable},
                "ports": {"inputs": [], "outputs": []},
                "parameters": {},
                "output": {"flagSupported": False},
            }
        }
        return LocalExecutor(tools_registry)

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, executor):
        """Test cancelling a non-existent task returns False"""
        result = await executor.cancel("non-existent-task")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_task_with_process_registry(self, executor):
        """Test cancelling a task through process registry"""
        from app.core.executor.process_registry import process_registry

        # Create a long-running process manually
        proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
        task_id = "test-exec:node-1"
        process_registry.register(task_id, proc)

        # Cancel through executor
        result = await executor.cancel(task_id)
        assert result is True

        # Verify process was terminated
        proc.wait(timeout=2)
        assert proc.poll() is not None

    @pytest.mark.asyncio
    async def test_execute_with_task_id(self, executor):
        """Test that execute passes task_id to shell runner"""
        from unittest.mock import patch

        # Mock the run_shell function to capture task_id
        captured_task_ids = []

        def mock_run_command(args, workdir, conda_env=None, log_callback=None, task_id=""):
            captured_task_ids.append(task_id)
            # Don't actually run anything

        # Patch run_command in the local executor module (imported symbol)
        with patch('app.core.executor.local.run_command', side_effect=mock_run_command):
            workspace = _make_workspace_dir()
            spec = TaskSpec(
                node_id="test-node",
                tool_id="test-tool",
                params={},
                input_paths=[],
                output_paths=[],
                workspace_path=workspace,
                task_id="test-exec:test-node"
            )

            await executor.execute(spec)

            # Verify task_id was passed
            assert len(captured_task_ids) > 0
            assert "test-exec:test-node" in captured_task_ids


class TestLocalExecutorIntegration:
    """Integration tests for LocalExecutor with ProcessRegistry"""

    @pytest.mark.asyncio
    async def test_full_cancel_workflow(self):
        """Test full workflow: register, execute, cancel"""
        import subprocess
        from app.core.executor.process_registry import process_registry

        # Create executor with a simple tool
        tools_registry = {
            "sleep-tool": {
                "id": "sleep-tool",
                "executionMode": "native",
                "command": {"executable": sys.executable},
                "ports": {"inputs": [], "outputs": []},
                "parameters": {"code": {"type": "value", "flag": "-c"}},
                "output": {"flagSupported": False},
            }
        }
        executor = LocalExecutor(tools_registry)

        # Execute a simple sleep command
        workspace = _make_workspace_dir()
        spec = TaskSpec(
            node_id="sleep-node",
            tool_id="sleep-tool",
            params={"code": "import time; time.sleep(10)"},
            input_paths=[],
            output_paths=[],
            workspace_path=workspace,
            task_id="test-exec:sleep-node"
        )

        # Start execution in background
        async def run_and_cancel():
            # Start execution
            task = asyncio.create_task(executor.execute(spec))
            # Wait a bit for process to start
            await asyncio.sleep(0.5)
            # Cancel
            result = await executor.cancel("test-exec:sleep-node")
            assert result is True
            # Try to wait for task (should be cancelled)
            try:
                await asyncio.wait_for(task, timeout=2)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                # Process may have been cancelled, which is expected
                pass

        await run_and_cancel()

        # Verify process was removed from registry
        assert "test-exec:sleep-node" not in process_registry.list_active()
