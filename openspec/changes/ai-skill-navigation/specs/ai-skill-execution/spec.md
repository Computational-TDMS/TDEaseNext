## ADDED Requirements

### Requirement: Skill Invocation
The AI Agent SHALL be able to invoke predefined Skills (scripted execution logic) to construct VueFlow JSON layouts based on interpreted user goals.

#### Scenario: Generating a workflow layout
- **WHEN** the internal goal is resolved
- **THEN** the agent invokes the `build_workflow` skill, which generates a valid VueFlow JSON payload containing the required nodes and edges

### Requirement: Dynamic Layout Deployment
The system SHALL automatically deploy the Agent-generated VueFlow JSON directly into the user's active workspace canvas.

#### Scenario: Deploying to canvas
- **WHEN** the agent returns a valid workflow JSON
- **THEN** the frontend automatically renders the nodes and connections on the VueFlow canvas without requiring manual user placement

### Requirement: Workflow Validation
The system SHALL validate the Agent-generated workflow JSON using the Backend WorkflowService before deployment.

#### Scenario: Invalid workflow generated
- **WHEN** the agent generates a workflow with missing required ports
- **THEN** the WorkflowService rejects the payload and prompts the agent internally to self-correct
