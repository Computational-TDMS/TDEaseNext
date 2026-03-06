<template>
  <div class="execution-page">
    <!-- 页面头部 -->
    <div class="execution-header">
      <div class="header-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>
            <router-link to="/workflow">工作流编辑器</router-link>
          </el-breadcrumb-item>
          <el-breadcrumb-item>
            <router-link to="/workflow">执行监控</router-link>
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="header-right">
        <el-button @click="refreshStatus" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
        <el-button v-if="canStop" @click="stopExecution" type="danger">
          停止执行
        </el-button>
      </div>
    </div>

    <!-- 执行信息 -->
    <div class="execution-info" v-if="execution">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">
          {{ execution.executionId }}
        </el-descriptions-item>
        <el-descriptions-item label="工作流">
          {{ workflowTitle }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag
            :type="getStatusTagType(execution.status)"
            :effect="getStatusTagEffect(execution.status)"
          >
            {{ getStatusText(execution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="进度">
          <el-progress :percentage="execution.progress" />
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(execution.startTime) }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间" v-if="execution.endTime">
          {{ formatDateTime(execution.endTime) }}
        </el-descriptions-item>
        <el-descriptions-item label="持续时间" v-if="execution.startTime && execution.endTime">
          {{ calculateDuration(execution.startTime, execution.endTime) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 实时日志 -->
    <div class="execution-logs" v-if="logs.length > 0">
      <div class="logs-header">
        <h3>执行日志</h3>
        <el-radio-group v-model="logLevel" size="small">
          <el-radio-button label="全部" value="all" />
          <el-radio-button label="信息" value="info" />
          <el-radio-button label="警告" value="warning" />
          <el-radio-button label="错误" value="error" />
        </el-radio-group>
        <div class="logs-actions">
          <el-button @click="clearLogs" size="small" type="info">
            清空日志
          </el-button>
          <el-button @click="downloadLogs" size="small" type="primary">
            下载日志
          </el-button>
        </div>
      </div>
      <div class="logs-content">
        <el-timeline>
          <el-timeline-item
            v-for="(log, index) in filteredLogs"
            :key="`${log.timestamp}-${index}`"
            :type="getLogItemType(log.level)"
            :timestamp="log.timestamp"
            placement="top"
          >
            <template #dot>
              <el-icon v-if="log.level === 'error'" color="#f56c6c" :size="16">
                <Warning />
              </el-icon>
              <el-icon v-else-if="log.level === 'warning'" color="#e6a23c" :size="16">
                <InfoFilled />
              </el-icon>
              <el-icon v-else color="#67c23a" :size="16">
                <SuccessFilled />
              </el-icon>
            </template>
            <template #content>
              <div class="log-entry">
                <div class="log-time">
                  {{ formatTime(log.timestamp) }}
                </div>
                <div class="log-message">
                  {{ log.message }}
                </div>
              </div>
            </template>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-if="!execution">
      <el-empty description="暂无执行中的工作流">
        <el-icon :size="64" color="#909399">
          <Document />
        </el-icon>
        <p>选择一个工作流开始执行</p>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { WorkflowService } from '@/services/workflow'
import { useWorkflowStore } from '@/stores/workflow'
import { WorkflowExecutionResponse } from '@/services/api'

interface ExecutionLog {
  timestamp: string
  level: 'info' | 'warning' | 'error'
  message: string
}

interface ExecutionWithLogs extends Omit<WorkflowExecutionResponse, 'logs'> {
  logs: ExecutionLog[]
}

const route = useRoute()
const workflowStore = useWorkflowStore()
const executionId = ref(route.query.executionId as string)
const execution = ref<ExecutionWithLogs | null>(null)
const logs = ref<ExecutionLog[]>([])
const loading = ref(false)
const logLevel = ref<'all' | 'info' | 'warning' | 'error'>('all')

const workflowTitle = computed(() => {
  const nameFromExec = (execution.value as any)?.workflowName
  const nameFromStore = workflowStore.currentWorkflow?.metadata.name
  return nameFromExec || nameFromStore || '未命名工作流'
})

// 状态映射
const statusMap = {
  pending: { text: '待执行', type: 'info', effect: 'light' },
  running: { text: '执行中', type: 'primary', effect: 'dark' },
  completed: { text: '已完成', type: 'success', effect: 'light' },
  failed: { text: '执行失败', type: 'danger', effect: 'dark' },
  cancelled: { text: '已取消', type: 'info', effect: 'light' }
}

// 计算属性
const canStop = computed(() => {
  return execution.value?.status === 'running' || execution.value?.status === 'pending'
})

const filteredLogs = computed(() => {
  if (!logs.value) return []

  return logs.value.filter(log => {
    if (logLevel.value === 'all') return true
    return log.level === logLevel.value
  })
})

// 加载执行状态
const loadExecutionStatus = async () => {
  if (!executionId.value) return

  loading.value = true
  try {
    const response = await WorkflowService.getExecutionStatus(executionId.value)
    if (response.logs) {
      execution.value = {
        ...response,
        logs: response.logs.map(log => ({
          timestamp: log.timestamp,
          level: log.level.toLowerCase() as 'info' | 'warning' | 'error',
          message: log.message
        }))
      }
    } else {
      execution.value = response
    }
  } catch (error) {
    console.error('Failed to load execution status:', error)
    ElMessage.error('加载执行状态失败')
  } finally {
    loading.value = false
  }
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  return statusMap[status as keyof typeof statusMap]?.type || 'info'
}

// 获取状态标签效果
const getStatusTagEffect = (status: string) => {
  return statusMap[status as keyof typeof statusMap]?.effect || 'light'
}

// 获取状态文本
const getStatusText = (status: string) => {
  return statusMap[status as keyof typeof statusMap]?.text || status
}

// 刷新状态
const refreshStatus = () => {
  loadExecutionStatus()
}

// 停止执行
const stopExecution = async () => {
  if (!executionId.value || !execution.value) return

  try {
    await ElMessageBox.confirm(
      '确定要停止当前工作流执行吗？',
      '停止执行',
      {
        confirmButtonText: '确定停止',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    await WorkflowService.stopExecution(executionId.value)
    ElMessage.success('执行已停止')
  } catch (error) {
    console.error('Failed to stop execution:', error)
    ElMessage.error('停止执行失败')
  }
}

// 清空日志
const clearLogs = () => {
  logs.value = []
  ElMessage.success('日志已清空')
}

// 下载日志
const downloadLogs = () => {
  if (!execution.value) return

  const logText = logs.value
    .map(log => `[${formatDateTime(log.timestamp)}] [${log.level.toUpperCase()}] ${log.message}`)
    .join('\n')

  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `execution-${executionId.value}-logs.txt`
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('日志下载成功')
}

// 格式化时间
const formatDateTime = (timestamp?: string) => {
  return new Date(timestamp || Date.now()).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化时长
const calculateDuration = (startTime: string, endTime: string) => {
  const start = new Date(startTime)
  const end = new Date(endTime)
  const duration = end.getTime() - start.getTime()

  const hours = Math.floor(duration / (1000 * 60 * 60))
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / 60000)
  const seconds = Math.floor((duration % 60000) / 1000)

  return `${hours}小时${minutes}分${seconds}秒`
}

// 获取日志项类型
const getLogItemType = (level: string) => {
  const typeMap = { error: 'danger', warning: 'warning', info: 'primary' } as const
  return typeMap[level as keyof typeof typeMap] || 'primary'
}

// 格式化时间（简化版）
const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

// 监控控制
let monitoringControl: { stop: () => void } | null = null

// 组件挂载
onMounted(() => {
  if (executionId.value) {
    // 先加载一次初始状态
    loadExecutionStatus()

    // 启动 WebSocket + 轮询降级监控
    monitoringControl = WorkflowService.startExecutionMonitoring(executionId.value, {
      onLog: (log) => {
        // 实时添加日志（避免重复）
        const logKey = `${log.timestamp}-${log.message}`
        if (!logs.value.some(l => `${l.timestamp}-${l.message}` === logKey)) {
          logs.value.push({
            timestamp: log.timestamp,
            level: log.level.toLowerCase() as 'info' | 'warning' | 'error',
            message: log.message
          })
        }
      },
      onStatus: (status, progress) => {
        if (execution.value) {
          execution.value.status = status as 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
          if (progress !== undefined) {
            execution.value.progress = progress
          }
        }
      },
      onError: (error) => {
        console.error('Monitoring error:', error)
      },
      usePollingFallback: true
    })
  }
})

// 组件卸载时清理
onUnmounted(() => {
  if (monitoringControl) {
    monitoringControl.stop()
    monitoringControl = null
  }
})
</script>

<style scoped>
.execution-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 12px;
}

.execution-info {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.execution-logs {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.logs-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.logs-actions {
  display: flex;
  gap: 8px;
}

.logs-content {
  height: 500px;
  overflow-y: auto;
  padding: 16px;
}

.log-entry {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: #909399;
  min-width: 80px;
}

.log-message {
  font-size: 14px;
  color: #303133;
  line-height: 1.4;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #909399;
}

.empty-state .el-icon {
  font-size: 64px;
  color: #909399;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0;
  text-align: center;
  color: #606266;
  line-height: 1.4;
}
</style>
