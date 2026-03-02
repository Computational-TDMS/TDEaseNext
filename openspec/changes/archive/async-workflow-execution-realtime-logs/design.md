# Design: Async Workflow Execution with Real-Time Logs

## Context

**Current State:**
- Workflow execution is synchronous in `app/api/workflow.py:813`: `result = await workflow_service.execute_workflow(...)` blocks HTTP connection
- Logs collected in memory (`execution.logs` list) but only accessible after execution completes
- Frontend polls `getExecutionStatus()` and `getExecutionLogs()` every 2 seconds starting after initial request completes
- Frontend timeout (30s) triggers before long-running workflows finish

**Constraints:**
- Must maintain backward compatibility with existing workflow execution logic (FlowEngine, ExecutionContext)
- Cannot introduce heavy external dependencies (no Celery, Redis, message queues)
- Frontend already has Vue 3 + Element Plus, WebSocket support built-in
- Current execution state stored in `ExecutionManager` (in-memory dict)

**Stakeholders:**
- Frontend users running data-intensive workflows (proteomics analysis takes minutes)
- Backend API consumers expecting standard async response patterns

## Goals / Non-Goals

**Goals:**
- Execute workflows asynchronously without blocking HTTP connections
- Stream logs to frontend in real-time as they're generated
- Maintain execution state in memory for polling fallback
- Support execution cancellation from frontend
- Zero external dependency additions

**Non-Goals:**
- Persistent execution queue (no Redis/Celery)
- Execution history persistence beyond current runtime
- Multi-worker distributed execution
- Authentication on WebSocket (reuse existing session/auth)

## Decisions

### 1. Async Execution Approach: FastAPI BackgroundTasks

**Decision:** Use FastAPI's `BackgroundTasks` for async workflow execution

**Rationale:**
- **Alternatives considered:**
  - `asyncio.create_task()`: Would work but requires manual lifecycle management
  - Celery + Redis: Overkill for single-server deployment, adds operational complexity
  - Python `threading`: Not async-compatible, blocks event loop
- **BackgroundTasks advantages:**
  - Built into FastAPI, designed for this exact use case
  - Automatic cleanup after task completes
  - Runs in same event loop, shares memory state
  - No external dependencies

**Implementation:**
```python
@router.post("/execute")
async def execute(
    request_data: dict,
    background_tasks: BackgroundTasks,
    ...
):
    execution_id = str(uuid4())
    execution_manager.create(execution_id, workspace, workflow_id)
    execution_manager.update_status(execution_id, "pending")

    # Add background task
    background_tasks.add_task(
        _execute_workflow_background,
        execution_id, workflow_json, workspace_dir, parameters
    )

    # Return immediately
    return WorkflowExecutionResponse(
        executionId=execution_id,
        status="pending",
        ...
    )
```

### 2. Real-Time Logs: WebSocket with Polling Fallback

**Decision:** Primary WebSocket delivery, HTTP polling as fallback

**Rationale:**
- **WebSocket advantages:**
  - True real-time push (no latency from polling interval)
  - Server-initiated (no client keep-alive needed)
  - Built-in reconnection handling in browsers
  - Lower bandwidth (no repeated HTTP headers)
- **Polling fallback:**
  - Simpler for clients that can't use WebSocket
  - Works through proxies that block WebSocket
  - Existing frontend code already implements polling

**Architecture:**
```
WebSocket Endpoint: WS /ws/executions/{execution_id}
  - Client connects after receiving executionId
  - Server sends JSON messages: {"type": "log", "data": {...}}
  - Server sends: {"type": "status", "status": "running"}
  - Server closes connection on completion/error

HTTP Fallback: GET /api/executions/{execution_id}/logs
  - Returns all logs collected so far
  - Frontend polls every 2s if WS not connected
```

**Implementation:**
- Extend `app/core/websocket.py` `ConnectionManager` with execution-specific broadcasting
- Each execution has its own WebSocket connection
- Log handler pushes to WebSocket when available

### 3. Execution State Management: In-Memory with Cleanup

**Decision:** Keep existing `ExecutionManager` with automatic cleanup

**Rationale:**
- Current design already uses in-memory dict for execution state
- Simple and fast for single-server deployment
- Cleanup on completion prevents memory leaks
- Database persistence (ExecutionStore) remains for audit trail

**State transitions:**
```
pending → running → completed/failed/cancelled
   ↓        ↓           ↓
  [immediate] [async] [cleanup after 1h]
```

### 4. Frontend Architecture: Hybrid WS + Polling

**Decision:** Attempt WebSocket first, fallback to polling

**Rationale:**
- Best of both worlds: real-time when possible, reliable fallback
- Graceful degradation for restrictive networks
- Minimal UI changes (swap polling for WS events)

**Implementation:**
```typescript
// Try WebSocket connection
const ws = new WebSocket(`ws://localhost:8000/ws/executions/${executionId}`)
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data)
  if (msg.type === 'log') logs.value.push(msg.data)
  if (msg.type === 'status') status.value = msg.status
}

// Fallback to polling if WS fails
setTimeout(() => {
  if (ws.readyState !== WebSocket.OPEN) {
    startPolling(executionId)
  }
}, 3000)
```

## Risks / Trade-offs

### Risk: Background Task Death on Server Restart

**Impact:** In-progress workflows lost if server restarts
**Mitigation:** Document limitation; users must restart workflows manually. Future enhancement could add checkpoint/resume.

### Risk: Memory Exhaustion from Concurrent Executions

**Impact:** Many concurrent workflows with large logs could exhaust memory
**Mitigation:**
- Add `max_logs` limit per execution (already implemented: 10,000 logs)
- Add execution queue with max concurrency limit (future enhancement)
- Monitor memory usage in production

### Risk: WebSocket Connection Limits

**Impact:** Browser limits concurrent WebSocket connections (~6 per domain)
**Mitigation:**
- Frontend closes previous connections before opening new ones
- Single WS connection per execution, reused across page navigation

### Trade-off: No Persistent Queue

**What we lose:** Workflows don't survive server restarts
**What we gain:** Simplicity, no Redis/Celery dependency
**Acceptable because:** Current system is single-server; restarts are infrequent

## Migration Plan

### Phase 1: Backend Async Execution (Priority 1)
1. Modify `app/api/workflow.py` execute endpoint to use BackgroundTasks
2. Extract execution logic to `_execute_workflow_background()` function
3. Update response to return `status: pending` immediately
4. Add log collection during background execution
5. Test with long-running workflow (>30s)

### Phase 2: WebSocket Implementation (Priority 2)
1. Extend `app/core/websocket.py` ConnectionManager for execution-specific connections
2. Add log broadcasting to WebSocket in log handler
3. Create WebSocket endpoint `WS /ws/executions/{execution_id}`
4. Test log streaming during execution

### Phase 3: Frontend Integration (Priority 3)
1. Add WebSocket connection logic to `src/services/workflow.ts`
2. Update `src/pages/workflow.vue` to use WS for real-time logs
3. Implement fallback to polling if WS fails
4. Update `src/pages/execution.vue` for WS support
5. Test with various network conditions

### Rollback Strategy
- Feature flag: `USE_ASYNC_EXECUTION=true` enables new behavior
- If critical issues: revert to synchronous execution by disabling flag
- WebSocket failures automatically fall back to polling (no rollback needed)

## Open Questions

1. **Should we log to file during execution for post-mortem debugging?**
   - Current: Logs only in memory
   - Consider: Write to `workspace/logs/execution.log` for debugging

2. **What's the max concurrent executions we should support?**
   - Current: Unlimited (could cause memory issues)
   - Consider: Add queue with configurable limit (e.g., 5 concurrent)

3. **Should execution status be persisted to database?**
   - Current: Only ExecutionStore (SQLite) has persistence
   - Consider: Update workflow table with last_execution_status column
