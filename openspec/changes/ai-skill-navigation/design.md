## Context
Currently, TDEase requires users to manually place nodes and wire edges on the VueFlow canvas to construct analytical pipelines. This process has a steep learning curve. We want to implement an AI Copilot that allows users to type queries like "I want to do Top-Down proteomics" and automatically generate the necessary pipeline on the canvas. 

## Goals / Non-Goals

**Goals:**
- Provide a conversational natural language interface (Copilot Sidebar) tightly integrated with the workspace.
- Allow an AI agent to dynamically construct valid VueFlow JSON structures (nodes and edges).
- Validate these generated structures using the existing `WorkflowService` before pushing them to the canvas.

**Non-Goals:**
- Allowing the AI to directly mutate local files or run arbitrary code outside of executing predefined "Skills".
- Completely replacing the manual workflow builder (the AI is an assistant, not a mandatory replacement).

## Decisions

- **Agent Framework**: We will use LangGraph / LangChain for the core agentic loop to allow stateful conversations and tool/skill usage.
- **Skill Registration**: Skills (like `build_workflow`) will be explicitly defined as Python functions decorated or registered with the Agent, and will rely on the existing `ToolRegistry` schema to know what parameter slots exist.
- **Frontend-Backend Comms**: We will extend the existing WebSocket channels (or use Server-Sent Events) to stream the AI's internal reasoning (chain-of-thought) to the Copilot Sidebar to improve UX.
- **Canvas Injection**: We will utilize the VueFlow store (`StateBus`) to listen for an `ai_generate_workflow` event and directly inject the `nodes` and `edges` arrays.

## Risks / Trade-offs

- **Risk: AI hallucinations generating invalid workflows.** 
  - *Mitigation*: We strictly validate the JSON payload against our `UnifiedWorkspaceManager` and `WorkflowService` validation schemas. Invalid payloads are rejected, and the agent is asked to self-correct.
- **Risk: High latency during AI generation.**
  - *Mitigation*: Stream partial completions and reasoning steps to the frontend to keep the user engaged.

## Migration Plan
1. Add `langchain` and `langgraph` to the backend dependencies.
2. Introduce a new `api/v1/agent/` router.
3. Add a new `CopilotSidebar.vue` component to the frontend `VisContainer`.
