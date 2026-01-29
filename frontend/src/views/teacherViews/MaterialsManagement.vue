<template>
  <div class="materials-management">
    <v-container fluid class="pa-4">
      <!-- 页面头部 -->
      <v-card class="header-card mb-4">
        <v-card-text class="pa-6">
          <v-row align="center" no-gutters>
            <!-- 左侧标题区域 -->
            <v-col cols="12" md="4" class="d-flex align-center">
              <v-icon color="white" size="large" class="me-3">mdi-folder-multiple</v-icon>
              <span class="text-h5 text-white font-weight-bold">资料管理</span>
            </v-col>
            
            <!-- 右侧操作区域 -->
            <v-col cols="12" md="8" class="d-flex align-center justify-end">
          <!-- 课程选择器 -->
          <v-select
            v-model="selectedCourseId"
            :items="courses"
            item-title="name"
            item-value="id"
            label="选择课程"
            variant="outlined"
            density="compact"
            clearable
                class="course-selector me-4"
                style="min-width: 250px; max-width: 300px;"
            bg-color="white"
                color="primary"
                hide-details
          >
            <template v-slot:prepend-inner>
                  <v-icon color="primary" size="small">mdi-school</v-icon>
            </template>
          </v-select>
          
          <!-- 上传资料按钮 -->
          <v-btn
            color="white"
            variant="outlined"
            size="large"
            prepend-icon="mdi-upload"
            @click="showUploadDialog = true"
            :disabled="!selectedCourseId"
                class="upload-btn flex-shrink-0"
          >
            上传资料
          </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 搜索和筛选栏 -->
      <v-card class="filter-card mb-4">
        <v-card-text class="pa-4">
          <v-row align="center">
            <v-col cols="12" md="4">
              <v-text-field
                v-model="searchQuery"
                prepend-inner-icon="mdi-magnify"
                label="搜索资料..."
                variant="outlined"
                density="compact"
                clearable
                @input="handleSearch"
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="typeFilter"
                :items="typeFilterOptions"
                label="资料类型"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="sortBy"
                :items="sortOptions"
                label="排序方式"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 统计信息 -->
      <v-row class="mb-4">
        <v-col cols="12" md="3">
          <v-card class="stats-card">
            <v-card-text class="pa-4 text-center">
              <v-icon size="32" color="primary" class="mb-2">mdi-video</v-icon>
              <div class="text-h4 font-weight-bold text-primary">{{ videoStats.total }}</div>
              <div class="text-body-2 text-medium-emphasis">视频总数</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="3">
          <v-card class="stats-card">
            <v-card-text class="pa-4 text-center">
              <v-icon size="32" color="green" class="mb-2">mdi-file-document</v-icon>
              <div class="text-h4 font-weight-bold text-green">{{ documentStats.total }}</div>
              <div class="text-body-2 text-medium-emphasis">文档总数</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="3">
          <v-card class="stats-card">
            <v-card-text class="pa-4 text-center">
              <v-icon size="32" color="orange" class="mb-2">mdi-harddisk</v-icon>
              <div class="text-h4 font-weight-bold text-orange">{{ formatFileSize(totalSize) }}</div>
              <div class="text-body-2 text-medium-emphasis">课件存储空间</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" md="3">
          <v-card class="stats-card">
            <v-card-text class="pa-4 text-center">
              <v-icon size="32" color="purple" class="mb-2">mdi-clock</v-icon>
              <div class="text-h4 font-weight-bold text-purple">{{ formatDuration(totalDuration) }}</div>
              <div class="text-body-2 text-medium-emphasis">教学视频总时长</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 资料展示区域 -->
      <div v-if="loading" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
        <div class="text-body-1 mt-4">加载中...</div>
      </div>

      <div v-else>
        <!-- 视频区域 -->
        <v-card class="materials-section mb-6">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon start color="primary">mdi-video</v-icon>
            <span>视频资料</span>
            <v-spacer></v-spacer>
            <v-chip :color="filteredVideos.length > 0 ? 'primary' : 'grey'" variant="tonal">
              {{ filteredVideos.length }} 个视频
            </v-chip>
          </v-card-title>
          
          <v-divider></v-divider>
          
          <v-card-text class="pa-4">
            <div v-if="filteredVideos.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey" class="mb-4">mdi-video-off</v-icon>
              <div class="text-h6 text-medium-emphasis">暂无视频资料</div>
              <div class="text-body-2 text-medium-emphasis">
                {{ selectedCourseId ? '该课程还没有视频资料' : '您还没有上传任何视频资料' }}
              </div>
            </div>
            
            <v-row v-else>
              <v-col 
                v-for="video in filteredVideos" 
                :key="video.id" 
                cols="12" sm="6" md="4" lg="3" xl="2"
              >
                <video-material-card
                  :video="video"
                  @edit="editMaterial"
                  @delete="deleteMaterial"
                  @view="viewMaterial"
                  @process="processMaterial"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- 文档区域 -->
        <v-card class="materials-section">
          <v-card-title class="d-flex align-center pa-4">
            <v-icon start color="green">mdi-file-document</v-icon>
            <span>文档资料</span>
            <v-spacer></v-spacer>
            <v-chip :color="filteredDocuments.length > 0 ? 'green' : 'grey'" variant="tonal">
              {{ filteredDocuments.length }} 个文档
            </v-chip>
          </v-card-title>
          
          <v-divider></v-divider>
          
          <v-card-text class="pa-4">
            <div v-if="filteredDocuments.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey" class="mb-4">mdi-file-document-off</v-icon>
              <div class="text-h6 text-medium-emphasis">暂无文档资料</div>
              <div class="text-body-2 text-medium-emphasis">
                {{ selectedCourseId ? '该课程还没有文档资料' : '您还没有上传任何文档资料' }}
              </div>
            </div>
            
            <v-row v-else>
              <v-col 
                v-for="document in filteredDocuments" 
                :key="document.id" 
                cols="12" sm="6" md="4" lg="3" xl="2"
              >
                <document-material-card
                  :document="document"
                  @edit="editMaterial"
                  @delete="deleteMaterial"
                  @download="downloadDocument"
                  @preview="previewDocument"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </div>
    </v-container>

    <!-- 上传资料对话框 -->
    <upload-content-dialog
      v-model="showUploadDialog"
      :course-id="selectedCourseId"
      @uploaded="handleContentUploaded"
    />

    <!-- 编辑资料对话框 -->
    <edit-material-dialog
      v-model="showEditDialog"
      :material="editingMaterial"
      @saved="handleMaterialSaved"
    />

    <!-- 文档预览对话框 -->
    <document-preview-dialog
      v-model="showPreviewDialog"
      :document="previewingDocument"
    />

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          确认删除
          <v-spacer></v-spacer>
          <v-btn icon @click="showDeleteDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon :color="deletingMaterial?.type === 'video' ? 'primary' : 'green'" size="64" class="mb-4">
            {{ deletingMaterial?.type === 'video' ? 'mdi-video' : 'mdi-file-document' }}
          </v-icon>
          <div class="text-body-1">
            您确定要删除{{ deletingMaterial?.type === 'video' ? '视频' : '文档' }}
            <strong>{{ deletingMaterial?.title }}</strong> 吗？
          </div>
          <div class="text-caption text-error mt-2">
            此操作无法撤销，该资料将被永久删除。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showDeleteDialog = false">
            取消
          </v-btn>
          <v-btn color="error" @click="confirmDelete" :loading="deleting">
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 通知提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3000"
      location="top right"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn icon @click="snackbar.show = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import courseService from '../../api/courseService'
import videoService from '../../api/videoService'
import { documentService } from '../../api/documentService'
import UploadContentDialog from './components/UploadContentDialog.vue'
import VideoMaterialCard from './components/VideoMaterialCard.vue'
import DocumentMaterialCard from './components/DocumentMaterialCard.vue'
import EditMaterialDialog from './components/EditMaterialDialog.vue'
import DocumentPreviewDialog from './components/DocumentPreviewDialog.vue'

// 路由
const route = useRoute()
const router = useRouter()

// 响应式数据
const courses = ref([])
const selectedCourseId = ref(Array.isArray(route.query.courseId) ? route.query.courseId[0] : route.query.courseId || null)
const loading = ref(false)
const searchQuery = ref('')
const typeFilter = ref('all')
const sortBy = ref('newest')

// 资料数据
const videos = ref<any[]>([])
const documents = ref<any[]>([])

// 对话框状态
const showUploadDialog = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showPreviewDialog = ref(false)
const editingMaterial = ref(null)
const deletingMaterial = ref(null)
const previewingDocument = ref(null)
const deleting = ref(false)

// 通知
const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
})

// 筛选选项
const typeFilterOptions = [
  { title: '全部', value: 'all' },
  { title: '视频', value: 'video' },
  { title: '文档', value: 'document' }
]

const sortOptions = [
  { title: '最新上传', value: 'newest' },
  { title: '最早上传', value: 'oldest' },
  { title: '文件名 A-Z', value: 'name_asc' },
  { title: '文件名 Z-A', value: 'name_desc' },
  { title: '文件大小', value: 'size' }
]

// 统计信息
const videoStats = computed(() => ({
  total: filteredVideos.value.length
}))

const documentStats = computed(() => ({
  total: filteredDocuments.value.length
}))

const totalSize = computed(() => {
  const videoSize = videos.value.reduce((sum, video) => sum + (video.fileSize || 0), 0)
  const docSize = documents.value.reduce((sum, doc) => sum + (doc.fileSize || 0), 0)
  return videoSize + docSize
})

const totalDuration = computed(() => {
  return videos.value.reduce((sum, video) => sum + (video.duration || 0), 0)
})

// 筛选后的数据
const filteredVideos = computed(() => {
  let filtered = videos.value

  // 类型筛选
  if (typeFilter.value === 'document') {
    return []
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(video => 
      video.title.toLowerCase().includes(query) ||
      (video.description && video.description.toLowerCase().includes(query))
    )
  }

  // 排序
  return sortMaterials(filtered, 'video')
})

const filteredDocuments = computed(() => {
  let filtered = documents.value

  // 类型筛选
  if (typeFilter.value === 'video') {
    return []
  }

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(doc => 
      doc.title.toLowerCase().includes(query) ||
      (doc.description && doc.description.toLowerCase().includes(query))
    )
  }

  // 排序
  return sortMaterials(filtered, 'document')
})

// 方法
function sortMaterials(materials: any[], type: string) {
  const sorted = [...materials]
  
  switch (sortBy.value) {
    case 'newest':
      return sorted.sort((a: any, b: any) => {
        const dateA = new Date(b.uploadTime || b.createTime).getTime()
        const dateB = new Date(a.uploadTime || a.createTime).getTime()
        return dateA - dateB
      })
    case 'oldest':
      return sorted.sort((a: any, b: any) => {
        const dateA = new Date(a.uploadTime || a.createTime).getTime()
        const dateB = new Date(b.uploadTime || b.createTime).getTime()
        return dateA - dateB
      })
    case 'name_asc':
      return sorted.sort((a: any, b: any) => a.title.localeCompare(b.title))
    case 'name_desc':
      return sorted.sort((a: any, b: any) => b.title.localeCompare(a.title))
    case 'size':
      return sorted.sort((a: any, b: any) => (b.fileSize || 0) - (a.fileSize || 0))
    default:
      return sorted
  }
}

function handleSearch() {
  // 搜索逻辑已经在computed中处理
}

async function fetchCourses() {
  try {
    const response = await courseService.getCourses()
    if (response.data && response.data.code === 200) {
      courses.value = response.data.data.list || []
    }
  } catch (error) {
    console.error('获取课程列表失败:', error)
    showMessage('获取课程列表失败', 'error')
  }
}

async function fetchMaterials() {
  loading.value = true
  
  try {
    // 无论是否选择课程，都获取对应的资料
    const [videosResponse, documentsResponse] = await Promise.all([
      selectedCourseId.value 
        ? videoService.getVideos({ courseId: selectedCourseId.value })
        : videoService.getVideos({}), // 获取所有视频
      selectedCourseId.value 
        ? documentService.getCourseDocuments(selectedCourseId.value)
        : documentService.getAllDocuments() // 获取所有文档
    ])

    // 处理视频数据
    if (videosResponse.data && videosResponse.data.code === 200) {
      videos.value = (videosResponse.data.data.list || []).map(v => ({ ...v, type: 'video' }))
    } else {
      console.error('视频响应错误:', videosResponse.data)
      videos.value = []
    }

    // 处理文档数据
    if (documentsResponse.data && documentsResponse.data.code === 200) {
      documents.value = documentsResponse.data.data.list || []
    } else {
      console.error('文档响应错误:', documentsResponse)
      documents.value = []
    }
  } catch (error) {
    console.error('获取资料失败:', error)
    showMessage('获取资料失败', 'error')
  } finally {
    loading.value = false
  }
}

// 这个函数现在不需要了，直接使用 documentService.getAllDocuments()

function handleContentUploaded(result: any) {
  showMessage('资料上传成功', 'success')
  fetchMaterials() // 重新加载资料列表
}

function editMaterial(material: any) {
  editingMaterial.value = material
  showEditDialog.value = true
}

function deleteMaterial(material: any) {
  deletingMaterial.value = material
  showDeleteDialog.value = true
}

function viewMaterial(material: any) {
  if (material.type === 'video') {
    router.push(`/course/${material.courseId}/video/${material.id}`)
  } else {
    // 文档预览或下载
    downloadDocument(material)
  }
}

function processMaterial(video: any) {
  // 跳转到视频处理页面或打开处理对话框
  // 修改为正确的路由路径
  router.push(`/CourseVideoManage/${video.course_id}`)
}

async function downloadDocument(doc: any) {
  try {
    const blob = await documentService.downloadDocument(doc.id)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = doc.title || 'document'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    showMessage('文档下载成功', 'success')
  } catch (error) {
    console.error('下载文档失败:', error)
    showMessage('下载文档失败', 'error')
  }
}

function previewDocument(doc: any) {
  // 直接使用预览对话框，无论什么文档类型
  previewingDocument.value = doc
  showPreviewDialog.value = true
}

async function confirmDelete() {
  if (!deletingMaterial.value) return
  
  deleting.value = true
  
  try {
    if (deletingMaterial.value.type === 'video') {
      await videoService.deleteVideo(deletingMaterial.value.id)
    } else {
      await documentService.deleteDocument(deletingMaterial.value.id)
    }
    
    showMessage('删除成功', 'success')
    fetchMaterials() // 重新加载列表
    showDeleteDialog.value = false
    deletingMaterial.value = null
  } catch (error) {
    console.error('删除失败:', error)
    showMessage('删除失败', 'error')
  } finally {
    deleting.value = false
  }
}

function handleMaterialSaved() {
  showMessage('保存成功', 'success')
  fetchMaterials() // 重新加载列表
}

function showMessage(message, color = 'success') {
  snackbar.value = {
    show: true,
    message,
    color
  }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDuration(seconds) {
  if (!seconds) return '0分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  return `${minutes}分钟`
}

// 监听器
watch(selectedCourseId, () => {
  fetchMaterials()
  // 更新URL参数
  if (selectedCourseId.value) {
    router.replace({ query: { courseId: selectedCourseId.value } })
  } else {
    router.replace({ query: {} })
  }
})

// 生命周期
onMounted(() => {
  fetchCourses()
  fetchMaterials()
})
</script>

<style scoped>
.materials-management {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
}

/* 课程选择器样式优化 */
.course-selector {
  background-color: white;
  border-radius: 8px;
  flex-shrink: 1;
}

.course-selector :deep(.v-field) {
  background-color: white;
  border-radius: 8px;
}

.course-selector :deep(.v-field__outline) {
  border-color: rgba(0, 0, 0, 0.12) !important;
}

.course-selector :deep(.v-field__outline--focused) {
  border-color: #1976d2 !important;
  border-width: 2px !important;
}

.course-selector :deep(.v-field__input) {
  color: #333 !important;
  min-height: 40px;
  align-items: center;
}

.course-selector :deep(.v-field__overlay) {
  background-color: white !important;
}

.course-selector :deep(.v-select__selection-text) {
  color: #333 !important;
}

.course-selector :deep(.v-field__label) {
  color: #666 !important;
}

.course-selector :deep(.v-field__label--floating) {
  color: #1976d2 !important;
}

/* 上传按钮样式优化 */
.upload-btn {
  height: 40px;
  border-color: white !important;
  color: white !important;
  font-weight: 500;
  transition: all 0.3s ease;
  min-width: 120px;
}

.upload-btn:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.upload-btn:disabled {
  opacity: 0.6;
  border-color: rgba(255, 255, 255, 0.3) !important;
  color: rgba(255, 255, 255, 0.6) !important;
}

.filter-card {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.stats-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid transparent;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.materials-section {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border-radius: 12px;
}

/* 响应式调整 */
@media (max-width: 960px) {
  .header-card .v-row {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-card .v-col:first-child {
    justify-content: center;
    margin-bottom: 16px;
  }
  
  .header-card .v-col:last-child {
    justify-content: center;
    flex-direction: column;
    gap: 12px;
  }
  
  .course-selector {
    min-width: 100% !important;
    max-width: 100% !important;
    margin-right: 0 !important;
    margin-bottom: 12px;
  }
  
  .upload-btn {
    width: 100%;
    justify-content: center;
  }
  
  .filter-card .v-row {
    flex-direction: column;
  }
}
</style> 