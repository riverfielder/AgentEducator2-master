<template>
  <v-container fluid class="course-detail-manage pa-0">
    <!-- 顶部导航栏 -->
    <v-app-bar elevation="1" color="white" class="course-header">
      <v-toolbar-title class="d-flex align-center">
        <div class="d-flex align-center">
          <v-btn icon @click="goBack" class="me-2">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <div class="text-h6">课程详情管理--{{ course?.name }}</div>
          <div class="text-caption text-medium-emphasis">{{ course?.code }}</div>
        </div>
      </v-toolbar-title>
      
      <v-spacer></v-spacer>
      
      <v-btn color="primary" prepend-icon="mdi-upload" @click="showUploadDialog = true" class="me-2">
        上传内容
      </v-btn>
      <v-btn color="orange" prepend-icon="mdi-cog-refresh" @click="showBatchProcessDialog = true" class="me-2">
        批量处理
      </v-btn>
      <v-btn color="success" prepend-icon="mdi-plus" @click="showNewChapterDialog = true">
        新建章节
      </v-btn>
    </v-app-bar>

    <!-- 主体内容区域 -->
    <div class="content-area">
      <v-row no-gutters class="fill-height">
        <!-- 左侧章节管理区域 -->
        <v-col cols="4" class="chapter-panel">
          <v-card flat class="fill-height rounded-0">
            <v-card-title class="py-3 px-4 bg-grey-lighten-5">
              <v-icon start>mdi-format-list-numbered</v-icon>
              章节管理
            </v-card-title>
            
            <v-card-text class="pa-0 scrollable-area">
              <!-- 未分配章节区域 -->
              <div class="unassigned-section pa-4 border-b">
                <div class="d-flex align-center mb-3">
                  <v-icon color="grey-darken-1" class="me-2">mdi-folder-open</v-icon>
                  <span class="text-subtitle-1 font-weight-medium">未分配内容</span>
                  <v-spacer></v-spacer>
                  <v-chip size="small" color="grey" variant="flat">
                    {{ unassignedItems.length }}
                  </v-chip>
                </div>
                
                <div 
                  class="drop-zone unassigned-drop"
                  :class="{ 'drag-over': dragState.overUnassigned }"
                  @dragenter.prevent="dragState.overUnassigned = true"
                  @dragleave.prevent="dragState.overUnassigned = false"
                  @dragover.prevent
                  @drop.prevent="handleDropToUnassigned"
                >
                  <div v-if="unassignedItems.length === 0" class="empty-state text-center pa-4">
                    <v-icon size="48" color="grey-lighten-1">mdi-inbox</v-icon>
                    <div class="text-body-2 text-grey-darken-1 mt-2">暂无未分配内容</div>
                  </div>
                  <div v-else class="text-body-2 text-grey-darken-1">
                    拖拽内容到此处取消章节分配
                  </div>
                </div>
              </div>

              <!-- 章节列表 -->
              <div class="chapters-list">
                <div
                  v-for="(chapter, index) in chapters"
                  :key="chapter.id"
                  class="chapter-item"
                >
                  <div class="d-flex align-center chapter-container pa-4">
                    <div class="chapter-number">{{ chapter.chapterNumber }}</div>
                    <div class="flex-grow-1 mx-3 chapter-content">
                      <div class="text-subtitle-1 font-weight-medium chapter-title">{{ chapter.title }}</div>
                      <div v-if="chapter.description" class="text-body-2 text-grey-darken-1 chapter-description">
                        {{ chapter.description }}
                      </div>
                    </div>
                    <div class="chapter-actions">
                      <v-chip size="small" :color="getChapterColor(chapter)" variant="flat">
                        {{ getChapterItemCount(chapter) }}
                      </v-chip>
                      <v-menu>
                        <template v-slot:activator="{ props }">
                          <v-btn icon size="small" v-bind="props">
                            <v-icon>mdi-dots-vertical</v-icon>
                          </v-btn>
                        </template>
                        <v-list>
                          <v-list-item @click="editChapter(chapter)">
                            <template v-slot:prepend>
                              <v-icon>mdi-pencil</v-icon>
                            </template>
                            <v-list-item-title>编辑</v-list-item-title>
                          </v-list-item>
                          <v-list-item @click="deleteChapter(chapter)">
                            <template v-slot:prepend>
                              <v-icon>mdi-delete</v-icon>
                            </template>
                            <v-list-item-title>删除</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                    </div>
                  </div>

                  <!-- 章节内容区域 -->
                  <div class="chapter-content pa-3">
                    <!-- 已分配的资源 -->
                    <div v-if="getChapterResources(String(chapter.id)).length > 0" class="chapter-resources mb-3">
                      <div class="text-caption text-grey-darken-1 mb-2">章节内容:</div>
                      <div class="resource-chips d-flex flex-wrap gap-2">
                        <v-chip
                          v-for="resource in getChapterResources(String(chapter.id))"
                          :key="resource.id"
                          size="small"
                          :color="getTypeColor(resource.type as 'video' | 'document')"
                          variant="flat"
                          class="resource-chip"
                          :prepend-icon="getResourceIcon(resource.type as 'video' | 'document')"
                        >
                          <span class="resource-title">{{ resource.title }}</span>
                          <template v-slot:append>
                            <v-btn
                              size="x-small"
                              icon
                              variant="text"
                              @click.stop="removeResourceFromChapter(resource as ResourceItem)"
                              class="ml-1"
                            >
                              <v-icon size="12">mdi-close</v-icon>
                            </v-btn>
                          </template>
                        </v-chip>
                      </div>
                    </div>
                    
                                         <!-- 拖拽放置区域 -->
                     <div 
                       class="chapter-drop-zone"
                       :class="{ 
                         'drag-over': dragState.overChapter === String(chapter.id),
                         'has-resources': getChapterResources(String(chapter.id)).length > 0
                       }"
                       @dragenter.prevent="dragState.overChapter = String(chapter.id)"
                       @dragleave.prevent="dragState.overChapter = null"
                       @dragover.prevent
                       @drop.prevent="handleDropToChapter(String(chapter.id))"
                     >
                       <div class="drop-hint text-center text-body-2 text-grey-darken-1">
                         <v-icon v-if="getChapterResources(String(chapter.id)).length === 0">mdi-download</v-icon>
                         <v-icon v-else size="small">mdi-plus</v-icon>
                         <div v-if="getChapterResources(String(chapter.id)).length === 0">拖拽内容到此章节</div>
                         <div v-else class="text-caption">继续添加内容</div>
                       </div>
                     </div>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- 右侧内容资源区域 -->
        <v-col cols="8" class="resource-panel">
          <v-card flat class="fill-height rounded-0">
            <v-card-title class="py-3 px-4 bg-grey-lighten-5">
              <v-icon start>mdi-folder-multiple</v-icon>
              课程资源
              <v-spacer></v-spacer>
              <v-btn-toggle v-model="resourceView" mandatory variant="outlined" density="compact">
                <v-btn value="grid">
                  <v-icon>mdi-view-grid</v-icon>
                </v-btn>
                <v-btn value="list">
                  <v-icon>mdi-view-list</v-icon>
                </v-btn>
              </v-btn-toggle>
            </v-card-title>
            
            <v-card-text class="pa-4 scrollable-area">
              <!-- 搜索和筛选 -->
              <div class="d-flex gap-3 mb-4">
                <v-text-field
                  v-model="searchQuery"
                  prepend-inner-icon="mdi-magnify"
                  label="搜索资源..."
                  single-line
                  hide-details
                  density="compact"
                  clearable
                  variant="outlined"
                  class="flex-grow-1"
                ></v-text-field>
                <v-select
                  v-model="typeFilter"
                  :items="typeFilterOptions"
                  label="类型筛选"
                  density="compact"
                  hide-details
                  variant="outlined"
                  style="min-width: 120px"
                ></v-select>
              </div>

              <!-- 网格视图 -->
              <div v-if="resourceView === 'grid'" class="resource-grid">
                <v-row>
                  <v-col
                    v-for="item in filteredResources"
                    :key="item.id"
                    cols="6"
                    sm="4"
                    md="3"
                  >
                    <div
                      :draggable="true"
                      @dragstart="(event) => handleDragStart(event, item)"
                    >
                      <template v-if="item.type === 'video'">
                        <VideoMaterialCard
                          :video="item"
                          @edit="handleVideoEdit"
                          @delete="handleResourceDelete"
                          @view="handleVideoPlay"
                          @view-detail="handleVideoDetailView"
                          @process="handleResourceProcess"
                        />
                      </template>
                      <template v-else>
                        <DocumentMaterialCard
                          :document="item"
                          @edit="handleResourceEdit"
                          @delete="handleResourceDelete"
                          @download="handleResourceDownload"
                          @preview="handleResourcePreview"
                        />
                      </template>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <!-- 列表视图 -->
              <div v-else class="resource-list">
                <v-list lines="two">
                  <v-list-item
                    v-for="item in filteredResources"
                    :key="item.id"
                    :draggable="true"
                    @dragstart="handleDragStart($event, item)"
                    @click="handleResourceClick(item)"
                    class="resource-list-item"
                  >
                    <template v-slot:prepend>
                      <v-avatar size="48" class="resource-avatar">
                        <img v-if="item.thumbnail" :src="item.thumbnail" />
                        <v-icon v-else>{{ getResourceIcon(item.type) }}</v-icon>
                      </v-avatar>
                    </template>

                    <v-list-item-title class="text-subtitle-1">
                      {{ item.title }}
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      <div class="d-flex align-center">
                        <v-chip size="x-small" :color="getTypeColor(item.type)" class="me-2">
                          {{ getTypeText(item.type) }}
                        </v-chip>
                        <span>{{ formatFileSize(item.fileSize) }}</span>
                        <v-spacer></v-spacer>
                        <span>{{ formatDate(item.uploadTime) }}</span>
                      </div>
                    </v-list-item-subtitle>

                    <template v-slot:append>
                      <v-menu>
                        <template v-slot:activator="{ props }">
                          <v-btn icon size="small" v-bind="props">
                            <v-icon>mdi-dots-vertical</v-icon>
                          </v-btn>
                        </template>
                        <v-list>
                          <!-- 只有文档才显示编辑选项 -->
                          <v-list-item v-if="item.type === 'document'" @click="handleResourceEdit(item)">
                            <template v-slot:prepend>
                              <v-icon>mdi-pencil</v-icon>
                            </template>
                            <v-list-item-title>编辑</v-list-item-title>
                          </v-list-item>
                          <v-list-item @click="handleResourceDelete(item)">
                            <template v-slot:prepend>
                              <v-icon>mdi-delete</v-icon>
                            </template>
                            <v-list-item-title>删除</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-menu>
                    </template>
                  </v-list-item>
                </v-list>
              </div>

              <!-- 空状态 -->
              <div v-if="filteredResources.length === 0" class="empty-state text-center pa-8">
                <v-icon size="64" color="grey-lighten-1">mdi-folder-open</v-icon>
                <div class="text-h6 mt-4 text-grey-darken-1">暂无课程资源</div>
                <div class="text-body-1 mt-2 text-grey-darken-1">
                  点击"上传内容"按钮添加视频或文档
                </div>
                <v-btn
                  color="primary"
                  class="mt-4"
                  @click="showUploadDialog = true"
                >
                  上传内容
                </v-btn>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- 新建章节对话框 -->
    <chapter-form-dialog
      v-model="showNewChapterDialog"
      :chapter="editingChapter"
      :is-editing="isEditingChapter"
      @save="handleChapterSave"
    />

    <!-- 上传内容对话框 -->
    <upload-content-dialog
      v-model="showUploadDialog"
      :course-id="courseId"
      @uploaded="handleContentUploaded"
    />

    <!-- 批量处理对话框 -->
    <batch-process-dialog
      v-model="showBatchProcessDialog"
      :course-id="courseId"
      :videos="videos"
      :documents="documents"
      @processed="handleBatchProcessed"
    />

    <!-- 资源详情对话框 -->
    <resource-detail-dialog
      v-model="showResourceDialog"
      :resource="selectedResource"
      :course-id="courseId"
    />

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteConfirmDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          确认删除
          <v-spacer></v-spacer>
          <v-btn icon @click="cancelDeleteResource">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon color="error" size="64" class="mb-4">
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要删除{{ resourceToDelete?.type === 'video' ? '视频' : '文档' }}
            <strong>{{ resourceToDelete?.title }}</strong> 吗？
          </div>
          <div class="text-caption text-error mt-2">
            此操作无法撤销，该资源将被永久删除。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancelDeleteResource">
            取消
          </v-btn>
          <v-btn color="error" @click="confirmDeleteResource">
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑视频对话框 -->
    <v-dialog v-model="showEditVideoDialog" max-width="600px">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          编辑视频信息
          <v-spacer></v-spacer>
          <v-btn icon @click="cancelVideoEdit">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form v-if="editingResource">
            <v-text-field
              v-model="editingResource.title"
              label="视频标题"
              required
              variant="outlined"
              density="comfortable"
              class="mb-3"
            ></v-text-field>
                          <v-textarea
                v-model="editingResource.description"
                label="视频描述"
                rows="3"
                variant="outlined"
                density="comfortable"
                placeholder="请输入视频描述..."
                class="mb-3"
              ></v-textarea>
              
              <!-- 视频封面上传 -->
              <div class="mb-3">
                <v-label class="text-subtitle-2 text-medium-emphasis mb-2">视频封面</v-label>
                <div class="d-flex align-center gap-3">
                  <!-- 当前封面预览 -->
                  <div class="cover-preview">
                    <v-img
                      :src="getCoverUrlForEdit(editingResource.coverUrl)"
                      width="120"
                      height="80"
                      cover
                      class="rounded"
                    >
                      <template v-slot:placeholder>
                        <div class="d-flex align-center justify-center fill-height">
                          <v-icon size="32" color="grey">mdi-video</v-icon>
                        </div>
                      </template>
                    </v-img>
                  </div>
                  
                  <!-- 上传按钮和状态 -->
                  <div class="flex-grow-1">
                    <v-btn
                      variant="outlined"
                      prepend-icon="mdi-upload"
                      @click="triggerCoverUpload"
                      :disabled="coverUploading"
                      class="mb-2"
                    >
                      {{ coverUploading ? '上传中...' : '更换封面' }}
                    </v-btn>
                    
                    <!-- 上传进度 -->
                    <v-progress-linear
                      v-if="coverUploading"
                      v-model="coverUploadProgress"
                      color="primary"
                      height="4"
                      rounded
                      class="mb-2"
                    ></v-progress-linear>
                    
                    <div class="text-caption text-medium-emphasis">
                      支持 JPG、PNG 格式，建议尺寸 16:9，最大 2MB
                    </div>
                  </div>
                </div>
                
                <!-- 隐藏的文件输入 -->
                <input
                  type="file"
                  ref="coverFileInput"
                  @change="handleCoverUpload"
                  accept="image/*"
                  style="display: none"
                />
              </div>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancelVideoEdit">
            取消
          </v-btn>
          <v-btn color="primary" @click="saveVideoEdit" :loading="saving">
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑文档对话框 -->
    <v-dialog v-model="showEditResourceDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          编辑文档
          <v-spacer></v-spacer>
          <v-btn icon @click="showEditResourceDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form v-if="editingResource">
            <v-text-field
              v-model="editingResource.title"
              label="文档标题"
              required
              variant="outlined"
              density="comfortable"
              class="mb-3"
            ></v-text-field>
            <v-textarea
              v-model="editingResource.description"
              label="文档描述"
              rows="3"
              variant="outlined"
              density="comfortable"
              placeholder="请输入文档描述..."
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancelResourceEdit">
            取消
          </v-btn>
          <v-btn color="primary" @click="saveResourceEdit">
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 文档预览对话框 -->
    <document-preview-dialog
      v-model="showDocumentPreviewDialog"
      :document="previewDocument"
    />

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
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ResourceCard from './components/ResourceCard.vue'
import ChapterFormDialog from './components/ChapterFormDialog.vue'
import UploadContentDialog from './components/UploadContentDialog.vue'
import BatchProcessDialog from './components/BatchProcessDialog.vue'
import ResourceDetailDialog from './components/ResourceDetailDialog.vue'
import VideoMaterialCard from './components/VideoMaterialCard.vue'
import DocumentMaterialCard from './components/DocumentMaterialCard.vue'
import DocumentPreviewDialog from './components/DocumentPreviewDialog.vue'
import { chapterService, type Chapter } from '../../api/chapterService'
import courseService from '../../api/courseService'
import videoService from '../../api/videoService'
import { documentService } from '../../api/documentService'
import uploadService from '../../api/uploadService'
import { parseCourseDescription } from '../../utils/courseUtils'

// 类型定义
interface ResourceItem {
  id: string
  type: 'video' | 'document'
  title: string
  description?: string
  thumbnail?: string | null | undefined
  coverUrl?: string | null | undefined
  duration?: number | null
  fileSize?: number
  uploadTime?: string
  chapterId?: string | null
  fileType?: string
  downloadCount?: number
  [key: string]: any
}

// 路由参数
const route = useRoute()
const router = useRouter()
const courseId = computed(() => route.params.courseId as string)

// 响应式数据
const course = ref<any>(null)
const chapters = ref<Chapter[]>([])
const videos = ref<ResourceItem[]>([])
const documents = ref<ResourceItem[]>([])
const loading = ref(false)

// 拖拽状态
const dragState = ref({
  overChapter: null as string | null,
  overUnassigned: false,
  draggedItem: null as ResourceItem | null
})

// 筛选和搜索
const searchQuery = ref('')
const typeFilter = ref('all')
const resourceView = ref('grid')

// 对话框状态
const showNewChapterDialog = ref(false)
const showUploadDialog = ref(false)
const showBatchProcessDialog = ref(false)
const showResourceDialog = ref(false)
const selectedResource = ref<ResourceItem | null>(null)
const showEditResourceDialog = ref(false)
const showEditVideoDialog = ref(false)
const showDeleteConfirmDialog = ref(false)
const editingResource = ref<ResourceItem | null>(null)
const resourceToDelete = ref<ResourceItem | null>(null)
const showDocumentPreviewDialog = ref(false)
const previewDocument = ref<ResourceItem | null>(null)

// 通知相关
const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
})

// 编辑状态
const editingChapter = ref<Chapter | null>(null)
const isEditingChapter = ref(false)

// 封面上传相关状态
const coverFileInput = ref<HTMLInputElement | null>(null)
const coverUploading = ref(false)
const coverUploadProgress = ref(0)
const saving = ref(false)

// 计算属性
const typeFilterOptions = [
  { title: '全部', value: 'all' },
  { title: '视频', value: 'video' },
  { title: '文档', value: 'document' }
]

const allResources = computed<ResourceItem[]>(() => [
  ...videos.value.map(v => ({ ...v, type: 'video' as const })),
  ...documents.value.map(d => ({ ...d, type: 'document' as const }))
])

const unassignedItems = computed(() => 
  allResources.value.filter(item => !item.chapterId)
)

const filteredResources = computed(() => {
  let filtered = allResources.value

  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(item => 
      item.title.toLowerCase().includes(query)
    )
  }

  // 类型筛选
  if (typeFilter.value !== 'all') {
    filtered = filtered.filter(item => item.type === typeFilter.value)
  }

  return filtered
})

// 方法
function goBack() {
  router.go(-1)
}

function getChapterItemCount(chapter: Chapter) {
  return allResources.value.filter(item => item.chapterId === chapter.id).length
}

function getChapterColor(chapter: Chapter) {
  const count = getChapterItemCount(chapter)
  if (count === 0) return 'grey'
  if (count < 3) return 'orange'
  return 'success'
}

function getChapterResources(chapterId: string) {
  return allResources.value.filter(item => item.chapterId === chapterId)
}

async function removeResourceFromChapter(resource: ResourceItem) {
  try {
    // 即时反馈
    showSnackbar('正在移除资源...', 'info')
    // 调用API将资源从章节中移除（设置chapterId为null）
    const response = await chapterService.assignResourceToChapter({
      resourceId: resource.id,
      resourceType: resource.type,
      chapterId: null
    })
    
    if (response.code === 200) {
      // 更新本地数据
      resource.chapterId = null
      showSnackbar('资源移除成功', 'success')
      console.log('资源已从章节中移除:', resource.title)
    } else {
      console.error('移除资源失败:', response.message)
      showSnackbar('移除失败: ' + response.message, 'error')
    }
  } catch (error) {
    console.error('移除资源失败:', error)
    showSnackbar('网络错误，移除失败', 'error')
  }
}

function handleDragStart(event: DragEvent, item: ResourceItem) {
  dragState.value.draggedItem = item
  event.dataTransfer!.effectAllowed = 'move'
}

function handleDropToChapter(chapterId: string) {
  const item = dragState.value.draggedItem
  if (item && item.chapterId !== chapterId) {
    // 添加即时视觉反馈
    showSnackbar('正在分配资源...', 'info')
    updateItemChapter(item, chapterId)
  }
  resetDragState()
}

function handleDropToUnassigned() {
  const item = dragState.value.draggedItem
  if (item && item.chapterId) {
    // 添加即时视觉反馈
    showSnackbar('正在移除资源...', 'info')
    updateItemChapter(item, null)
  }
  resetDragState()
}

function resetDragState() {
  dragState.value.overChapter = null
  dragState.value.overUnassigned = false
  dragState.value.draggedItem = null
}

async function updateItemChapter(item: ResourceItem, chapterId: string | null) {
  // 添加加载状态
  const loadingItem = dragState.value.draggedItem
  if (loadingItem) {
    loadingItem.isLoading = true
  }

  try {
    // 先乐观更新本地数据（立即反馈）
    const oldChapterId = item.chapterId
    item.chapterId = chapterId
    
    // 强制触发响应式更新
    const targetArray = item.type === 'video' ? videos.value : documents.value
    const index = targetArray.findIndex(r => r.id === item.id)
    if (index !== -1) {
      targetArray[index] = { ...targetArray[index], chapterId }
    }
    
    // 调用API更新章节关联
    const response = await chapterService.assignResourceToChapter({
      resourceId: item.id,
      resourceType: item.type,
      chapterId: chapterId
    })
    
    if (response.code === 200) {
      console.log('章节分配成功:', item.title)
      // 显示成功提示
      showSnackbar('资源分配成功', 'success')
    } else {
      console.error('章节分配失败:', response.message)
      // API失败时回滚本地数据
      item.chapterId = oldChapterId
      if (index !== -1) {
        targetArray[index] = { ...targetArray[index], chapterId: oldChapterId }
      }
      showSnackbar('资源分配失败: ' + response.message, 'error')
    }
  } catch (error) {
    console.error('更新项目章节失败:', error)
    // 网络错误时回滚本地数据
    const targetArray = item.type === 'video' ? videos.value : documents.value
    const index = targetArray.findIndex(r => r.id === item.id)
    if (index !== -1) {
      item.chapterId = null // 回滚到未分配状态
      targetArray[index] = { ...targetArray[index], chapterId: null }
    }
    showSnackbar('网络错误，资源分配失败', 'error')
  } finally {
    // 移除加载状态
    if (loadingItem) {
      loadingItem.isLoading = false
    }
  }
}

function editChapter(chapter: Chapter) {
  editingChapter.value = { ...chapter }
  isEditingChapter.value = true
  showNewChapterDialog.value = true
}

async function deleteChapter(chapter: any) {
  try {
    const response = await chapterService.deleteChapter(chapter.id)
    if (response.code === 200) {
      // 从本地章节列表中移除
      const index = chapters.value.findIndex(c => c.id === chapter.id)
      if (index !== -1) {
        chapters.value.splice(index, 1)
      }
      console.log('章节删除成功')
      // 重新加载数据以确保视频/文档的chapter_id更新
      loadCourseData()
    }
  } catch (error) {
    console.error('删除章节失败:', error)
  }
}

async function handleChapterSave(chapterData: any) {
  try {
    if (isEditingChapter.value && editingChapter.value?.id) {
      // 编辑现有章节
      const response = await chapterService.updateChapter(editingChapter.value.id, chapterData)
      if ((response as any).code === 200) {
        // 更新本地章节列表
        const index = chapters.value.findIndex((c: Chapter) => c.id === editingChapter.value?.id)
        if (index !== -1) {
          chapters.value[index] = (response as any).data
        }
        console.log('章节更新成功')
      }
    } else {
      // 创建新章节
      const newChapterData = {
        ...chapterData,
        courseId: courseId.value
      }
      const response = await chapterService.createChapter(newChapterData)
      if ((response as any).code === 200) {
        // 添加到本地章节列表
        chapters.value.push((response as any).data)
        console.log('章节创建成功')
      }
    }
    
    showNewChapterDialog.value = false
    editingChapter.value = null
    isEditingChapter.value = false
  } catch (error) {
    console.error('保存章节失败:', error)
  }
}

function handleContentUploaded(content: any) {
  // TODO: 处理内容上传完成
  console.log('内容上传完成:', content)
  loadCourseData()
}

function handleBatchProcessed(result: any) {
  console.log('批量处理完成:', result)
  // 重新加载课程数据
  loadCourseData()
  showSnackbar('批量处理完成', 'success')
}

function handleResourceClick(resource: ResourceItem) {
  selectedResource.value = resource
  showResourceDialog.value = true
}

function handleResourceEdit(resource: ResourceItem) {
  if (resource.type === 'video') {
    // 视频不支持编辑
    console.log('视频资源不支持编辑')
    return
  }
  // 编辑文档
  editingResource.value = { ...resource }
  showEditResourceDialog.value = true
}

function handleResourceDelete(resource: ResourceItem) {
  resourceToDelete.value = resource
  showDeleteConfirmDialog.value = true
}

async function confirmDeleteResource() {
  if (!resourceToDelete.value) return
  
  const deletingTitle = resourceToDelete.value.title
  const deletingType = resourceToDelete.value.type === 'video' ? '视频' : '文档'
  
  try {
    let response: any
    if (resourceToDelete.value.type === 'video') {
      response = await videoService.deleteVideo(resourceToDelete.value.id)
    } else if (resourceToDelete.value.type === 'document') {
      response = await documentService.deleteDocument(resourceToDelete.value.id)
    }
    
    // 修复：axios 返回的结构是 response.data，我们需要检查 response.data.code
    if (response && response.data && response.data.code === 200) {
      // 先从基础数组中移除（这会自动更新计算属性 allResources）
      if (resourceToDelete.value.type === 'video') {
        const videoIndex = videos.value.findIndex(v => v.id === resourceToDelete.value!.id)
        if (videoIndex !== -1) {
          videos.value.splice(videoIndex, 1)
          console.log(`✅ 已从 videos 数组中移除索引 ${videoIndex}`)
        }
      } else {
        const docIndex = documents.value.findIndex(d => d.id === resourceToDelete.value!.id)
        if (docIndex !== -1) {
          documents.value.splice(docIndex, 1)
          console.log(`✅ 已从 documents 数组中移除索引 ${docIndex}`)
        }
      }
      
      // 显示删除成功消息
      showSnackbar(`${deletingType} "${deletingTitle}" 删除成功`, 'success')
      
      // 输出删除日志（如果后端返回了）
      if (response.data.data && response.data.data.deletionLog) {
        console.log(`📋 ${deletingType}删除日志:`)
        response.data.data.deletionLog.forEach((log: string) => {
          console.log(`   ✓ ${log}`)
        })
      }
      
      console.log(`🎯 ${deletingType}删除成功，界面已更新`)
      
    } else {
      const errorMsg = response?.data?.message || response?.message || '删除失败'
      showSnackbar(`${deletingType}删除失败: ${errorMsg}`, 'error')
      console.error('删除失败，完整响应:', response)
    }
  } catch (error: any) {
    const errorMsg = error?.response?.data?.message || error?.message || '网络错误'
    showSnackbar(`删除${deletingType}失败: ${errorMsg}`, 'error')
    console.error('删除资源失败:', error)
  } finally {
    showDeleteConfirmDialog.value = false
    resourceToDelete.value = null
  }
}

function cancelDeleteResource() {
  showDeleteConfirmDialog.value = false
  resourceToDelete.value = null
}

function showSnackbar(message: string, color: string = 'success') {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

async function handleResourceProcess(video: ResourceItem) {
  try {
    // 获取视频处理状态
    const statusResponse = await videoService.getVideoProcessingStatus(video.id)
    if (statusResponse.data && statusResponse.data.code === 200) {
      const status = statusResponse.data.data
      
      // 检查是否有未处理的步骤
      const unprocessedSteps: string[] = []
      const allSteps = [
        { value: 'keyframe', label: '关键帧提取' },
        { value: 'ocr', label: 'OCR文字识别' },
        { value: 'asr', label: 'ASR语音识别' },
        { value: 'vector', label: '向量索引构建' },
        { value: 'summary', label: '智能摘要生成' }
      ]
      
      allSteps.forEach(step => {
        if (!status[step.value]) {
          unprocessedSteps.push(step.value)
        }
      })
      
      if (unprocessedSteps.length === 0) {
        snackbar.value = { show: true, message: '视频已完成所有处理步骤', color: 'success' }
        return
      }
      
      // 开始处理未完成的步骤
      const processResponse = await videoService.processVideoWithSettings(video.id, {
        processing_steps: unprocessedSteps,
        preview_mode: false
      })
      
      if (processResponse.data && processResponse.data.code === 200) {
        snackbar.value = { 
          show: true, 
          message: `开始处理视频，共 ${unprocessedSteps.length} 个步骤`, 
          color: 'success' 
        }
      } else {
        snackbar.value = { 
          show: true, 
          message: processResponse.data?.message || '处理视频失败', 
          color: 'error' 
        }
      }
    } else {
      snackbar.value = { 
        show: true, 
        message: '获取视频状态失败', 
        color: 'error' 
      }
    }
  } catch (error) {
    console.error('处理视频失败:', error)
    snackbar.value = { 
      show: true, 
      message: '处理视频时发生错误', 
      color: 'error' 
    }
  }
}

async function handleResourceDownload(document: ResourceItem) {
  try {
    showSnackbar('正在下载文档...', 'info')
    
    const blob = await documentService.downloadDocument(document.id)
    const url = window.URL.createObjectURL(blob)
    const link = window.document.createElement('a')
    link.href = url
    link.download = document.title || 'document'
    window.document.body.appendChild(link)
    link.click()
    window.document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    showSnackbar('文档下载成功', 'success')
  } catch (error) {
    console.error('文档下载失败:', error)
    showSnackbar('文档下载失败', 'error')
  }
}

function handleResourcePreview(document: ResourceItem) {
  previewDocument.value = document
  showDocumentPreviewDialog.value = true
}

// 处理视频播放
function handleVideoPlay(video: ResourceItem) {
  // 直接跳转到视频播放页面
  router.push(`/course/${courseId.value}/video/${video.id}`)
}

// 处理视频详情查看
function handleVideoDetailView(video: ResourceItem) {
  selectedResource.value = video
  showResourceDialog.value = true
}

// 处理视频编辑
function handleVideoEdit(video: ResourceItem) {
  editingResource.value = { 
    ...video,
    thumbnail: video.thumbnail || undefined // 处理null值转为undefined
  }
  showEditVideoDialog.value = true
}

async function saveResourceEdit() {
  if (!editingResource.value) return
  try {
    const response = await documentService.updateDocument(editingResource.value.id, {
      title: editingResource.value.title,
      description: editingResource.value.description
    })
    
    // 检查响应结构
    const result = response.data || response
    
    if (result.code === 200) {
      // 更新documents数组中的对应文档
      const docIndex = documents.value.findIndex(d => d.id === editingResource.value!.id)
      if (docIndex !== -1) {
        documents.value[docIndex] = {
          ...documents.value[docIndex],
          title: editingResource.value.title,
          description: editingResource.value.description
        }
      }
      
      showSnackbar('文档更新成功', 'success')
      showEditResourceDialog.value = false
      editingResource.value = null
    } else {
      showSnackbar(result.message || '更新失败', 'error')
      console.error('更新失败:', result.message)
    }
  } catch (error: any) {
    console.error('更新文档失败:', error)
    showSnackbar(error?.response?.data?.message || '更新文档失败', 'error')
  }
}

function cancelResourceEdit() {
  showEditResourceDialog.value = false
  editingResource.value = null
}

function cancelVideoEdit() {
  showEditVideoDialog.value = false
  editingResource.value = null
  // 重置封面上传状态
  coverUploading.value = false
  coverUploadProgress.value = 0
  saving.value = false
}

// 触发封面上传
function triggerCoverUpload() {
  if (coverFileInput.value) {
    coverFileInput.value.click()
  }
}

// 处理封面上传
async function handleCoverUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !editingResource.value) return

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    showSnackbar('请选择图片文件', 'error')
    return
  }

  // 验证文件大小 (最大2MB)
  if (file.size > 2 * 1024 * 1024) {
    showSnackbar('图片大小不能超过2MB', 'error')
    return
  }

  coverUploading.value = true
  coverUploadProgress.value = 0

  try {
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (coverUploadProgress.value < 90) {
        coverUploadProgress.value += 10
      }
    }, 200)

    // 调用上传接口
    const response = await uploadService.uploadImage(file)
    
    clearInterval(progressInterval)
    coverUploadProgress.value = 100

    if (response.data.code === 200) {
      // 获取相对路径并转换为完整URL
      const relativeUrl = response.data.data.imageUrl
      const baseURL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:5000')
      const fullUrl = relativeUrl.startsWith('http') ? relativeUrl : `${baseURL}${relativeUrl}`
      
      // 更新封面URL
      editingResource.value.coverUrl = fullUrl
      showSnackbar('封面上传成功', 'success')
      
      // 延迟重置状态
      setTimeout(() => {
        coverUploading.value = false
        coverUploadProgress.value = 0
      }, 500)
    } else {
      throw new Error(response.data.message || '上传失败')
    }
  } catch (error: any) {
    coverUploading.value = false
    coverUploadProgress.value = 0
    const errorMsg = error?.response?.data?.message || error?.message || '上传失败'
    showSnackbar(`封面上传失败: ${errorMsg}`, 'error')
    console.error('封面上传失败:', error)
  }

  // 清空文件输入
  if (target) {
    target.value = ''
  }
}

async function saveVideoEdit() {
  if (!editingResource.value) return
  
  saving.value = true
  
  try {
    const updateData: any = {
      title: editingResource.value.title,
      description: editingResource.value.description
    }
    
    // 如果有封面URL，也包含在更新数据中
    if (editingResource.value.coverUrl) {
      // 如果是完整URL，提取相对路径部分
      let coverUrl = editingResource.value.coverUrl
      const baseURL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:5000')
      if (coverUrl.startsWith(baseURL)) {
        coverUrl = coverUrl.replace(baseURL, '')
      }
      updateData.coverUrl = coverUrl
    }
    
    const response = await videoService.updateVideo(editingResource.value.id, updateData)
    
    console.log('视频更新响应:', response)
    
    // 检查响应结构 - axios返回的数据在response.data中
    const result = response.data
    
    if (result && result.code === 200) {
      // 更新videos数组中的对应视频
      const videoIndex = videos.value.findIndex(v => v.id === editingResource.value!.id)
      if (videoIndex !== -1) {
        videos.value[videoIndex] = {
          ...videos.value[videoIndex],
          title: editingResource.value.title,
          description: editingResource.value.description,
          coverUrl: editingResource.value.coverUrl,
          thumbnail: editingResource.value.coverUrl // 同时更新thumbnail字段以确保兼容性
        }
      }
      
      showSnackbar('视频更新成功', 'success')
      showEditVideoDialog.value = false
      editingResource.value = null
      
      // 强制刷新视频列表数据，确保封面更新生效
      console.log('视频更新成功，重新加载数据...')
      setTimeout(() => {
        loadCourseData()
      }, 100)
    } else {
      const errorMsg = result?.message || result?.msg || '更新失败'
      showSnackbar(errorMsg, 'error')
      console.error('更新失败:', result)
    }
  } catch (error: any) {
    console.error('更新视频失败:', error)
    
    // 更详细的错误处理
    if (error.response) {
      // 服务器返回了错误响应
      const errorData = error.response.data
      const errorMsg = errorData?.message || errorData?.msg || `请求失败(${error.response.status})`
      showSnackbar(errorMsg, 'error')
    } else if (error.request) {
      // 请求发出但没有收到响应
      showSnackbar('网络错误，请检查网络连接', 'error')
    } else {
      // 其他错误
      showSnackbar('更新视频失败: ' + error.message, 'error')
    }
  } finally {
    saving.value = false
  }
}

function getResourceIcon(type: 'video' | 'document') {
  const iconMap = {
    video: 'mdi-play-circle',
    document: 'mdi-file-document'
  }
  return iconMap[type] || 'mdi-file'
}

function getTypeColor(type: 'video' | 'document') {
  const colorMap = {
    video: 'blue',
    document: 'green'
  }
  return colorMap[type] || 'grey'
}

function getTypeText(type: 'video' | 'document') {
  const textMap = {
    video: '视频',
    document: '文档'
  }
  return textMap[type] || type
}

function getCoverUrlForEdit(coverUrl: string | null | undefined): string {
  if (!coverUrl) return '/default-video-thumbnail.jpg'
  
  // 如果已经是完整URL，直接返回
  if (coverUrl.startsWith('http')) return coverUrl
  
  // 如果是相对路径，添加后端服务器地址
  const baseURL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.PROD ? '' : 'http://localhost:5000')
  return `${baseURL}${coverUrl}`
}

function formatFileSize(bytes: number | null | undefined) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(date: string | undefined) {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

async function loadCourseData() {
  loading.value = true
  try {
    console.log('开始加载课程数据，课程ID:', courseId.value)
    
    // 并行加载课程基本信息、章节列表、视频列表、文档列表
    const [courseResponse, chaptersResponse, videosResponse, documentsResponse] = await Promise.all([
      courseService.getCourseDetails(courseId.value),
      chapterService.getCourseChapters(courseId.value),
      videoService.getVideos({ courseId: courseId.value }),
      documentService.getCourseDocuments(courseId.value)
    ])

    console.log('API响应结构:', {
      courseResponse: courseResponse.data,
      chaptersResponse: chaptersResponse,
      videosResponse: videosResponse.data,
      documentsResponse: documentsResponse
    })

    // 设置课程基本信息
    if (courseResponse.data.code === 200) {
      const descObj = parseCourseDescription(courseResponse.data.data.description)
      course.value = {
        ...courseResponse.data.data,
        description: descObj.description || '',
        category: descObj.category || []
      }
      console.log('课程信息加载成功:', course.value)
    }

    // 设置章节列表
    if (chaptersResponse.code === 200) {
      chapters.value = chaptersResponse.data.list
      console.log('章节列表加载成功:', chapters.value)
    } else {
      console.log('章节列表加载失败:', chaptersResponse)
    }

    // 设置视频列表
    if (videosResponse.data.code === 200) {
      const videoList = videosResponse.data.data.list || []
      console.log('原始视频数据:', videoList)
      
      videos.value = videoList.map((video: any): ResourceItem => ({
        id: video.id,
        type: 'video',
        title: video.title,
        description: video.description,
        thumbnail: video.coverUrl || undefined, // 修改为undefined而不是null
        coverUrl: video.coverUrl || undefined, // 添加coverUrl字段
        duration: video.duration,
        fileSize: video.fileSize || undefined,
        uploadTime: video.uploadTime,
        chapterId: video.chapterId || undefined // 修改为undefined而不是null
      }))
      console.log('处理后的视频数据:', videos.value)
    } else {
      console.log('视频列表加载失败:', videosResponse.data)
    }

    // 设置文档列表
    if (documentsResponse.data && documentsResponse.data.code === 200) {
      const documentList = documentsResponse.data.data.list || []
      console.log('原始文档数据:', documentList)
      
      documents.value = documentList.map((document: any): ResourceItem => ({
        id: document.id,
        type: 'document',
        title: document.title,
        description: document.description,
        thumbnail: undefined, // 修改为undefined
        duration: undefined, // 修改为undefined
        fileSize: document.fileSize,
        uploadTime: document.uploadTime,
        chapterId: document.chapterId || undefined, // 修改为undefined
        fileType: document.fileType,
        downloadCount: document.downloadCount
      }))
      console.log('处理后的文档数据:', documents.value)
    } else {
      console.log('文档列表加载失败:', documentsResponse)
    }

    console.log('课程数据加载完成:', {
      course: course.value,
      chapters: chapters.value.length,
      videos: videos.value.length,
      documents: documents.value.length,
      allResources: allResources.value.length
    })
  } catch (error) {
    console.error('加载课程数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadCourseData()
})
</script>

<style scoped>
.course-detail-manage {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.course-header {
  flex-shrink: 0;
}

.content-area {
  flex: 1;
  overflow: hidden;
}

.chapter-panel, .resource-panel {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
}

.chapter-panel .v-card,
.resource-panel .v-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.scrollable-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0; /* 重要：允许flex子项缩小 */
}

/* 确保章节列表可以滚动 */
.chapters-list {
  max-height: none; /* 移除最大高度限制 */
  overflow: visible; /* 让父容器处理滚动 */
  min-height: calc(100vh - 200px); /* 确保有足够高度触发滚动 */
  padding-bottom: 20px; /* 底部留一些空间 */
}

/* 优化滚动条样式 */
.scrollable-area::-webkit-scrollbar {
  width: 8px;
}

.scrollable-area::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 4px;
}

.scrollable-area::-webkit-scrollbar-thumb {
  background: #bdbdbd;
  border-radius: 4px;
  border: 2px solid #f5f5f5;
}

.scrollable-area::-webkit-scrollbar-thumb:hover {
  background: #9e9e9e;
}

/* 强制显示滚动条（用于调试） */
.scrollable-area {
  scrollbar-width: thin;
  scrollbar-color: #bdbdbd #f5f5f5;
}

/* 移除重复的 chapter-item 样式，已在下面重新定义 */

.chapter-container {
  width: 100%;
  gap: 16px;
}

.chapter-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  flex-shrink: 0; /* 防止被压缩 */
  min-width: 32px; /* 确保最小宽度 */
}

.drop-zone {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  transition: all 0.3s;
}

.drop-zone.drag-over {
  border-color: #1976d2;
  background: rgba(25, 118, 210, 0.1);
}

.chapter-drop-zone {
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  transition: all 0.3s;
}

.chapter-drop-zone.has-resources {
  min-height: 40px;
  border-style: solid;
  border-color: transparent;
}

.chapter-drop-zone.drag-over {
  border-color: #4caf50;
  background: rgba(76, 175, 80, 0.1);
  transform: scale(1.02);
}

.chapter-drop-zone.drag-over .drop-hint {
  color: #4caf50 !important;
  font-weight: 500;
}

.chapter-item {
  border-radius: 8px;
  margin-bottom: 8px; /* 添加章节间距 */
  min-width: 0; /* 允许内容区域在必要时缩小 */
  flex: 1;
  background-color: transparent; /* 移除背景色 */
}

.chapter-content {
  min-width: 0;
  flex: 1;
  background-color: transparent; /* 确保没有背景色 */
}

.chapter-resources {
  background: #fff;
  border-radius: 6px;
  padding: 12px;
  border-left: 3px solid #1976d2;
  max-height: 200px; /* 限制资源区域最大高度 */
  overflow-y: auto; /* 资源太多时可以滚动 */
}

/* 优化章节item的spacing */
.chapter-item:last-child {
  border-bottom: none; /* 最后一个章节不需要下边框 */
}

.resource-chips {
  gap: 8px;
}

.resource-chip {
  cursor: pointer;
  transition: all 0.2s;
}

.resource-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.resource-title {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unassigned-drop {
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resource-grid .v-col {
  padding: 8px;
}

.resource-list-item {
  border-bottom: 1px solid #f0f0f0;
}

.resource-list-item:hover {
  background: #f5f5f5;
}

.resource-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.border-b {
  border-bottom: 1px solid #e0e0e0;
}

.chapter-title {
  word-break: break-word;
  overflow-wrap: break-word;
  margin-bottom: 4px;
}

.chapter-description {
  word-break: break-word;
  overflow-wrap: break-word;
}

.chapter-actions {
  flex-shrink: 0; /* 防止操作区域被压缩 */
}
</style>