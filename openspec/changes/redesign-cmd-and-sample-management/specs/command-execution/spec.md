## ADDED Requirements

### Requirement: Pipeline-based command construction
CommandBuilder SHALL construct shell commands through a fixed pipeline of steps (filter → executable → output-flag → param-flags → positional-args), driven entirely by the Tool Definition, without branching on tool_type or tool_id.

#### Scenario: Native command tool (e.g. TopPIC)
- **WHEN** a node with `executionMode: "native"` and `command.executable: "toppic.exe"` is executed
- **THEN** the command SHALL be constructed as `<executable> <param-flags> <positional-inputs>` with no `-o` flag (since `output.flagSupported` is `false`)

#### Scenario: Script tool (e.g. data_loader)
- **WHEN** a node with `executionMode: "script"` and `command.interpreter: "python"` is executed
- **THEN** the command SHALL be constructed as `<interpreter> <script-path> <input-flags> <output-flag> <param-flags>`

#### Scenario: Tool with output flag value (e.g. msconvert)
- **WHEN** a tool has `output.flagSupported: true` and `output.flagValue: "."`
- **THEN** the command SHALL include `<output.flag> <output.flagValue>` (e.g. `-o .`)

### Requirement: Empty parameter filtering at pipeline entry
The system SHALL filter out null, empty string, and case-insensitive "none" parameter values as the first step of the command construction pipeline, before any flag mapping occurs.

#### Scenario: Parameter with null value
- **WHEN** a node parameter has value `null`
- **THEN** the parameter SHALL be completely omitted from the command (no flag, no value)

#### Scenario: Parameter with empty string value
- **WHEN** a node parameter has value `""` or `"  "`
- **THEN** the parameter SHALL be completely omitted from the command

#### Scenario: Parameter with string "None"
- **WHEN** a node parameter has value `"None"` or `"none"` or `"NONE"`
- **THEN** the parameter SHALL be completely omitted from the command

#### Scenario: Parameter with false boolean value
- **WHEN** a boolean-type parameter has value `false`
- **THEN** the boolean flag SHALL NOT appear in the command

#### Scenario: Parameter with valid value
- **WHEN** a parameter has a non-empty, non-null value (e.g. `"FILE"`, `"10"`, `true`)
- **THEN** the parameter SHALL be included in the command with its configured flag

### Requirement: Positional parameter ordering
The system SHALL place positional input arguments at the end of the command, ordered by each input port's `positionalOrder` field in the Tool Definition.

#### Scenario: TopPIC with two positional inputs
- **WHEN** TopPIC has positional inputs `fasta_file` (order 0) and `msalign_files` (order 1)
- **THEN** the command SHALL end with `<fasta_file_path> <msalign_file_path>`

#### Scenario: TopFD with single positional input
- **WHEN** TopFD has positional input `input_files` (order 0)
- **THEN** the command SHALL end with `<input_file_path>`

### Requirement: No implicit output path for positional-input tools
The system SHALL NOT add an output path flag (`-o`, `--output`) to tools where `output.flagSupported` is `false`, regardless of whether output_paths are resolved.

#### Scenario: TopPIC execution
- **WHEN** TopPIC is executed and `output.flagSupported` is `false`
- **THEN** no `-o` flag SHALL appear in the command

#### Scenario: MSConvert execution
- **WHEN** MSConvert is executed and `output.flagSupported` is `true`
- **THEN** the `-o .` flag SHALL appear in the command

### Requirement: Shell quoting for paths with spaces
The system SHALL properly quote file paths that contain spaces, using double quotes on Windows and `shlex.quote` on Unix.

#### Scenario: Path with spaces on Windows
- **WHEN** a file path contains spaces (e.g. `C:\Program Files\tool.exe`) and the OS is Windows
- **THEN** the path SHALL be wrapped in double quotes in the command string

#### Scenario: Path without spaces
- **WHEN** a file path does not contain spaces
- **THEN** the path SHALL NOT be wrapped in quotes
