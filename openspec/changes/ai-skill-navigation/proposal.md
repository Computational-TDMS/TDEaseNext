# Proposal: AI Skill Navigation

## Why
Current TDEase systems require users to manually orchestrate their node connections, which can be daunting for non-experts. By introducing an AI Agent equipped with specialized "skills" (scripted logic pathways and instructions), we can help navigate users through complex operations based on their natural language queries. This allows the agent to dynamically build workflows and answer questions, vastly reducing the learning curve.

## Capabilities
- `ai-workflow-navigation`: Introduce a unified agent interface where users can ask questions and specify experimental goals.
- `ai-skill-execution`: The agent can invoke diverse Skills to dynamically generate and deploy VueFlow JSON layouts to the user's workspace, guiding them step-by-step.

## Modified Capabilities


## Impact
- Frontend: VueFlow components will need an augmented interface (Chat/Copilot Sidebar) to receive Agent-generated payloads.
- Backend: WorkflowService will need to bind and parse the agent's generated workflow schemas.
