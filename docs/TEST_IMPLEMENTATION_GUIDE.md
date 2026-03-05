# Test Implementation Guide - Interactive Visualization Architecture

**Purpose**: Step-by-step guide for implementing comprehensive test coverage
**Target**: 80%+ coverage across backend and frontend
**Timeline**: 4 weeks

---

## Table of Contents

1. [Setup and Configuration](#1-setup-and-configuration)
2. [Phase 1: Backend Unit Tests](#2-phase-1-backend-unit-tests)
3. [Phase 2: Backend Integration Tests](#3-phase-2-backend-integration-tests)
4. [Phase 3: Frontend Unit Tests](#4-phase-3-frontend-unit-tests)
5. [Phase 4: E2E Tests](#5-phase-4-e2e-tests)
6. [Running Tests](#6-running-tests)
7. [CI/CD Integration](#7-cicd-integration)

---

## 1. Setup and Configuration

### 1.1 Backend Setup

#### Install Dependencies

```bash
cd D:\Projects\TDEase-Backend
uv pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
```

#### Create Test Configuration

**File**: `pytest.ini` (already exists, verify content)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --asyncio-mode=auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    requires_docker: Tests that require Docker
    requires_network: Tests that require network access
```

#### Create Coverage Configuration

**File**: `.coveragerc`
```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*
    */.venv/*

[report]
precision = 2
show_missing = True
skip_covered = False
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

#### Create Test Directory Structure

```bash
mkdir -p tests/unit/services
mkdir -p tests/unit/api
mkdir -p tests/unit/schemas
mkdir -p tests/integration
mkdir -p tests/e2e
mkdir -p tests/fixtures
```

### 1.2 Frontend Setup

#### Install Dependencies

```bash
cd TDEase-FrontEnd
pnpm add -D vitest @vue/test-utils @playwright/test jsdom @vitest/ui
```

#### Create Vitest Configuration

**File**: `TDEase-FrontEnd/vitest.config.ts`
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.ts',
      ],
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80,
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
```

#### Create Test Setup File

**File**: `TDEase-FrontEnd/src/test/setup.ts`
```typescript
import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Global mocks
config.global.stubs = {
  transition: false,
  'transition-group': false,
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})
```

---

## 2. Phase 1: Backend Unit Tests

### 2.1 Test Fixtures

**File**: `tests/fixtures/database.py`
```python
"""
Test fixtures for database and common test data
"""
import sqlite3
import tempfile
from pathlib import Path
import pytest
import json


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    db_path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create tables
    conn.execute("""
        CREATE TABLE executions (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            workflow_snapshot TEXT,
            workspace_path TEXT,
            sample_id TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE samples (
            id TEXT PRIMARY KEY,
            name TEXT,
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    yield conn

    conn.close()
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_execution(temp_db):
    """Create a sample execution in database"""
    workflow_snapshot = {
        "nodes": [
            {
                "id": "node1",
                "type": "featuremap_viewer",
                "data": {"label": "Test Node"}
            },
            {
                "id": "node2",
                "type": "topfd",
                "data": {"label": "Compute Node"}
            }
        ],
        "edges": []
    }

    temp_db.execute(
        "INSERT INTO executions (id, workflow_id, workflow_snapshot, workspace_path, status) VALUES (?, ?, ?, ?, ?)",
        ("exec1", "workflow1", json.dumps(workflow_snapshot), "/tmp/workspace", "completed")
    )

    temp_db.execute(
        "INSERT INTO samples (id, name, context) VALUES (?, ?, ?)",
        ("sample1", "test_sample", json.dumps({"sample": "test"}))
    )

    temp_db.commit()
    return "exec1"


@pytest.fixture
def sample_workspace(tmp_path):
    """Create sample workspace with output files"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create sample output file
    output_file = workspace / "test_output.tsv"
    output_file.write_text("col1\tcol2\tcol3\nval1\tval2\tval3\nval4\tval5\tval6\n")

    return workspace


@pytest.fixture
def mock_tool_registry(mocker):
    """Mock tool registry with sample tools"""
    mock_tools = {
        "featuremap_viewer": {
            "id": "featuremap_viewer",
            "name": "Feature Map Viewer",
            "executionMode": "interactive",
            "ports": {
                "outputs": [
                    {
                        "id": "output",
                        "pattern": "{sample}.feature",
                        "schema": [
                            {"name": "col1", "type": "number", "description": "Column 1"},
                            {"name": "col2", "type": "string", "description": "Column 2"}
                        ]
                    }
                ]
            },
            "defaultMapping": {
                "x": "col1",
                "y": "col2"
            }
        },
        "topfd": {
            "id": "topfd",
            "name": "TopFD",
            "executionMode": "compute",
            "ports": {
                "outputs": [
                    {
                        "id": "output",
                        "pattern": "{sample}.ms1ft"
                    }
                ]
            }
        }
    }

    mock_registry = mocker.patch('app.services.tool_registry.get_tool_registry')
    mock_instance = mocker.MagicMock()
    mock_instance.get.return_value = mock_tools.get("featuremap_viewer")
    mock_instance.get_tool.return_value = mock_tools.get("featuremap_viewer")
    mock_instance.list_tools.return_value = mock_tools
    mock_registry.return_value = mock_instance

    return mock_instance
```

### 2.2 Cache Service Tests

**File**: `tests/unit/services/test_node_data_cache.py`

```python
"""
Unit tests for NodeDataCache service
"""
import pytest
import time
import threading
from app.services.node_data_cache import NodeDataCache, get_node_data_cache


class TestNodeDataCacheBasics:
    """Test basic cache operations"""

    @pytest.fixture
    def cache(self):
        """Fresh cache instance for each test"""
        return NodeDataCache(max_size=5, default_ttl=1)

    def test_get_cache_miss(self, cache):
        """Test get returns None for non-existent key"""
        result = cache.get("exec1", "node1")
        assert result is None

    def test_set_and_get(self, cache):
        """Test set and get basic operation"""
        data = {"key": "value", "numbers": [1, 2, 3]}
        cache.set("exec1", "node1", data)
        result = cache.get("exec1", "node1")
        assert result == data

    def test_get_with_port_id(self, cache):
        """Test cache key includes port_id"""
        data1 = {"port": "output1", "values": [1, 2]}
        data2 = {"port": "output2", "values": [3, 4]}

        cache.set("exec1", "node1", data1, port_id="output1")
        cache.set("exec1", "node1", data2, port_id="output2")

        assert cache.get("exec1", "node1", "output1") == data1
        assert cache.get("exec1", "node1", "output2") == data2
        assert cache.get("exec1", "node1") is None  # No port_id

    def test_update_existing_entry(self, cache):
        """Test updating existing cache entry"""
        cache.set("exec1", "node1", {"version": 1})
        cache.set("exec1", "node1", {"version": 2})

        result = cache.get("exec1", "node1")
        assert result == {"version": 2}


class TestNodeDataCacheTTL:
    """Test TTL-based expiration"""

    @pytest.fixture
    def cache(self):
        """Cache with short TTL for testing"""
        return NodeDataCache(max_size=10, default_ttl=0.5)

    def test_ttl_expiration(self, cache):
        """Test cache entries expire after TTL"""
        cache.set("exec1", "node1", {"data": "test"})
        time.sleep(0.6)  # Wait for TTL to expire

        result = cache.get("exec1", "node1")
        assert result is None

    def test_ttl_not_expired(self, cache):
        """Test cache entries don't expire before TTL"""
        cache.set("exec1", "node1", {"data": "test"})
        time.sleep(0.3)  # Less than TTL

        result = cache.get("exec1", "node1")
        assert result == {"data": "test"}

    def test_ttl_on_port_specific_key(self, cache):
        """Test TTL works correctly with port_id"""
        cache.set("exec1", "node1", {"data": "test"}, port_id="output1")
        time.sleep(0.6)

        result = cache.get("exec1", "node1", "output1")
        assert result is None


class TestNodeDataCacheLRU:
    """Test LRU eviction"""

    @pytest.fixture
    def cache(self):
        """Small cache for testing eviction"""
        return NodeDataCache(max_size=3, default_ttl=3600)

    def test_lru_eviction_when_full(self, cache):
        """Test LRU eviction when cache reaches max size"""
        # Fill cache to max_size
        for i in range(3):
            cache.set(f"exec{i}", f"node{i}", {"data": i})

        # Add one more - should evict oldest (exec0)
        cache.set("exec3", "node3", {"data": 3})

        # Oldest entry should be evicted
        assert cache.get("exec0", "node0") is None

        # Other entries should still exist
        assert cache.get("exec1", "node1") == {"data": 1}
        assert cache.get("exec2", "node2") == {"data": 2}
        assert cache.get("exec3", "node3") == {"data": 3}

    def test_lru_updates_on_access(self, cache):
        """Test that accessing an entry updates its position in LRU"""
        # Fill cache
        for i in range(3):
            cache.set(f"exec{i}", f"node{i}", {"data": i})

        # Access first entry (should make it newer)
        cache.get("exec0", "node0")

        # Add new entry - should evict exec1 (now oldest)
        cache.set("exec3", "node3", {"data": 3})

        assert cache.get("exec0", "node0") == {"data": 0}  # Still exists
        assert cache.get("exec1", "node1") is None  # Evicted
        assert cache.get("exec2", "node2") == {"data": 2}


class TestNodeDataCacheInvalidation:
    """Test cache invalidation"""

    @pytest.fixture
    def cache(self):
        """Pre-populated cache"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)
        cache.set("exec1", "node1", {"data": "1"})
        cache.set("exec1", "node2", {"data": "2"})
        cache.set("exec1", "node1", {"data": "3"}, port_id="output1")
        cache.set("exec2", "node1", {"data": "4"})
        return cache

    def test_invalidate_execution(self, cache):
        """Test invalidating all entries for an execution"""
        count = cache.invalidate_execution("exec1")

        assert count == 3  # exec1:node1, exec1:node2, exec1:node1:output1
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec1", "node2") is None
        assert cache.get("exec1", "node1", "output1") is None
        assert cache.get("exec2", "node1") == {"data": "4"}  # Unaffected

    def test_invalidate_node(self, cache):
        """Test invalidating entries for a specific node"""
        count = cache.invalidate_node("exec1", "node1")

        assert count == 2  # exec1:node1, exec1:node1:output1
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec1", "node1", "output1") is None
        assert cache.get("exec1", "node2") == {"data": "2"}  # Unaffected
        assert cache.get("exec2", "node1") == {"data": "4"}  # Unaffected

    def test_invalidate_nonexistent(self, cache):
        """Test invalidating non-existent entries"""
        count = cache.invalidate_execution("nonexistent")
        assert count == 0

        count = cache.invalidate_node("exec1", "nonexistent")
        assert count == 0

    def test_clear(self, cache):
        """Test clearing all cache entries"""
        count = cache.clear()

        assert count == 4
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec2", "node1") is None


class TestNodeDataCacheConcurrency:
    """Test thread-safe operations"""

    def test_concurrent_reads(self):
        """Test concurrent reads are thread-safe"""
        cache = NodeDataCache(max_size=100, default_ttl=3600)
        cache.set("exec1", "node1", {"data": "test"})

        results = []
        def read_cache():
            for _ in range(100):
                results.append(cache.get("exec1", "node1"))

        threads = [threading.Thread(target=read_cache) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == {"data": "test"} for r in results)

    def test_concurrent_writes(self):
        """Test concurrent writes are thread-safe"""
        cache = NodeDataCache(max_size=100, default_ttl=3600)

        def write_cache(prefix):
            for i in range(50):
                cache.set(f"{prefix}_exec{i}", f"node{i}", {"data": i})

        threads = [threading.Thread(target=write_cache, args=(f"t{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify cache is consistent
        stats = cache.get_stats()
        assert stats["size"] == 250  # 5 threads * 50 entries


class TestNodeDataCacheStats:
    """Test cache statistics"""

    def test_get_stats(self):
        """Test getting cache statistics"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)
        cache.set("exec1", "node1", {"data": "1"})
        cache.set("exec2", "node2", {"data": "2"})

        stats = cache.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["ttl"] == 3600
        assert "exec1:node1" in stats["keys"]
        assert "exec2:node2" in stats["keys"]


class TestNodeDataCacheEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_cache_key_generation(self):
        """Test cache key generation patterns"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)

        cache.set("exec_1", "node_1", {"data": "1"})
        cache.set("exec_1", "node_1", {"data": "2"}, port_id="port_1")

        stats = cache.get_stats()
        assert "exec_1:node_1" in stats["keys"]
        assert "exec_1:node_1:port_1" in stats["keys"]

    def test_empty_cache_operations(self):
        """Test operations on empty cache"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)

        assert cache.get("exec1", "node1") is None
        assert cache.invalidate_execution("exec1") == 0
        assert cache.invalidate_node("exec1", "node1") == 0
        assert cache.clear() == 0

    def test_large_data_serialization(self):
        """Test caching large data structures"""
        cache = NodeDataCache(max_size=10, default_ttl=3600)

        large_data = {"rows": [{"id": i, "data": "x" * 100} for i in range(1000)]}
        cache.set("exec1", "node1", large_data)

        result = cache.get("exec1", "node1")
        assert result == large_data
        assert len(result["rows"]) == 1000


class TestGlobalCacheInstance:
    """Test global cache instance"""

    def test_get_node_data_cache_singleton(self):
        """Test that get_node_data_cache returns singleton"""
        cache1 = get_node_data_cache()
        cache2 = get_node_data_cache()

        assert cache1 is cache2

    def test_global_cache_persistence(self):
        """Test that global cache persists across calls"""
        cache = get_node_data_cache()
        cache.clear()  # Start fresh

        cache.set("exec1", "node1", {"data": "test"})

        cache2 = get_node_data_cache()
        result = cache2.get("exec1", "node1")

        assert result == {"data": "test"}
```

### 2.3 Data Service Tests

**File**: `tests/unit/services/test_node_data_service.py`

```python
"""
Unit tests for NodeDataService
"""
import pytest
from pathlib import Path
from app.services.node_data_service import parse_tabular_file, TABULAR_EXTENSIONS


class TestParseTabularFile:
    """Test suite for parse_tabular_file"""

    def test_parse_tsv_file(self, tmp_path):
        """Test parsing TSV file"""
        file_path = tmp_path / "test.tsv"
        content = "col1\tcol2\tcol3\nval1\tval2\tval3\nval4\tval5\tval6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert len(result["rows"]) == 2
        assert result["total_rows"] == 2
        assert result["rows"][0] == {"col1": "val1", "col2": "val2", "col3": "val3"}
        assert result["rows"][1] == {"col1": "val4", "col2": "val5", "col3": "val6"}

    def test_parse_csv_file(self, tmp_path):
        """Test parsing CSV file"""
        file_path = tmp_path / "test.csv"
        content = "col1,col2,col3\nval1,val2,val3\nval4,val5,val6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert len(result["rows"]) == 2

    def test_parse_with_max_rows(self, tmp_path):
        """Test parsing with max_rows limit"""
        file_path = tmp_path / "test.tsv"
        content = "col1\tcol2\n" + "\n".join(f"val{i}\tval{i}" for i in range(100))
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path, max_rows=10)

        assert len(result["rows"]) == 10  # Only 10 rows loaded
        assert result["total_rows"] == 100  # But total count is correct

    def test_parse_nonexistent_file(self, tmp_path):
        """Test error when file doesn't exist"""
        with pytest.raises(FileNotFoundError, match="File not found"):
            parse_tabular_file(tmp_path / "nonexistent.tsv")

    def test_parse_empty_file(self, tmp_path):
        """Test parsing empty file"""
        file_path = tmp_path / "empty.tsv"
        file_path.write_text("", encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == []
        assert result["rows"] == []
        assert result["total_rows"] == 0

    def test_parse_file_with_only_header(self, tmp_path):
        """Test parsing file with only header row"""
        file_path = tmp_path / "header_only.tsv"
        file_path.write_text("col1\tcol2\tcol3\n", encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert result["rows"] == []
        assert result["total_rows"] == 0

    def test_parse_malformed_rows(self, tmp_path):
        """Test handling rows with mismatched column count"""
        file_path = tmp_path / "malformed.tsv"
        content = "col1\tcol2\tcol3\nval1\tval2\nval4\tval5\tval6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        # Malformed row should use index-based keys
        assert len(result["rows"]) == 2
        assert result["rows"][0] == {"col_0": "val1", "col_1": "val2"}
        assert result["rows"][1] == {"col1": "val4", "col2": "val5", "col3": "val6"}

    def test_parse_with_unicode_characters(self, tmp_path):
        """Test parsing file with Unicode characters"""
        file_path = tmp_path / "unicode.tsv"
        content = "col1\tcol2\n测试\t数据\nemoji\t😀\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["rows"][0] == {"col1": "测试", "col2": "数据"}
        assert result["rows"][1] == {"col1": "emoji", "col2": "😀"}

    def test_parse_large_file(self, tmp_path):
        """Test parsing large file (>10k rows)"""
        file_path = tmp_path / "large.tsv"
        lines = ["col1\tcol2\n"] + [f"val{i}\tval{i}\n" for i in range(15000)]
        file_path.write_text("".join(lines), encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert result["total_rows"] == 15000
        assert len(result["rows"]) == 15000

    def test_parse_with_trailing_newline(self, tmp_path):
        """Test parsing file with trailing newline"""
        file_path = tmp_path / "trailing.tsv"
        content = "col1\tcol2\nval1\tval2\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)

        assert len(result["rows"]) == 1
        assert result["rows"][0] == {"col1": "val1", "col2": "val2"}

    @pytest.mark.parametrize("extension,expected_delimiter", [
        (".tsv", "\t"),
        (".txt", "\t"),
        (".csv", ","),
        (".ms1ft", "\t"),
        (".feature", "\t"),
    ])
    def test_delimiter_detection(self, tmp_path, extension, expected_delimiter):
        """Test correct delimiter detection for different file types"""
        file_path = tmp_path / f"test{extension}"
        if expected_delimiter == "\t":
            content = "col1\tcol2\nval1\tval2\n"
        else:
            content = "col1,col2\nval1,val2\n"

        file_path.write_text(content, encoding='utf-8')
        result = parse_tabular_file(file_path)

        assert result["columns"] == ["col1", "col2"]
        assert len(result["rows"]) == 1
```

---

## 3. Phase 2: Backend Integration Tests

### 3.1 API Endpoint Tests

**File**: `tests/integration/test_nodes_api.py`

```python
"""
Integration tests for Nodes API endpoints
"""
import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_database
from app.services.node_data_cache import get_node_data_cache


@pytest.fixture
def client(temp_db, sample_workspace):
    """Test client with mocked database"""
    def override_get_database():
        return temp_db

    app.dependency_overrides[get_database] = override_get_database
    yield TestClient(app)
    app.dependency_overrides.clear()

    # Clear cache after each test
    get_node_data_cache().clear()


@pytest.fixture
def sample_execution(temp_db, sample_workspace):
    """Create sample execution with workspace"""
    workflow_snapshot = {
        "nodes": [
            {
                "id": "node1",
                "type": "featuremap_viewer",
                "data": {"label": "Test Visualization"}
            }
        ]
    }

    temp_db.execute(
        "INSERT INTO executions (id, workflow_id, workflow_snapshot, workspace_path, status) VALUES (?, ?, ?, ?, ?)",
        ("exec1", "workflow1", json.dumps(workflow_snapshot), str(sample_workspace), "completed")
    )
    temp_db.commit()
    return "exec1"


class TestNodeDataSchemaEndpoint:
    """Test suite for GET /executions/{execution_id}/nodes/{node_id}/data/schema"""

    def test_get_schema_success(self, client, sample_execution):
        """Test successful schema retrieval from tool definition"""
        response = client.get("/executions/exec1/nodes/node1/data/schema")

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec1"
        assert data["node_id"] == "node1"
        assert "schema" in data
        assert isinstance(data["schema"], list)

    def test_get_schema_with_port_id(self, client, sample_execution):
        """Test schema retrieval with specific port_id"""
        response = client.get("/executions/exec1/nodes/node1/data/schema?port_id=output")

        assert response.status_code == 200
        data = response.json()
        assert "port_id" in data

    def test_get_schema_execution_not_found(self, client):
        """Test 404 when execution doesn't exist"""
        response = client.get("/executions/nonexec/nodes/node1/data/schema")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_schema_node_not_found(self, client, sample_execution):
        """Test 404 when node doesn't exist in workflow"""
        response = client.get("/executions/exec1/nodes/nonnode/data/schema")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_schema_cached(self, client, sample_execution):
        """Test that schema is cached on second request"""
        # First request
        response1 = client.get("/executions/exec1/nodes/node1/data/schema")
        assert response1.status_code == 200

        # Second request (should hit cache)
        response2 = client.get("/executions/exec1/nodes/node1/data/schema")
        assert response2.status_code == 200

        # Responses should be identical
        assert response1.json() == response2.json()

    def test_get_schema_cache_invalidation(self, client, sample_execution):
        """Test that cache is invalidated on execution update"""
        # First request - cache schema
        response1 = client.get("/executions/exec1/nodes/node1/data/schema")
        assert response1.status_code == 200

        # Invalidate cache
        from app.services.node_data_cache import get_node_data_cache
        cache = get_node_data_cache()
        cache.invalidate_execution("exec1")

        # Second request - should fetch fresh data
        response2 = client.get("/executions/exec1/nodes/node1/data/schema")
        assert response2.status_code == 200


class TestNodeDataRowsEndpoint:
    """Test suite for GET /executions/{execution_id}/nodes/{node_id}/data/rows"""

    def test_get_rows_default_pagination(self, client, sample_execution):
        """Test row retrieval with default pagination"""
        response = client.get("/executions/exec1/nodes/node1/data/rows")

        assert response.status_code == 200
        data = response.json()
        assert "rows" in data
        assert "columns" in data
        assert "total_rows" in data
        assert data["offset"] == 0
        assert data["limit"] == 100

    def test_get_rows_custom_pagination(self, client, sample_execution):
        """Test pagination with custom offset and limit"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?offset=1&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 1
        assert data["limit"] == 1
        assert len(data["rows"]) == 1

    def test_get_rows_max_limit(self, client, sample_execution):
        """Test pagination with maximum limit"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?limit=10000")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10000

    def test_get_rows_limit_exceeds_max(self, client, sample_execution):
        """Test that limit exceeding max is handled"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?limit=20000")

        # Should either reject or cap at max
        assert response.status_code in [200, 422]

    def test_get_rows_with_row_ids(self, client, sample_execution):
        """Test row retrieval with specific row IDs"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?row_ids=0,1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["rows"]) <= 2

    def test_get_rows_invalid_row_ids(self, client, sample_execution):
        """Test error with invalid row_ids format"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?row_ids=abc,def")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_get_rows_execution_not_found(self, client):
        """Test 404 when execution doesn't exist"""
        response = client.get("/executions/nonexec/nodes/node1/data/rows")

        assert response.status_code == 404

    def test_get_rows_node_not_found(self, client, sample_execution):
        """Test 404 when node doesn't exist"""
        response = client.get("/executions/exec1/nodes/nonnode/data/rows")

        assert response.status_code == 404
```

---

## 6. Running Tests

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run specific test file
pytest tests/unit/services/test_node_data_cache.py

# Run specific test
pytest tests/unit/services/test_node_data_cache.py::TestNodeDataCacheBasics::test_set_and_get

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x

# Run with debugger
pytest --pdb
```

### Frontend Tests

```bash
# Run all tests
pnpm test

# Run with coverage
pnpm test:coverage

# Run in watch mode
pnpm test:watch

# Run UI mode
pnpm test:ui

# Run specific test file
pnpm test src/components/visualization/InteractiveNode.test.ts

# Run E2E tests
pnpm test:e2e
```

---

## 7. CI/CD Integration

### GitHub Actions Workflow

**File**: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --cov=app --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: backend

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: backend-coverage
          path: htmlcov/

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install

      - name: Run tests
        run: pnpm test:coverage

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: frontend

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: frontend-coverage
          path: coverage/

  e2e-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup pnpm
        uses: pnpm/action-setup@v2

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'pnpm'

      - name: Install dependencies
        run: pnpm install

      - name: Install Playwright browsers
        run: pnpm exec playwright install --with-deps

      - name: Run E2E tests
        run: pnpm test:e2e

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

**Next Steps**:

1. Review and approve this implementation guide
2. Set up test infrastructure (fixtures, config)
3. Implement Phase 1 tests (backend unit)
4. Verify coverage reaches 60%+
5. Proceed to Phase 2-4

**Questions?** Refer to `TEST_COVERAGE_ANALYSIS.md` for detailed gap analysis.
