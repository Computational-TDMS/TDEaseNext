# Capability: Realtime Log Streaming

## ADDED Requirements

### Requirement: WebSocket endpoint for execution logs
The system SHALL provide a WebSocket endpoint at `/ws/executions/{execution_id}` that streams log messages in real-time.

#### Scenario: Connect to WebSocket for running execution
- **WHEN** client establishes WebSocket connection to `/ws/executions/{execution_id}`
- **AND** execution is currently running
- **THEN** system accepts connection
- **AND** system sends JSON messages for each log entry
- **AND** system keeps connection open until execution completes

#### Scenario: WebSocket message format
- **WHEN** system sends log message via WebSocket
- **THEN** message format is: `{"type": "log", "data": {"timestamp": "ISO-8601", "level": "info|warning|error", "message": "text"}}`
- **AND** timestamp is in UTC with `Z` suffix
- **AND** level is lowercase

### Requirement: Status updates via WebSocket
The system SHALL send execution status updates through the WebSocket connection.

#### Scenario: Status change notification
- **WHEN** execution status changes (e.g., `pending → running → completed`)
- **THEN** system sends WebSocket message: `{"type": "status", "status": "new_status"}`
- **AND** client receives notification within 1 second of status change

### Requirement: WebSocket connection lifecycle
The system SHALL close WebSocket connection when execution completes or fails.

#### Scenario: Connection closes on completion
- **WHEN** execution status changes to `completed`
- **THEN** system sends final status message
- **AND** system closes WebSocket connection with code `1000` (normal closure)

#### Scenario: Connection closes on error
- **WHEN** execution status changes to `failed`
- **THEN** system sends final status message with error details
- **AND** system closes WebSocket connection

#### Scenario: Connection rejected for invalid execution
- **WHEN** client connects to WebSocket for non-existent execution
- **THEN** system rejects connection with code `4001` (custom: execution not found)

### Requirement: HTTP polling fallback
The system SHALL support HTTP polling for logs when WebSocket is unavailable.

#### Scenario: Retrieve logs via HTTP
- **WHEN** client sends `GET /api/executions/{execution_id}/logs`
- **THEN** system returns all collected logs so far
- **AND** response format is: `{"logs": [{"timestamp": "...", "level": "...", "message": "..."}]}`
- **AND** logs are in chronological order

#### Scenario: Filter logs by level
- **WHEN** client requests logs with `?level=error` parameter
- **THEN** system returns only error-level logs
- **AND** other log levels are excluded from response

### Requirement: Log collection during execution
The system SHALL collect logs generated during background execution and make them immediately available.

#### Scenario: Real-time log collection
- **WHEN** workflow execution generates a log message
- **THEN** system adds log to in-memory log buffer
- **AND** system sends log via WebSocket if connected
- **AND** system makes log available via HTTP polling
- **AND** system processes log within 100ms of generation

### Requirement: Log buffer limits
The system SHALL limit log buffer size to prevent memory exhaustion.

#### Scenario: Log buffer overflow
- **WHEN** log buffer reaches 10,000 entries
- **THEN** system removes oldest entries to make room for new logs
- **AND** system keeps most recent 10,000 logs
- **AND** system logs warning when buffer overflows

### Requirement: Frontend automatic reconnection
The system SHALL support automatic WebSocket reconnection on connection loss.

#### Scenario: Connection drops during execution
- **WHEN** WebSocket connection is interrupted during execution
- **THEN** frontend automatically attempts reconnection
- **AND** frontend falls back to HTTP polling if reconnection fails after 3 attempts
- **AND** frontend resumes log display from last received log
