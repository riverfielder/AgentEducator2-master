<template>
  <v-slide-y-transition>
    <div v-if="showStatus || currentToolInfo" class="status-bar">
      <div class="status-content">
        <!-- 工具执行状态显示 -->
        <div v-if="currentToolInfo" class="tool-execution-status">
          <div class="d-flex align-center">
            <v-avatar :color="currentToolInfo.tool_color || 'primary'" size="20" class="me-2">
              <v-icon :icon="currentToolInfo.tool_icon || 'mdi-tools'" size="12" color="white" />
            </v-avatar>
            <span class="text-subtitle-2 font-weight-medium">{{ currentToolInfo.tool_name }}</span>
            <v-spacer />
            <v-chip :color="getToolStatusColor(currentToolInfo.status)" variant="flat" size="x-small" class="ms-2">
              <v-icon :icon="getToolStatusIcon(currentToolInfo.status)" start size="x-small" />
              {{ getToolStatusText(currentToolInfo.status) }}
            </v-chip>
          </div>
          
          <div v-if="currentToolInfo.description" class="text-caption mt-1">
            {{ currentToolInfo.description }}
          </div>
          
          <!-- 工具上下文信息 -->
          <div v-if="currentToolInfo.context" class="tool-context-chips mt-1">
            <v-chip v-for="(value, key) in currentToolInfo.context" :key="String(key)" size="x-small"
              variant="outlined" color="white" class="me-1 mb-1">
              {{ formatContextInfo(String(key), value) }}
            </v-chip>
          </div>
        </div>
        
        <!-- 通用状态显示 -->
        <div v-else-if="showStatus" class="general-status">
          <v-progress-circular 
            indeterminate 
            size="16" 
            width="2" 
            color="white"
            class="me-2"
          />
          <span class="status-text">{{ currentStatus }}</span>
          <div v-if="statusStats" class="status-stats">
            <span v-if="statusStats.document_count" class="stats-item">
              文档片段: {{ statusStats.document_count }}
            </span>
            <span v-if="statusStats.tokens" class="stats-item">
              Token: {{ statusStats.tokens }}
            </span>
            <span v-if="statusStats.sources" class="stats-item">
              引用: {{ statusStats.sources }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </v-slide-y-transition>
</template>

<script setup lang="ts">
interface Props {
  showStatus: boolean
  currentStatus: string
  statusStats?: any
  currentToolInfo?: any
}

defineProps<Props>()

// 工具状态相关辅助函数
const getToolStatusColor = (status: string) => {
  switch (status) {
    case 'running': return 'primary'
    case 'success': return 'success'
    case 'error': return 'error'
    default: return 'grey'
  }
}

const getToolStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return 'mdi-loading mdi-spin'
    case 'success': return 'mdi-check'
    case 'error': return 'mdi-alert'
    default: return 'mdi-help'
  }
}

const getToolStatusText = (status: string) => {
  switch (status) {
    case 'running': return '执行中'
    case 'success': return '已完成'
    case 'error': return '失败'
    default: return '未知'
  }
}

const formatContextInfo = (key: string, value: any) => {
  if (key === 'course_id') return `课程: ${value}`
  if (key === 'video_id') return `视频: ${value}`
  if (key === 'query') return `查询: ${value.toString().slice(0, 20)}${value.toString().length > 20 ? '...' : ''}`
  return `${key}: ${value}`
}
</script>

<style scoped>
.status-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.status-content {
  display: flex;
  align-items: center;
  font-size: 14px;
  z-index: 1;
  position: relative;
}

.status-text {
  font-weight: 500;
  margin-right: 16px;
}

.status-stats {
  display: flex;
  gap: 12px;
  margin-left: auto;
  font-size: 12px;
  opacity: 0.9;
}

.stats-item {
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.tool-execution-status {
  width: 100%;
}

.tool-context-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style> 