/**
 * Workspace Data Types
 *
 * Type definitions for workspace data access APIs including:
 * - Node output data retrieval
 * - Workspace file browsing
 * - File content preview
 */

/**
 * Table data structure for tabular file contents
 */
export interface TableData {
  /** Column names from the first row of the file */
  columns: string[];
  /** Data rows (array of objects with column name -> value mappings) */
  rows: Record<string, string>[];
  /** Total number of rows in the file */
  total_rows: number;
  /** Number of rows included in this response (for preview) */
  preview_rows?: number;
}

/**
 * Column schema definition from tool/output metadata
 */
export interface ColumnSchema {
  name: string;
  type: string;
  description?: string;
  optional?: boolean;
}

/**
 * Output entry for a single port
 */
export interface OutputEntry {
  /** Port identifier (e.g., "ms1ft", "output") */
  port_id: string;
  /** Data type identifier (often the file extension) */
  data_type: string;
  /** File name */
  file_name: string;
  /** File path relative to workspace */
  file_path: string;
  /** File size in bytes */
  file_size: number;
  /** Whether the file exists on disk */
  exists: boolean;
  /** Whether the file can be parsed as tabular data */
  parseable: boolean;
  /** Optional schema for this output port */
  schema?: ColumnSchema[];
  /** Parsed table data (only included when include_data=true and file is parseable) */
  data: TableData | null;
}

/**
 * Response for node output data endpoint
 */
export interface NodeOutputResponse {
  /** Execution identifier */
  execution_id: string;
  /** Node identifier */
  node_id: string;
  /** Array of output entries (one per output port) */
  outputs: OutputEntry[];
}

/**
 * File tree node for directory structure
 */
export interface FileTreeNode {
  /** File or directory name */
  name: string;
  /** Type: "file" or "directory" */
  type: "file" | "directory";
  /** Path relative to workspace root */
  path: string;
  /** File size in bytes (only for files) */
  size?: number;
  /** File extension (only for files) */
  extension?: string;
  /** Last modified timestamp (only for files) */
  modified?: number;
  /** Child nodes (only for directories) */
  children?: FileTreeNode[];
}

/**
 * Response for workspace files endpoint
 */
export interface WorkspaceFilesResponse {
  /** User identifier */
  user_id: string;
  /** Workspace identifier */
  workspace_id: string;
  /** Absolute workspace path */
  workspace_path: string;
  /** Directory tree structure */
  tree: FileTreeNode[];
}

/**
 * File content response types
 */
export type FileContentType = "tabular" | "text" | "binary";

/**
 * Response for file content endpoint
 */
export interface FileContentResponse {
  /** File path relative to workspace */
  file_path: string;
  /** File name */
  file_name: string;
  /** File size in bytes */
  file_size: number;
  /** File type classification */
  file_type: FileContentType;
  /** File content (null for binary, object for tabular, string for text) */
  content: TableData | string | null;
}

/**
 * Latest execution metadata
 */
export interface LatestExecutionResponse {
  /** Execution identifier */
  id: string;
  /** Workflow identifier */
  workflow_id: string;
  /** Sample identifier */
  sample_id: string | null;
  /** Execution status */
  status: string;
  /** Start timestamp */
  start_time: string;
  /** End timestamp */
  end_time: string;
  /** Workspace path */
  workspace_path: string;
}

/**
 * API request parameters
 */
export interface GetNodeDataParams {
  execution_id: string;
  node_id: string;
  port_id?: string;
  include_data?: boolean;
  max_rows?: number;
}

export interface GetFileContentParams {
  user_id: string;
  workspace_id: string;
  path: string;
  max_rows?: number;
}
