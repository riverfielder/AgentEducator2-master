<template>
  <div class="document-viewer">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular indeterminate size="64" color="primary"></v-progress-circular>
      <p class="mt-4 text-h6">正在加载文档...</p>
    </div>

    <!-- 调试信息（开发模式） -->
    <div v-else-if="!document.id && !loading" class="d-flex flex-column justify-center align-center pa-8">
      <v-icon size="64" color="error">mdi-alert-circle</v-icon>
      <h3 class="text-h5 mt-4 text-error">文档加载失败</h3>
      <p class="text-body-1 mt-2 text-center">
        无法获取文档信息，请检查文档ID是否正确<br>
        文档ID: {{ documentId }}
      </p>
      <v-btn variant="outlined" color="primary" @click="loadDocument" class="mt-4">
        重新加载
      </v-btn>
    </div>

    <!-- 文档查看器 -->
    <div v-else class="viewer-container">
      <!-- 顶部工具栏 -->
      <div class="document-header">
        <div class="document-info">
          <v-breadcrumbs :items="breadcrumbs" class="pa-0">
            <template v-slot:prepend>
              <v-icon icon="mdi-file-document" size="small"></v-icon>
            </template>
          </v-breadcrumbs>
          <h2 class="document-title" @click="goBack">{{ document.title }}</h2>
          <p v-if="document.description" class="document-description">{{ document.description }}</p>
        </div>
        <div class="document-actions">
          <v-btn 
            variant="outlined" 
            prepend-icon="mdi-download" 
            @click="downloadDocument"
            class="mr-2">
            下载文档
          </v-btn>
          <v-btn 
            variant="outlined" 
            prepend-icon="mdi-arrow-left" 
            @click="goBack">
            返回
          </v-btn>
        </div>
      </div>

      <!-- 主内容区域 -->
      <div class="main-container" ref="mainContainer">
        <!-- 左侧：PDF预览区域 -->
        <div class="document-preview" :style="{ width: documentWidth + '%' }">
          <div class="h-100">
              <!-- 加载状态 -->
              <div v-if="loading" class="d-flex justify-center align-center h-100">
                <div class="text-center">
                  <v-progress-circular indeterminate size="32" color="primary"></v-progress-circular>
                  <p class="mt-2 text-body-2">正在加载文档...</p>
                </div>
              </div>
              
              <!-- PDF预览 -->
              <div v-else-if="isPdfDocument" class="pdf-container h-100">
                <object 
                  ref="pdfObject"
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
              
              <!-- 其他文件类型 -->
              <div v-else class="d-flex justify-center align-center h-100">
                <div class="text-center">
                  <v-icon size="64" color="grey-lighten-1">mdi-file-outline</v-icon>
                  <p class="mt-2 text-body-1">暂不支持此文件类型的预览</p>
                  <v-btn variant="outlined" color="primary" @click="downloadDocument">
                    下载文档
                  </v-btn>
                </div>
              </div>
          </div>
        </div>

        <!-- 分隔条 -->
        <div 
          v-if="!sidebarCollapsed"
          class="resizer" 
          @mousedown="startResize">
        </div>

        <!-- 右侧：AI分析侧边栏 -->
        <div 
          v-if="!sidebarCollapsed"
          class="sidebar-container" 
          :style="{ width: `${100 - documentWidth}%` }">
          
          <!-- 侧边栏头部 -->
          <div class="sidebar-header">
            <h3>AI 分析</h3>
            <v-btn 
              icon="mdi-close" 
              variant="text" 
              size="small"
              @click="toggleSidebar">
            </v-btn>
          </div>

          <!-- 标签页 -->
          <v-tabs v-model="activeTab" class="sidebar-tabs">
            <v-tab value="summary">摘要</v-tab>
            <v-tab value="chat">问答</v-tab>
            <v-tab value="comments">随笔</v-tab>
          </v-tabs>

          <!-- 标签页内容 -->
          <v-tabs-window v-model="activeTab" class="sidebar-content">            <!-- 文档摘要 -->
            <v-tabs-window-item value="summary">
              <div class="tab-content summary-content">
                <!-- 当前分段信息 -->
                <div v-if="currentSegment !== null" class="current-segment-info pa-3 mb-3 bg-blue-lighten-5 rounded">
                  <div class="d-flex align-center mb-2">
                    <v-icon color="blue" class="me-2">mdi-bookmark</v-icon>
                    <span class="text-subtitle-2 font-weight-medium">当前分段 #{{ currentSegment }}</span>
                  </div>
                  <div class="text-caption text-grey-darken-1">
                    已定位到文档中的相关内容
                  </div>
                </div>
                
                <DocumentSummary 
                  :document-id="documentId" 
                  :current-segment="currentSegment" />
              </div>
            </v-tabs-window-item><!-- 问答 -->
            <v-tabs-window-item value="chat">
              <div class="tab-content chat-content">
                <AIChat 
                  :video-id="undefined"
                  :course-id="document?.course_id"
                  :document-id="documentId"
                  @jump-to-document-segment="handleDocumentSegmentJump"
                  class="document-chat h-100" />
              </div>
            </v-tabs-window-item>            <!-- 文档笔记 -->
            <v-tabs-window-item value="comments">
              <div class="tab-content comments-content">
                <DocumentNotes :document-id="documentId" />
              </div>
            </v-tabs-window-item>
          </v-tabs-window>
        </div>

        <!-- 展开按钮（当侧边栏收起时显示） -->
        <v-btn
          v-if="sidebarCollapsed"
          class="expand-sidebar-btn"
          icon="mdi-chevron-left"
          color="primary"
          @click="toggleSidebar">
        </v-btn>
      </div>
    </div>

    <!-- 错误提示 -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="5000">
      {{ errorMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="errorSnackbar = false">关闭</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { documentService, type Document, type DocumentSegment } from '@/api/documentService'
import DocumentSummary from '../components/DocumentSummary.vue'
import DocumentComments from '../components/DocumentComments.vue'
import DocumentNotes from '../components/DocumentNotes.vue'
import AIChat from '../components/AIChat.vue'

// 路由和基础状态
const route = useRoute()
const router = useRouter()
const documentId = computed(() => route.params.documentId as string)

// 文档数据
const document = ref<any>({})
const documentUrl = ref<string>('')
const loading = ref(true)

// UI状态
const activeTab = ref('summary')
const sidebarCollapsed = ref(false)
const documentWidth = ref(65) // 文档区域宽度百分比

// 错误处理
const errorSnackbar = ref(false)
const errorMessage = ref('')

// 新增状态
const segments = ref<DocumentSegment[]>([])
const currentSegment = ref<number | null>(null)
const pdfObject = ref<HTMLObjectElement | null>(null)

// 阅读时间统计相关
const readingStartTime = ref<Date | null>(null)
const totalReadingTime = ref(0) // 累计阅读时间（秒）
const readingTimer = ref<number | null>(null)
const isDocumentVisible = ref(true) // 文档是否在视窗中可见
const lastProgressUpdate = ref<Date | null>(null)

// 调整大小相关
let isResizing = false

// 面包屑导航
const breadcrumbs = computed(() => [
  { title: '课程', disabled: true },
  { title: document.value.course?.name || '课程', href: `/course/${document.value.course?.id || document.value.courseId}` },
  { title: document.value.title || '文档', disabled: true }
])

// 计算属性
const pdfViewerUrl = computed(() => {
  if (!document.value?.id) return ''
    // 使用正确的预览API URL，而不是直接使用文件路径
  return documentService.getPreviewUrl(document.value.id)
})

// 判断是否为PDF文件
const isPdfDocument = computed(() => {
  if (!document.value?.fileType) return false
  const fileType = document.value.fileType.toLowerCase()
  console.log('检查文件类型:', fileType)
  return fileType === 'pdf' || fileType === 'application/pdf' || fileType.includes('pdf')
})

// 生命周期
onMounted(async () => {
  await loadDocument()
  startReadingTracking()
  window.addEventListener('mousemove', handleResize)
  window.addEventListener('mouseup', stopResize)
  window.addEventListener('visibilitychange', handleVisibilityChange)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  stopReadingTracking()
  window.removeEventListener('mousemove', handleResize)
  window.removeEventListener('mouseup', stopResize)
  window.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

// 加载文档信息
const loadDocument = async () => {
  try {
    loading.value = true
    console.log('加载文档详情，documentId:', documentId.value)
    
    const response = await documentService.getDocumentDetail(documentId.value)
    console.log('API响应:', response)
    
    // 检查axios响应结构
    if (response && response.data) {
      if (response.data.code === 200 && response.data.data) {
        document.value = response.data.data
        console.log('成功加载文档信息:', document.value)
        console.log('文档文件类型:', document.value.fileType)
        console.log('isPdfDocument计算结果:', isPdfDocument.value)
        
        // 加载文档分段信息
        await loadDocumentSegments()
        
        // 加载当前阅读进度
        await loadReadingProgress()
      } else {
        console.error('API返回错误:', response.data)
        throw new Error(response.data.message || '获取文档信息失败')
      }
    } else {
      console.error('响应结构异常:', response)
      throw new Error('服务器响应异常')
    }
  } catch (error: any) {
    console.error('加载文档失败:', error)
    if (error.response) {
      console.error('错误响应:', error.response)
      showError(`加载文档失败: ${error.response.data?.message || error.message}`)
    } else {
      showError(`加载文档失败: ${error.message || '网络错误'}`)
    }
  } finally {
    loading.value = false
  }
}

// 加载文档分段信息
const loadDocumentSegments = async () => {
  try {
    const response = await documentService.getDocumentSegments(documentId.value)
    if (response.data.code === 200) {
      segments.value = response.data.data
      console.log('成功加载文档分段:', segments.value)
    }
  } catch (error) {
    console.error('加载文档分段失败:', error)
  }
}

// 下载文档
const downloadDocument = async () => {
  if (!document.value?.id) {
    showError('文档信息不完整，无法下载')
    return
  }
  
  try {
    // 使用后端API下载文档
    const blob = await documentService.downloadDocument(document.value.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    
    // 设置下载文件名，优先使用文档标题，否则使用原文件名
    let filename = document.value.title || 'document'
    
    // 如果标题没有扩展名，尝试从file_url中提取
    if (!filename.includes('.') && document.value.file_url) {
      const urlParts = document.value.file_url.split('/')
      const originalFilename = urlParts[urlParts.length - 1]
      if (originalFilename.includes('.')) {
        const extension = originalFilename.substring(originalFilename.lastIndexOf('.'))
        filename += extension
      }
    }
    
    link.download = filename
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
    
    // 清理URL对象
    window.URL.revokeObjectURL(url)
    
    console.log('文档下载成功')
  } catch (error) {
    console.error('下载文档失败:', error)
    showError('文档下载失败，请稍后重试')
  }
}

// 返回上级页面
const goBack = () => {
  const courseId = document.value.course?.id || document.value.courseId
  if (courseId) {
    router.push(`/course/${courseId}`)
  } else {
    router.go(-1)
  }
}

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 开始调整大小
const startResize = (e: MouseEvent) => {
  isResizing = true
  e.preventDefault()
}

// 处理调整大小
const handleResize = (e: MouseEvent) => {
  if (!isResizing) return
  
  const container = window.document.querySelector('.main-container') as HTMLElement
  if (!container) return
  
  const containerRect = container.getBoundingClientRect()
  const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100
  
  // 限制宽度范围
  if (newWidth >= 30 && newWidth <= 80) {
    documentWidth.value = newWidth
  }
}

// 停止调整大小
const stopResize = () => {
  isResizing = false
}

// 跳转到指定分段
const jumpToSegment = async (segmentNumber: number) => {
  try {
    currentSegment.value = segmentNumber
    
    // 获取分段内容
    const response = await documentService.getDocumentSegment(documentId.value, segmentNumber)
    if (response.data.code === 200) {
      const segment = response.data.data as DocumentSegment
      
      // 如果是PDF文档，尝试在PDF中搜索文本
      if (isPdfDocument.value && pdfObject.value) {
        await searchInPdf(segment.content)
      }
      
      // 切换到摘要标签页显示分段信息
      activeTab.value = 'summary'
      
      console.log('跳转到分段:', segment)
    }
  } catch (error) {
    console.error('跳转到分段失败:', error)
    showError('跳转到分段失败')
  }
}

// 在PDF中搜索文本
const searchInPdf = async (content: string) => {
  if (!pdfObject.value) return
  
  try {
    // 提取纯文本（去除markdown格式）
    const plainText = extractPlainText(content)
    
    // 找到最长的连续文本片段
    const longestText = findLongestTextSegment(plainText)
    
    if (longestText && longestText.length > 10) {
      // 使用PDF.js的搜索功能
      const pdfWindow = pdfObject.value?.contentWindow as any
      if (pdfWindow && pdfWindow.PDFViewerApplication) {
        const searchText = longestText.substring(0, 50) // 限制搜索文本长度
        pdfWindow.PDFViewerApplication.findController.executeCommand('find', {
          query: searchText,
          highlightAll: true,
          findPrevious: false
        })
      }
    }
  } catch (error) {
    console.error('PDF搜索失败:', error)
  }
}

// 提取纯文本（去除markdown格式）
const extractPlainText = (content: string): string => {
  return content
    .replace(/[#*_`\[\]()]/g, '') // 去除markdown标记
    .replace(/\s+/g, ' ') // 合并多个空白字符
    .trim()
}

// 找到最长的连续文本片段
const findLongestTextSegment = (text: string): string => {
  const sentences = text.split(/[。！？.!?]/).filter(s => s.trim().length > 0)
  return sentences.reduce((longest, current) => 
    current.length > longest.length ? current : longest, '')
}

// 显示错误信息
const showError = (message: string) => {
  errorMessage.value = message
  errorSnackbar.value = true
}

// 处理来自AI助手的文档分段跳转
const handleDocumentSegmentJump = (documentId: string, segmentNumber: number) => {
  if (documentId === route.params.documentId) {
    jumpToSegment(segmentNumber)
  } else {
    // 如果是其他文档，导航到该文档
    router.push({
      path: `/document/${documentId}`,
      query: { segment: segmentNumber.toString() }
    })
  }
}

// 监听路由查询参数变化
watch(() => route.query.segment, (segmentNumber) => {
  if (segmentNumber && segments.value.length > 0) {
    const num = parseInt(segmentNumber as string)
    if (!isNaN(num)) {
      nextTick(() => {
        jumpToSegment(num)
      })
    }
  }
}, { immediate: true })

// ===================== 阅读时间统计相关函数 =====================

// 开始阅读时间追踪
const startReadingTracking = () => {
  readingStartTime.value = new Date()
  isDocumentVisible.value = true
  
  // 设置定时器，每30秒上报一次阅读时间
  readingTimer.value = window.setInterval(() => {
    if (isDocumentVisible.value && readingStartTime.value) {
      const currentTime = new Date()
      const sessionReadingTime = Math.floor((currentTime.getTime() - readingStartTime.value.getTime()) / 1000)
      
      // 如果本次会话阅读时间超过5秒，才上报
      if (sessionReadingTime >= 5) {
        updateReadingProgress(sessionReadingTime)
        readingStartTime.value = currentTime // 重置开始时间
      }
    }
  }, 30000) // 30秒间隔
}

// 停止阅读时间追踪
const stopReadingTracking = () => {
  if (readingTimer.value) {
    clearInterval(readingTimer.value)
    readingTimer.value = null
  }
  
  // 最后一次上报
  if (readingStartTime.value && isDocumentVisible.value) {
    const currentTime = new Date()
    const sessionReadingTime = Math.floor((currentTime.getTime() - readingStartTime.value.getTime()) / 1000)
    if (sessionReadingTime >= 1) {
      updateReadingProgress(sessionReadingTime)
    }
  }
  
  readingStartTime.value = null
}

// 处理页面可见性变化
const handleVisibilityChange = () => {
  if (window.document.hidden) {
    // 页面不可见，暂停计时并上报当前进度
    isDocumentVisible.value = false
    if (readingStartTime.value) {
      const currentTime = new Date()
      const sessionReadingTime = Math.floor((currentTime.getTime() - readingStartTime.value.getTime()) / 1000)
      if (sessionReadingTime >= 1) {
        updateReadingProgress(sessionReadingTime)
      }
    }
  } else {
    // 页面可见，重新开始计时
    isDocumentVisible.value = true
    readingStartTime.value = new Date()
  }
}

// 处理页面关闭前事件
const handleBeforeUnload = () => {
  stopReadingTracking()
}

// 更新阅读进度
const updateReadingProgress = async (readingTime: number) => {
  try {
    if (!document.value?.id || readingTime <= 0) return
    
    // 避免重复请求，限制最小间隔为10秒
    const now = new Date()
    if (lastProgressUpdate.value && 
        (now.getTime() - lastProgressUpdate.value.getTime()) < 10000) {
      return
    }
    
    const response = await documentService.updateDocumentProgress(document.value.id, {
      reading_time: readingTime
    })
    
    if (response.data.code === 200) {
      totalReadingTime.value = response.data.data.total_reading_time
      lastProgressUpdate.value = now
      
      console.log(`阅读进度更新成功: +${readingTime}秒, 总计: ${totalReadingTime.value}秒, 进度: ${response.data.data.progress_percentage}%`)
      
      // 如果达到100%完成度，可以显示提示
      if (response.data.data.is_completed) {
        console.log('恭喜！文档阅读完成')
      }
    }
  } catch (error: any) {
    console.error('更新阅读进度失败:', error)
    // 静默失败，不影响用户体验
  }
}

// 获取当前阅读进度
const loadReadingProgress = async () => {
  try {
    if (!document.value?.id) return
    
    const response = await documentService.getDocumentProgress(document.value.id)
    if (response.data.code === 200) {
      totalReadingTime.value = response.data.data.total_reading_time
      console.log(`当前阅读进度: ${response.data.data.total_reading_time}秒, ${response.data.data.progress_percentage}%`)
    }
  } catch (error: any) {
    console.error('获取阅读进度失败:', error)
  }
}
</script>

<style scoped>
.document-viewer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
}

.viewer-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.document-header {
  background: white;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-shrink: 0;
}

.document-info {
  flex: 1;
}

.document-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin: 8px 0 4px 0;
  color: #1a1a1a;
}

.document-description {
  color: #666;
  margin: 0;
}

.document-actions {
  display: flex;
  align-items: center;
}

.main-container {
  display: flex;
  flex: 1;
  position: relative;
  overflow: hidden;
}

.document-preview {
  background: white;
  position: relative;
  transition: width 0.3s ease;
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

.resizer {
  width: 4px;
  background: #e0e0e0;
  cursor: col-resize;
  position: relative;
  flex-shrink: 0;
}

.resizer:hover {
  background: #2196f3;
}

.sidebar-container {
  display: flex;
  flex-direction: column;
  background: white;
  border-left: 1px solid #e0e0e0;
  transition: width 0.3s ease;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 500;
}

.sidebar-tabs {
  flex-shrink: 0;
  border-bottom: 1px solid #e0e0e0;
}

.sidebar-content {
  flex: 1;
  overflow: hidden;
}

.tab-content {
  height: calc(100vh - 280px); /* 进一步减少预留空间，增加可用高度 */
  overflow: hidden; /* 改为hidden，让AIChat自己处理滚动 */
  padding: 0; /* 移除padding，让AIChat组件自己控制间距 */
  display: flex;
  flex-direction: column;
}

/* 为摘要和笔记页面添加padding和滚动 */
.summary-content,
.comments-content {
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* AI对话页面不需要padding，充满整个容器 */
.chat-content {
  padding: 0;
  overflow: hidden;
}

/* 确保AIChat组件占满整个高度 */
.chat-content .document-chat {
  height: 100%;
}

.loading-state {
  display: flex;
  align-items: center;
  color: #666;
}

.summary-placeholder,
.chat-placeholder,
.comments-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
}

.expand-sidebar-btn {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* 深层组件样式覆盖 */
:deep(.v-tabs-window-item) {
  height: 100%;
}

:deep(.v-breadcrumbs) {
  padding: 0;
}

:deep(.v-breadcrumbs-item) {
  font-size: 0.875rem;
}

/* 确保禁用的面包屑项目保持黑色 */
:deep(.v-breadcrumbs-item--disabled) {
  color: rgba(0, 0, 0, 0.87) !important;
  opacity: 1 !important;
}

/* 强制显示滚动条 */
.tab-content::-webkit-scrollbar {
  width: 8px !important;
}

.tab-content::-webkit-scrollbar-track {
  background: #f5f5f5 !important;
  border-radius: 4px !important;
}

.tab-content::-webkit-scrollbar-thumb {
  background: #bdbdbd !important;
  border-radius: 4px !important;
  border: 2px solid #f5f5f5 !important;
}

.tab-content::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e !important;
}

/* 文档聊天特定样式 */
.document-chat {
  height: 100%;
  width: 100%;
  position: relative;
  z-index: 1;
}

/* 确保AI聊天组件在文档查看器中正确显示 */
:deep(.ai-chat-container) {
  height: 100% !important;
  min-height: 0;
  background: white;
  display: flex !important;
  flex-direction: column !important;
  max-height: 100% !important; /* 确保不会超出容器 */
}

:deep(.chat-messages-container) {
  flex: 1 !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  padding: 8px !important;
  padding-bottom: 8px !important; /* 保持适当的底部padding */
}

:deep(.chat-input-container) {
  flex-shrink: 0 !important;
  background: white;
  border-top: 1px solid #e0e0e0;
  margin-bottom: 0 !important;
  padding-bottom: 12px !important; /* 增加底部间距 */
  min-height: 120px !important; /* 确保输入区域有最小高度 */
}

/* 确保对话框和弹窗有足够高的z-index */
:deep(.v-dialog) {
  z-index: 2000 !important;
}

:deep(.v-overlay) {
  z-index: 1900 !important;
}

:deep(.v-navigation-drawer) {
  z-index: 1800 !important;
}
</style>