<template>
  <div class="file-explorer">
    <!-- Header -->
    <div class="file-explorer-header">
      <div class="header-title">
        <CatppuccinIcon name="FolderOpened" />
        <span>文件浏览器</span>
      </div>
      <div class="header-actions">
        <el-button
          size="small"
          text
          @click="handleRefresh"
          :loading="loading"
          title="刷新"
        >
          <CatppuccinIcon v-if="!loading" name="Refresh" />
        </el-button>
        <el-button
          size="small"
          text
          @click="handleExpandAll"
          title="展开全部"
        >
          <CatppuccinIcon name="FolderOpened" />
        </el-button>
        <el-button
          size="small"
          text
          @click="handleCollapseAll"
          title="折叠全部"
        >
          <CatppuccinIcon name="Folder" />
        </el-button>
      </div>
    </div>

    <!-- Workspace Info -->
    <div class="workspace-info">
      <div class="info-item">
        <span class="info-label">用户:</span>
        <span class="info-value">{{ workspaceStore.currentUserId }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">工作区:</span>
        <span class="info-value">{{ workspaceStore.currentWorkspaceId }}</span>
      </div>
    </div>

    <!-- Error Message -->
    <el-alert
      v-if="workspaceStore.error"
      :title="workspaceStore.error"
      type="error"
      :closable="false"
      show-icon
      style="margin: 8px"
    />

    <!-- File Tree -->
    <div class="file-tree-container">
      <div v-if="loading && fileTree.length === 0" class="loading-state">
        <CatppuccinIcon name="Loading" class="is-loading" />
        <span>加载中...</span>
      </div>
      <div v-else-if="fileTree.length === 0" class="empty-state">
        <CatppuccinIcon name="Document" />
        <span>工作区为空</span>
      </div>
      <el-tree
        v-else
        :data="fileTree"
        :props="treeProps"
        :expand-on-click-node="false"
        :highlight-current="true"
        node-key="path"
        :default-expanded-keys="Array.from(workspaceStore.expandedPaths)"
        @node-click="handleNodeClick"
        class="file-tree"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <CatppuccinIcon v-if="data.type === 'directory'" :name="node.expanded ? 'FolderOpened' : 'Folder'" />
            <CatppuccinIcon v-else name="Document" />
            <span class="node-label">{{ data.name }}</span>
            <span v-if="data.type === 'file'" class="node-size">
              {{ formatFileSize(data.size || 0) }}
            </span>
          </div>
        </template>
      </el-tree>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import type { FileTreeNode } from '@/types/workspace-data'
import { CatppuccinIcon } from '@/components/icons'

const workspaceStore = useWorkspaceStore()

// Computed
const loading = computed(() => workspaceStore.loading)
const fileTree = computed(() => workspaceStore.fileTree)

const treeProps = {
  children: 'children',
  label: 'name',
}

// Methods
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

function handleNodeClick(data: FileTreeNode) {
  if (data.type === 'directory') {
    workspaceStore.toggleExpand(data.path)
  } else {
    workspaceStore.selectFile(data.path)
  }
}

function handleRefresh() {
  workspaceStore.loadFileTree()
}

function handleExpandAll() {
  workspaceStore.expandAll()
}

function handleCollapseAll() {
  workspaceStore.collapseAll()
}

// Lifecycle
onMounted(() => {
  workspaceStore.loadFileTree()
})
</script>

<style scoped>
.file-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--ctp-mantle);
  border-right: 1px solid var(--ctp-surface0);
}

.file-explorer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--ctp-surface0);
  background: var(--ctp-base);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--ctp-text);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.workspace-info {
  padding: 8px 12px;
  background: var(--ctp-base);
  border-bottom: 1px solid var(--ctp-surface0);
  font-size: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  color: var(--ctp-subtext0);
  font-weight: 500;
}

.info-value {
  color: var(--ctp-text);
}

.file-tree-container {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--ctp-overlay0);
  gap: 12px;
}

.loading-state .el-icon,
.empty-state .el-icon {
  color: var(--icon-muted);
}

.loading-state .el-icon {
  font-size: 32px;
}

.empty-state .el-icon {
  font-size: 48px;
}

.file-tree {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 28px;
  padding: 0 4px;
  border-radius: 4px;
}

:deep(.el-tree-node__content:hover) {
  background: var(--ctp-surface0);
}

:deep(.el-tree-node__content.is-current) {
  background: color-mix(in srgb, var(--ctp-blue) 15%, transparent);
  color: var(--ctp-blue);
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: var(--ctp-text);
}

.node-size {
  font-size: 11px;
  color: var(--ctp-subtext0);
  margin-left: auto;
  flex-shrink: 0;
}
</style>
