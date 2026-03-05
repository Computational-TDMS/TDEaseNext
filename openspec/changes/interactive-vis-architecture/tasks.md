# Implementation Tasks: Interactive Visualization Architecture

## Phase 1: Backend Foundation (Tool Definition & API)

### Task 1.1: Extend Tool Definition Schema
**Priority**: High | **Estimated Effort**: 2-3 days

**Objective**: Update tool definition JSON schema to support interactive nodes and column schemas.

**Subtasks**:
- [x] 1.1.1 Add `executionMode` field to tool definitions (values: `"compute"`, `"interactive"`)
- [x] 1.1.2 Add `schema` field to output port definitions with column metadata
- [x] 1.1.3 Add `defaultMapping` field to interactive tool definitions
- [x] 1.1.4 Create JSON schema validation for new fields
- [x] 1.1.5 Update tool registry loader to parse new fields

**Acceptance Criteria**:
- Tool definitions can specify `executionMode: "interactive"`
- Output ports can declare column schemas with `id` and `type`
- Interactive tools can specify default column-to-axis mappings
- Invalid tool definitions are rejected with clear error messages

**Example Tool Definition**:
```json
{
  "id": "featuremap_viewer",
  "executionMode": "interactive",
  "inputs": [
    { "id": "input_file", "dataType": "feature" }
  ],
  "outputs": [
    { "id": "selection", "dataType": "state/selection_ids" }
  ],
  "defaultMapping": {
    "xAxis": "RT",
    "yAxis": "Mass"
  }
}
```


### Task 1.2: Update Workflow Execution Engine
**Priority**: High | **Estimated Effort**: 2 days

**Objective**: Modify workflow executor to skip interactive nodes during backend execution.

**Subtasks**:
- [x] 1.2.1 Update `WorkflowExecutor` to check `executionMode` before node execution
- [x] 1.2.2 Mark interactive nodes with `status: skipped` in execution logs
- [x] 1.2.3 Ensure data flow edges bypass interactive nodes for dependency resolution
- [x] 1.2.4 Add unit tests for execution skipping logic

**Acceptance Criteria**:
- Backend execution skips all nodes with `executionMode: "interactive"`
- Workflow execution logs clearly indicate skipped interactive nodes
- Data dependencies are correctly resolved even when interactive nodes are present
- No performance degradation in workflow execution

---

### Task 1.3: Enhance NodeDataAccess API
**Priority**: High | **Estimated Effort**: 3-4 days

**Objective**: Extend data access API to support schema queries and row-based filtering.

**Subtasks**:
- [x] 1.3.1 Add `/api/nodes/{node_id}/data/schema` endpoint to return column metadata
- [x] 1.3.2 Add `/api/nodes/{node_id}/data/rows` endpoint with row ID filtering
- [x] 1.3.3 Implement aggressive caching strategy for file data (LRU cache with configurable size)
- [x] 1.3.4 Add cache invalidation on workflow re-execution
- [ ] 1.3.5 Implement streaming for large datasets (chunked responses)
- [x] 1.3.6 Add API documentation and integration tests

**Acceptance Criteria**:
- Schema endpoint returns column names and types for any node output
- Row filtering endpoint supports array of row indices with sub-millisecond response
- Cache hit rate > 90% for repeated queries within same session
- Memory usage stays within configured limits (default: 500MB)
- API handles files up to 100MB without blocking

**API Examples**:
```
GET /api/nodes/topfd_1/data/schema?output=ms1feature
Response: [{"id": "Mass", "type": "number"}, {"id": "RT", "type": "number"}]

POST /api/nodes/topfd_1/data/rows?output=ms1feature
Body: {"rowIndices": [0, 5, 12]}
Response: [{"Mass": 1234.5, "RT": 45.2}, ...]
```


---

## Phase 2: Frontend Components (VueFlow & Interactive Nodes)

### Task 2.1: Create View Node Base Component
**Priority**: High | **Estimated Effort**: 3-4 days

**Objective**: Implement base `InteractiveNode.vue` component with configuration panel support.

**Subtasks**:
- [x] 2.1.1 Create `InteractiveNode.vue` base component extending standard node
- [x] 2.1.2 Implement configuration panel modal/drawer UI
- [x] 2.1.3 Add schema fetching logic from NodeDataAccess API
- [x] 2.1.4 Implement dynamic dropdown rendering for column mapping
- [x] 2.1.5 Add default mapping auto-population from tool definition
- [x] 2.1.6 Persist mapping configuration in workflow state
- [x] 2.1.7 Add visual indicator for "data ready" vs "awaiting data" states

**Acceptance Criteria**:
- Double-clicking interactive node opens configuration panel
- Panel displays dropdowns populated with upstream file columns
- Default mappings are pre-selected when available
- Configuration persists across workflow saves/loads
- Node visually indicates when upstream data is available

**UI Mockup Requirements**:
- Configuration panel shows: X Axis, Y Axis, Color (optional), Size (optional)
- Each dropdown shows column name and type (e.g., "Mass (number)")
- "Apply" button validates and saves configuration
- "Reset to Defaults" button restores defaultMapping


### Task 2.2: Implement Semantic State Bus
**Priority**: High | **Estimated Effort**: 2-3 days

**Objective**: Create frontend event bus for state/selection edge communication.

**Subtasks**:
- [x] 2.2.1 Create `StateBus` singleton service with event emitter pattern
- [x] 2.2.2 Define event protocol for `state/selection_ids` messages
- [x] 2.2.3 Implement edge-based routing (emit to specific connected nodes)
- [x] 2.2.4 Add event logging/debugging support
- [ ] 2.2.5 Implement event throttling/debouncing for performance
- [x] 2.2.6 Add unit tests for event routing logic

**Acceptance Criteria**:
- StateBus can emit events with `{nodeId, eventType, payload}` structure
- Events are routed only to nodes connected via state edges
- Multiple listeners can subscribe to same node's events
- Event history is available for debugging (last 100 events)
- Performance: handles 60+ events/second without lag

**Event Protocol**:
```typescript
interface SelectionEvent {
  sourceNodeId: string;
  eventType: 'state/selection_ids';
  payload: {
    rowIndices: number[];
    timestamp: number;
  };
}
```

---

### Task 2.3: Enhance VueFlow Edge Rendering
**Priority**: Medium | **Estimated Effort**: 1-2 days

**Objective**: Add visual distinction for state edges vs data edges.

**Subtasks**:
- [x] 2.3.1 Create custom edge component for `state/selection` type
- [x] 2.3.2 Apply distinct styling (dashed line, different color)
- [x] 2.3.3 Add animated flow indicator for active state propagation
- [x] 2.3.4 Update edge creation logic to support state edge type
- [x] 2.3.5 Add edge type selector in UI when connecting nodes (automatic based on portKind)

**Acceptance Criteria**:
- State edges are visually distinct (e.g., dashed orange line)
- Data edges remain solid (e.g., solid blue line)
- Active state propagation shows animated flow
- Users can choose edge type when creating connections
- Edge labels indicate type ("Data" vs "State")


### Task 2.4: Implement FeatureMap Viewer Component
**Priority**: High | **Estimated Effort**: 4-5 days

**Objective**: Create interactive scatter plot viewer for MS1 feature data.

**Subtasks**:
- [x] 2.4.1 Create `FeatureMapViewer.vue` component extending InteractiveNode
- [x] 2.4.2 Integrate plotting library (e.g., Plotly.js or D3.js)
- [x] 2.4.3 Implement brush selection tool
- [x] 2.4.4 Emit selection events to StateBus on brush end
- [x] 2.4.5 Add zoom/pan controls
- [x] 2.4.6 Implement data point tooltips
- [x] 2.4.7 Add loading state and error handling
- [ ] 2.4.8 Optimize rendering for large datasets (10k+ points)

**Acceptance Criteria**:
- Renders scatter plot with configurable X/Y axes
- Brush selection emits row indices to StateBus
- Handles datasets up to 50k points with smooth interaction
- Tooltips show all column values for hovered point
- Zoom/pan state persists during session
- Loading spinner shown while fetching data

**Performance Targets**:
- Initial render: < 500ms for 10k points
- Brush selection response: < 100ms
- Memory usage: < 100MB for 50k points


### Task 2.5: Implement Spectrum Viewer Component
**Priority**: High | **Estimated Effort**: 3-4 days

**Objective**: Create MS2 spectrum viewer that responds to selection events.

**Subtasks**:
- [x] 2.5.1 Create `SpectrumViewer.vue` component extending InteractiveNode
- [x] 2.5.2 Implement line/bar chart for m/z vs intensity
- [x] 2.5.3 Subscribe to StateBus selection events
- [x] 2.5.4 Filter/highlight peaks based on received row indices
- [x] 2.5.5 Add peak annotation display
- [x] 2.5.6 Implement zoom to selected region
- [x] 2.5.7 Add export functionality (PNG/SVG)

**Acceptance Criteria**:
- Renders spectrum with m/z on X-axis, intensity on Y-axis
- Responds to selection events within 100ms
- Highlights selected peaks with distinct color
- Annotations are readable at all zoom levels
- Export generates publication-quality images

---

### Task 2.6: Implement HTML Viewer Component
**Priority**: Medium | **Estimated Effort**: 2-3 days

**Objective**: Create viewer for TopPIC HTML fragment rendering.

**Subtasks**:
- [x] 2.6.1 Create `HtmlViewer.vue` component extending InteractiveNode
- [x] 2.6.2 Implement iframe or shadow DOM for HTML rendering
- [x] 2.6.3 Subscribe to selection events for dynamic loading
- [ ] 2.6.4 Query backend for specific HTML fragments by row ID
- [x] 2.6.5 Add security sandboxing for untrusted HTML
- [x] 2.6.6 Implement loading states and error handling

**Acceptance Criteria**:
- Renders HTML fragments in isolated context
- Loads specific fragments based on selection events
- Prevents XSS and other security issues
- Shows loading indicator during fetch
- Handles missing/invalid HTML gracefully


### Task 2.7: Implement Table Viewer Component
**Priority**: Medium | **Estimated Effort**: 2-3 days

**Objective**: Create filterable table viewer for PrSM results.

**Subtasks**:
- [x] 2.7.1 Create `TableViewer.vue` component extending InteractiveNode
- [ ] 2.7.2 Implement virtual scrolling for large datasets
- [x] 2.7.3 Subscribe to selection events for row filtering
- [x] 2.7.4 Add column sorting and filtering
- [x] 2.7.5 Implement row selection (emit to StateBus)
- [x] 2.7.6 Add CSV export functionality

**Acceptance Criteria**:
- Renders tables with 100k+ rows smoothly (virtual scrolling)
- Filters rows based on selection events within 50ms
- Supports sorting by any column
- Row selection emits events for downstream nodes
- Export preserves filtered/sorted state

---

## Phase 3: Tool Definitions & Configuration

### Task 3.1: Create Interactive Tool Definitions
**Priority**: High | **Estimated Effort**: 1-2 days

**Objective**: Define JSON configurations for all interactive viewer tools.

**Subtasks**:
- [x] 3.1.1 Create `config/tools/featuremap_viewer.json`
- [x] 3.1.2 Create `config/tools/spectrum_viewer.json`
- [x] 3.1.3 Create `config/tools/html_viewer.json`
- [x] 3.1.4 Create `config/tools/table_viewer.json`
- [x] 3.1.5 Define schemas for common bioinformatics file types
- [x] 3.1.6 Validate all tool definitions against schema

**Acceptance Criteria**:
- All interactive tools have valid JSON definitions
- Schemas accurately reflect TopFD/ProMex/MSPathFinder outputs
- Default mappings match common use cases
- Tool registry successfully loads all definitions


### Task 3.2: Update Compute Tool Schemas
**Priority**: Medium | **Estimated Effort**: 1-2 days

**Objective**: Add output schemas to existing compute tool definitions.

**Subtasks**:
- [x] 3.2.1 Add schema to `topfd.json` for ms1feature output
- [x] 3.2.2 Add schema to `promex.json` for feature output
- [x] 3.2.3 Add schema to `mspathfinder.json` for PrSM output
- [x] 3.2.4 Add schema to `toppic.json` for HTML output metadata
- [ ] 3.2.5 Document schema format in `docs/TOOL_DEFINITION_SCHEMA.md`

**Acceptance Criteria**:
- All compute tools declare output schemas
- Schemas include column names, types, and descriptions
- Documentation is clear and includes examples
- Backward compatibility maintained (schema is optional)

---

## Phase 4: Integration & Testing

### Task 4.1: Create Test Workflow
**Priority**: High | **Estimated Effort**: 2 days

**Objective**: Build comprehensive test workflow demonstrating all features.

**Subtasks**:
- [ ] 4.1.1 Create `wf_test_interactive.json` workflow definition
- [ ] 4.1.2 Include TopFD -> FeatureMap -> Spectrum chain
- [ ] 4.1.3 Add MSPathFinder -> Table viewer branch
- [ ] 4.1.4 Add TopPIC -> HTML viewer branch
- [ ] 4.1.5 Connect all viewers with state edges
- [ ] 4.1.6 Prepare test data files (sample mzML, FASTA)

**Acceptance Criteria**:
- Workflow loads without errors
- All nodes render correctly on canvas
- Data and state edges are visually distinct
- Workflow matches requirements in `docs/WORKFLOW_REQUIREMENTS.md`


### Task 4.2: Backend Unit Tests
**Priority**: High | **Estimated Effort**: 2-3 days

**Objective**: Comprehensive unit test coverage for backend changes.

**Subtasks**:
- [ ] 4.2.1 Test tool definition schema validation
- [ ] 4.2.2 Test workflow executor skipping logic
- [ ] 4.2.3 Test NodeDataAccess schema endpoint
- [ ] 4.2.4 Test NodeDataAccess row filtering endpoint
- [ ] 4.2.5 Test cache hit/miss behavior
- [ ] 4.2.6 Test cache invalidation on re-execution
- [ ] 4.2.7 Test error handling for invalid schemas

**Acceptance Criteria**:
- All new backend code has > 90% test coverage
- Tests follow pytest conventions
- Tests are marked appropriately (`@pytest.mark.unit`)
- All tests pass: `uv run pytest tests/ -m unit`

**Test Files to Create**:
- `tests/test_tool_schema_validation.py`
- `tests/test_interactive_execution.py`
- `tests/test_node_data_access.py`
- `tests/test_data_cache.py`

---

### Task 4.3: Frontend Unit Tests
**Priority**: High | **Estimated Effort**: 2-3 days

**Objective**: Unit test coverage for frontend components.

**Subtasks**:
- [ ] 4.3.1 Test InteractiveNode configuration panel logic
- [ ] 4.3.2 Test StateBus event routing
- [ ] 4.3.3 Test FeatureMapViewer selection emission
- [ ] 4.3.4 Test SpectrumViewer event subscription
- [ ] 4.3.5 Test data fetching and caching logic
- [ ] 4.3.6 Test edge rendering logic

**Acceptance Criteria**:
- All components have > 80% test coverage
- Tests use Vue Test Utils
- Mock API calls appropriately
- All tests pass in CI/CD pipeline


### Task 4.4: Integration Tests
**Priority**: High | **Estimated Effort**: 3-4 days

**Objective**: End-to-end integration testing of complete workflows.

**Subtasks**:
- [ ] 4.4.1 Test complete workflow execution (compute + interactive)
- [ ] 4.4.2 Test cross-filtering: FeatureMap -> Spectrum
- [ ] 4.4.3 Test cross-filtering: FeatureMap -> Table
- [ ] 4.4.4 Test HTML viewer dynamic loading
- [ ] 4.4.5 Test workflow save/load with interactive nodes
- [ ] 4.4.6 Test performance with large datasets (50k+ rows)
- [ ] 4.4.7 Test error recovery (network failures, invalid data)

**Acceptance Criteria**:
- All integration tests pass: `uv run pytest tests/ -m integration`
- Tests cover all critical user workflows
- Performance benchmarks are met
- Error scenarios are handled gracefully

**Test Scenarios**:
1. Load workflow -> Execute compute nodes -> Open FeatureMap -> Brush selection -> Verify Spectrum updates
2. Load workflow with saved interactive config -> Verify mappings restored
3. Execute workflow with 50k features -> Verify < 2s render time
4. Simulate network failure during data fetch -> Verify error message shown

---

### Task 4.5: E2E Tests
**Priority**: Medium | **Estimated Effort**: 2-3 days

**Objective**: Browser-based end-to-end testing.

**Subtasks**:
- [ ] 4.5.1 Set up Playwright/Cypress test framework
- [ ] 4.5.2 Test workflow creation with interactive nodes
- [ ] 4.5.3 Test configuration panel interactions
- [ ] 4.5.4 Test brush selection and cross-filtering
- [ ] 4.5.5 Test edge creation (data vs state)
- [ ] 4.5.6 Record test videos for documentation

**Acceptance Criteria**:
- E2E tests run in CI/CD pipeline
- Tests cover all user-facing features
- Test videos demonstrate key workflows
- All tests pass: `npm run test:e2e`


---

## Phase 5: Documentation & Polish

### Task 5.1: Update Documentation
**Priority**: Medium | **Estimated Effort**: 2 days

**Objective**: Comprehensive documentation for new architecture.

**Subtasks**:
- [ ] 5.1.1 Update `docs/ARCHITECTURE.md` with View Node design
- [ ] 5.1.2 Create `docs/INTERACTIVE_NODES.md` user guide
- [ ] 5.1.3 Update `docs/TOOL_DEFINITION_SCHEMA.md` with new fields
- [ ] 5.1.4 Create `docs/STATE_BUS_PROTOCOL.md` for developers
- [ ] 5.1.5 Add API documentation for new endpoints
- [ ] 5.1.6 Create tutorial video/screenshots for users

**Acceptance Criteria**:
- All documentation is clear and accurate
- Examples are tested and working
- Screenshots show current UI
- Tutorial covers common workflows

---

### Task 5.2: Performance Optimization
**Priority**: Medium | **Estimated Effort**: 2-3 days

**Objective**: Optimize rendering and data access performance.

**Subtasks**:
- [ ] 5.2.1 Profile FeatureMapViewer rendering performance
- [ ] 5.2.2 Implement WebGL rendering for large datasets (if needed)
- [ ] 5.2.3 Optimize StateBus event throttling
- [ ] 5.2.4 Tune cache size and eviction policy
- [ ] 5.2.5 Add performance monitoring/metrics
- [ ] 5.2.6 Document performance characteristics

**Acceptance Criteria**:
- FeatureMap renders 50k points in < 1s
- Selection events propagate in < 100ms
- Memory usage stays under 500MB for typical workflows
- Performance metrics are logged and monitored


### Task 5.3: UI/UX Polish
**Priority**: Low | **Estimated Effort**: 2 days

**Objective**: Refine user interface and experience.

**Subtasks**:
- [ ] 5.3.1 Add keyboard shortcuts for common actions
- [ ] 5.3.2 Improve loading states and progress indicators
- [ ] 5.3.3 Add tooltips and help text throughout UI
- [ ] 5.3.4 Implement undo/redo for configuration changes
- [ ] 5.3.5 Add accessibility features (ARIA labels, keyboard nav)
- [ ] 5.3.6 Conduct user testing and gather feedback

**Acceptance Criteria**:
- All interactive elements have keyboard shortcuts
- Loading states are clear and informative
- Help text is contextual and helpful
- Undo/redo works for all configuration changes
- Basic accessibility requirements are met

---

### Task 5.4: Migration Guide
**Priority**: Low | **Estimated Effort**: 1 day

**Objective**: Help users migrate existing workflows to new architecture.

**Subtasks**:
- [ ] 5.4.1 Document breaking changes
- [ ] 5.4.2 Create migration script for old workflows (if needed)
- [ ] 5.4.3 Provide before/after examples
- [ ] 5.4.4 Create FAQ for common migration issues

**Acceptance Criteria**:
- Migration guide is clear and complete
- Migration script handles common cases
- Examples demonstrate key differences
- FAQ addresses anticipated questions

---

## Summary

**Recommended Team Structure**:
- 1 Backend Developer (Phase 1, 3)
- 2 Frontend Developers (Phase 2)
- 1 QA Engineer (Phase 4)
- 1 Technical Writer (Phase 5)

**Parallel Work Opportunities**:
- Phase 1 and Phase 2 can be developed in parallel after Task 1.1 completes
- Phase 3 can start once Task 1.1 completes
- Phase 4 tests can be written alongside implementation
- Phase 5 documentation can start once design is stable

**Risk Areas**:
- Performance with very large datasets (>100k points)
- Browser memory limits for data caching
- Complex state synchronization across multiple viewers
- Security concerns with HTML viewer
