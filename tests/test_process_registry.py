"""
Unit tests for ProcessRegistry

Tests process registration, cancellation, and concurrent access.
"""
import pytest
import subprocess
import time
import threading
from app.core.executor.process_registry import process_registry, ProcessRegistry


class TestProcessRegistry:
    """Test suite for ProcessRegistry"""

    def setup_method(self):
        """Clear registry before each test"""
        process_registry.clear()

    def teardown_method(self):
        """Clear registry after each test"""
        process_registry.clear()

    def test_register_and_unregister(self):
        """Test basic register and unregister operations"""
        # Create a simple sleep process
        proc = subprocess.Popen(["sleep", "10"])
        task_id = "test-exec:node-1"

        # Register process
        process_registry.register(task_id, proc)
        assert process_registry.get(task_id) == proc
        assert task_id in process_registry.list_active()

        # Unregister process
        process_registry.unregister(task_id)
        assert process_registry.get(task_id) is None
        assert task_id not in process_registry.list_active()

        # Clean up
        proc.kill()
        proc.wait()

    def test_unregister_nonexistent_key(self):
        """Test unregistering a non-existent task_id should not raise exception"""
        # Should not raise exception
        process_registry.unregister("non-existent-task")
        process_registry.unregister("another-non-existent")

    def test_double_unregister(self):
        """Test double unregistering should not raise exception"""
        proc = subprocess.Popen(["sleep", "10"])
        task_id = "test-exec:node-2"

        process_registry.register(task_id, proc)
        process_registry.unregister(task_id)
        # Second unregister should succeed silently
        process_registry.unregister(task_id)

        # Clean up
        proc.kill()
        proc.wait()

    def test_cancel_with_sigterm(self):
        """Test cancelling a process with SIGTERM"""
        # Create a long-running process
        proc = subprocess.Popen(["sleep", "100"])
        task_id = "test-exec:node-3"

        process_registry.register(task_id, proc)

        # Cancel the process
        result = process_registry.cancel(task_id, timeout=1)
        assert result is True

        # Process should be terminated
        proc.wait(timeout=2)
        assert proc.poll() is not None

    def test_cancel_nonexistent_task(self):
        """Test cancelling a non-existent task returns False"""
        result = process_registry.cancel("non-existent-task")
        assert result is False

    def test_cancel_already_exited_process(self):
        """Test cancelling an already exited process returns True"""
        # Create a short-lived process
        proc = subprocess.Popen(["echo", "done"])
        proc.wait()  # Wait for it to complete
        task_id = "test-exec:node-4"

        process_registry.register(task_id, proc)

        # Cancel should return True even though process is already exited
        result = process_registry.cancel(task_id)
        assert result is True

    def test_list_active_excludes_dead_processes(self):
        """Test list_active only returns running processes"""
        # Create a short-lived process
        proc1 = subprocess.Popen(["echo", "done"])
        task_id_1 = "test-exec:node-5"
        process_registry.register(task_id_1, proc1)
        proc1.wait()

        # Create a long-running process
        proc2 = subprocess.Popen(["sleep", "10"])
        task_id_2 = "test-exec:node-6"
        process_registry.register(task_id_2, proc2)

        # Only the running process should be in the list
        active_tasks = process_registry.list_active()
        assert task_id_1 not in active_tasks  # Dead process
        assert task_id_2 in active_tasks  # Running process

        # Clean up
        proc2.kill()
        proc2.wait()

    def test_concurrent_access(self):
        """Test thread-safe concurrent access"""
        results = {"registered": 0, "unregistered": 0}
        errors = []

        def register_worker(task_id: str):
            try:
                proc = subprocess.Popen(["sleep", "5"])
                process_registry.register(task_id, proc)
                results["registered"] += 1
                # Immediately unregister
                process_registry.unregister(task_id)
                results["unregistered"] += 1
                # Clean up
                proc.kill()
                proc.wait()
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=register_worker, args=(f"test-exec:node-{i}",))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert results["registered"] == 10
        assert results["unregistered"] == 10


class TestProcessRegistrySingleton:
    """Test ProcessRegistry singleton behavior"""

    def test_singleton_instance(self):
        """Test that ProcessRegistry returns the same instance"""
        registry1 = ProcessRegistry()
        registry2 = ProcessRegistry()
        assert registry1 is registry2

    def test_global_instance(self):
        """Test global process_registry instance"""
        from app.core.executor.process_registry import process_registry as global_registry
        assert isinstance(global_registry, ProcessRegistry)
        assert global_registry is ProcessRegistry()
