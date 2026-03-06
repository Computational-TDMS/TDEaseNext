/**
 * Workspace Data API Client
 *
 * API client functions for workspace data access including:
 * - Node output data retrieval
 * - Workspace file browsing
 * - File content preview
 * - Latest execution queries
 */

import type { APIClientLike } from './client'
import type {
  NodeOutputResponse,
  WorkspaceFilesResponse,
  FileContentResponse,
  LatestExecutionResponse,
  GetNodeDataParams,
  GetFileContentParams,
} from '../../types/workspace-data'
import { createError, ErrorCode } from '../../types/errors'

/**
 * Get node output data with optional inline content
 *
 * @param client - APIClient instance
 * @param params - Request parameters including execution_id, node_id, include_data, max_rows
 * @returns Node output data response
 */
export async function getNodeData(
  client: APIClientLike,
  params: GetNodeDataParams
): Promise<NodeOutputResponse> {
  try {
    const { execution_id, node_id, port_id, include_data = false, max_rows } = params
    const queryParams: Record<string, unknown> = {}
    if (port_id) queryParams.port_id = port_id
    if (include_data) queryParams.include_data = true
    if (max_rows !== undefined) queryParams.max_rows = max_rows

    const response = await client.get<NodeOutputResponse>(
      `/api/executions/${execution_id}/nodes/${node_id}/data`,
      queryParams
    )
    return response.data
  } catch (error) {
    throw createError(ErrorCode.API_ERROR, 'Failed to get node data', undefined, error)
  }
}

/**
 * Get node output files list (without data content)
 *
 * @param client - APIClient instance
 * @param execution_id - Execution identifier
 * @param node_id - Node identifier
 * @returns Node output files response
 */
export async function getNodeFiles(
  client: APIClientLike,
  execution_id: string,
  node_id: string
): Promise<NodeOutputResponse> {
  try {
    const response = await client.get<NodeOutputResponse>(
      `/api/executions/${execution_id}/nodes/${node_id}/files`
    )
    return response.data
  } catch (error) {
    throw createError(ErrorCode.API_ERROR, 'Failed to get node files', undefined, error)
  }
}

/**
 * Get the latest completed execution for a workflow
 *
 * @param client - APIClient instance
 * @param workflow_id - Workflow identifier
 * @returns Latest execution metadata
 */
export async function getLatestExecution(
  client: APIClientLike,
  workflow_id: string
): Promise<LatestExecutionResponse> {
  try {
    const response = await client.get<LatestExecutionResponse>(
      `/api/workflows/${workflow_id}/latest-execution`
    )
    return response.data
  } catch (error) {
    throw createError(ErrorCode.API_ERROR, 'Failed to get latest execution', undefined, error)
  }
}

/**
 * Get workspace directory tree structure
 *
 * @param client - APIClient instance
 * @param user_id - User identifier
 * @param workspace_id - Workspace identifier
 * @returns Workspace files tree response
 */
export async function getWorkspaceFiles(
  client: APIClientLike,
  user_id: string,
  workspace_id: string
): Promise<WorkspaceFilesResponse> {
  try {
    const response = await client.get<WorkspaceFilesResponse>(
      `/api/users/${user_id}/workspaces/${workspace_id}/files`
    )
    return response.data
  } catch (error) {
    throw createError(ErrorCode.API_ERROR, 'Failed to get workspace files', undefined, error)
  }
}

/**
 * Get file content preview
 *
 * @param client - APIClient instance
 * @param params - Request parameters including user_id, workspace_id, path, max_rows
 * @returns File content response
 */
export async function getFileContent(
  client: APIClientLike,
  params: GetFileContentParams
): Promise<FileContentResponse> {
  try {
    const { user_id, workspace_id, path, max_rows = 100 } = params
    const response = await client.get<FileContentResponse>(
      `/api/users/${user_id}/workspaces/${workspace_id}/file-content`,
      { path, max_rows }
    )
    return response.data
  } catch (error) {
    throw createError(ErrorCode.API_ERROR, 'Failed to get file content', undefined, error)
  }
}

/**
 * Workspace data API client interface
 */
export const workspaceDataApi = {
  getNodeData,
  getNodeFiles,
  getLatestExecution,
  getWorkspaceFiles,
  getFileContent,
} as const

export type WorkspaceDataApi = typeof workspaceDataApi
