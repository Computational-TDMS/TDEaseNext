# Implementation Tasks

## 1. Backend Async Execution (Phase 1 - Priority 1)

- [ ] 1.1 Extract workflow execution logic into background function
  - Create `_execute_workflow_background()` function in `app/api/workflow.py`
  - Move existing execution logic from `execute()` endpoint into background function
  - Ensure all parameters (workflow_json, workspace, execution_id, etc.) are passed correctly

- [ ] 1.2 Modify execute endpoint to use BackgroundTasks
  - Add `background_tasks: BackgroundTasks` parameter to `execute()` endpoint
  - Call `execution_manager.create()` and `execution_manager.update_status(execution_id, "pending")` before background task
  - Replace direct `await workflow_service.execute_workflow()` with `background_tasks.add_task()`
  - Return `WorkflowExecutionResponse` with `status: "pending"` immediately

- [ ] 1.3 Update execution status during background task
  - Add `execution_manager.update_status(execution_id, "running")` at start of background function
  - Ensure status transitions: pending → running → completed/failed/cancelled
  - Store `start_time` when status changes to running
  - Store `end_time` when status changes to terminal state

- [ ] 1.4 Enhance log collection during background execution
  - Ensure `log_callback` is properly connected to `execution_manager` logs array
  - Verify logs are appended during execution (not just at completion)
  - Test that logs are accessible via `GET /api/executions/{execution_id}` during execution

- [ ] 1.5 Add error handling for background execution
  - Wrap background execution in try/except block
  - Update execution status to `failed` on exception
  - Store error message in execution record
  - Ensure errors propagate to status endpoint

- [ ] 1.6 Test long-running workflow
  - Create test workflow that runs for >60 seconds
  - Verify execute endpoint returns within 1 second
  - Verify execution continues in background
  - Verify status endpoint shows correct status during execution
  - Verify logs are accessible during execution

## 2. WebSocket Real-Time Log Streaming (Phase 2 - Priority 2)

- [ ] 2.1 Extend ConnectionManager for execution-specific connections
  - Add `execution_connections: Dict[str, WebSocket]` to `ConnectionManager` in `app/core/websocket.py`
  - Add `connect_to_execution(execution_id, websocket)` method
  - Add `disconnect_from_execution(execution_id)` method
  - Add `broadcast_to_execution(execution_id, message)` method

- [ ] 2.2 Create WebSocket endpoint for executions
  - Add `@app.websocket("/ws/executions/{execution_id}")` endpoint in `app/main.py`
  - Validate execution exists before accepting connection
  - Return custom close code `4001` if execution not found
  - Store connection in ConnectionManager

- [ ] 2.3 Integrate log handler with WebSocket broadcasting
  - Modify `ExecutionLogHandler.emit()` in `app/services/log_handler.py`
  - Check for active WebSocket connection for execution
  - Broadcast log entries via WebSocket if connected
  - Use JSON format: `{"type": "log", "data": {"timestamp": "...", "level": "...", "message": "..."}}`

- [ ] 2.4 Send status updates via WebSocket
  - Add status broadcasting in `execution_manager.update_status()`
  - Send `{"type": "status", "status": "new_status"}` on status changes
  - Send final status before closing connection

- [ ] 2.5 Implement WebSocket connection lifecycle
  - Close connection with code `1000` when execution completes
  - Close connection when execution fails or is cancelled
  - Add cleanup in ConnectionManager to remove closed connections

- [ ] 2.6 Test WebSocket log streaming
  - Connect to WebSocket for running execution
  - Verify log messages are received in real-time
  - Verify status updates are received
  - Verify connection closes on completion
  - Test with execution that generates many logs

## 3. Frontend Integration (Phase 3 - Priority 3)

- [ ] 3.1 Add WebSocket service in frontend
  - Create `connectToExecutionWebSocket(executionId)` function in `src/services/workflow.ts`
  - Handle WebSocket connection lifecycle (connect, message, close, error)
  - Parse JSON messages from server
  - Return callback/event emitter pattern for log and status updates

- [ ] 3.2 Update workflow.vue to use WebSocket
  - Import WebSocket service
  - Establish WebSocket connection after receiving executionId from execute
  - Replace polling-based log display with WebSocket event handlers
  - Update executionLogs reactively when WebSocket messages received

- [ ] 3.3 Implement polling fallback
  - Add timeout to detect WebSocket connection failure (3 seconds)
  - If WebSocket not connected, fall back to existing polling logic
  - Implement automatic retry logic for WebSocket reconnection
  - Ensure graceful degradation if WebSocket unavailable

- [ ] 3.4 Update execution.vue for WebSocket support
  - Add WebSocket connection on component mount
  - Display real-time logs as they arrive via WebSocket
  - Update status display when status messages received
  - Clean up WebSocket connection on component unmount

- [ ] 3.5 Handle WebSocket errors and reconnection
  - Implement automatic reconnection with exponential backoff
  - Limit reconnection attempts (e.g., 5 attempts)
  - Fall back to polling after reconnection failures
  - Show user-friendly error messages if connection fails

- [ ] 3.6 Test frontend integration
  - Test WebSocket connection establishment
  - Test real-time log display during execution
  - Test status updates in real-time
  - Test polling fallback when WebSocket blocked
  - Test reconnection after connection loss
  - Test with various network conditions (slow, unstable)

## 4. Testing & Documentation

- [ ] 4.1 Add backend unit tests
  - Test background task execution
  - Test status transitions
  - Test error handling in background tasks
  - Test WebSocket broadcasting

- [ ] 4.2 Add frontend tests
  - Test WebSocket service functions
  - Test polling fallback logic
  - Test reconnection logic

- [ ] 4.3 Integration testing
  - End-to-end test: submit workflow, receive immediate response, monitor via WebSocket
  - Test cancellation during execution
  - Test error propagation to frontend

- [ ] 4.4 Update API documentation
  - Document async execution behavior
  - Document WebSocket endpoint and message format
  - Document status response codes
  - Add examples for WebSocket usage

- [ ] 4.5 Update user documentation
  - Explain real-time log feature
  - Document troubleshooting for WebSocket issues
  - Add notes about polling fallback behavior
