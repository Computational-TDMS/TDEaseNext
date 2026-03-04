#!/usr/bin/env python3
"""
Quick verification script for workflow cancellation functionality.

Tests the basic workflow cancellation implementation without requiring pytest.
"""
import sys
import os
import subprocess
import asyncio
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_process_registry():
    """Test ProcessRegistry basic functionality"""
    print("[TEST] Testing ProcessRegistry...")
    from app.core.executor.process_registry import process_registry

    # Clear registry
    process_registry.clear()

    # Test 1: Register and unregister
    print("  [1/5] Testing register/unregister...")
    proc = subprocess.Popen(["sleep", "10"])
    task_id = "test-exec:node-1"
    process_registry.register(task_id, proc)
    assert process_registry.get(task_id) == proc
    assert task_id in process_registry.list_active()
    process_registry.unregister(task_id)
    assert process_registry.get(task_id) is None
    proc.kill()
    proc.wait()
    print("  [PASS]")

    # Test 2: Cancel process
    print("  [2/5] Testing cancel...")
    proc = subprocess.Popen(["sleep", "100"])
    task_id = "test-exec:node-2"
    process_registry.register(task_id, proc)
    result = process_registry.cancel(task_id, timeout=1)
    assert result is True
    proc.wait(timeout=2)
    assert proc.poll() is not None
    print("  [PASS]")

    # Test 3: Non-existent task
    print("  [3/5] Testing non-existent task...")
    result = process_registry.cancel("non-existent")
    assert result is False
    print("  [PASS]")

    # Test 4: Double unregister
    print("  [4/5] Testing double unregister...")
    proc = subprocess.Popen(["sleep", "10"])
    task_id = "test-exec:node-3"
    process_registry.register(task_id, proc)
    process_registry.unregister(task_id)
    process_registry.unregister(task_id)  # Should not raise
    proc.kill()
    proc.wait()
    print("  [PASS]")

    # Test 5: List active
    print("  [5/5] Testing list_active...")
    proc = subprocess.Popen(["sleep", "10"])
    task_id = "test-exec:node-4"
    process_registry.register(task_id, proc)
    active = process_registry.list_active()
    assert task_id in active
    process_registry.unregister(task_id)
    proc.kill()
    proc.wait()
    print("  [PASS]")

    # Clean up
    process_registry.clear()
    print("[TEST] ProcessRegistry tests PASSED\n")


async def test_local_executor_cancel():
    """Test LocalExecutor.cancel() method"""
    print("[TEST] Testing LocalExecutor.cancel()...")
    from app.core.executor.local import LocalExecutor
    from app.core.executor.process_registry import process_registry
    import tempfile

    executor = LocalExecutor({})

    # Test cancel non-existent task
    print("  [1/1] Testing cancel non-existent task...")
    result = await executor.cancel("non-existent-task")
    assert result is False
    print("  [PASS]")

    print("[TEST] LocalExecutor.cancel() tests PASSED\n")


def test_execution_manager():
    """Test ExecutionManager.stop() method"""
    print("[TEST] Testing ExecutionManager.stop()...")
    from app.services.runner import ExecutionManager

    manager = ExecutionManager()

    # Create execution
    print("  [1/2] Creating execution...")
    execution_id = "test-exec-123"
    workspace = "/tmp/test-workspace"
    ex = manager.create(execution_id, workspace, "test-workflow")
    assert ex.id == execution_id
    assert ex.status == "pending"
    print("  [PASS]")

    # Test stop
    print("  [2/2] Testing stop...")
    # Simulate running nodes
    ex.add_running_node("node-1")
    ex.add_running_node("node-2")

    # Stop execution
    await_manager_stop(manager, execution_id)

    assert ex.status == "cancelled"
    assert len(ex.get_running_nodes()) == 0  # Should be cleared
    print("  [PASS]")

    print("[TEST] ExecutionManager.stop() tests PASSED\n")


def await_manager_stop(manager, execution_id):
    """Helper to async stop"""
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.stop(execution_id))


def test_task_spec():
    """Test TaskSpec has task_id field"""
    print("[TEST] Testing TaskSpec...")
    from app.core.executor.base import TaskSpec

    spec = TaskSpec(
        node_id="test-node",
        tool_id="test-tool",
        params={},
        input_paths=[],
        output_paths=[],
        workspace_path="/tmp",
        task_id="test-exec:test-node"
    )

    assert spec.task_id == "test-exec:test-node"
    print("  [PASS]")
    print("[TEST] TaskSpec tests PASSED\n")


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("WORKFLOW CANCELLATION VERIFICATION")
    print("=" * 60)
    print()

    try:
        test_process_registry()
        asyncio.run(test_local_executor_cancel())
        test_execution_manager()
        test_task_spec()

        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Summary:")
        print("  [OK] ProcessRegistry: register, unregister, cancel")
        print("  [OK] LocalExecutor: cancel() method")
        print("  [OK] ExecutionManager: stop() method")
        print("  [OK] TaskSpec: task_id field")
        print()
        print("Next steps:")
        print("  1. Run integration tests (start workflow, cancel it)")
        print("  2. Manual test via UI")
        print("  3. Monitor for process leaks")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
