"""
Unit tests for LocalExecutor.cancel() method

Tests workflow cancellation through executor.
"""
import pytest
import asyncio
from pathlib import Path
from app.core.executor.local import LocalExecutor
from app.core.executor.base import TaskSpec


class TestLocalExecutorCancel:
    """Test suite for LocalExecutor.cancel()"""

    @pytest.fixture
    def executor(self):
        """Create LocalExecutor instance"""
        tools_registry = {}
        return LocalExecutor(tools_registry)

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, executor):
        """Test cancelling a non-existent task returns False"""
        result = await executor.cancel("non-existent-task")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_task_with_process_registry(self, executor):
        """Test cancelling a task through process registry"""
        import subprocess
        from app.core.executor.process_registry import process_registry

        # Create a long-running process manually
        proc = subprocess.Popen(["sleep", "10"])
        task_id = "test-exec:node-1"
        process_registry.register(task_id, proc)

        # Cancel through executor
        result = await executor.cancel(task_id)
        assert result is True

        # Verify process was terminated
        proc.wait(timeout=2)
        assert proc.poll() is not None

    @pytest.mark.asyncio
    async def test_execute_with_task_id(self, executor, tmp_path):
        """Test that execute passes task_id to shell runner"""
        import subprocess
        from unittest.mock import patch, MagicMock

        # Mock the run_shell function to capture task_id
        captured_task_ids = []

        original_run_shell = None
        def mock_run_shell(cmd, workdir, conda_env=None, log_callback=None, task_id=""):
            captured_task_ids.append(task_id)
            # Don't actually run anything

        # Patch run_shell in the shell_runner module
        with patch('app.core.executor.shell_runner.run_shell', side_effect=mock_run_shell):
            spec = TaskSpec(
                node_id="test-node",
                tool_id="test-tool",
                params={},
                input_paths=[],
                output_paths=[],
                workspace_path=tmp_path,
                task_id="test-exec:test-node"
            )

            await executor.execute(spec)

            # Verify task_id was passed
            assert len(captured_task_ids) > 0
            assert "test-exec:test-node" in captured_task_ids


class TestLocalExecutorIntegration:
    """Integration tests for LocalExecutor with ProcessRegistry"""

    @pytest.mark.asyncio
    async def test_full_cancel_workflow(self, tmp_path):
        """Test full workflow: register, execute, cancel"""
        import subprocess
        from app.core.executor.process_registry import process_registry

        # Create executor with a simple tool
        tools_registry = {
            "sleep-tool": {
                "command": {"executable": "sleep"},
                "ports": {"inputs": [], "outputs": []},
            }
        }
        executor = LocalExecutor(tools_registry)

        # Execute a simple sleep command
        spec = TaskSpec(
            node_id="sleep-node",
            tool_id="sleep-tool",
            params={},
            input_paths=[],
            output_paths=[],
            workspace_path=tmp_path,
            cmd="sleep 10",  # Use pre-built command for simplicity
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
