<template>
  <v-card 
    class="document-card" 
    elevation="2" 
    hover
  >
    <!-- 文档图标区域 -->
    <div class="document-icon-area">
      <div class="document-icon-container">
        <v-icon 
          :color="getFileTypeColor(document.fileType)" 
          size="48"
          class="document-icon"
        >
          {{ getFileTypeIcon(document.fileType) }}
        </v-icon>
        
        <!-- 文件类型标签 -->
        <div class="file-type-badge">
          {{ getFileTypeText(document.fileType) }}
        </div>
      </div>
    </div>

    <!-- 卡片内容 -->
    <v-card-text class="pa-3 flex-grow-1 d-flex flex-column">
      <div class="document-title text-subtitle-2 font-weight-medium mb-2">
        {{ document.title }}
      </div>
      
      <!-- 描述区域 - 始终保留固定高度 -->
      <div class="document-description text-caption text-medium-emphasis mb-3">
        <span v-if="document.description">{{ truncateText(document.description, 50) }}</span>
        <span v-else class="description-placeholder">暂无描述</span>
      </div>
      
      <!-- 文档信息和时间信息放在同一行 -->
      <div class="document-meta d-flex align-center justify-space-between mb-2">
        <div class="d-flex align-center">
        <v-chip
          color="grey"
          size="x-small"
          variant="outlined"
          class="me-2"
          v-if="document.fileSize"
        >
          {{ formatFileSize(document.fileSize) }}
        </v-chip>
        
        <v-chip
          color="blue"
          size="x-small"
          variant="tonal"
          v-if="document.pageCount"
        >
          {{ document.pageCount }} 页
        </v-chip>
        </div>
        
        <!-- 时间信息移到右侧，与文档信息同一行 -->
        <div class="text-caption text-medium-emphasis">
          {{ formatDate(document.uploadTime || document.createTime) }}
        </div>
      </div>
      
      <!-- 处理状态 -->
      <div v-if="document.processingStatus" class="mb-2">
        <v-chip
          :color="getStatusColor(document.processingStatus)"
          size="x-small"
          variant="tonal"
        >
          {{ getStatusText(document.processingStatus) }}
        </v-chip>
      </div>
    </v-card-text>

    <!-- 操作按钮 -->
    <v-card-actions class="pa-3 pt-0 mt-auto">
      <v-btn
        size="small"
        variant="outlined"
        prepend-icon="mdi-download"
        @click.stop="$emit('download', document)"
        class="me-2"
      >
        下载
      </v-btn>
      
      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-eye"
        @click.stop="previewDocument"
        v-if="canPreview(document.fileType)"
      >
        预览
      </v-btn>
      
      <v-spacer></v-spacer>
      
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            icon="mdi-dots-vertical"
            size="small"
            variant="text"
            v-bind="props"
            @click.stop
          ></v-btn>
        </template>
        
        <v-list density="compact">
          <v-list-item
            prepend-icon="mdi-pencil"
            title="编辑信息"
            @click="$emit('edit', document)"
          ></v-list-item>
          
          <v-list-item
            prepend-icon="mdi-information-outline"
            title="详细信息"
            @click="showDocumentInfo"
          ></v-list-item>
          
          <v-divider></v-divider>
          
          <v-list-item
            prepend-icon="mdi-delete"
            title="删除"
            class="text-error"
            @click="$emit('delete', { ...document, type: 'document' })"
          ></v-list-item>
        </v-list>
      </v-menu>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
const props = defineProps({
  document: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'download', 'preview'])

function getFileTypeIcon(fileType: string): string {
  const type = fileType?.toLowerCase() || ''
  
  if (type.includes('pdf')) return 'mdi-file-pdf-box'
  if (type.includes('word') || type.includes('doc')) return 'mdi-file-word-box'
  if (type.includes('excel') || type.includes('xls')) return 'mdi-file-excel-box'
  if (type.includes('powerpoint') || type.includes('ppt')) return 'mdi-file-powerpoint-box'
  if (type.includes('text') || type.includes('txt')) return 'mdi-file-document-outline'
  if (type.includes('image') || type.includes('jpg') || type.includes('png')) return 'mdi-file-image'
  
  return 'mdi-file-document'
}

function getFileTypeColor(fileType: string): string {
  const type = fileType?.toLowerCase() || ''
  
  if (type.includes('pdf')) return 'red'
  if (type.includes('word') || type.includes('doc')) return 'blue'
  if (type.includes('excel') || type.includes('xls')) return 'green'
  if (type.includes('powerpoint') || type.includes('ppt')) return 'orange'
  if (type.includes('text') || type.includes('txt')) return 'grey'
  if (type.includes('image')) return 'purple'
  
  return 'grey'
}

function getFileTypeText(fileType: string): string {
  const type = fileType?.toLowerCase() || ''
  
  if (type.includes('pdf')) return 'PDF'
  if (type.includes('word') || type.includes('doc')) return 'Word'
  if (type.includes('excel') || type.includes('xls')) return 'Excel'
  if (type.includes('powerpoint') || type.includes('ppt')) return 'PPT'
  if (type.includes('text') || type.includes('txt')) return 'TXT'
  if (type.includes('image')) return '图片'
  
  return '文档'
}

// 预览功能支持PDF、文本、图片等格式
function canPreview(fileType: string): boolean {
  const type = fileType?.toLowerCase() || ''
  return type.includes('pdf') || 
         type.includes('txt') || 
         type.includes('md') ||
         type.includes('image') ||
         type.includes('jpg') ||
         type.includes('png') ||
         type.includes('gif') ||
         type.includes('jpeg')
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'pending': return 'blue'
    case 'processing': return 'orange'
    case 'running': return 'orange'
    case 'completed': return 'green'
    case 'failed': return 'red'
    case 'unprocessed': return 'grey'
    default: return 'grey'
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'pending': return '等待处理'
    case 'processing': return '处理中'
    case 'running': return '处理中'
    case 'completed': return '已处理'
    case 'failed': return '处理失败'
    case 'unprocessed': return '未处理'
    default: return '未知状态'
  }
}

function previewDocument() {
  // 触发预览事件，由父组件处理
  emit('preview', props.document)
}

function showDocumentInfo() {
  // 显示文档详细信息的功能
  console.log('显示文档详细信息:', props.document)
  // 这里可以触发一个新的事件或者显示详细信息对话框
}
</script>

<style scoped>
.document-card {
  transition: all 0.3s ease;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  height: 320px; /* 与视频卡片保持一致的高度 */
  display: flex;
  flex-direction: column;
  min-height: 320px; /* 确保最小高度 */
  max-height: 320px; /* 确保最大高度 */
}

.document-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
}

.document-icon-area {
  height: 120px; /* 与视频缩略图保持一致的高度 */
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.document-icon-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.document-icon {
  transition: transform 0.3s ease;
}

.document-card:hover .document-icon {
  transform: scale(1.1);
}

.file-type-badge {
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  backdrop-filter: blur(4px);
}

.document-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
  min-height: 2.6em;
  font-size: 0.875rem;
}

.document-description {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
  min-height: 2.8em; /* 固定高度，确保一致性 */
  max-height: 2.8em; /* 固定高度，确保一致性 */
}

.description-placeholder {
  color: #9e9e9e;
  font-style: italic;
}

.document-meta {
  flex-wrap: wrap;
  gap: 4px;
}

/* 确保v-card-text高度一致 */
.document-card .v-card-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 允许flex子项收缩 */
}

/* 确保操作按钮区域高度一致 */
.document-card .v-card-actions {
  min-height: 56px; /* 固定操作按钮区域的最小高度 */
  flex-shrink: 0;
}

/* 文件类型特定样式 */
.document-card:has(.mdi-file-pdf-box) .document-icon-area {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
}

.document-card:has(.mdi-file-word-box) .document-icon-area {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.document-card:has(.mdi-file-excel-box) .document-icon-area {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
}

.document-card:has(.mdi-file-powerpoint-box) .document-icon-area {
  background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
}
</style> 