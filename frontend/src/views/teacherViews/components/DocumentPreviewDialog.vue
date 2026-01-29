<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:model-value="emit('update:modelValue', $event)"
    fullscreen
    transition="dialog-bottom-transition"
  >
    <v-card>
      <!-- 工具栏 -->
      <v-toolbar dark color="primary">
        <v-btn icon @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        
        <v-toolbar-title>
          <v-icon start>{{ getFileTypeIcon(document?.fileType) }}</v-icon>
          文档预览 - {{ document?.title }}
        </v-toolbar-title>
        
        <v-spacer></v-spacer>
        
        <v-btn icon @click="downloadDocument" title="下载文档">
          <v-icon>mdi-download</v-icon>
        </v-btn>
      </v-toolbar>

      <!-- 预览内容区域 -->
      <v-card-text class="pa-0 preview-container">
        <!-- PDF预览 - 优先显示 -->
        <div v-if="isPdf" class="pdf-container h-100">
          <object 
            :data="pdfViewerUrl" 
            type="application/pdf" 
            class="pdf-viewer"
            width="100%" 
            height="100%">
            <embed 
              :src="pdfViewerUrl" 
              type="application/pdf" 
              width="100%" 
              height="100%" />
            <p class="text-center pa-4">
              您的浏览器不支持PDF预览。
              <v-btn variant="outlined" size="small" @click="downloadDocument">
                点击下载
              </v-btn>
            </p>
          </object>
        </div>
        
        <!-- 加载状态 -->
        <div v-else-if="loading" class="d-flex justify-center align-center fill-height">
          <div class="text-center">
            <v-progress-circular 
              indeterminate 
              color="primary" 
              size="48"
              class="mb-4"
            ></v-progress-circular>
            <div class="text-body-1">正在加载预览...</div>
          </div>
        </div>
        
        <!-- 错误状态 -->
        <div v-else-if="error" class="d-flex align-center justify-center fill-height">
          <div class="text-center pa-6">
            <v-icon size="64" color="error" class="mb-4">mdi-alert-circle</v-icon>
            <div class="text-h6 mb-2">预览失败</div>
            <div class="text-body-2 text-medium-emphasis mb-4">{{ error }}</div>
            
            <div class="d-flex justify-center gap-2 flex-wrap">
              <v-btn 
                color="primary" 
                variant="outlined"
                @click="retryPreview"
                prepend-icon="mdi-refresh"
                size="small"
              >
                重试
              </v-btn>
              
              <v-btn
                color="success"
                variant="outlined"
                @click="downloadDocument"
                prepend-icon="mdi-download"
                size="small"
              >
                下载查看
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- Office文档预览选择 -->
        <div v-else-if="isOfficeDocument" class="office-preview-options pa-6">
          <div class="text-center mb-6">
            <v-icon 
              size="80" 
              :color="getFileTypeColor(document?.fileType)" 
              class="mb-4"
            >
              {{ getFileTypeIcon(document?.fileType) }}
            </v-icon>
            <h3 class="text-h5 mb-2">{{ document?.title }}</h3>
            <p class="text-body-2 text-medium-emphasis">请选择预览方式</p>
          </div>
          
          <v-row justify="center">
            <v-col cols="12" md="8" lg="6">
              <v-card class="mb-3 preview-option-card" hover @click="openWithGoogleDocs">
                <v-card-text class="d-flex align-center pa-4">
                  <v-icon size="32" color="orange" class="me-4">mdi-google</v-icon>
                  <div class="flex-grow-1">
                    <div class="font-weight-medium">Google Docs预览</div>
                    <div class="text-caption text-medium-emphasis">在线预览Office文档</div>
                  </div>
                  <v-icon>mdi-open-in-new</v-icon>
                </v-card-text>
              </v-card>
              
              <v-card class="mb-3 preview-option-card" hover @click="tryOfficeOnlinePreview">
                <v-card-text class="d-flex align-center pa-4">
                  <v-icon size="32" color="blue" class="me-4">mdi-microsoft-office</v-icon>
                  <div class="flex-grow-1">
                    <div class="font-weight-medium">Office Online预览</div>
                    <div class="text-caption text-medium-emphasis">使用微软Office Online查看</div>
                  </div>
                  <v-icon>mdi-open-in-new</v-icon>
                </v-card-text>
              </v-card>
              
              <v-card class="preview-option-card" hover @click="downloadDocument">
                <v-card-text class="d-flex align-center pa-4">
                  <v-icon size="32" color="purple" class="me-4">mdi-download</v-icon>
                  <div class="flex-grow-1">
                    <div class="font-weight-medium">下载到本地（推荐）</div>
                    <div class="text-caption text-medium-emphasis">下载后使用Office软件查看</div>
                  </div>
                  <v-icon>mdi-download</v-icon>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>
        
        <!-- 其他文件类型的直接预览 -->
        <iframe
          v-else-if="canPreview && previewUrl"
          :src="previewUrl"
          class="preview-iframe"
          frameborder="0"
          loading="lazy"
          :title="`预览 ${document?.title}`"
        ></iframe>
        
        <!-- 不支持预览的文件类型 -->
        <div v-else-if="!canPreview" class="d-flex align-center justify-center fill-height">
          <div class="text-center pa-6">
            <v-icon size="80" color="grey" class="mb-4">mdi-file-question</v-icon>
            <div class="text-h5 mb-2">暂不支持预览</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              当前文件格式不支持在线预览，请下载后查看
            </div>
            <v-btn
              color="primary"
              @click="downloadDocument"
              prepend-icon="mdi-download"
            >
              下载文件
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { documentService } from '../../../api/documentService'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  document: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

// 响应式数据
const loading = ref(false)
const error = ref('')
const previewUrl = ref('')

// 计算属性
const isPdf = computed(() => {
  if (!props.document?.fileType) return false
  const fileType = props.document.fileType.toLowerCase()
  return fileType.includes('pdf')
})

const isOfficeDocument = computed(() => {
  if (!props.document?.fileType) return false
  const fileType = props.document.fileType.toLowerCase()
  return ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].some(ext => fileType.includes(ext))
})

const canPreview = computed(() => {
  if (!props.document?.fileType) return false
  const fileType = props.document.fileType.toLowerCase()
  return ['pdf', 'txt', 'md', 'html', 'htm', 'xml', 'json'].some(ext => fileType.includes(ext))
})

// PDF预览URL（确保token正确编码）
const pdfViewerUrl = computed(() => {
  if (!props.document?.id) return ''
  const token = localStorage.getItem('wendao_token')
  if (!token) {
    console.warn('未找到认证token，预览可能失败')
    return ''
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
  // 确保token正确编码
  const encodedToken = encodeURIComponent(token)
  const url = `${baseUrl}/api/documents/${props.document.id}/preview?token=${encodedToken}`
  console.log('PDF预览URL:', url)
  console.log('使用的token:', token.substring(0, 20) + '...')
  return url
})

// 获取文件类型图标
function getFileTypeIcon(fileType: string) {
  if (!fileType) return 'mdi-file'
  const type = fileType.toLowerCase()
  if (type.includes('pdf')) return 'mdi-file-pdf-box'
  if (type.includes('doc')) return 'mdi-file-word'
  if (type.includes('xls')) return 'mdi-file-excel'
  if (type.includes('ppt')) return 'mdi-file-powerpoint'
  if (type.includes('txt')) return 'mdi-file-document'
  if (type.includes('image')) return 'mdi-file-image'
  return 'mdi-file'
}

// 获取文件类型颜色
function getFileTypeColor(fileType: string) {
  if (!fileType) return 'grey'
  const type = fileType.toLowerCase()
  if (type.includes('pdf')) return 'red'
  if (type.includes('doc')) return 'blue'
  if (type.includes('xls')) return 'green'
  if (type.includes('ppt')) return 'orange'
  if (type.includes('txt')) return 'grey'
  if (type.includes('image')) return 'purple'
  return 'grey'
}

// 关闭对话框
function close() {
  emit('update:modelValue', false)
}

// 加载预览
async function loadPreview() {
  if (!props.document?.id || !canPreview.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    // 清理之前的URL
    if (previewUrl.value) {
      window.URL.revokeObjectURL(previewUrl.value)
    }
    
    // 获取预览URL
    previewUrl.value = documentService.getPreviewUrl(props.document.id)
    
  } catch (err: any) {
    error.value = err.message || '预览加载失败'
    console.error('预览加载失败:', err)
  } finally {
    loading.value = false
  }
}

// 重试预览
function retryPreview() {
  loadPreview()
}

// 下载文档
async function downloadDocument() {
  if (!props.document?.id) return
  
  try {
    const blob = await documentService.downloadDocument(props.document.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = props.document.title || 'document'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
  }
}

// 在新窗口中打开
function openInNewWindow() {
  if (previewUrl.value) {
    window.open(previewUrl.value, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes')
  } else if (props.document?.id) {
    const directUrl = documentService.getPreviewUrl(props.document.id)
    window.open(directUrl, '_blank', 'width=1200,height=800,scrollbars=yes,resizable=yes')
  }
}

// 监听对话框打开/关闭
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen && props.document) {
    error.value = ''
    // 对于PDF文档，直接显示预览，不需要额外的加载逻辑
    // 只有非PDF且支持预览的文档才加载预览
    if (canPreview.value && !isPdf.value) {
      await loadPreview()
    }
  } else {
    // 清理资源
    if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
      window.URL.revokeObjectURL(previewUrl.value)
      previewUrl.value = ''
    }
  }
})

// 尝试Office Online预览（通过新窗口）
function tryOfficeOnlinePreview() {
  if (!props.document?.id) return
  
  const message = `Office Online预览需要文件可公开访问。

推荐方案：
1. 点击"下载查看"获得最佳体验
2. 尝试"Google Docs"预览

是否继续尝试Office Online预览？`

  if (confirm(message)) {
    const fileUrl = encodeURIComponent(documentService.getPreviewUrl(props.document.id))
    const officeUrl = `https://view.officeapps.live.com/op/embed.aspx?src=${fileUrl}`
    window.open(officeUrl, '_blank')
  }
}

// 使用Google Docs打开
function openWithGoogleDocs() {
  if (!props.document?.id) return
  
  const fileUrl = encodeURIComponent(documentService.getPreviewUrl(props.document.id))
  const googleUrl = `https://docs.google.com/viewer?url=${fileUrl}&embedded=true`
  window.open(googleUrl, '_blank')
}
</script>

<style scoped>
.preview-container {
  height: calc(100vh - 64px); /* 减去工具栏高度 */
  overflow: hidden;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

.preview-options {
  height: 100%;
  overflow-y: auto;
}

.preview-option-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.preview-option-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preview-toolbar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  min-height: 48px;
  background: #f8f9fa;
}

.preview-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-viewer .preview-iframe {
  flex: 1;
  height: calc(100% - 48px);
}

.office-preview-options {
  height: 100%;
  overflow-y: auto;
}

.fill-height {
  height: 100%;
}

.pdf-container {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
}
</style> 