<template>
  <div class="document-summary">
    <!-- 加载状态 -->
    <div v-if="loading" class="d-flex justify-center align-center pa-8">
      <div class="text-center">
        <v-progress-circular indeterminate size="32" color="primary"></v-progress-circular>
        <p class="mt-2 text-body-2 text-grey">正在加载摘要...</p>
      </div>
    </div>

    <!-- 摘要内容 -->
    <div v-else-if="summaryData" class="summary-content pa-4">
      <!-- 整体摘要 -->
      <v-card v-if="summaryData.whole_summary" class="mb-4" elevation="1">
        <v-card-title class="d-flex align-center pa-3 bg-blue-grey-lighten-5">
          <v-icon icon="mdi-file-document-outline" class="me-2 text-blue-grey"></v-icon>
          <span class="text-subtitle-1 font-weight-medium">摘要</span>
        </v-card-title>
        <v-card-text class="pa-3">
          <p class="text-body-1 text-grey-darken-2">{{ summaryData.whole_summary }}</p>
        </v-card-text>
      </v-card>

      <!-- 主要要点 -->
      <v-card v-if="parsedMainPoints && parsedMainPoints.length > 0" class="mb-4" elevation="1">
        <v-card-title class="d-flex align-center pa-3 bg-green-lighten-5">
          <v-icon icon="mdi-lightbulb-outline" class="me-2 text-green-darken-1"></v-icon>
          <span class="text-subtitle-1 font-weight-medium">要点</span>
        </v-card-title>
        <v-card-text class="pa-3">
          <v-list density="compact">
            <v-list-item 
              v-for="(point, index) in parsedMainPoints" 
              :key="index"
              class="pa-2">
              <template #prepend>
                <v-avatar size="24" color="green-lighten-1" class="text-white">
                  <span class="text-caption font-weight-bold">{{ index + 1 }}</span>
                </v-avatar>
              </template>
              <v-list-item-title class="text-body-2 text-grey-darken-2 main-point-text" :class="{'text-truncate': isPointLong(point)}">
                {{ point }}
                <v-tooltip v-if="isPointLong(point)" activator="parent" location="top" max-width="400">
                  <div class="pa-2">{{ point }}</div>
                </v-tooltip>
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>

      <!-- 关键词 -->
      <v-card v-if="keywordsList && keywordsList.length > 0" class="mb-4" elevation="1">
        <v-card-title class="d-flex align-center pa-3 bg-orange-lighten-5">
          <v-icon icon="mdi-tag-multiple-outline" class="me-2 text-orange-darken-1"></v-icon>
          <span class="text-subtitle-1 font-weight-medium">关键词</span>
        </v-card-title>
        <v-card-text class="pa-3">
          <div class="d-flex flex-wrap ga-2">
            <v-chip
              v-for="(keyword, index) in keywordsList"
              :key="getKeywordChipKey(keyword, index)"
              size="small"
              color="orange-lighten-1"
              variant="outlined"
              class="text-caption keyword-chip"
              @click="() => handleKeywordClick(keyword)">
              {{ keyword.name }}
              <v-tooltip activator="parent" location="top">
                <div class="text-caption">
                  点击查看掌握情况
                </div>
              </v-tooltip>
            </v-chip>
          </div>
        </v-card-text>
      </v-card>

      <!-- 章节摘要 -->
      <v-card v-if="summaryData.sections && summaryData.sections.length > 0" class="mb-4" elevation="1">
        <v-card-title class="d-flex align-center pa-3 bg-purple-lighten-5">
          <v-icon icon="mdi-format-list-numbered" class="me-2 text-purple-darken-1"></v-icon>
          <span class="text-subtitle-1 font-weight-medium">章节摘要</span>
        </v-card-title>
        <v-card-text class="pa-3">
          <v-expansion-panels variant="accordion">
            <v-expansion-panel
              v-for="(section, index) in summaryData.sections"
              :key="index">
              <v-expansion-panel-title>
                <div class="d-flex align-center w-100">
                  <v-avatar size="20" color="purple-lighten-1" class="text-white me-3">
                    <span class="text-caption">{{ index + 1 }}</span>
                  </v-avatar>
                  <span class="text-body-2 font-weight-medium">{{ section.title || `第${index + 1}部分` }}</span>
                  <v-spacer></v-spacer>
                  <v-chip size="x-small" color="purple-lighten-3" variant="outlined">
                    {{ section.segment_count || 0 }}段
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p class="text-body-2 text-grey-darken-2">{{ section.content }}</p>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
      </v-card>

      <!-- 生成时间 -->
      <v-card v-if="summaryData.created_at || summaryData.updated_at" elevation="0" class="bg-grey-lighten-5">
        <v-card-text class="pa-2 text-center">
          <v-icon icon="mdi-clock-outline" size="16" class="me-1 text-grey"></v-icon>
          <span class="text-caption text-grey">生成于 {{ formatDate(summaryData.created_at || summaryData.updated_at) }}</span>
        </v-card-text>
      </v-card>
    </div>

    <!-- 无摘要状态 -->
    <div v-else class="d-flex flex-column justify-center align-center pa-8">
      <v-icon size="64" color="grey-lighten-2">mdi-file-document-outline</v-icon>
      <p class="mt-4 text-body-1 text-grey text-center">暂无摘要信息</p>
      <v-btn 
        variant="outlined" 
        color="primary"
        size="small" 
        @click="refreshSummary"
        :loading="loading"
        class="mt-2">
        刷新
      </v-btn>
    </div>

    <!-- 错误提示 -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="5000">
      {{ errorMessage }}
      <template #actions>
        <v-btn variant="text" @click="errorSnackbar = false">关闭</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, readonly } from 'vue'
import { documentService } from '@/api/documentService'
import knowledgeMapService from '@/api/knowledgeMapService'
import { useKeywordNavigation, useKeywordDisplay } from '@/composables/useKeywordNavigation'
import type { KeywordData, DocumentSummaryData } from '@/types/keyword'

// Props
interface Props {
  documentId: string
}

const props = defineProps<Props>()

// 使用composables
const { handleKeywordClick } = useKeywordNavigation()
const { getKeywordChipKey } = useKeywordDisplay()

// 响应式数据
const loading = ref(false)
const summaryData = ref<DocumentSummaryData | null>(null)
const errorSnackbar = ref(false)
const errorMessage = ref('')
const keywordsList = ref<KeywordData[]>([])

// 计算属性
const parsedMainPoints = computed(() => {
  if (!summaryData.value?.main_points) return []
  
  try {
    // 尝试解析JSON字符串
    const parsed = JSON.parse(summaryData.value.main_points)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    // 如果解析失败，尝试按行分割
    return summaryData.value.main_points.split('\n').filter((point: string) => point.trim())
  }
})

// 判断要点文本是否过长需要截断
const isPointLong = (point: string) => {
  return point.length > 100 // 超过100字符显示悬停提示
}

// 方法
const loadSummary = async () => {
  try {
    loading.value = true
    console.log('正在加载文档摘要，documentId:', props.documentId)
    
    const response = await documentService.getDocumentSummary(props.documentId)
    console.log('摘要API响应:', response)
    
    if (response.data && response.data.code === 200 && response.data.data) {
      summaryData.value = response.data.data
      console.log('摘要数据:', summaryData.value)
    } else {
      console.log('无摘要数据:', response.data)
      summaryData.value = null
    }
    
    // 加载文档关键词
    await loadDocumentKeywords()
  } catch (error) {
    console.error('加载文档摘要失败:', error)
    showError('加载摘要失败')
  } finally {
    loading.value = false
  }
}

const loadDocumentKeywords = async () => {
  try {
    const response = await knowledgeMapService.getDocumentKeywords(props.documentId)
    if (response.data.code === 200 && response.data.data.keywords) {
      keywordsList.value = response.data.data.keywords
      console.log('文档关键词:', keywordsList.value)
    }
  } catch (error) {
    console.error('加载文档关键词失败:', error)
  }
}

const refreshSummary = () => {
  loadSummary()
}

const formatDate = (dateString: string | undefined) => {
  try {
    if (!dateString) return '未知时间'
    return new Date(dateString).toLocaleString('zh-CN')
  } catch {
    return dateString || '未知时间'
  }
}

const showError = (message: string) => {
  errorMessage.value = message
  errorSnackbar.value = true
}



// 生命周期
onMounted(() => {
  loadSummary()
})
</script>

<style scoped>
.document-summary {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  /* 改善滚动体验 */
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.2) transparent;
}

/* WebKit 浏览器滚动条样式 */
.document-summary::-webkit-scrollbar {
  width: 8px;
}

.document-summary::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.document-summary::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  border: 1px solid transparent;
}

.document-summary::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.summary-content {
  max-width: 100%;
  padding-bottom: 16px; /* 底部留一些空间 */
}

/* 确保内容区域可以正确滚动 */
.document-summary {
  -webkit-overflow-scrolling: touch; /* iOS 滚动优化 */
  scroll-behavior: smooth; /* 平滑滚动 */
}

/* 当内容过长时显示滚动提示 */
.document-summary::after {
  content: '';
  position: sticky;
  bottom: 0;
  height: 8px;
  background: linear-gradient(transparent, rgba(255, 255, 255, 0.8));
  pointer-events: none;
  z-index: 1;
}

/* 关键词芯片样式 */
.keyword-chip {
  cursor: pointer;
  transition: all 0.2s ease;
}

.keyword-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 主要要点样式 */
.main-point-text {
  position: relative;
  transition: all 0.2s ease;
}

.main-point-text.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: help;
}

.main-point-text.text-truncate:hover {
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 4px;
}
</style>