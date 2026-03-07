## ADDED Requirements

### Requirement: Cross-Validation Reasoning
The `ai-cross-validation` feature SHALL orchestrate a rigorous debate between the internal algorithmic predictions (e.g., TopPIC's PTM inferences) and the external truths retrieved via the MCP server.

#### Scenario: Validating inferred PTMs
- **WHEN** an inferred +42.01 Da (Acetylation) is proposed by the workflow
- **THEN** the Agent cross-references this with external MCP data and calculates a "Symmetrical Confidence Score", explaining if the inference is biologically likely.

### Requirement: Agentic Model Fallbacks
The system SHALL dynamically route the depth of validation based on the capability of the locally selected LLM.

#### Scenario: Routing to low-capability models
- **WHEN** the user is running a smaller `8B` local model
- **THEN** the system bypasses the complex multi-step MCP orchestration and falls back to a simpler LangChain single-shot REST query to prevent hallucination looping.
