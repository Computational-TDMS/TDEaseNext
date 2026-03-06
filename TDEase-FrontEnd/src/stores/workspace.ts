/**
 * Workspace Store
 * 
 * Manages workspace file browser state and file content preview
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { FileTreeNode, FileContentResponse } from '@/types/workspace-data'
import { workspaceDataApi } from '@/services/api/workspace-data'
import type { APIClientLike } from '@/services/api/client'

export const useWorkspaceStore = defineStore('workspace', () => {
  // State
  const currentUserId = ref<string>('test_user')
  const currentWorkspaceId = ref<string>('test_workspace')
  const fileTree = ref<FileTreeNode[]>([])
  const expandedPaths = ref<Set<string>>(new Set())
  const selectedFilePath = ref<string | null>(null)
  const fileContent = ref<FileContentResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const apiClient = ref<APIClientLike | null>(null)

  // Getters
  const workspacePath = computed(() => {
    return fileContent.value?.file_path ? 
      fileContent.value.file_path.split('/').slice(0, -1).join('/') : 
      ''
  })

  const isPathExpanded = computed(() => (path: string) => {
    return expandedPaths.value.has(path)
  })

  // Actions

  /**
   * Set API client for data fetching
   */
  function setApiClient(client: APIClientLike) {
    apiClient.value = client
  }

  /**
   * Set current workspace context
   */
  function setWorkspace(userId: string, workspaceId: string) {
    currentUserId.value = userId
    currentWorkspaceId.value = workspaceId
    // Clear previous state
    fileTree.value = []
    expandedPaths.value.clear()
    selectedFilePath.value = null
    fileContent.value = null
  }

  /**
   * Load workspace file tree
   */
  async function loadFileTree() {
    if (!apiClient.value) {
      console.error('[WorkspaceStore] API client not set')
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await workspaceDataApi.getWorkspaceFiles(
        apiClient.value,
        currentUserId.value,
        currentWorkspaceId.value
      )
      fileTree.value = response.tree || []
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load file tree'
      console.error('[WorkspaceStore] Failed to load file tree:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Toggle directory expansion
   */
  function toggleExpand(path: string) {
    if (expandedPaths.value.has(path)) {
      expandedPaths.value.delete(path)
    } else {
      expandedPaths.value.add(path)
    }
  }

  /**
   * Expand all directories
   */
  function expandAll() {
    const allPaths = new Set<string>()
    const collectPaths = (nodes: FileTreeNode[]) => {
      for (const node of nodes) {
        if (node.type === 'directory') {
          allPaths.add(node.path)
          if (node.children) {
            collectPaths(node.children)
          }
        }
      }
    }
    collectPaths(fileTree.value)
    expandedPaths.value = allPaths
  }

  /**
   * Collapse all directories
   */
  function collapseAll() {
    expandedPaths.value.clear()
  }

  /**
   * Select a file and load its content
   */
  async function selectFile(path: string) {
    if (!apiClient.value) {
      console.error('[WorkspaceStore] API client not set')
      return
    }

    selectedFilePath.value = path
    loading.value = true
    error.value = null

    try {
      const response = await workspaceDataApi.getFileContent(apiClient.value, {
        user_id: currentUserId.value,
        workspace_id: currentWorkspaceId.value,
        path,
        max_rows: 100
      })
      fileContent.value = response
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load file content'
      console.error('[WorkspaceStore] Failed to load file content:', err)
      fileContent.value = null
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear file selection
   */
  function clearSelection() {
    selectedFilePath.value = null
    fileContent.value = null
  }

  return {
    // State
    currentUserId,
    currentWorkspaceId,
    fileTree,
    expandedPaths,
    selectedFilePath,
    fileContent,
    loading,
    error,

    // Getters
    workspacePath,
    isPathExpanded,

    // Actions
    setApiClient,
    setWorkspace,
    loadFileTree,
    toggleExpand,
    expandAll,
    collapseAll,
    selectFile,
    clearSelection,
  }
})
