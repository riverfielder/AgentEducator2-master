<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="600">
    <v-card v-if="resource">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon start :color="getTypeColor(resource.type)">{{ getTypeIcon(resource.type) }}</v-icon>
        {{ resource.title }}
        <v-spacer></v-spacer>
        <v-btn icon @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text class="pa-6">
        <!-- 资源预览 -->
        <div class="resource-preview mb-6">
          <div v-if="resource.thumbnail" class="thumbnail-container">
            <img :src="resource.thumbnail" :alt="resource.title" class="thumbnail" />
          </div>
          <div v-else class="thumbnail-placeholder" :class="`type-${resource.type}`">
            <v-icon size="64" color="white">{{ getTypeIcon(resource.type) }}</v-icon>
          </div>
        </div>
        
        <!-- 基本信息 -->
        <div class="resource-info">
          <v-row>
            <v-col cols="6">
              <div class="info-item">
                <div class="info-label">类型</div>
                <v-chip :color="getTypeColor(resource.type)" size="small">
                  {{ getTypeText(resource.type) }}
                </v-chip>
              </div>
            </v-col>
            <v-col cols="6" v-if="resource.type === 'document'">
              <div class="info-item">
                <div class="info-label">文件大小</div>
                <div class="info-value">{{ formatFileSize(resource.fileSize) }}</div>
              </div>
            </v-col>
          </v-row>
          
          <v-row v-if="resource.type === 'video'">
            <v-col cols="6">
              <div class="info-item">
                <div class="info-label">时长</div>
                <div class="info-value">{{ formatDuration(resource.duration) }}</div>
              </div>
            </v-col>
            <v-col cols="6">
              <div class="info-item">
                <div class="info-label">观看次数</div>
                <div class="info-value">{{ resource.viewCount || 0 }} 次</div>
              </div>
            </v-col>
          </v-row>
          
          <v-row v-if="resource.type === 'document'">
            <v-col cols="6">
              <div class="info-item">
                <div class="info-label">下载次数</div>
                <div class="info-value">{{ resource.downloadCount || 0 }} 次</div>
              </div>
            </v-col>
            <v-col cols="6">
              <div class="info-item">
                <div class="info-label">文件格式</div>
                <div class="info-value">{{ getFileExtension(resource.title) }}</div>
              </div>
            </v-col>
          </v-row>
          
          <v-row>
            <v-col cols="12">
              <div class="info-item">
                <div class="info-label">上传时间</div>
                <div class="info-value">{{ formatDateTime(resource.uploadTime) }}</div>
              </div>
            </v-col>
          </v-row>
          
          <v-row v-if="resource.chapterId && resource.type === 'document'">
            <v-col cols="12">
              <div class="info-item">
                <div class="info-label">所属章节</div>
                <div class="info-value">
                  <v-chip color="primary" size="small" variant="outlined">
                    {{ getChapterName(resource.chapterId) }}
                  </v-chip>
                </div>
              </div>
            </v-col>
          </v-row>
        </div>
        
        <!-- 描述信息 -->
        <div v-if="resource.description" class="resource-description mt-4">
          <div class="info-label mb-2">描述</div>
          <div class="info-value">{{ resource.description }}</div>
        </div>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="pa-6">
        <v-btn
          v-if="resource.type === 'video'"
          color="primary"
          prepend-icon="mdi-play"
          @click="playVideo"
        >
          播放视频
        </v-btn>
        <template v-else>
          <v-btn
            v-if="canPreviewDocument(resource)"
            color="primary"
            prepend-icon="mdi-eye"
            @click="previewDocument"
            class="me-2"
          >
            预览文档
          </v-btn>
        <v-btn
          color="success"
          prepend-icon="mdi-download"
          @click="downloadFile"
        >
          下载文件
        </v-btn>
        </template>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="close">
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { API_BASE_URL } from '../../../config'

interface ResourceItem {
  id: string
  title: string
  type: 'video' | 'document'
  fileSize?: number
  uploadTime?: string
  thumbnail?: string
  duration?: number
  chapterId?: string
  description?: string
  viewCount?: number
  downloadCount?: number
  fileUrl?: string
}

interface Props {
  modelValue: boolean
  resource?: ResourceItem | null
  courseId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()
const route = useRoute()

function close() {
  emit('update:modelValue', false)
}

function getTypeIcon(type: string): string {
  const iconMap: Record<string, string> = {
    video: 'mdi-play-circle',
    document: 'mdi-file-document'
  }
  return iconMap[type] || 'mdi-file'
}

function getTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    video: 'blue',
    document: 'green'
  }
  return colorMap[type] || 'grey'
}

function getTypeText(type: string): string {
  const textMap: Record<string, string> = {
    video: '视频',
    document: '文档'
  }
  return textMap[type] || type
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDuration(seconds?: number): string {
  if (!seconds) return '未知'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

function formatDateTime(date?: string): string {
  if (!date) return '未知'
  return new Date(date).toLocaleString('zh-CN')
}

function getFileExtension(filename: string): string {
  const ext = filename.split('.').pop()?.toUpperCase()
  return ext || '未知'
}

function getChapterName(chapterId: string): string {
  // TODO: 从章节列表中获取章节名称
  return `章节 ${chapterId}`
}

function playVideo() {
  if (props.resource?.id) {
    // 跳转到视频播放页面
    // 需要获取当前课程ID，从父组件传入或者从路由中获取
    const courseId = getCourseId()
    if (courseId) {
      router.push(`/course/${courseId}/video/${props.resource.id}`)
      close()
    } else {
      console.error('无法获取课程ID')
    }
  }
}

async function downloadFile() {
  if (props.resource?.id) {
    try {
      // 创建一个隐藏的a标签来触发下载
      const downloadUrl = `${API_BASE_URL}/api/documents/${props.resource.id}/download`
      
      // 添加认证token
      const token = localStorage.getItem('wendao_token')
      
      // 使用fetch下载文件
      const response = await fetch(downloadUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        // 获取文件名
        const contentDisposition = response.headers.get('Content-Disposition')
        let filename = props.resource.title
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename="([^"]*)"/)
          if (matches) {
            filename = matches[1]
          }
        }
        
        // 创建blob并下载
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        
        console.log('文件下载成功')
      } else {
        console.error('下载失败:', response.statusText)
      }
    } catch (error) {
      console.error('下载文件失败:', error)
  }
  }
}

// 获取当前课程ID的辅助函数
function getCourseId(): string | null {
  // 优先使用props传递的courseId，然后从路由参数中获取
  return props.courseId || (route.params.courseId as string) || null
}

// 判断文档是否可以预览
function canPreviewDocument(resource: ResourceItem): boolean {
  if (resource.type !== 'document') return false
  const fileType = getFileExtension(resource.title).toLowerCase()
  return ['PDF'].includes(fileType)
}

// 预览文档
function previewDocument() {
  if (props.resource?.id) {
    // 构建预览URL
    const token = localStorage.getItem('wendao_token')
    const previewUrl = `${API_BASE_URL}/api/documents/${props.resource.id}/preview?token=${token}`
    
    // 在新窗口中打开预览
    window.open(previewUrl, '_blank')
  }
}
</script>

<style scoped>
.resource-preview {
  text-align: center;
}

.thumbnail-container {
  display: inline-block;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.thumbnail {
  max-width: 100%;
  max-height: 200px;
  object-fit: cover;
}

.thumbnail-placeholder {
  width: 200px;
  height: 120px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.thumbnail-placeholder.type-video {
  background: linear-gradient(135deg, #2196f3, #1976d2);
}

.thumbnail-placeholder.type-document {
  background: linear-gradient(135deg, #4caf50, #388e3c);
}

.info-item {
  margin-bottom: 16px;
}

.info-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
}

.info-value {
  font-size: 16px;
  font-weight: 500;
}

.resource-description {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
}
</style> 