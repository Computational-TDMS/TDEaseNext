## MODIFIED Requirements

### Requirement: Data Provider Instantiation
The topmsv-prsm-bundle tool definition provides a single execution entry point to process TSV outputs into sub-resource JSON parts representing PrSM records.

#### Scenario: Interactive PrSM loading
- **WHEN** the tool is executed in interactive mode
- **THEN** it generates a master manifest and sliceable PrSM json resources

**MODIFIED Behavior:**
The data provider SHALL dynamically bind to the Agentic `StateBus`, continually broadcasting the underlying Data Hologram (stats & shapes) of the currently viewed spectrum.

#### Scenario: Agent watches the user's viewport
- **WHEN** the user zooms into a specific 10 Da window in the spectrum viewer
- **THEN** the `topmsv-prsm-bundle` recalculates a localized micro-summary of just that window and feeds it instantaneously to the AI Copilot's context window.
