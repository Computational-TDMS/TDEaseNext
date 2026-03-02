## ADDED Requirements

### Requirement: Single tool registry access point
The system SHALL provide a single implementation of tool registry access through dependency injection.

#### Scenario: Tool registry injection in API endpoints
- **WHEN** an API endpoint requires tool registry access
- **THEN** the endpoint SHALL use `Depends(get_tool_registry)` from `app.services.tool_registry`
- **AND** the implementation SHALL be the single source of truth from `app/services/tool_registry.py`

### Requirement: Removal of duplicate implementations
The system SHALL NOT contain duplicate implementations of tool registry access functions.

#### Scenario: Duplicate function removal
- **WHEN** refactoring tool registry access
- **THEN** the system SHALL remove `get_tool_registry()` from `app/dependencies.py`
- **AND** the system SHALL remove `get_tool_registry()` from `app/api/tools.py`
- **AND** the system SHALL keep only the implementation in `app/services/tool_registry.py`

### Requirement: No external src import dependencies
The system SHALL NOT import tool registry from external `src.nodes.tool_registry` module.

#### Scenario: External import removal
- **WHEN** the application starts
- **THEN** `app/dependencies.py` SHALL NOT contain `from src.nodes.tool_registry import ToolRegistry`
- **AND** all tool registry access SHALL use internal `app.services.tool_registry`
