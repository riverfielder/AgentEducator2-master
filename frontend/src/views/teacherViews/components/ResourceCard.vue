<template>
  <v-card
    class="resource-card"
    :draggable="draggable"
    @dragstart="handleDragStart"
    @click="handleClick"
    hover
    elevation="2"
  >
    <!-- 缩略图区域 -->
    <div class="thumbnail-container">
      <img
        v-if="item.thumbnail"
        :src="item.thumbnail"
        :alt="item.title"
        class="thumbnail-image"
      />
      <div v-else class="thumbnail-placeholder" :class="`type-${item.type}`">
        <v-icon size="48" color="white">{{ getTypeIcon(item.type) }}</v-icon>
      </div>
      
      <!-- 类型标签 -->
      <v-chip
        size="small"
        :color="getTypeColor(item.type)"
        class="type-chip"
        variant="flat"
      >
        {{ getTypeText(item.type) }}
      </v-chip>
      
      <!-- 时长显示（仅视频） -->
      <div v-if="item.type === 'video' && item.duration" class="duration-badge">
        {{ formatDuration(item.duration) }}
      </div>
    </div>

    <!-- 内容信息 -->
    <v-card-text class="pa-3">
      <div class="text-subtitle-2 font-weight-medium text-truncate mb-1">
        {{ item.title }}
      </div>
      <div class="text-caption text-medium-emphasis d-flex align-center">
        <v-icon size="12" class="me-1">mdi-file</v-icon>
        {{ formatFileSize(item.fileSize) }}
        <v-spacer></v-spacer>
        <span>{{ formatDate(item.uploadTime) }}</span>
      </div>
    </v-card-text>

    <!-- 操作按钮 -->
    <v-card-actions class="pa-2">
      <v-spacer></v-spacer>
      <!-- 只有文档才显示编辑按钮 -->
      <v-btn v-if="item.type === 'document'" icon size="small" @click.stop="$emit('edit', item)">
        <v-icon>mdi-pencil</v-icon>
      </v-btn>
      <v-btn icon size="small" @click.stop="$emit('delete', item)">
        <v-icon>mdi-delete</v-icon>
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
interface ResourceItem {
  id: string
  title: string
  type: 'video' | 'document'
  fileSize?: number
  uploadTime?: string
  thumbnail?: string
  duration?: number
  chapterId?: string
}

interface Props {
  item: ResourceItem
  draggable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  draggable: false
})

const emit = defineEmits<{
  click: [item: ResourceItem]
  edit: [item: ResourceItem]
  delete: [item: ResourceItem]
  dragstart: [event: DragEvent, item: ResourceItem]
}>()

function handleClick() {
  emit('click', props.item)
}

function handleDragStart(event: DragEvent) {
  emit('dragstart', event, props.item)
}

function getTypeIcon(type: string) {
  const iconMap: Record<string, string> = {
    video: 'mdi-play-circle',
    document: 'mdi-file-document'
  }
  return iconMap[type] || 'mdi-file'
}

function getTypeColor(type: string) {
  const colorMap: Record<string, string> = {
    video: 'blue',
    document: 'green'
  }
  return colorMap[type] || 'grey'
}

function getTypeText(type: string) {
  const textMap: Record<string, string> = {
    video: '视频',
    document: '文档'
  }
  return textMap[type] || type
}

function formatFileSize(bytes?: number) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(date?: string) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

function formatDuration(seconds?: number) {
  if (!seconds) return ''
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.resource-card {
  cursor: pointer;
  transition: all 0.3s;
}

.resource-card:hover {
  transform: translateY(-2px);
}

.thumbnail-container {
  position: relative;
  height: 120px;
  overflow: hidden;
}

.thumbnail-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumbnail-placeholder.type-video {
  background: linear-gradient(135deg, #2196f3, #1976d2);
}

.thumbnail-placeholder.type-document {
  background: linear-gradient(135deg, #4caf50, #388e3c);
}

.type-chip {
  position: absolute;
  top: 8px;
  left: 8px;
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}
</style> 