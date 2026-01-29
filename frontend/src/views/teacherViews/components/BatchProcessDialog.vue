<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="1200" persistent>
    <v-card>
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon start color="orange">mdi-cog-refresh</v-icon>
        批量处理课程内容
        <v-spacer></v-spacer>
        <v-btn icon @click="close" :disabled="processing">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text class="pa-6" style="max-height: 70vh; overflow-y: auto;">
        <!-- 内容选择区域 -->
        <div class="content-selection mb-6">
          <v-alert type="info" variant="tonal" class="mb-4">
            <v-icon start>mdi-information</v-icon>
            <div class="text-body-2">
              <strong>批量处理功能</strong>：重新处理已上传的课程内容，适用于之前处理失败或需要更新处理结果的情况。
            </div>
          </v-alert>

          <!-- 视频内容选择 -->
          <v-card v-if="videos.length > 0" variant="outlined" class="mb-4">
            <v-card-subtitle class="pa-4 pb-2">
              <v-icon color="blue" class="mr-2">mdi-video</v-icon>
              视频内容 ({{ videos.length }} 个)
            </v-card-subtitle>
            
            <v-card-text class="pa-4 pt-0">
              <div class="d-flex align-center mb-3">
                <v-checkbox
                  v-model="selectAllVideos"
                  @change="toggleAllVideos"
                  label="全选视频"
                  density="compact"
                  hide-details
                ></v-checkbox>
                <v-spacer></v-spacer>
                <v-btn
                  v-if="!loadingStatus"
                  size="small"
                  variant="outlined"
                  color="primary"
                  @click="loadProcessingStatusAndAutoSelect"
                  class="mr-2"
                >
                  <v-icon start size="small">mdi-refresh</v-icon>
                  刷新状态
                </v-btn>
                <v-progress-circular
                  v-if="loadingStatus"
                  size="20"
                  width="2"
                  color="primary"
                  indeterminate
                  class="mr-2"
                ></v-progress-circular>
                <v-chip size="small" color="blue" variant="flat">
                  已选择 {{ selectedVideos.length }} 个
                </v-chip>
              </div>
              
              <v-row>
                <v-col
                  v-for="video in videos"
                  :key="video.id"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <v-card variant="outlined" class="video-selection-card">
                    <v-card-text class="pa-3">
                      <div class="d-flex align-center mb-2">
                        <v-checkbox
                          v-model="selectedVideos"
                          :value="video.id"
                          density="compact"
                          hide-details
                        ></v-checkbox>
                        <div class="flex-grow-1 ml-2">
                          <div class="text-body-2 font-weight-medium">{{ video.title }}</div>
                          <div class="text-caption text-medium-emphasis">
                            {{ formatFileSize(video.fileSize) }} • {{ formatDate(video.uploadTime) }}
                          </div>
                          <!-- 处理状态显示 -->
                          <div class="mt-1">
                            <template v-if="loadingStatus">
                              <v-chip size="x-small" color="grey" variant="flat">
                                <v-icon start size="x-small">mdi-loading</v-icon>
                                检查状态中...
                              </v-chip>
                            </template>
                            <template v-else>
                              <template v-if="getVideoStatusInfo(video.id).completed">
                                <v-chip size="x-small" color="success" variant="flat">
                                  <v-icon start size="x-small">mdi-check</v-icon>
                                  已完成
                                </v-chip>
                              </template>
                              <template v-else>
                                <v-chip size="x-small" color="warning" variant="flat">
                                  <v-icon start size="x-small">mdi-clock</v-icon>
                                  {{ getVideoStatusInfo(video.id).info }}
                                </v-chip>
                              </template>
                            </template>
                          </div>
                        </div>
                      </div>
                      <div v-if="video.thumbnail" class="video-thumbnail">
                        <img :src="video.thumbnail" alt="缩略图" />
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 文档内容选择 -->
          <v-card v-if="documents.length > 0" variant="outlined" class="mb-4">
            <v-card-subtitle class="pa-4 pb-2">
              <v-icon color="green" class="mr-2">mdi-file-document-multiple</v-icon>
              文档内容 ({{ documents.length }} 个)
            </v-card-subtitle>
            
            <v-card-text class="pa-4 pt-0">
              <div class="d-flex align-center mb-3">
                <v-checkbox
                  v-model="selectAllDocuments"
                  @change="toggleAllDocuments"
                  label="全选文档"
                  density="compact"
                  hide-details
                ></v-checkbox>
                <v-spacer></v-spacer>
                <v-btn
                  v-if="!loadingStatus"
                  size="small"
                  variant="outlined"
                  color="primary"
                  @click="loadProcessingStatusAndAutoSelect"
                  class="mr-2"
                >
                  <v-icon start size="small">mdi-refresh</v-icon>
                  刷新状态
                </v-btn>
                <v-progress-circular
                  v-if="loadingStatus"
                  size="20"
                  width="2"
                  color="primary"
                  indeterminate
                  class="mr-2"
                ></v-progress-circular>
                <v-chip size="small" color="green" variant="flat">
                  已选择 {{ selectedDocuments.length }} 个
                </v-chip>
              </div>
              
              <v-row>
                <v-col
                  v-for="document in documents"
                  :key="document.id"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <v-card variant="outlined" class="document-selection-card">
                    <v-card-text class="pa-3">
                      <div class="d-flex align-center">
                        <v-checkbox
                          v-model="selectedDocuments"
                          :value="document.id"
                          density="compact"
                          hide-details
                        ></v-checkbox>
                        <div class="flex-grow-1 ml-2">
                          <div class="text-body-2 font-weight-medium">{{ document.title }}</div>
                          <div class="text-caption text-medium-emphasis">
                            {{ getFileIcon(document.fileType || 'unknown') }} {{ formatFileSize(document.fileSize) }} • {{ formatDate(document.uploadTime) }}
                          </div>
                          <!-- 处理状态显示 -->
                          <div class="mt-1">
                            <template v-if="loadingStatus">
                              <v-chip size="x-small" color="grey" variant="flat">
                                <v-icon start size="x-small">mdi-loading</v-icon>
                                检查状态中...
                              </v-chip>
                            </template>
                            <template v-else>
                              <template v-if="getDocumentStatusInfo(document.id).completed">
                                <v-chip size="x-small" color="success" variant="flat">
                                  <v-icon start size="x-small">mdi-check</v-icon>
                                  已完成
                                </v-chip>
                              </template>
                              <template v-else>
                                <v-chip size="x-small" color="warning" variant="flat">
                                  <v-icon start size="x-small">mdi-clock</v-icon>
                                  {{ getDocumentStatusInfo(document.id).info }}
                                </v-chip>
                              </template>
                            </template>
                          </div>
                        </div>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 空状态 -->
          <v-card v-if="videos.length === 0 && documents.length === 0" variant="outlined" class="pa-8 text-center">
            <v-icon size="64" color="grey-lighten-1">mdi-folder-open</v-icon>
            <div class="text-h6 mt-4 text-grey-darken-1">暂无可处理内容</div>
            <div class="text-body-1 mt-2 text-grey-darken-1">
              请先上传视频或文档内容
            </div>
          </v-card>
        </div>

        <!-- 处理设置区域 - 简化版本 -->
        <div v-if="hasSelectedContent" class="processing-settings mb-4">
          <!-- 视频处理设置 -->
          <v-card v-if="selectedVideos.length > 0" variant="outlined" class="pa-4 mb-4">
            <v-card-subtitle class="pa-0 mb-3">
              <v-icon color="blue" class="mr-2">mdi-video</v-icon>
              视频处理设置 ({{ selectedVideos.length }} 个视频)
            </v-card-subtitle>
            
            <!-- 处理模式选择 -->
            <div class="mb-4">
              <v-card-subtitle class="pa-0 mb-2">选择处理模式</v-card-subtitle>
              <v-radio-group v-model="videoProcessMode" density="compact">
                <v-radio
                  value="full_reprocess"
                  label="清空记录并重新处理"
                  class="mb-2"
                >
                  <template v-slot:label>
                    <div class="d-flex align-center">
                      <v-icon class="mr-2" size="small">mdi-refresh</v-icon>
                      <span>清空记录并重新处理</span>
                      <v-tooltip activator="parent" location="top">
                        删除所有已有的处理结果，重新执行完整处理流程
                      </v-tooltip>
                    </div>
                  </template>
                </v-radio>
                <v-radio
                  value="process_remaining"
                  label="处理还未处理的步骤"
                  class="mb-2"
                >
                  <template v-slot:label>
                    <div class="d-flex align-center">
                      <v-icon class="mr-2" size="small">mdi-playlist-plus</v-icon>
                      <span>处理还未处理的步骤</span>
                      <v-tooltip activator="parent" location="top">
                        只处理那些尚未完成的步骤，保留已有结果
                      </v-tooltip>
                    </div>
                  </template>
                </v-radio>
              </v-radio-group>
            </div>

          </v-card>

          <!-- 文档处理设置 -->
          <v-card v-if="selectedDocuments.length > 0" variant="outlined" class="pa-4">
            <v-card-subtitle class="pa-0 mb-3">
              <v-icon color="green" class="mr-2">mdi-file-document-multiple</v-icon>
              文档处理设置 ({{ selectedDocuments.length }} 个文档)
            </v-card-subtitle>
            
            <!-- 处理模式选择 -->
            <div class="mb-4">
              <v-card-subtitle class="pa-0 mb-2">选择处理模式</v-card-subtitle>
              <v-radio-group v-model="documentProcessMode" density="compact">
                <v-radio
                  value="full_reprocess"
                  label="清空记录并重新处理"
                  class="mb-2"
                >
                  <template v-slot:label>
                    <div class="d-flex align-center">
                      <v-icon class="mr-2" size="small">mdi-refresh</v-icon>
                      <span>清空记录并重新处理</span>
                      <v-tooltip activator="parent" location="top">
                        删除所有已有的处理结果，重新执行完整处理流程
                      </v-tooltip>
                    </div>
                  </template>
                </v-radio>
                <v-radio
                  value="process_remaining"
                  label="处理还未处理的步骤"
                  class="mb-2"
                >
                  <template v-slot:label>
                    <div class="d-flex align-center">
                      <v-icon class="mr-2" size="small">mdi-playlist-plus</v-icon>
                      <span>处理还未处理的步骤</span>
                      <v-tooltip activator="parent" location="top">
                        只处理那些尚未完成的步骤，保留已有结果
                      </v-tooltip>
                    </div>
                  </template>
                </v-radio>
              </v-radio-group>
            </div>
          </v-card>
        </div>

        <!-- 处理进度 -->
        <div v-if="processing" class="processing-progress mb-4">
          <v-card variant="outlined" class="pa-4">
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-body-2 font-weight-medium">批量处理进度</span>
              <span class="text-body-2">{{ Math.round(processingProgress) }}%</span>
            </div>
            <v-progress-linear
              :model-value="processingProgress"
              height="8"
              rounded
              color="primary"
              striped
            ></v-progress-linear>
            
            <div v-if="currentProcessingItem" class="text-caption text-medium-emphasis mt-2">
              <v-icon class="mr-1" size="small">mdi-cog</v-icon>
              {{ currentProcessingItem }}
            </div>
            
            <div class="text-caption mt-1">
              已完成: {{ completedItems }}/{{ totalItems }} 项
            </div>
          </v-card>
        </div>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="pa-6">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="close" :disabled="processing">
          取消
        </v-btn>
        <v-btn
          color="primary"
          size="large"
          :loading="processing"
          :disabled="!hasSelectedContent"
          @click="startBatchProcess"
        >
          <v-icon start>mdi-play</v-icon>
          开始批量处理
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import videoService from '../../../api/videoService'
import { documentService } from '../../../api/documentService'

interface Props {
  modelValue: boolean
  videos: any[]
  documents: any[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  processed: [result: any]
}>()

// 响应式数据
const selectedVideos = ref<string[]>([])
const selectedDocuments = ref<string[]>([])
const selectAllVideos = ref(false)
const selectAllDocuments = ref(false)

const videoProcessMode = ref('process_remaining')  // 默认处理未完成的步骤
const documentProcessMode = ref('process_remaining')

// 处理状态
const processing = ref(false)
const processingProgress = ref(0)
const currentProcessingItem = ref('')
const completedItems = ref(0)
const totalItems = ref(0)

// 状态相关数据
const loadingStatus = ref(false)
const videoStatuses = ref<any[]>([])
const documentStatuses = ref<any[]>([])

// 计算属性
const hasSelectedContent = computed(() => {
  return selectedVideos.value.length > 0 || selectedDocuments.value.length > 0
})

// 方法
function close() {
  if (!processing.value) {
    emit('update:modelValue', false)
    resetForm()
  }
}

function resetForm() {
  selectedVideos.value = []
  selectedDocuments.value = []
  selectAllVideos.value = false
  selectAllDocuments.value = false
  videoProcessMode.value = 'process_remaining'
  documentProcessMode.value = 'process_remaining'
  processing.value = false
  processingProgress.value = 0
  currentProcessingItem.value = ''
  completedItems.value = 0
  totalItems.value = 0
}

function toggleAllVideos() {
  if (selectAllVideos.value) {
    selectedVideos.value = props.videos.map(v => v.id)
  } else {
    selectedVideos.value = []
  }
}

function toggleAllDocuments() {
  if (selectAllDocuments.value) {
    selectedDocuments.value = props.documents.map(d => d.id)
  } else {
    selectedDocuments.value = []
  }
}

function getFileIcon(fileType: string): string {
  switch (fileType?.toLowerCase()) {
    case 'pdf': return '📄'
    case 'doc':
    case 'docx': return '📝'
    case 'ppt':
    case 'pptx': return '📊'
    case 'xls':
    case 'xlsx': return '📈'
    default: return '📄'
  }
}

// 工具函数
function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// 开始批量处理
async function startBatchProcess() {
  processing.value = true
  completedItems.value = 0
  totalItems.value = selectedVideos.value.length + selectedDocuments.value.length
  processingProgress.value = 0

  try {
    const results: any[] = []

    // 处理视频
    for (let i = 0; i < selectedVideos.value.length; i++) {
      const videoId = selectedVideos.value[i]
      const video = props.videos.find(v => v.id === videoId)
      
      if (video) {
        currentProcessingItem.value = `正在处理视频: ${video.title}`
        
        try {
          const requestData = {
            process_mode: videoProcessMode.value
          }
          
          const response = await videoService.processVideoWithSettings(videoId, requestData)
          
          if (response.data && response.data.code === 200) {
            results.push({
              type: 'video',
              id: videoId,
              title: video.title,
              status: 'success',
              message: '处理成功'
            })
          } else {
            results.push({
              type: 'video',
              id: videoId,
              title: video.title,
              status: 'error',
              message: response.data?.message || '处理失败'
            })
          }
        } catch (error) {
          results.push({
            type: 'video',
            id: videoId,
            title: video.title,
            status: 'error',
            message: (error as Error).message || '处理失败'
          })
        }
        
        completedItems.value++
        processingProgress.value = (completedItems.value / totalItems.value) * 100
      }
    }

    // 处理文档
    for (let i = 0; i < selectedDocuments.value.length; i++) {
      const documentId = selectedDocuments.value[i]
      const document = props.documents.find(d => d.id === documentId)
      
      if (document) {
        currentProcessingItem.value = `正在处理文档: ${document.title}`
        
        try {
          const requestData = {
            process_mode: documentProcessMode.value
          }
          
          const response = await documentService.processDocument(documentId, requestData)
          
          if (response.data && response.data.code === 200) {
            results.push({
              type: 'document',
              id: documentId,
              title: document.title,
              status: 'success',
              message: '处理成功'
            })
          } else {
            results.push({
              type: 'document',
              id: documentId,
              title: document.title,
              status: 'error',
              message: response.data?.message || '处理失败'
            })
          }
        } catch (error) {
          results.push({
            type: 'document',
            id: documentId,
            title: document.title,
            status: 'error',
            message: (error as Error).message || '处理失败'
          })
        }
        
        completedItems.value++
        processingProgress.value = (completedItems.value / totalItems.value) * 100
      }
    }

    // 处理完成
    currentProcessingItem.value = `批量处理完成，共处理 ${totalItems.value} 项`
    
    const successCount = results.filter(r => r.status === 'success').length
    const errorCount = results.filter(r => r.status === 'error').length
    
    ElMessage.success(`批量处理完成！成功: ${successCount} 项，失败: ${errorCount} 项`)
    
    emit('processed', results)
    
    // 延迟关闭，让用户看到完成状态
    setTimeout(() => {
      close()
    }, 2000)
    
  } catch (error) {
    console.error('批量处理失败:', error)
    ElMessage.error('批量处理失败: ' + ((error as Error).message || '未知错误'))
  } finally {
    processing.value = false
  }
}

// 自动获取状态并勾选未完成的内容
async function loadProcessingStatusAndAutoSelect() {
  if (loadingStatus.value) return
  
  loadingStatus.value = true
  try {
    const promises = []
    
    // 获取视频处理状态
    if (props.videos.length > 0) {
      const videoIds = props.videos.map(v => v.id)
      promises.push(
        videoService.getBatchProcessingStatus(videoIds)
          .then(response => {
            if (response.data.code === 200) {
              videoStatuses.value = response.data.data.videos
              // 自动勾选未完成的视频
              const uncompletedVideoIds = videoStatuses.value
                .filter(status => !status.error && !status.is_fully_completed)
                .map(status => status.video_id)
              selectedVideos.value = uncompletedVideoIds
              selectAllVideos.value = uncompletedVideoIds.length === props.videos.length
            }
          })
      )
    }
    
    // 获取文档处理状态
    if (props.documents.length > 0) {
      const documentIds = props.documents.map(d => d.id)
      promises.push(
        documentService.getBatchProcessingStatus(documentIds)
          .then(response => {
            if (response.data.code === 200) {
              documentStatuses.value = response.data.data.documents
              // 自动勾选未完成的文档
              const uncompletedDocumentIds = documentStatuses.value
                .filter(status => !status.error && !status.is_fully_completed)
                .map(status => status.document_id)
              selectedDocuments.value = uncompletedDocumentIds
              selectAllDocuments.value = uncompletedDocumentIds.length === props.documents.length
            }
          })
      )
    }
    
    await Promise.all(promises)
    
    // 显示状态统计
    const totalUncompletedVideos = videoStatuses.value.filter(s => !s.error && !s.is_fully_completed).length
    const totalUncompletedDocuments = documentStatuses.value.filter(s => !s.error && !s.is_fully_completed).length
    
    if (totalUncompletedVideos === 0 && totalUncompletedDocuments === 0) {
      ElMessage.info('所有内容都已完成处理，无需重新处理')
    } else {
      const message = `已自动选择 ${totalUncompletedVideos} 个未完成的视频和 ${totalUncompletedDocuments} 个未完成的文档`
      ElMessage.success(message)
    }
    
  } catch (error) {
    console.error('获取处理状态失败:', error)
    ElMessage.error('获取处理状态失败，请手动选择内容')
  } finally {
    loadingStatus.value = false
  }
}

// 获取视频的完成状态信息
function getVideoStatusInfo(videoId: string) {
  const status = videoStatuses.value.find(s => s.video_id === videoId)
  if (!status || status.error) {
    return { completed: false, percentage: 0, info: '状态未知' }
  }
  return {
    completed: status.is_fully_completed,
    percentage: status.completion_percentage || 0,
    info: `${status.completed_steps}/${status.total_steps} 步骤完成`
  }
}

// 获取文档的完成状态信息
function getDocumentStatusInfo(documentId: string) {
  const status = documentStatuses.value.find(s => s.document_id === documentId)
  if (!status || status.error) {
    return { completed: false, percentage: 0, info: '状态未知' }
  }
  return {
    completed: status.is_fully_completed,
    percentage: status.completion_percentage || 0,
    info: `${status.completed_steps}/${status.total_steps} 步骤完成`
  }
}

// 监听对话框开启，自动加载状态
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    // 对话框打开时，自动获取状态并选择未完成的内容
    loadProcessingStatusAndAutoSelect()
  }
})
</script>

<style scoped>
.content-selection {
  max-height: 400px;
  overflow-y: auto;
}

.video-selection-card,
.document-selection-card {
  transition: all 0.2s ease;
}

.video-selection-card:hover,
.document-selection-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.video-thumbnail {
  width: 100%;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-thumbnail img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.processing-settings {
  background: #f8f9fa;
  border-radius: 8px;
}

.processing-progress {
  background: #f5f5f5;
  border-radius: 8px;
}
</style>
