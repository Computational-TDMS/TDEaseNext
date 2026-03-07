## 1. Backend Agent Infrastructure

- [ ] 1.1 Add LangChain/LangGraph dependencies to `pyproject.toml`
- [ ] 1.2 Create `app/services/agent/agent_service.py` with basic conversational state management
- [ ] 1.3 Create the `build_workflow` skill function mapped to `ToolRegistry` schema context
- [ ] 1.4 Add `POST /api/executions/{exec_id}/agent/chat` streaming endpoint (SSE or WebSockets)

## 2. Agent Validation & Logic

- [ ] 2.1 Implement the JSON schema parser to force AI to output valid VueFlow node/edge arrays
- [ ] 2.2 Wire the generated JSON to `WorkflowService` for validation before returning success
- [ ] 2.3 Implement the self-correction retry loop if `WorkflowService` throws validation errors

## 3. Frontend Copilot Sidebar

- [ ] 3.1 Create `CopilotSidebar.vue` component with chat UI (user messages, AI responses, loading states)
- [ ] 3.2 Wire the Chat UI to the backend streaming endpoint using an EventSource or WebSocket client
- [ ] 3.3 Add a trigger within the `VisContainer` layout to toggle the Sidebar visibility

## 4. VueFlow Canvas Integration

- [ ] 4.1 Create a listener in the Pinia workflow store to accept `ai_generate_workflow` payloads
- [ ] 4.2 Write frontend mapping logic to instantiate `VueFlow` node elements and edge elements from the JSON payload
- [ ] 4.3 Add a confirmation dialog "Agent generated a workflow. Apply to canvas?" to allow user to accept/reject changes
