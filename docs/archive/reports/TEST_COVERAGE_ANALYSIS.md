# Test Coverage Analysis - Interactive Visualization Architecture

**Date**: 2026-03-05
**Status**: Critical Gap Identified
**Current Coverage**: ~5% (estimated)

## Executive Summary

The interactive-vis-architecture implementation has **severely inadequate test coverage**. Only 4 basic integration tests exist, covering ~5% of the codebase. Critical paths including API endpoints, caching logic, error handling, and frontend components are **completely untested**.

**Risk Level**: HIGH - Production deployment not recommended without comprehensive testing.

---

## 1. Current Test Coverage Assessment

### Existing Tests (4 tests)

**File**: `tests/test_interactive_execution_simple.py`

| Test | Coverage | Quality |
|------|----------|---------|
| `test_tool_registry_loads_interactive_tool` | Schema validation only | Basic |
| `test_tool_registry_loads_compute_tool` | Schema validation only | Basic |
| `test_tool_definition_schema_validation` | Pydantic model creation | Basic |
| `test_output_column_schema_field` | Pydantic model field | Basic |

**Coverage Estimate**:
- Backend: ~8% (only schema validation)
- Frontend: 0% (no tests)
- API Endpoints: 0%
- Error Paths: 0%
- Edge Cases: 0%

### Code Coverage by Module

| Module | Lines of Code | Tested Lines | Coverage |
|--------|---------------|--------------|----------|
| `app/schemas/tool.py` | 127 | 40 | 31% |
| `app/services/tool_registry.py` | 238 | 20 | 8% |
| `app/services/node_data_cache.py` | 181 | 0 | 0% |
| `app/services/node_data_service.py` | 279 | 0 | 0% |
| `app/api/nodes.py` | 337 | 0 | 0% |
| **Backend Total** | **1,162** | **60** | **5%** |
| Frontend Components | ~2,500+ | 0 | 0% |
| **Grand Total** | **~3,700** | **60** | **1.6%** |

---

## 2. Critical Test Gaps

### 2.1 Backend - API Endpoints (Priority: CRITICAL)

**File**: `app/api/nodes.py` (337 lines, 0% coverage)

#### Missing Tests:

1. **GET `/executions/{execution_id}/nodes/{node_id}/data/schema`** (lines 23-201)
   - [ ] Successful schema retrieval with cached result
   - [ ] Schema retrieval without cache (first request)
   - [ ] Schema inference from file when tool definition missing
   - [ ] Error: Execution not found (404)
   - [ ] Error: Node not found in workflow (404)
   - [ ] Error: Output file not available (400)
   - [ ] Error: Output file not parseable (400)
   - [ ] Error: Database connection failure (500)
   - [ ] Error: Invalid JSON in workflow_snapshot (500)
   - [ ] Edge: Empty schema array
   - [ ] Edge: Multiple output ports with port_id filter
   - [ ] Performance: Cache hit vs miss timing

2. **GET `/executions/{execution_id}/nodes/{node_id}/data/rows`** (lines 204-336)
   - [ ] Successful row retrieval with pagination
   - [ ] Row retrieval with row_ids filter
   - [ ] Pagination: offset=0, limit=100 (default)
   - [ ] Pagination: offset=1000, limit=10000 (max)
   - [ ] Error: Invalid row_ids format (400)
   - [ ] Error: Output file does not exist (404)
   - [ ] Error: Output file not parseable (400)
   - [ ] Error: No outputs found for node (404)
   - [ ] Edge: Empty result set (0 rows)
   - [ ] Edge: Single row result
   - [ ] Edge: Large dataset (>10k rows)
   - [ ] Security: SQL injection prevention
   - [ ] Performance: Pagination with large offset

### 2.2 Backend - Cache Service (Priority: HIGH)

**File**: `app/services/node_data_cache.py` (181 lines, 0% coverage)

#### Missing Tests:

1. **Cache Operations**
   - [ ] `get()`: Cache hit (fresh entry)
   - [ ] `get()`: Cache miss (key not found)
   - [ ] `get()`: Cache expired (TTL exceeded)
   - [ ] `set()`: New entry
   - [ ] `set()`: Update existing entry
   - [ ] `set()`: LRU eviction when cache full
   - [ ] `invalidate_execution()`: Remove all execution entries
   - [ ] `invalidate_node()`: Remove specific node entries
   - [ ] `clear()`: Remove all entries
   - [ ] `get_stats()`: Return accurate statistics

2. **Concurrency**
   - [ ] Thread-safe `get()` with concurrent readers
   - [ ] Thread-safe `set()` with concurrent writers
   - [ ] Thread-safe `invalidate_execution()` during `get()`
   - [ ] Race condition: Eviction during read

3. **Edge Cases**
   - [ ] Cache key generation with/without port_id
   - [ ] TTL boundary conditions (exactly at TTL)
   - [ ] Max size boundary (exactly at max_size)
   - [ ] Empty cache operations
   - [ ] Large data serialization

### 2.3 Backend - Node Data Service (Priority: HIGH)

**File**: `app/services/node_data_service.py` (279 lines, 0% coverage)

#### Missing Tests:

1. **File Parsing**
   - [ ] `parse_tabular_file()`: TSV file parsing
   - [ ] `parse_tabular_file()`: CSV file parsing
   - [ ] `parse_tabular_file()`: File not found error
   - [ ] `parse_tabular_file()`: max_rows parameter
   - [ ] `parse_tabular_file()`: Malformed rows (column mismatch)
   - [ ] `parse_tabular_file()`: Empty file
   - [ ] `parse_tabular_file()`: UTF-8 encoding handling
   - [ ] `parse_tabular_file()`: Large file (>10k rows)

2. **Output Resolution**
   - [ ] `resolve_node_outputs()`: Successful resolution
   - [ ] `resolve_node_outputs()`: Execution not found
   - [ ] `resolve_node_outputs()`: Invalid workflow snapshot JSON
   - [ ] `resolve_node_outputs()`: Node not found in workflow
   - [ ] `resolve_node_outputs()`: Tool not found in registry
   - [ ] `resolve_node_outputs()`: With sample_context
   - [ ] `resolve_node_outputs()`: Without sample_context (default)
   - [ ] `resolve_node_outputs()`: include_data=True
   - [ ] `resolve_node_outputs()`: include_data=False
   - [ ] `resolve_node_outputs()`: Non-existent output files
   - [ ] `resolve_node_outputs()`: Multiple output ports

### 2.4 Backend - Tool Registry (Priority: MEDIUM)

**File**: `app/services/tool_registry.py` (238 lines, 8% coverage)

#### Missing Tests:

1. **Registry Operations**
   - [ ] `reload()`: Reload all tool definitions
   - [ ] `reload()`: Handle invalid JSON files
   - [ ] `reload()`: Handle missing required fields
   - [ ] `get()`: Retrieve existing tool
   - [ ] `get()`: Retrieve non-existent tool (None)
   - [ ] `get_definition()`: Retrieve Pydantic definition
   - [ ] `list_tools()`: Return all tools
   - [ ] `list_definitions()`: Return all Pydantic definitions

2. **UI Schema Generation**
   - [ ] `get_ui_schema()`: Interactive tool with params
   - [ ] `get_ui_schema()`: Tool with outputs schema
   - [ ] `get_ui_schema()`: Tool with defaultMapping
   - [ ] `get_ui_schema()`: Non-existent tool (None)
   - [ ] `get_ui_schema()`: Tool with param_mapping

3. **Validation**
   - [ ] `_validate_tool_definition()`: Valid tool
   - [ ] `_validate_tool_definition()`: Invalid tool (schema error)
   - [ ] `_validate_tool_definition()`: Missing validation schema (skip)
   - [ ] `_normalize_tool_data()`: New format with executionMode
   - [ ] `_normalize_tool_data()`: Missing required field (error)
   - [ ] `_normalize_tool_data()`: Legacy format compatibility

### 2.5 Frontend - Components (Priority: HIGH)

**File**: `TDEase-FrontEnd/src/components/visualization/InteractiveNode.vue` (853 lines, 0% coverage)

#### Missing Tests:

1. **Component Lifecycle**
   - [ ] `onMounted()`: Loads data successfully
   - [ ] `onMounted()`: Handles load error
   - [ ] `onMounted()`: Shows pending execution state
   - [ ] `onUnmounted()`: Cleans up subscriptions

2. **State Management**
   - [ ] Loading state display
   - [ ] Error state display with retry
   - [ ] Pending execution state display
   - [ ] Empty state (no input) display
   - [ ] Ready state with data

3. **Configuration**
   - [ ] Toggle edit mode
   - [ ] Column mapping configuration
   - [ ] Color scheme configuration
   - [ ] Heatmap specific configuration
   - [ ] Volcano plot specific configuration
   - [ ] Config change emits event

4. **Data Handling**
   - [ ] Load data from file source
   - [ ] Load data from state source
   - [ ] Handle upstream selection changes
   - [ ] Handle selection changes (emit)
   - [ ] Handle state changes (dispatch)
   - [ ] Handle viewport changes (dispatch)

5. **Edge Cases**
   - [ ] No execution ID (pending execution)
   - [ ] Failed API requests
   - [ ] Malformed data response
   - [ ] Missing tool in registry
   - [ ] Invalid visualization type
   - [ ] Empty columns list
   - [ ] No numeric columns for axis mapping

### 2.6 Frontend - State Bus (Priority: HIGH)

**Estimated Coverage**: 0% (service not reviewed but critical)

#### Missing Tests:

1. **State Bus Operations**
   - [ ] Subscribe to state port
   - [ ] Dispatch state update
   - [ ] Unsubscribe from state port
   - [ ] Multiple subscribers to same port
   - [ ] Subscribe with semantic type filter

2. **State Payload Handling**
   - [ ] Selection state (Set of IDs)
   - [ ] Selection state (SelectionState object)
   - [ ] Viewport state (viewport object)
   - [ ] Sequence state (string)
   - [ ] Annotation state (object)

3. **Edge Cases**
   - [ ] Subscribe to non-existent port
   - [ ] Dispatch without subscribers
   - [ ] Invalid payload format
   - [ ] Concurrent dispatch operations

### 2.7 Frontend - Services (Priority: MEDIUM)

#### Missing Tests:

1. **API Client** (`src/services/api/client.ts`)
   - [ ] GET request with query params
   - [ ] POST request with JSON body
   - [ ] Error handling (4xx, 5xx)
   - [ ] Timeout handling
   - [ ] Retry logic

2. **Visualization Store** (`src/stores/visualization.ts`)
   - [ ] Load node data
   - [ ] Cache node data
   - [ ] Update selection
   - [ ] Get loading state
   - [ ] Clear node data

3. **Workflow Connector** (`src/services/workflow-connector.ts`)
   - [ ] Resolve node input source (file)
   - [ ] Resolve node input source (state)
   - [ ] Resolve node input source (none)
   - [ ] Handle circular dependencies

---

## 3. Test Quality Issues

### 3.1 Existing Test Problems

1. **No Error Path Testing**
   - Only happy paths tested
   - No validation error scenarios
   - No failure recovery tests

2. **No Edge Case Coverage**
   - Empty data not tested
   - Boundary values not tested
   - Null/undefined inputs not tested

3. **No Integration Testing**
   - API endpoints not tested end-to-end
   - Database interactions not tested
   - Cache invalidation not tested

4. **No Performance Testing**
   - Large datasets not tested
   - Concurrent access not tested
   - Cache efficiency not measured

5. **No Security Testing**
   - SQL injection not tested
   - Path traversal not tested
   - XSS not tested (frontend)

### 3.2 Test Anti-Patterns Detected

1. **Testing Implementation Details**
   - Tests check internal field names instead of behavior
   - Tests couple to Pydantic model structure

2. **Insufficient Assertions**
   - Tests only check "not None"
   - No validation of actual data correctness

3. **No Test Isolation**
   - Tests share global tool registry
   - Tests may depend on execution order

---

## 4. Recommended Test Suite

### 4.1 Backend Unit Tests (Priority: CRITICAL)

#### Test File: `tests/unit/test_node_data_cache.py`

```python
"""
Unit tests for NodeDataCache service
"""
import pytest
import time
from app.services.node_data_cache import NodeDataCache

@pytest.fixture
def cache():
    """Fresh cache instance for each test"""
    return NodeDataCache(max_size=5, default_ttl=1)

class TestNodeDataCache:
    """Test suite for NodeDataCache"""

    def test_get_cache_miss(self, cache):
        """Test get returns None for non-existent key"""
        result = cache.get("exec1", "node1")
        assert result is None

    def test_set_and_get(self, cache):
        """Test set and get basic operation"""
        data = {"key": "value"}
        cache.set("exec1", "node1", data)
        result = cache.get("exec1", "node1")
        assert result == data

    def test_get_with_port_id(self, cache):
        """Test cache key includes port_id"""
        data1 = {"port": "output1"}
        data2 = {"port": "output2"}
        cache.set("exec1", "node1", data1, port_id="output1")
        cache.set("exec1", "node1", data2, port_id="output2")

        assert cache.get("exec1", "node1", "output1") == data1
        assert cache.get("exec1", "node1", "output2") == data2

    def test_ttl_expiration(self, cache):
        """Test cache entries expire after TTL"""
        cache.set("exec1", "node1", {"data": "test"})
        time.sleep(1.1)  # Wait for TTL to expire
        result = cache.get("exec1", "node1")
        assert result is None

    def test_lru_eviction(self, cache):
        """Test LRU eviction when cache is full"""
        # Fill cache to max_size
        for i in range(5):
            cache.set(f"exec{i}", f"node{i}", {"data": i})

        # Add one more - should evict oldest
        cache.set("exec5", "node5", {"data": 5})

        # First entry should be evicted
        assert cache.get("exec0", "node0") is None
        assert cache.get("exec5", "node5") == {"data": 5}

    def test_invalidate_execution(self, cache):
        """Test invalidating all entries for an execution"""
        cache.set("exec1", "node1", {"data": "1"})
        cache.set("exec1", "node2", {"data": "2"})
        cache.set("exec2", "node1", {"data": "3"})

        count = cache.invalidate_execution("exec1")
        assert count == 2
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec1", "node2") is None
        assert cache.get("exec2", "node1") == {"data": "3"}

    def test_invalidate_node(self, cache):
        """Test invalidating entries for a specific node"""
        cache.set("exec1", "node1", {"data": "1"}, port_id="output1")
        cache.set("exec1", "node1", {"data": "2"}, port_id="output2")
        cache.set("exec1", "node2", {"data": "3"})

        count = cache.invalidate_node("exec1", "node1")
        assert count == 2
        assert cache.get("exec1", "node1", "output1") is None
        assert cache.get("exec1", "node2") == {"data": "3"}

    def test_clear(self, cache):
        """Test clearing all cache entries"""
        cache.set("exec1", "node1", {"data": "1"})
        cache.set("exec2", "node2", {"data": "2"})

        count = cache.clear()
        assert count == 2
        assert cache.get("exec1", "node1") is None
        assert cache.get("exec2", "node2") is None

    def test_get_stats(self, cache):
        """Test getting cache statistics"""
        cache.set("exec1", "node1", {"data": "1"})
        stats = cache.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 5
        assert stats["ttl"] == 1
        assert "exec1:node1" in stats["keys"]

    @pytest.mark.parametrize("execution_id,node_id,port_id,expected_key", [
        ("exec1", "node1", None, "exec1:node1"),
        ("exec1", "node1", "output1", "exec1:node1:output1"),
        ("exec_2", "node_2", "port_3", "exec_2:node_2:port_3"),
    ])
    def test_cache_key_generation(self, cache, execution_id, node_id, port_id, expected_key):
        """Test cache key generation pattern"""
        cache.set(execution_id, node_id, {"test": "data"}, port_id=port_id)
        stats = cache.get_stats()
        assert expected_key in stats["keys"]
```

#### Test File: `tests/unit/test_node_data_service.py`

```python
"""
Unit tests for NodeDataService
"""
import pytest
from pathlib import Path
from app.services.node_data_service import parse_tabular_file

@pytest.fixture
def sample_tsv(tmp_path):
    """Create a sample TSV file for testing"""
    file_path = tmp_path / "test.tsv"
    content = "col1\tcol2\tcol3\nval1\tval2\tval3\nval4\tval5\tval6\n"
    file_path.write_text(content, encoding='utf-8')
    return file_path

@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing"""
    file_path = tmp_path / "test.csv"
    content = "col1,col2,col3\nval1,val2,val3\nval4,val5,val6\n"
    file_path.write_text(content, encoding='utf-8')
    return file_path

class TestParseTabularFile:
    """Test suite for parse_tabular_file"""

    def test_parse_tsv_file(self, sample_tsv):
        """Test parsing TSV file"""
        result = parse_tabular_file(sample_tsv)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert len(result["rows"]) == 2
        assert result["total_rows"] == 2
        assert result["rows"][0] == {"col1": "val1", "col2": "val2", "col3": "val3"}

    def test_parse_csv_file(self, sample_csv):
        """Test parsing CSV file"""
        result = parse_tabular_file(sample_csv)

        assert result["columns"] == ["col1", "col2", "col3"]
        assert len(result["rows"]) == 2

    def test_parse_with_max_rows(self, sample_tsv):
        """Test parsing with max_rows limit"""
        result = parse_tabular_file(sample_tsv, max_rows=1)

        assert len(result["rows"]) == 1
        assert result["total_rows"] == 2  # Still counts total

    def test_parse_nonexistent_file(self, tmp_path):
        """Test error when file doesn't exist"""
        with pytest.raises(FileNotFoundError):
            parse_tabular_file(tmp_path / "nonexistent.tsv")

    def test_parse_empty_file(self, tmp_path):
        """Test parsing empty file"""
        file_path = tmp_path / "empty.tsv"
        file_path.write_text("", encoding='utf-8')

        result = parse_tabular_file(file_path)
        assert result["columns"] == []
        assert result["rows"] == []

    def test_parse_malformed_rows(self, tmp_path):
        """Test handling rows with mismatched column count"""
        file_path = tmp_path / "malformed.tsv"
        content = "col1\tcol2\tcol3\nval1\tval2\nval4\tval5\tval6\n"
        file_path.write_text(content, encoding='utf-8')

        result = parse_tabular_file(file_path)
        # Malformed row should use index-based keys
        assert len(result["rows"]) == 2
```

#### Test File: `tests/integration/test_nodes_api.py`

```python
"""
Integration tests for Nodes API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_database

@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)

@pytest.fixture
def mock_db(mocker):
    """Mock database connection"""
    # Setup mock database cursor
    mock_cursor = mocker.MagicMock()
    mock_conn = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Override dependency
    app.dependency_overrides[get_database] = lambda: mock_conn
    yield mock_conn
    app.dependency_overrides.clear()

class TestNodeDataSchemaAPI:
    """Test suite for /data/schema endpoint"""

    def test_get_schema_success(self, client, mock_db):
        """Test successful schema retrieval"""
        # Mock database response
        mock_db.fetchone.return_value = ['{"nodes": [{"id": "node1", "type": "test_tool"}]}', "/workspace", None]

        response = client.get("/executions/exec1/nodes/node1/data/schema")

        assert response.status_code == 200
        data = response.json()
        assert "schema" in data

    def test_get_schema_execution_not_found(self, client, mock_db):
        """Test 404 when execution doesn't exist"""
        mock_db.fetchone.return_value = None

        response = client.get("/executions/exec1/nodes/node1/data/schema")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_schema_cached(self, client, mock_db):
        """Test schema caching"""
        mock_db.fetchone.return_value = ['{"nodes": [{"id": "node1", "type": "test_tool"}]}', "/workspace", None]

        # First request
        response1 = client.get("/executions/exec1/nodes/node1/data/schema")
        # Second request (should hit cache)
        response2 = client.get("/executions/exec1/nodes/node1/data/schema")

        assert response1.status_code == 200
        assert response2.status_code == 200

class TestNodeDataRowsAPI:
    """Test suite for /data/rows endpoint"""

    def test_get_rows_default_pagination(self, client, mock_db):
        """Test row retrieval with default pagination"""
        # Setup mocks...
        response = client.get("/executions/exec1/nodes/node1/data/rows")

        assert response.status_code == 200
        data = response.json()
        assert "rows" in data
        assert "offset" in data
        assert "limit" in data

    def test_get_rows_with_offset_limit(self, client, mock_db):
        """Test pagination with custom offset and limit"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?offset=100&limit=50")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 100
        assert data["limit"] == 50

    def test_get_rows_invalid_row_ids(self, client, mock_db):
        """Test error with invalid row_ids format"""
        response = client.get("/executions/exec1/nodes/node1/data/rows?row_ids=abc,def")

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
```

### 4.2 Frontend Unit Tests (Priority: HIGH)

#### Test File: `src/components/visualization/InteractiveNode.test.ts`

```typescript
/**
 * Unit tests for InteractiveNode.vue
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import InteractiveNode from './InteractiveNode.vue'
import { useVisualizationStore } from '@/stores/visualization'
import { useStateBusStore } from '@/stores/state-bus'

// Mock stores
vi.mock('@/stores/visualization')
vi.mock('@/stores/state-bus')
vi.mock('@/services/workflow-connector')
vi.mock('@/services/tools/registry')

describe('InteractiveNode', () => {
  let wrapper: VueWrapper
  const mockVisualizationStore = {
    getNodeData: vi.fn(),
    getNodeSelection: vi.fn(),
    hasNodeData: vi.fn(),
    loadNodeData: vi.fn(),
    updateSelection: vi.fn(),
    getLoadingState: vi.fn()
  }

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks()
    vi.mocked(useVisualizationStore).mockReturnValue(mockVisualizationStore)
  })

  describe('Component Rendering', () => {
    it('renders loading state when loading', () => {
      wrapper = mount(InteractiveNode, {
        props: {
          id: 'node1',
          data: { label: 'Test Node' }
        }
      })
      // Trigger loading state
      // ...assert loading UI
    })

    it('renders error state when error occurs', () => {
      // ...test error display
    })

    it('renders pending execution state', () => {
      // ...test pending state
    })

    it('renders empty state when no data', () => {
      // ...test empty state
    })
  })

  describe('Data Loading', () => {
    it('loads data on mount', async () => {
      // ...test data loading
    })

    it('handles load errors gracefully', async () => {
      // ...test error handling
    })

    it('retries data load on retry click', async () => {
      // ...test retry functionality
    })
  })

  describe('Configuration', () => {
    it('toggles edit mode', async () => {
      // ...test edit mode toggle
    })

    it('emits config change on configuration update', async () => {
      // ...test config change emission
    })

    it('initializes local config from base config', () => {
      // ...test config initialization
    })
  })

  describe('Selection Handling', () => {
    it('emits selection change event', async () => {
      // ...test selection emission
    })

    it('receives upstream selection', async () => {
      // ...test upstream selection
    })
  })

  describe('State Bus Integration', () => {
    it('subscribes to state ports on mount', () => {
      // ...test subscription
    })

    it('unsubscribes on unmount', () => {
      // ...test cleanup
    })

    it('dispatches state changes', () => {
      // ...test dispatch
    })
  })

  describe('Edge Cases', () => {
    it('handles missing executionId', async () => {
      // ...test no execution ID
    })

    it('handles malformed tool data', async () => {
      // ...test invalid data
    })

    it('handles empty columns list', () => {
      // ...test no columns
    })
  })
})
```

### 4.3 E2E Tests (Priority: MEDIUM)

#### Test File: `tests/e2e/test_interactive_workflow.spec.ts`

```typescript
/**
 * E2E tests for interactive visualization workflow
 */
import { test, expect } from '@playwright/test'

test.describe('Interactive Visualization Workflow', () => {
  test('creates and executes interactive workflow', async ({ page }) => {
    // Navigate to workflow editor
    await page.goto('/workflows/new')

    // Add file input node
    await page.click('[data-testid="add-node"]')
    await page.click('text="File Input"')

    // Add interactive visualization node
    await page.click('[data-testid="add-node"]')
    await page.click('text="Feature Map Viewer"')

    // Connect nodes
    // ...drag and drop connection

    // Run workflow
    await page.click('text="Run Workflow"')

    // Wait for execution
    await expect(page.locator('.node-ready')).toBeVisible()

    // Verify data loaded
    await expect(page.locator('.node-content')).toBeVisible()
  })

  test('configures interactive node visualization', async ({ page }) => {
    // ...test configuration panel
  })

  test('filters data through interactive node', async ({ page }) => {
    // ...test selection filtering
  })

  test('exports visualization data', async ({ page }) => {
    // ...test export functionality
  })
})
```

---

## 5. Implementation Priority

### Phase 1: Critical Backend Tests (Week 1)
**Priority**: CRITICAL
**Estimated Effort**: 20-30 hours

1. ✅ Write unit tests for `NodeDataCache` (8 hours)
2. ✅ Write unit tests for `parse_tabular_file()` (4 hours)
3. ✅ Write integration tests for `/data/schema` endpoint (6 hours)
4. ✅ Write integration tests for `/data/rows` endpoint (6 hours)
5. ✅ Write error path tests for all endpoints (4 hours)
6. ✅ Add edge case tests (empty, null, large data) (2 hours)

**Target Coverage**: Backend 60%+

### Phase 2: Frontend Component Tests (Week 2)
**Priority**: HIGH
**Estimated Effort**: 15-20 hours

1. ✅ Write tests for `InteractiveNode.vue` (10 hours)
2. ✅ Write tests for state bus integration (4 hours)
3. ✅ Write tests for visualization store (3 hours)
4. ✅ Write tests for configuration panels (3 hours)

**Target Coverage**: Frontend 50%+

### Phase 3: Integration & E2E Tests (Week 3)
**Priority**: MEDIUM
**Estimated Effort**: 15-20 hours

1. ✅ Write API integration tests (8 hours)
2. ✅ Write database integration tests (4 hours)
3. ✅ Write E2E workflow tests (6 hours)
4. ✅ Write performance tests (2 hours)

**Target Coverage**: Overall 70%+

### Phase 4: Security & Edge Cases (Week 4)
**Priority**: MEDIUM
**Estimated Effort**: 10-15 hours

1. ✅ Security tests (SQL injection, XSS) (4 hours)
2. ✅ Concurrency tests (cache, state bus) (4 hours)
3. ✅ Boundary value tests (2 hours)
4. ✅ Error recovery tests (2 hours)

**Target Coverage**: Overall 80%+

---

## 6. Test Infrastructure Setup

### Required Dependencies

**Backend** (add to `requirements-dev.txt`):
```txt
pytest>=9.0.0
pytest-asyncio>=1.3.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
httpx>=0.26.0  # For TestClient
```

**Frontend** (add to `package.json`):
```json
{
  "devDependencies": {
    "vitest": "^1.2.0",
    "@vue/test-utils": "^2.4.0",
    "@playwright/test": "^1.40.0",
    "jsdom": "^23.0.0"
  }
}
```

### Coverage Configuration

**Backend** (`.coveragerc`):
```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False
```

**Frontend** (`vitest.config.ts`):
```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80
    }
  }
})
```

### CI/CD Integration

Add to `.github/workflows/test.yml`:
```yaml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=app --cov-report=xml --cov-report=html
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: pnpm install
      - run: pnpm test:coverage
      - uses: codecov/codecov-action@v3
```

---

## 7. Success Criteria

### Coverage Targets

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Backend Line Coverage | 5% | 80% | ❌ |
| Backend Branch Coverage | ~2% | 80% | ❌ |
| Frontend Line Coverage | 0% | 80% | ❌ |
| Frontend Branch Coverage | 0% | 80% | ❌ |
| Overall Coverage | 1.6% | 80% | ❌ |

### Quality Targets

- [ ] All public functions have unit tests
- [ ] All API endpoints have integration tests
- [ ] All error paths tested
- [ ] All edge cases covered (null, empty, invalid)
- [ ] No hardcoded values in tests (use fixtures)
- [ ] Tests are independent (no shared state)
- [ ] Test execution time < 5 minutes
- [ ] No test flakiness

### Functional Targets

- [ ] Can run workflow with interactive nodes
- [ ] Can configure visualizations
- [ ] Can filter data through nodes
- [ ] Can export visualization data
- [ ] Handles errors gracefully
- [ ] Performance acceptable (< 2s for data load)

---

## 8. Recommendations

### Immediate Actions (This Week)

1. **STOP** deploying to production until critical tests pass
2. Set up test infrastructure (pytest, vitest, coverage)
3. Write Phase 1 backend tests (cache, parsing, API)
4. Add test coverage badge to README

### Short-term Actions (This Month)

1. Complete Phase 1-3 tests
2. Set up CI/CD test automation
3. Add pre-commit hooks for tests
4. Document test writing guidelines
5. Train team on TDD practices

### Long-term Actions (This Quarter)

1. Achieve 80%+ coverage target
2. Add performance benchmarking
3. Add security scanning
4. Implement mutation testing
5. Establish test-driven culture

---

## 9. Conclusion

The interactive-vis-architecture implementation has **severely inadequate test coverage** (~1.6%). This represents a **high-risk situation** for production deployment.

**Critical gaps**:
- API endpoints completely untested
- Cache logic untested (thread safety issues likely)
- Error paths untested
- Frontend components untested
- No integration or E2E tests

**Recommended action**: Implement test suite following the 4-phase plan above before deploying to production. Target 80%+ coverage within 4 weeks.

**Estimated effort**: 60-85 hours total across 4 weeks.

---

**Review Date**: 2026-03-05
**Next Review**: After Phase 1 completion (estimated 2026-03-12)
