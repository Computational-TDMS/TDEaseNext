## ADDED Requirements

### Requirement: Unified Agent Interface
The system SHALL provide a conversational interface (Copilot Sidebar) where users can specify their experimental goals using natural language.

#### Scenario: User requests a workflow
- **WHEN** the user types "I want to perform a Top-Down analysis on my raw data"
- **THEN** the system forwards the query to the underlying AI agent for analysis

### Requirement: Goal Interpretation
The AI Agent SHALL analyze the user's natural language input to determine the required nodes and connections needed for the experiment.

#### Scenario: Interpreting intent
- **WHEN** the system receives the query
- **THEN** the agent correctly identifies the required tools (e.g., TopFD, TopPIC) and their expected data flow

### Requirement: Interactive Feedback
The system SHALL inform the user about the AI's understanding and ask for clarification if the request is ambiguous.

#### Scenario: Ambiguous request
- **WHEN** the user types an incomplete request like "analyze data"
- **THEN** the agent responds by asking what kind of analysis (e.g., Bottom-Up, Top-Down) is required
