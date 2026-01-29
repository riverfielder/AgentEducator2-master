<template>
  <v-card 
    class="video-card" 
    elevation="2" 
    hover
    @click="$emit('view', video)"
  >
    <!-- 视频缩略图 -->
    <div class="video-thumbnail">
      <v-img
        :src="getCoverUrl(video.coverUrl)"
        height="120"
        cover
        class="thumbnail-img"
      >
        <template v-slot:placeholder>
          <div class="d-flex align-center justify-center fill-height">
            <v-icon size="48" color="grey">mdi-video</v-icon>
          </div>
        </template>
        
        <!-- 时长标签 -->
        <div class="duration-badge" v-if="video.duration">
          {{ formatDuration(video.duration) }}
        </div>
        
        <!-- 播放按钮 -->
        <div class="play-overlay">
          <v-btn
            icon
            size="large"
            color="white"
            class="play-btn"
            @click.stop="$emit('view', video)"
          >
            <v-icon size="32">mdi-play</v-icon>
          </v-btn>
        </div>
      </v-img>
    </div>

    <!-- 卡片内容 -->
    <v-card-text class="pa-3 flex-grow-1 d-flex flex-column">
      <div class="video-title text-subtitle-2 font-weight-medium mb-2">
        {{ video.title }}
      </div>
      
      <!-- 描述区域 - 始终保留固定高度 -->
      <div class="video-description text-caption text-medium-emphasis mb-3">
        <span v-if="video.description">{{ truncateText(video.description, 50) }}</span>
        <span v-else class="description-placeholder">暂无描述</span>
      </div>
      
      <!-- 状态信息 -->
      <div class="video-meta d-flex align-center mb-2">
        <v-chip
          :color="getStatusColor(video.processingStatus)"
          size="x-small"
          variant="tonal"
          class="me-2"
        >
          {{ getStatusText(video.processingStatus) }}
        </v-chip>
        
        <v-chip
          color="grey"
          size="x-small"
          variant="outlined"
          v-if="video.fileSize"
        >
          {{ formatFileSize(video.fileSize) }}
        </v-chip>
      </div>
      
      <!-- 处理进度 -->
      <div v-if="video.processingProgress && video.processingProgress < 100" class="mb-2">
        <div class="text-caption text-medium-emphasis mb-1">处理进度</div>
        <v-progress-linear
          :model-value="video.processingProgress"
          color="primary"
          height="3"
          rounded
        ></v-progress-linear>
      </div>
      
      <!-- 时间信息 -->
      <div class="text-caption text-medium-emphasis mt-auto">
        {{ formatDate(video.uploadTime || video.createTime) }}
      </div>
    </v-card-text>

    <!-- 操作按钮 -->
    <v-card-actions class="pa-3 pt-0 mt-auto">
      <v-btn
        size="small"
        variant="outlined"
        prepend-icon="mdi-play"
        @click.stop="playVideo"
      >
        播放
      </v-btn>
      
      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-information-outline"
        @click.stop="$emit('view-detail', video)"
      >
        详情
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
            @click="$emit('edit', video)"
          ></v-list-item>
          
          <v-list-item
            prepend-icon="mdi-cog"
            title="处理设置"
            @click="$emit('process', video)"
            v-if="video.processingStatus !== 'processing' && video.processingStatus !== 'running'"
          ></v-list-item>
          
          <v-divider></v-divider>
          
          <v-list-item
            prepend-icon="mdi-delete"
            title="删除"
            class="text-error"
            @click="$emit('delete', { ...video, type: 'video' })"
          ></v-list-item>
        </v-list>
      </v-menu>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
const props = defineProps({
  video: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['view', 'edit', 'delete', 'process', 'view-detail'])

function formatDuration(seconds: number): string {
  if (!seconds) return '0:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
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

function getCoverUrl(coverUrl: string | null | undefined): string {
  if (!coverUrl) return '/default-video-thumbnail.jpg'
  
  // 如果已经是完整URL，直接返回
  if (coverUrl.startsWith('http')) return coverUrl
  
  // 如果是相对路径，添加后端服务器地址
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
  return `${baseURL}${coverUrl}`
}

function getStatusText(status: string): string {
  switch (status) {
    case 'pending': return '等待处理'
    case 'processing': return '处理中'
    case 'running': return '处理中'
    case 'completed': return '已完成'
    case 'failed': return '处理失败'
    case 'unprocessed': return '未处理'
    default: return '未知状态'
  }
}

function playVideo() {
  // 触发播放事件，让父组件处理跳转到播放页面
  emit('view', props.video)
}
</script>

<style scoped>
.video-card {
  transition: all 0.3s ease;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  height: 320px; /* 与文档卡片保持一致的高度 */
  display: flex;
  flex-direction: column;
  min-height: 320px; /* 确保最小高度 */
  max-height: 320px; /* 确保最大高度 */
}

.video-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
}

.video-thumbnail {
  position: relative;
  overflow: hidden;
}

.thumbnail-img {
  transition: transform 0.3s ease;
  height: 120px !important; /* 调整缩略图高度从100px到120px */
  min-height: 120px;
  max-height: 120px;
}

.video-card:hover .thumbnail-img {
  transform: scale(1.05);
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.video-card:hover .play-overlay {
  opacity: 1;
}

.play-btn {
  background: rgba(0, 0, 0, 0.7) !important;
  backdrop-filter: blur(4px);
}

.play-btn:hover {
  background: rgba(0, 0, 0, 0.9) !important;
}

.video-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
  min-height: 2.6em;
  font-size: 0.875rem;
}

.video-description {
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

.video-meta {
  flex-wrap: wrap;
  gap: 4px;
}

/* 确保v-card-text高度一致 */
.video-card .v-card-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 允许flex子项收缩 */
}

/* 确保操作按钮区域高度一致 */
.video-card .v-card-actions {
  min-height: 56px; /* 固定操作按钮区域的最小高度 */
  flex-shrink: 0;
}
</style> 