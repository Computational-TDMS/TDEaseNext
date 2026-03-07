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
  /** Relative path from execution workspace (when available) */
  relative_path?: string;
  /** File size in bytes */
  file_size: number;
  /** Whether the file exists on disk */
  exists: boolean;
  /** Whether the output path is a directory */
  is_directory?: boolean;
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

export interface TopMSVSequenceModification {
  kind: string;
  label: string;
  ptm_type: string;
  left_position: number | null;
  right_position: number | null;
  annotation: string;
  mono_mass: number | null;
  unimod: string;
}

export interface TopMSVIon {
  ion_type: string;
  ion_position: number | null;
  display_position: number | null;
  theoretical_mass: number | null;
  mass_error: number | null;
  ppm: number | null;
  label: string;
}

export interface TopMSVMatchedPeak {
  peak_id: number | null;
  spec_id: number | null;
  monoisotopic_mass: number | null;
  monoisotopic_mz: number | null;
  intensity: number | null;
  charge: number | null;
  matched_ion_count: number;
  matched_ions: TopMSVIon[];
  matched_ion_labels: string;
}

export interface TopMSVRawPeak {
  index: number;
  mz: number;
  intensity: number;
}

export interface TopMSVEnvelopeSummary {
  id: number | null;
  mono_mass: number | null;
  charge: number | null;
  peak_count: number;
}

export interface TopMSVPrsmDataResponse {
  execution_id?: string | null;
  workflow_id?: string;
  node_id: string;
  port_id: string;
  prsm_id: number;
  resolution?: Record<string, unknown>;
  protein_accession: string;
  protein_description: string;
  source: {
    html_root: string;
    prsm_file: string;
    spectrum_file: string | null;
  };
  ms_header: {
    spectrum_file_name: string;
    ms1_ids: number[];
    ms1_scans: number[];
    spectrum_ids: number[];
    scans: number[];
    precursor_mono_mass: number | null;
    precursor_charge: number | null;
    precursor_mz: number | null;
    feature_inte: number | null;
  };
  sequence: {
    value: string;
    annotated: string;
    first_position: number | null;
    last_position: number | null;
    protein_length: number | null;
    breakpoints: number[];
    modifications: TopMSVSequenceModification[];
  };
  ms2: {
    available_spectrum_ids: number[];
    selected_spectrum_id: number | null;
    selected_scan_id: number | null;
    raw_peaks: TopMSVRawPeak[];
    raw_peak_count: number;
    envelopes: TopMSVEnvelopeSummary[];
    target_mz: number | null;
    min_mz: number | null;
    max_mz: number | null;
    retention_time: number | null;
    matched_peaks: TopMSVMatchedPeak[];
  };
}

export interface GetTopMSVPrsmParams {
  execution_id?: string;
  workflow_id?: string;
  node_id: string;
  prsm_id: number;
  spectrum_id?: number;
  port_id?: string;
  sample?: string;
}
