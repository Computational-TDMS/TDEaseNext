# Node Data API Documentation

## Overview

The Node Data API provides endpoints for retrieving data from workflow node outputs, specifically designed for interactive visualization tools. This API supports:

- Column schema metadata retrieval
- Paginated row data access
- Row ID filtering for specific data points
- Aggressive caching for performance

## Base URL

```
/api
```

## Endpoints

### 1. Get Node Data Schema

Retrieve column schema metadata for a node's output data.

**Endpoint:** `GET /executions/{execution_id}/nodes/{node_id}/data/schema`

**Path Parameters:**
- `execution_id` (string): The execution ID
- `node_id` (string): The node ID

**Query Parameters:**
- `port_id` (string, optional): Output port ID (if node has multiple outputs)

**Response (200 OK):**

```json
{
  "execution_id": "exec_123",
  "node_id": "node_456",
  "port_id": "ms1feature",
  "schema": [
    {
      "name": "feature_id",
      "type": "number",
      "description": "Unique feature identifier",
      "optional": false
    },
    {
      "name": "mz",
      "type": "number",
      "description": "Mass-to-charge ratio (m/z)",
      "optional": false
    },
    {
      "name": "intensity",
      "type": "number",
      "description": "Peak intensity",
      "optional": false
    }
  ]
}
```

**Column Types:**
- `string`: Text data
- `number`: Numeric data (integers or floats)
- `boolean`: True/false values
- `datetime`: Date/time values

**Error Responses:**
- `404 Not Found`: Execution or node not found
- `400 Bad Request`: Output file not available or not parseable
- `500 Internal Server Error`: Server error

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/executions/exec_123/nodes/node_456/data/schema?port_id=ms1feature"
```

---

### 2. Get Node Data Rows

Retrieve data rows from a node's output with pagination and filtering support.

**Endpoint:** `GET /executions/{execution_id}/nodes/{node_id}/data/rows`

**Path Parameters:**
- `execution_id` (string): The execution ID
- `node_id` (string): The node ID

**Query Parameters:**
- `port_id` (string, optional): Output port ID (if node has multiple outputs)
- `offset` (integer, default: 0): Row offset for pagination
- `limit` (integer, default: 100, max: 10000): Maximum rows to return
- `row_ids` (string, optional): Comma-separated list of row indices to filter

**Response (200 OK):**

```json
{
  "execution_id": "exec_123",
  "node_id": "node_456",
  "port_id": "ms1feature",
  "columns": ["feature_id", "mz", "rt", "intensity"],
  "rows": [
    {
      "feature_id": "1",
      "mz": "500.1234",
      "rt": "120.5",
      "intensity": "1000000"
    },
    {
      "feature_id": "2",
      "mz": "600.2345",
      "rt": "130.2",
      "intensity": "500000"
    }
  ],
  "total_rows": 1500,
  "offset": 0,
  "limit": 100
}
```

**Error Responses:**
- `404 Not Found`: Execution, node, or output file not found
- `400 Bad Request`: File not parseable or invalid row_ids format
- `500 Internal Server Error`: Server error

**Example Requests:**

Get first 100 rows:
```bash
curl -X GET "http://localhost:8000/api/executions/exec_123/nodes/node_456/data/rows"
```

Get rows with pagination:
```bash
curl -X GET "http://localhost:8000/api/executions/exec_123/nodes/node_456/data/rows?offset=100&limit=50"
```

Get specific rows by ID:
```bash
curl -X GET "http://localhost:8000/api/executions/exec_123/nodes/node_456/data/rows?row_ids=0,1,2,10,20"
```

---

## Caching

The API implements aggressive caching to improve performance:

- **Cache Key**: `{execution_id}:{node_id}:{port_id}`
- **TTL**: 1 hour (default)
- **Cache Size**: 128 entries (LRU eviction)

### Cache Invalidation

The cache is automatically invalidated when:
- A workflow is re-executed (all entries for that execution are cleared)
- The TTL expires (1 hour of inactivity)

### Cache Statistics

You can check cache stats through the cache service (not exposed via API currently).

---

## Supported File Formats

The API can parse and serve data from the following tabular formats:

- TSV (Tab-Separated Values)
- CSV (Comma-Separated Values)
- TXT (Text files with consistent delimiter)
- `.ms1ft` (MS1 feature files)
- `.feature` (Feature files)

**Binary files are not supported** for data retrieval (e.g., .mzML, .raw).

---

## Integration with Interactive Tools

### Tool Definition

Interactive tools should define:

1. **Execution Mode**: `"executionMode": "interactive"`
2. **Default Mapping**: `"defaultMapping": { "x": "col1", "y": "col2" }`
3. **Input Ports**: Define expected data types

Example:
```json
{
  "id": "featuremap_viewer",
  "name": "Feature Map Viewer",
  "executionMode": "interactive",
  "defaultMapping": {
    "x": "mz",
    "y": "rt",
    "color": "intensity"
  },
  "ports": {
    "inputs": [
      {
        "id": "feature_data",
        "dataType": "feature",
        "required": true
      }
    ],
    "outputs": []
  }
}
```

### Workflow Execution

Interactive nodes are **automatically skipped** during workflow execution:

- Status marked as `"skipped"` in execution logs
- No output files are generated
- Downstream compute nodes can still connect (edges bypass interactive nodes)

### Frontend Integration

1. **Query Schema**: Call `/data/schema` to get column metadata
2. **Apply Mapping**: Use `defaultMapping` from tool definition as initial mapping
3. **Fetch Data**: Call `/data/rows` with pagination to display data
4. **Handle Updates**: Re-fetch data when workflow is re-executed

---

## Performance Considerations

1. **Use Pagination**: Always use `offset` and `limit` for large datasets
2. **Cache Wisely**: Schema data is cached; use it to avoid redundant calls
3. **Filter by ID**: Use `row_ids` for specific data points instead of fetching all rows
4. **Limit Requests**: Maximum 10,000 rows per request

---

## Error Handling

All errors return a JSON response:

```json
{
  "detail": "Error message description"
}
```

Common error scenarios:
- File not found → Check execution completed successfully
- File not parseable → Verify file format is supported
- Invalid parameters → Check query parameter types and ranges

---

## Future Enhancements

Planned features:
- Streaming responses for very large datasets
- Column filtering (select specific columns)
- Data aggregation endpoints (min, max, avg, etc.)
- Export endpoints (download as CSV/TSV)
