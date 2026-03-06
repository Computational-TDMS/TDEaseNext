/**
 * Data processing and visualization framework (Preparation / Section 8)
 *
 * 8.1 Extensible data processing architecture
 * 8.2 TSV data handling interfaces (placeholder)
 * 8.5 Amino acid sequence editing framework (placeholder)
 */

/** 8.1 Pipeline stage: one step in a data processing pipeline */
export interface DataPipelineStage {
  id: string
  type: string
  config: Record<string, unknown>
  inputs: string[]
  outputs: string[]
}

/** 8.1 Data processing pipeline definition (extensible) */
export interface DataPipeline {
  id: string
  name: string
  stages: DataPipelineStage[]
  metadata?: Record<string, unknown>
}

/** 8.1 Result of running a pipeline stage */
export interface PipelineStageResult {
  stageId: string
  outputPaths: string[]
  metadata?: Record<string, unknown>
}

/** 8.1 Processor interface for pluggable data processors */
export interface IDataProcessor {
  readonly type: string
  process(input: DataProcessorInput): Promise<DataProcessorOutput>
}

export interface DataProcessorInput {
  filePaths: string[]
  config: Record<string, unknown>
  context?: Record<string, unknown>
}

export interface DataProcessorOutput {
  success: boolean
  outputPaths?: string[]
  error?: string
  metadata?: Record<string, unknown>
}

/** 8.2 TSV data handling (placeholder) */
export interface TSVLoadOptions {
  path: string
  delimiter?: string
  hasHeader?: boolean
  maxRows?: number
  encoding?: string
}

export interface TSVParseResult {
  columns: string[]
  rows: string[][]
  totalRows: number
  sourcePath: string
}

/** 8.2 TSV loader interface – to be implemented when TSV support is added */
export interface ITSVDataHandler {
  load(options: TSVLoadOptions): Promise<TSVParseResult>
  parseChunk?(raw: string, options?: { delimiter?: string }): string[][]
}

/** 8.5 Amino acid sequence editing (placeholder) */
export interface SequenceEditorState {
  sequence: string
  cursorPosition: number
  selection?: { start: number; end: number }
  annotations?: SequenceAnnotation[]
}

export interface SequenceAnnotation {
  start: number
  end: number
  type: string
  label?: string
  metadata?: Record<string, unknown>
}

/** 8.5 Sequence editor interface – for future amino acid / peptide editing */
export interface ISequenceEditor {
  getState(): SequenceEditorState
  setState(state: Partial<SequenceEditorState>): void
  validate?(sequence: string): { valid: boolean; errors?: string[] }
}
