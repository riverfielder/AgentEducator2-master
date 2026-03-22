<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="1200" persistent>
    <v-card>
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon start color="primary">mdi-upload</v-icon>
        上传课程内容
        <v-spacer></v-spacer>
        <v-btn icon @click="close" :disabled="uploading">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text class="pa-6" style="max-height: 70vh; overflow-y: auto;">
        <!-- 上传区域 -->
        <div class="upload-section">
          <!-- 文件选择 -->
          <v-file-input
            v-model="allFiles"
            multiple
            label="选择视频文件、字幕文件或教学资料"
            variant="outlined"
            density="compact"
            accept="video/*,.json,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
            class="mb-4"
          ></v-file-input>
          
          <!-- 显示匹配结果 -->
          <div v-if="allFiles.length" class="selected-files mb-4">
            <v-card variant="outlined" class="pa-3">
              <v-card-subtitle>文件匹配情况</v-card-subtitle>
              <!-- 视频和字幕匹配 -->
              <div v-if="fileMatches.length > 0">
                <div class="text-subtitle-2 mb-2">视频文件</div>
                <div v-for="match in fileMatches" :key="match.video.name" class="mb-2">
                  <div class="d-flex align-center">
                    <v-icon color="primary" class="mr-2">mdi-video</v-icon>
                    <span class="text-body-2">{{ match.video.name }}</span>
                  </div>
                  <div v-if="match.subtitle" class="d-flex align-center ml-6">
                    <v-icon color="success" class="mr-2">mdi-subtitles</v-icon>
                    <span class="text-body-2 text-success">{{ match.subtitle.name }}</span>
                  </div>
                  <div v-else class="d-flex align-center ml-6">
                    <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
                    <span class="text-body-2 text-warning">未找到匹配的字幕文件</span>
                  </div>
                </div>
              </div>
              <!-- 教学资料 -->
              <div v-if="documentFiles.length > 0" class="mt-4">
                <div class="text-subtitle-2 mb-2">教学资料</div>
                <div v-for="file in documentFiles" :key="file.name" class="mb-2">
                  <div class="d-flex align-center">
                    <v-icon :color="getFileIconColor(file)" class="mr-2">{{ getFileIcon(file) }}</v-icon>
                    <span class="text-body-2">{{ file.name }}</span>
                    <span class="text-caption ml-2">({{ formatFileSize(file.size) }})</span>
                  </div>
                </div>
              </div>
            </v-card>
          </div>
              
          <!-- 智能处理设置 - 简化版本 -->
          <div v-if="allFiles.length" class="processing-settings mb-4">
            <!-- 视频处理设置 -->
            <v-card v-if="hasVideoFiles" variant="outlined" class="pa-4 mb-4">
              <v-card-subtitle class="pa-0 mb-3">
                <v-icon color="primary" class="mr-2">mdi-video</v-icon>
                视频处理设置
              </v-card-subtitle>
              
              <v-alert type="info" variant="tonal" density="compact">
                <v-icon start size="small">mdi-auto-fix</v-icon>
                上传的视频将自动进行完整处理（关键帧提取、文字识别、语音识别、向量化、智能摘要）
              </v-alert>
            </v-card>
          
            <!-- 文档处理设置 -->
            <v-card v-if="hasDocumentFiles" variant="outlined" class="pa-4">
              <v-card-subtitle class="pa-0 mb-3">
                <v-icon color="orange" class="mr-2">mdi-file-document-multiple</v-icon>
                文档处理设置
              </v-card-subtitle>
              
              <v-alert type="info" variant="tonal" density="compact">
                <v-icon start size="small">mdi-auto-fix</v-icon>
                上传的文档将自动进行完整处理（格式转换、智能分段、向量化、智能摘要）
              </v-alert>
            </v-card>
          </div>

          <!-- 上传进度条 -->
          <div v-if="uploading" class="upload-progress mb-4">
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-body-2">
                {{ isProcessing ? '处理进度' : '上传进度' }}
              </span>
              <span class="text-body-2">{{ uploadProgress }}%</span>
            </div>
            <v-progress-linear
              v-model="uploadProgress"
              height="8"
              rounded
              :color="isProcessing ? 'success' : 'primary'"
              :striped="isProcessing"
            ></v-progress-linear>
            
            <!-- 处理状态显示 -->
            <div v-if="processingStatus" class="text-caption text-medium-emphasis mt-2">
              <v-icon v-if="isProcessing" class="mr-1" size="small">mdi-cog</v-icon>
              {{ processingStatus }}
            </div>
          </div>
        </div>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="pa-6">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="close" :disabled="uploading">
          取消
        </v-btn>
        <v-btn
          color="primary"
          size="large"
          :loading="uploading"
          :disabled="!allFiles.length"
          @click="uploadFiles"
        >
          <v-icon start>mdi-cloud-upload</v-icon>
          上传文件
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { documentService } from '../../../api/documentService'
import videoService from '../../../api/videoService'

interface Props {
  modelValue: boolean
  courseId: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  uploaded: [result: any]
}>()

// 响应式数据
const allFiles = ref<File[]>([])
const uploading = ref(false)
const uploadProgress = ref(0)
const processingStatus = ref('')
const isProcessing = ref(false)

// 处理设置（简化版本）
const videoPreviewMode = ref(false)
const documentPreviewMode = ref(false)

// 计算属性
const fileMatches = computed(() => {
  if (!allFiles.value || allFiles.value.length === 0) return []
  
  const videoFiles = allFiles.value.filter(file => file.type.startsWith('video/'))
  const subtitleFiles = allFiles.value.filter(file => file.name.endsWith('.json'))
  
  return videoFiles.map(video => {
    const videoName = video.name.replace(/\.[^/.]+$/, '')
    const matchingSubtitle = subtitleFiles.find(subtitle => {
      const subtitleName = subtitle.name.replace(/\.[^/.]+$/, '')
      return subtitleName === videoName
    })
    
    return {
      video,
      subtitle: matchingSubtitle
    }
  })
})

const documentFiles = computed(() => {
  if (!allFiles.value || allFiles.value.length === 0) return []
  
  const documentTypes = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']
  return allFiles.value.filter(file => 
    documentTypes.some(type => file.name.toLowerCase().endsWith(type))
  )
})

const hasVideoFiles = computed(() => {
  return fileMatches.value.length > 0
})

const hasDocumentFiles = computed(() => {
  return documentFiles.value.length > 0
})

// 方法
function close() {
  if (!uploading.value) {
    emit('update:modelValue', false)
    resetForm()
  }
}

function resetForm() {
  allFiles.value = []
  uploadProgress.value = 0
  processingStatus.value = ''
  isProcessing.value = false
  videoPreviewMode.value = false
  documentPreviewMode.value = false
}

function getFileIcon(file: File): string {
  const name = file.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'mdi-file-pdf-box'
  if (name.endsWith('.doc') || name.endsWith('.docx')) return 'mdi-file-word-box'
  if (name.endsWith('.ppt') || name.endsWith('.pptx')) return 'mdi-file-powerpoint-box'
  if (name.endsWith('.xls') || name.endsWith('.xlsx')) return 'mdi-file-excel-box'
  return 'mdi-file-document'
}

function getFileIconColor(file: File): string {
  const name = file.name.toLowerCase()
  if (name.endsWith('.pdf')) return 'red'
  if (name.endsWith('.doc') || name.endsWith('.docx')) return 'blue'
  if (name.endsWith('.ppt') || name.endsWith('.pptx')) return 'orange'
  if (name.endsWith('.xls') || name.endsWith('.xlsx')) return 'green'
  return 'grey'
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 上传文件
async function uploadFiles() {
  if (!allFiles.value.length) return
  
  uploading.value = true
  uploadProgress.value = 0
  
  try {
    const totalFiles = allFiles.value.length
    let completedUploads = 0
    
    const updateUploadProgress = () => {
      const newProgress = Math.round((completedUploads / totalFiles) * 100)
      uploadProgress.value = newProgress
    }
    
    const uploadResults = {
      videos: [] as any[],
      documents: [] as any[]
    }
    
    // 处理视频文件
    for (const match of fileMatches.value) {
      try {
        const result = await uploadVideoWithSubtitle(match.video, match.subtitle)
        if (result && result.type === 'video') {
          uploadResults.videos.push(result.data)
        }
        completedUploads++
        updateUploadProgress()
      } catch (error) {
        console.error('视频上传失败:', match.video.name, error)
        completedUploads++
        updateUploadProgress()
      }
    }
    
    // 处理文档文件
    for (const docFile of documentFiles.value) {
      try {
        const result = await uploadDocumentFile(docFile)
        if (result && result.type === 'document') {
          uploadResults.documents.push(result.data)
        }
        completedUploads++
        updateUploadProgress()
      } catch (error) {
        console.error('文档上传失败:', docFile.name, error)
        completedUploads++
        updateUploadProgress()
      }
    }
    
    uploadProgress.value = 100
    processingStatus.value = '上传完成！'

    console.log('上传完成:', uploadResults)
    emit('uploaded', uploadResults)
    
    setTimeout(() => {
      close()
    }, 2000)
    
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error('上传失败: ' + ((error as Error).message || '未知错误'))
  } finally {
    uploading.value = false
    isProcessing.value = false
  }
}

// 上传视频（带字幕）
async function uploadVideoWithSubtitle(videoFile: File, subtitleFile?: File) {
  try {
    const formData = new FormData()
    formData.append('file', videoFile)
    formData.append('courseId', props.courseId)
    formData.append('title', videoFile.name.replace(/\.[^/.]+$/, ''))
    formData.append('description', `上传的视频文件：${videoFile.name}`)
    
    if (subtitleFile) {
      formData.append('json_sub', subtitleFile)
    }
    
    // 添加预览模式设置
    if (videoPreviewMode.value) {
      formData.append('previewMode', 'true')
    }
    
    const response = await videoService.uploadVideo(formData)
    
    if (response.data.code === 200) {
      return {
        type: 'video',
        data: response.data.data
      }
    } else {
      throw new Error(response.data.message || '视频上传失败')
    }
  } catch (error) {
    console.error('视频上传失败:', videoFile.name, error)
    throw error
  }
}

// 上传文档文件
async function uploadDocumentFile(documentFile: File) {
  try {
    const formData = new FormData()
    formData.append('file', documentFile)
    formData.append('courseId', props.courseId)
    formData.append('title', documentFile.name.replace(/\.[^/.]+$/, ''))
    formData.append('description', `上传的文档文件：${documentFile.name}`)
    

    
    const api = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:5000'),
      timeout: 60000
    })
    
    const token = localStorage.getItem('wendao_token')
    if (token) {
      api.defaults.headers.Authorization = `Bearer ${token}`
    }
    
    const response = await api.post('/api/uploads/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.code === 200) {
      return {
        type: 'document',
        data: response.data.data
      }
    } else {
      throw new Error(response.data.message || '文档上传失败')
    }
  } catch (error) {
    console.error('文档上传失败:', documentFile.name, error)
    throw error
  }
}
</script>

<style scoped>
.upload-section {
  min-height: 300px;
}

.selected-files {
  max-height: 300px;
  overflow-y: auto;
}

.processing-settings {
  background: #f8f9fa;
  border-radius: 8px;
}

.upload-progress {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
}

.selected-files::-webkit-scrollbar {
  width: 6px;
}

.selected-files::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.selected-files::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.selected-files::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
