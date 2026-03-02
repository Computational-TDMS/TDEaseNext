# Proposal: Async Workflow Execution with Real-Time Logs

## Why

Currently, workflow execution is synchronous: the HTTP request blocks until completion, causing two critical problems:

1. **Timeout failures**: Long-running workflows (>30s) cause frontend timeouts, but backend continues execution silently
2. **No real-time feedback**: Users cannot see execution logs until completion, making long workflows appear "frozen"

This degrades user experience for data-intensive workflows that can take minutes to complete.

## What Changes

- **Async workflow execution**: Change `POST /api/workflows/execute` to return immediately with `executionId` and `status: pending`, while execution continues in background
- **Real-time log streaming**: Add WebSocket endpoint `/ws/executions/{executionId}` to push logs as they're generated
- **Frontend polling enhancement**: Update execution monitoring to combine WebSocket (when available) with polling fallback
- **Progress tracking**: Store intermediate execution state and logs in memory for API access during execution
- **Error handling**: Properly handle execution cancellation and error propagation to frontend

## Capabilities

### New Capabilities

- **`async-workflow-execution`**: Backend async execution using FastAPI BackgroundTasks
- **`realtime-log-streaming`**: WebSocket connection for live log推送 during execution
- **`execution-state-management`**: In-memory execution state with real-time status updates

### Modified Capabilities

- **`workflow-execution-api`**: Change execution endpoint from blocking to async response model

## Impact

- **Backend**: `app/api/workflow.py` execute endpoint, `app/services/workflow_service.py`, new WebSocket handler in `app/core/websocket.py`
- **Frontend**: `src/services/workflow.ts`, `src/pages/workflow.vue`, `src/pages/execution.vue`
- **API changes**: Execution endpoint now returns `status: pending` immediately instead of waiting for completion
- **Dependencies**: No new external dependencies (uses FastAPI built-in BackgroundTasks and WebSocket)
- **Migration**: Frontend must handle immediate response and start polling/WS connection; old blocking behavior removed
