## ADDED Requirements

### Requirement: Unified Tool Definition Schema
The system SHALL use a single JSON Schema for tool definitions that is shared between frontend and backend, containing: tool identity, execution mode, command configuration, input/output ports, parameters with UI metadata, and output flag configuration.

#### Scenario: Frontend loads tool definition
- **WHEN** the frontend loads `config/tools/toppic.json`
- **THEN** it SHALL render input/output ports from `ports.inputs` and `ports.outputs`, and render parameter form from `parameters`

#### Scenario: Backend builds command from tool definition
- **WHEN** the backend CommandBuilder receives a tool definition
- **THEN** it SHALL build the command using `command.executable`, `parameters`, `ports.inputs` (positional), and `output` fields without any hardcoded tool_type branches

#### Scenario: Tool definition validation
- **WHEN** a tool definition JSON is loaded
- **THEN** the system SHALL validate it against the schema and report clear errors for missing required fields (id, name, executionMode, command.executable)

### Requirement: Input port definition with positional semantics
Each input port in the Tool Definition SHALL declare whether it is positional and its ordering via `positional` and `positionalOrder` fields. Non-positional inputs SHALL use flag-based injection.

#### Scenario: TopPIC input ports
- **WHEN** TopPIC defines inputs `fasta_file (positional: true, positionalOrder: 0)` and `msalign_files (positional: true, positionalOrder: 1)`
- **THEN** the CommandBuilder SHALL place them as positional arguments in order: `<fasta_path> <msalign_path>`

#### Scenario: Data loader input (non-positional)
- **WHEN** data_loader defines input `input_sources (positional: false)` with flag `--input`
- **THEN** the CommandBuilder SHALL include `--input <path>` in the command

### Requirement: Output port with pattern and handle
Each output port SHALL declare a `pattern` (with `{placeholder}` syntax), a `handle` for edge matching, and a `dataType` for type-based connection validation.

#### Scenario: TopFD output port
- **WHEN** TopFD declares output `{ id: "msalign", pattern: "{sample}_ms2.msalign", handle: "msalign", dataType: "msalign" }`
- **THEN** the resolved output path SHALL be `<workspace>/SampleA_ms2.msalign` for sample `SampleA`

#### Scenario: Edge connection type validation
- **WHEN** a user connects TopFD's `msalign` output (dataType: msalign) to TopPIC's `msalign_files` input (accept: [msalign])
- **THEN** the connection SHALL be accepted

#### Scenario: Incompatible connection
- **WHEN** a user connects a `raw` output to a `fasta` input
- **THEN** the connection SHALL be rejected with a type incompatibility warning

### Requirement: Parameter definition with UI metadata
Each parameter in the Tool Definition SHALL include: flag, type (value/boolean/choice), label, description, default, required, choices (for choice type), group, and advanced flag.

#### Scenario: Frontend renders value parameter
- **WHEN** a parameter has `{ flag: "-e", type: "value", label: "Mass Error Tolerance", default: "10", group: "Search" }`
- **THEN** the frontend SHALL render a text input labeled "Mass Error Tolerance" in the "Search" group, pre-filled with "10"

#### Scenario: Frontend renders boolean parameter
- **WHEN** a parameter has `{ flag: "-d", type: "boolean", label: "Decoy", default: false }`
- **THEN** the frontend SHALL render a toggle/checkbox labeled "Decoy", default off

#### Scenario: Frontend renders choice parameter
- **WHEN** a parameter has `{ flag: "", type: "choice", label: "Format", choices: { "mzML": "--mzML", "mzXML": "--mzXML" } }`
- **THEN** the frontend SHALL render a dropdown with options "mzML" and "mzXML"

#### Scenario: Advanced parameters hidden by default
- **WHEN** a parameter has `advanced: true`
- **THEN** the frontend SHALL hide it in a collapsible "Advanced" section

### Requirement: Execution mode declaration
The Tool Definition SHALL declare `executionMode` as one of: `native` (direct executable), `script` (interpreter + script path), `docker` (container image), or `interactive` (future visualization).

#### Scenario: Native command execution
- **WHEN** a tool has `executionMode: "native"` and `command.executable: "toppic.exe"`
- **THEN** the CommandBuilder SHALL invoke the executable directly

#### Scenario: Script execution
- **WHEN** a tool has `executionMode: "script"` and `command.interpreter: "python"` and `command.executable: "src/nodes/data_loader.py"`
- **THEN** the CommandBuilder SHALL construct `python src/nodes/data_loader.py ...` (or `uv run python ...` if available)

#### Scenario: Unknown execution mode
- **WHEN** a tool has an unsupported executionMode
- **THEN** the system SHALL raise a clear error rather than silently falling back

### Requirement: Parameter serialization contract
The frontend SHALL only serialize parameters that the user has explicitly set or that differ from default values. The backend SHALL use Tool Definition defaults for any parameters not present in the node's params.

#### Scenario: User sets only 2 of 15 parameters
- **WHEN** TopPIC has 15 parameters and the user only changes `activation` and `thread_number`
- **THEN** the saved workflow JSON SHALL only contain `{ "activation": "FILE", "thread_number": "12" }` in the node params

#### Scenario: Backend fills defaults for missing parameters
- **WHEN** a node params contains only `{ "activation": "FILE" }` but the tool defines `thread_number` with default `1`
- **THEN** the CommandBuilder SHALL include `-u 1` in the command using the tool's default
