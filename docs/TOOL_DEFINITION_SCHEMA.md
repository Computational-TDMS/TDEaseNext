# Tool Definition Schema

This document describes the JSON schema format for tool definitions in TDEase-Backend, including support for interactive visualization nodes and output schemas.

## Overview

Tool definitions are JSON files stored in `config/tools/` that define:
- **Compute Nodes**: Backend tools that process data (TopFD, ProMex, MSPathFinderT, TopPIC)
- **Interactive Nodes**: Frontend visualization tools that display data and emit selections

## Tool Definition Structure

```json
{
  "id": "tool_id",
  "name": "Tool Display Name",
  "version": "1.0.0",
  "description": "Human-readable description",
  "executionMode": "native|interactive",
  "command": { ... },
  "ports": { ... },
  "parameters": { ... },
  "output": { ... },
  "defaultMapping": { ... },
  "visualization": { ... }
}
```

## Core Fields

### `id` (required)
Unique identifier for the tool. Used in workflow definitions and API calls.
- Type: `string`
- Example: `"topfd"`, `"featuremap_viewer"`

### `name` (required)
Human-readable display name shown in the UI.
- Type: `string`
- Example: `"TopFD"`, `"FeatureMap Viewer"`

### `version` (required)
Tool version string.
- Type: `string`
- Example: `"1.8.0"`

### `description` (required)
Detailed description of the tool's purpose.
- Type: `string`

### `executionMode` (required)
Defines how the tool is executed.
- Type: `string`
- Values:
  - `"native"`: Backend compute tool (executed by workflow engine)
  - `"interactive"`: Frontend visualization tool (skipped in backend execution)

### `command` (required for native tools)
Defines how to execute the tool.

```json
"command": {
  "executable": "path/to/tool.exe"
}
```

For interactive tools, this can be a placeholder:

```json
"command": {
  "executable": "featuremap_viewer"
}
```

## Ports

Defines input and output data connections.

### `ports.inputs`

Array of input port definitions.

```json
"inputs": [
  {
    "id": "input_file",
    "name": "Input File",
    "dataType": "mzml",
    "required": true,
    "accept": ["mzml", "mzxml"],
    "description": "Input data file",
    "flag": "-i",
    "positional": true,
    "positionalOrder": 0,
    "pattern": "{sample}.mzML"
  }
]
```

#### Input Port Fields

- **`id`** (required): Unique port identifier
- **`name`** (required): Display name
- **`dataType`** (required): Expected data type
- **`required`** (optional): Whether input is mandatory (default: `false`)
- **`accept`** (optional): Array of accepted data types
- **`description`** (optional): Port description
- **`flag`** (optional): Command-line flag for native tools
- **`positional`** (optional): Whether this is a positional argument
- **`positionalOrder`** (optional): Order for positional arguments (0-indexed)
- **`pattern`** (optional): File name pattern with `{sample}` placeholder
- **`portKind`** (optional): Port kind for interactive nodes (`"state-in"` for selection inputs)
- **`semanticType`** (optional): Semantic type for state ports (`"state/selection_ids"`)

### `ports.outputs`

Array of output port definitions.

```json
"outputs": [
  {
    "id": "ms1feature",
    "name": "MS1 Feature File",
    "dataType": "feature",
    "pattern": "{sample}_ms1.feature",
    "handle": "ms1feature",
    "provides": ["feature", "ms1feature"],
    "description": "LC-MS feature file",
    "conditional": "always",
    "schema": [
      {"id": "FeatureID", "name": "Feature ID", "type": "string"},
      {"id": "Mass", "name": "Mass (Da)", "type": "number"},
      {"id": "RT", "name": "Retention Time (min)", "type": "number"}
    ]
  }
]
```

#### Output Port Fields

- **`id`** (required): Unique port identifier
- **`name`** (required): Display name
- **`dataType`** (required): Output data type
- **`pattern`** (optional): File name pattern with `{sample}` placeholder
- **`handle`** (optional): Internal handle for the output
- **`provides`** (optional): Array of data types this output provides
- **`description`** (optional): Port description
- **`conditional`** (optional): Condition for output generation
- **`portKind`** (optional): Port kind for interactive nodes (`"state-out"` for selection outputs)
- **`semanticType`** (optional): Semantic type for state ports (`"state/selection_ids"`)
- **`schema`** (optional): Array of column definitions for tabular data (see below)

## Output Schema

The `schema` field defines the structure of tabular output data, enabling interactive nodes to auto-populate column mapping dropdowns.

### Schema Format

```json
"schema": [
  {
    "id": "FeatureID",
    "name": "Feature ID",
    "type": "string"
  },
  {
    "id": "Mass",
    "name": "Mass (Da)",
    "type": "number"
  }
]
```

### Schema Column Fields

- **`id`** (required): Column identifier (matches file header)
- **`name`** (required): Human-readable column name
- **`type`** (required): Data type
  - `"string"`: Text data
  - `"text"`: Long text (sequences, descriptions)
  - `"number"`: Numeric data
  - `"boolean"`: True/false values

### Example Schemas

#### TopFD MS1 Feature Schema

```json
"schema": [
  {"id": "FeatureID", "name": "Feature ID", "type": "string"},
  {"id": "Mass", "name": "Mass (Da)", "type": "number"},
  {"id": "RT", "name": "Retention Time (min)", "type": "number"},
  {"id": "Intensity", "name": "Intensity", "type": "number"},
  {"id": "Charge", "name": "Charge State", "type": "number"},
  {"id": "EValue", "name": "E-Value", "type": "number"},
  {"id": "QValue", "name": "Q-Value", "type": "number"}
]
```

#### ProMex Feature Schema

```json
"schema": [
  {"id": "FeatureID", "name": "Feature ID", "type": "string"},
  {"id": "Mass", "name": "Mass (Da)", "type": "number"},
  {"id": "RT", "name": "Retention Time (min)", "type": "number"},
  {"id": "Intensity", "name": "Intensity", "type": "number"},
  {"id": "Charge", "name": "Charge State", "type": "number"},
  {"id": "EValue", "name": "E-Value", "type": "number"},
  {"id": "QValue", "name": "Q-Value", "type": "number"}
]
```

#### MSPathFinderT PrSM Schema

```json
"schema": [
  {"id": "PrSMID", "name": "PrSM ID", "type": "string"},
  {"id": "Sequence", "name": "Sequence", "type": "text"},
  {"id": "ProteinName", "name": "Protein Name", "type": "text"},
  {"id": "Mass", "name": "Mass (Da)", "type": "number"},
  {"id": "Charge", "name": "Charge", "type": "number"},
  {"id": "EValue", "name": "E-Value", "type": "number"},
  {"id": "QValue", "name": "Q-Value", "type": "number"},
  {"id": "Score", "name": "Score", "type": "number"}
]
```

#### TopPIC HTML Schema

```json
"schema": [
  {"id": "PrSMID", "name": "PrSM ID", "type": "string"},
  {"id": "Sequence", "name": "Sequence", "type": "text"},
  {"id": "Proteoform", "name": "Proteoform", "type": "text"},
  {"id": "Mass", "name": "Mass (Da)", "type": "number"},
  {"id": "EValue", "name": "E-Value", "type": "number"},
  {"id": "QValue", "name": "Q-Value", "type": "number"}
]
```

## Interactive Node Specific Fields

### `defaultMapping`

Defines default column-to-axis mappings for visualization.

```json
"defaultMapping": {
  "xAxis": "RT",
  "yAxis": "Mass",
  "colorAxis": "Intensity"
}
```

- **`xAxis`**: Default column for X-axis
- **`yAxis`**: Default column for Y-axis
- **`colorAxis`**: Default column for color coding
- **`sizeAxis`**: Default column for point sizing (optional)

### `visualization`

Defines visualization configuration for interactive nodes.

```json
"visualization": {
  "type": "featuremap",
  "dataSource": "file",
  "filePath": "{sample}_ms1.feature",
  "columns": [
    {
      "id": "x",
      "name": "RT (min)",
      "type": "number",
      "visible": true,
      "sortable": false,
      "filterable": false
    }
  ],
  "config": {
    "plotType": "scatter",
    "xAxisLabel": "RT (min)",
    "yAxisLabel": "Mass (Da)",
    "colorScale": "viridis",
    "pointSize": 3,
    "opacity": 0.7,
    "zoomEnabled": true,
    "panEnabled": true,
    "tooltipEnabled": true,
    "exportFormats": ["png", "svg", "csv"]
  }
}
```

#### Visualization Types

- **`featuremap`**: Scatter plot (RT vs Mass)
- **`spectrum`**: Mass spectrum (m/z vs Intensity)
- **`table`**: Tabular data viewer
- **`html`**: HTML fragment viewer

## Parameters

Defines tool parameters and their UI configuration.

```json
"parameters": {
  "min_mass": {
    "flag": "-minMass",
    "type": "value",
    "label": "Min Mass",
    "description": "Minimum mass in Da",
    "group": "basic",
    "default": "2000"
  },
  "feature_map": {
    "flag": "-featureMap",
    "type": "boolean",
    "label": "Feature Heatmap",
    "description": "Output the feature heatmap PNG",
    "group": "basic",
    "default": true
  },
  "activation": {
    "flag": "-a",
    "type": "choice",
    "label": "Activation",
    "description": "Activation type",
    "group": "basic",
    "default": "21.0",
    "choices": ["CID", "ETD", "HCD"]
  }
}
```

### Parameter Types

- **`value`**: Text/numeric input
- **`boolean`**: Checkbox/toggle
- **`choice`**: Dropdown selection

### Parameter Fields

- **`flag`**: Command-line flag
- **`type`**: Parameter type
- **`label`**: Display label
- **`description`**: Parameter description
- **`group`**: UI group (`"basic"` or `"advanced"`)
- **`default`**: Default value
- **`choices`**: Array of choices (for `type: "choice"`)
- **`constraints`**: Value constraints (min, max, etc.)

## Output Configuration

```json
"output": {
  "flagSupported": true,
  "flag": "-o",
  "flagValue": "."
}
```

## Complete Examples

### Compute Tool (TopFD)

```json
{
  "id": "topfd",
  "name": "TopFD",
  "version": "1.8.0",
  "description": "TopFD: Deconvolute mass spectra and generate MSAlign files",
  "executionMode": "native",
  "command": {
    "executable": "D:\\Projects\\TDEase-Backend\\toppic-windows-1.8.0\\topfd.exe"
  },
  "ports": {
    "inputs": [
      {
        "id": "input_files",
        "name": "mzML Files",
        "dataType": "mzml",
        "required": true,
        "accept": ["mzml", "mzxml"],
        "positional": true,
        "positionalOrder": 0,
        "pattern": "{sample}.mzML"
      }
    ],
    "outputs": [
      {
        "id": "ms1feature",
        "name": "MS1 Feature File",
        "dataType": "feature",
        "pattern": "{sample}_ms1.feature",
        "handle": "ms1feature",
        "provides": ["feature", "ms1feature"],
        "description": "LC-MS feature file containing MS1 features",
        "schema": [
          {"id": "FeatureID", "name": "Feature ID", "type": "string"},
          {"id": "Mass", "name": "Mass (Da)", "type": "number"},
          {"id": "RT", "name": "Retention Time (min)", "type": "number"},
          {"id": "Intensity", "name": "Intensity", "type": "number"},
          {"id": "Charge", "name": "Charge State", "type": "number"},
          {"id": "EValue", "name": "E-Value", "type": "number"},
          {"id": "QValue", "name": "Q-Value", "type": "number"}
        ]
      }
    ]
  },
  "parameters": { ... },
  "output": {
    "flagSupported": false
  }
}
```

### Interactive Tool (FeatureMap Viewer)

```json
{
  "id": "featuremap_viewer",
  "name": "FeatureMap Viewer",
  "version": "1.0.0",
  "description": "Interactive scatter plot visualization for MS1 feature data (RT vs Mass)",
  "executionMode": "interactive",
  "command": {
    "executable": "featuremap_viewer"
  },
  "ports": {
    "inputs": [
      {
        "id": "ms1feature_file",
        "name": "MS1 Feature File",
        "dataType": "ms1feature",
        "required": true,
        "accept": ["ms1feature", "ms1ft", "feature"],
        "description": "MS1 feature file (TopPIC .ms1.feature or ProMex .ms1ft)"
      },
      {
        "id": "selection_in",
        "name": "Selection In",
        "dataType": "selection",
        "required": false,
        "description": "Optional feature selection propagated from upstream interactive viewers",
        "portKind": "state-in",
        "semanticType": "state/selection_ids"
      }
    ],
    "outputs": [
      {
        "id": "selection",
        "name": "Selection",
        "dataType": "selection",
        "required": false,
        "description": "Selected features for downstream processing",
        "portKind": "state-out",
        "semanticType": "state/selection_ids"
      }
    ]
  },
  "defaultMapping": {
    "xAxis": "RT",
    "yAxis": "Mass",
    "colorAxis": "Intensity"
  },
  "parameters": { ... },
  "output": {
    "flagSupported": false
  },
  "visualization": { ... }
}
```

## Best Practices

1. **Schema Definitions**: Always define schemas for outputs that will be consumed by interactive viewers
2. **Default Mappings**: Provide sensible defaults for visualization axes
3. **Data Types**: Use appropriate data types (`number` vs `string`) for proper sorting/filtering
4. **Descriptive Names**: Use human-readable names for columns and parameters
5. **Backward Compatibility**: Schema field is optional - maintain compatibility with existing tools
6. **Port Kinds**: Use `portKind` and `semanticType` for interactive node state ports
7. **Parameter Groups**: Group parameters into `"basic"` and `"advanced"` for better UX

## Validation

Tool definitions should be validated against the schema before deployment. Use the validation utility:

```bash
python scripts/validate_tool_definitions.py
```

This will check:
- Required fields are present
- Data types are valid
- Schemas are properly formatted
- Parameter configurations are valid
