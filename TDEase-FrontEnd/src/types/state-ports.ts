export type SemanticType =
  | 'data/table'
  | 'data/spectrum'
  | 'state/selection_ids'
  | 'state/range'
  | 'state/viewport'
  | 'state/annotation'
  | 'state/sequence'

export interface StatePayload {
  semanticType: SemanticType | string
  data: unknown
  timestamp: number
  sourceNodeId?: string
  portId?: string
}
