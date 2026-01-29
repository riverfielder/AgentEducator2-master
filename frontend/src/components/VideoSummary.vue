<template>
  <div class="video-summary">
    <!-- 视频总结部分 -->
    <v-card v-if="summary" variant="flat" class="summary-section mb-2">
      <v-card-title class="text-subtitle-1 pb-2 pt-3 px-3">视频总结</v-card-title>
      <v-card-text class="summary-content pt-0 px-3 pb-3">
        <div class="main-points">
          <div class="text-subtitle-2 font-weight-medium mb-2">主要内容</div>
          <p class="text-body-2">{{ summary.mainPoints }}</p>
        </div>
        
        <div class="keywords mt-3">
          <div class="text-subtitle-2 font-weight-medium mb-2">知识点</div>
          <div class="d-flex flex-wrap gap-1">
            <v-chip
              v-for="(keyword, index) in summary.keywordsList"
              :key="getKeywordChipKey(keyword, index)"
              size="x-small"
              color="primary"
              variant="flat"
              class="ma-1 keyword-chip"
              @click="() => handleKeywordClick(keyword)"
              @click.right.prevent="() => goToKnowledgePointDetail(keyword)"
            >
              {{ keyword.name }}
              <v-tooltip activator="parent" location="top">
                <div class="text-caption">
                  <div>左键：查看相关视频</div>
                  <div>右键：查看掌握情况</div>
                </div>
              </v-tooltip>
            </v-chip>
          </div>
        </div>
        
        <!-- 知识点详情卡片 -->
        <v-expand-transition>
          <v-card v-if="selectedKeyword" class="mt-3" variant="outlined">
            <v-card-title class="text-h6 pa-4">
              {{ selectedKeyword.name }}
              <v-chip
                color="primary"
                size="small"
                class="ml-2"
              >
                知识点
              </v-chip>
            </v-card-title>
            <v-card-text class="pt-2">
              <p class="text-body-1">{{ selectedKeyword.description }}</p>
              <div v-if="selectedKeyword.relatedVideos?.length" class="mt-3">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="text-subtitle-2 font-weight-medium">相关视频</div>
                  <div class="d-flex gap-2">
                    <v-btn
                      color="success"
                      size="small"
                      variant="text"
                      prepend-icon="mdi-chart-line"
                      @click="goToKnowledgePointDetail(selectedKeyword)"
                    >
                      掌握情况
                    </v-btn>
                    <v-btn
                      color="primary"
                      size="small"
                      variant="text"
                      prepend-icon="mdi-robot"
                      @click="askAI(selectedKeyword)"
                    >
                      问AI
                    </v-btn>
                  </div>
                </div>
                <v-list density="compact" class="bg-transparent pa-0">
                  <v-list-item
                    v-for="video in selectedKeyword.relatedVideos"
                    :key="video.id"
                    @click="() => emit('jump-to-video', video.id)"
                    class="rounded-lg mb-1"
                    hover
                  >
                    <template v-slot:prepend>
                      <v-icon size="small" color="primary" class="mr-2">mdi-play-circle</v-icon>
                    </template>
                    
                    <v-list-item-title class="text-body-2">{{ video.title }}</v-list-item-title>
                    
                    <v-list-item-subtitle class="mt-1">
                      <div class="d-flex align-center text-caption">
                        <span class="text-primary">{{ video.courseName }}</span>
                        <v-icon size="12" class="mx-1">mdi-circle-small</v-icon>
                        <span class="mr-2">
                          <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                          {{ video.viewCount }}
                        </span>
                        <span>
                          <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                          {{ formatDuration(video.duration) }}
                        </span>
                      </div>
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>
              <div v-else class="mt-3 text-center text-body-2 text-medium-emphasis">
                暂无相关视频
              </div>
            </v-card-text>
          </v-card>
        </v-expand-transition>
        
        <div class="sections mt-3">
          <div class="text-subtitle-2 font-weight-medium mb-2">章节标记</div>
          <div class="sections-container">
            <v-list lines="one" density="compact" class="bg-transparent pa-0 sections-list">
              <v-list-item
                v-for="(section, index) in summary.sections"
                :key="index"
                @click="emitJumpToTimepoint(section.startTime || section.time_point)"
                class="pa-1 mb-1 rounded section-item"
                :class="{'section-expanded': isSectionExpanded(index)}"
                hover
              >
                <template v-slot:prepend>
                  <v-chip size="x-small" color="primary" variant="flat" class="me-2">
                    {{ formatTime(section.startTime || section.time_point) }}
                  </v-chip>
                </template>
                
                <div class="d-flex flex-column w-100">
                  <div class="d-flex align-center justify-space-between">
                    <v-list-item-title class="section-title text-body-2" :class="{'section-title-expanded': isSectionExpanded(index)}">
                      {{ section.title }}
                    </v-list-item-title>
                    
                    <v-btn
                      size="x-small"
                      icon
                      variant="text"
                      density="comfortable"
                      @click="toggleSection(index, $event)"
                    >
                      <v-icon size="small">
                        {{ isSectionExpanded(index) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                      </v-icon>
                    </v-btn>
                  </div>
                  
                  <v-expand-transition>
                    <div v-if="isSectionExpanded(index)" class="section-content-expanded mt-1">
                      <div class="text-caption">{{ section.content }}</div>
                    </div>
                  </v-expand-transition>
                </div>
              </v-list-item>
            </v-list>
          </div>
          <div class="text-center mt-1">
            <v-btn 
              size="x-small" 
              variant="text" 
              density="comfortable"
              @click="expandedSections = expandedSections.length === summary.sections.length ? [] : [...Array(summary.sections.length).keys()]"
            >
              {{ expandedSections.length === summary.sections.length ? '全部折叠' : '全部展开' }}
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>
    
    <v-card v-else class="d-flex align-center justify-center pa-3 mb-2" variant="flat" min-height="120">
      <div v-if="summaryLoading" class="text-center">
        <v-progress-circular indeterminate color="primary" size="32" class="mb-2"></v-progress-circular>
        <div class="text-caption">正在加载视频总结...</div>
      </div>
      <div v-else class="text-center">
        <div class="text-body-2">该视频暂无总结</div>
      </div>
    </v-card>

    <!-- 分集列表 -->
    <v-card variant="flat" class="episodes-section">
      <v-card-title class="text-subtitle-1 d-flex align-center pb-2 pt-3 px-3">
        课程视频列表
        <v-spacer></v-spacer>
        <v-chip
          v-if="episodes.length > 0"
          size="x-small" 
          color="primary" 
          variant="flat"
        >
          {{ episodes.length }}个视频
        </v-chip>
      </v-card-title>
      
      <v-card-text class="episodes-list pt-0 px-2 pb-2">
        <div v-if="episodesLoading" class="d-flex justify-center py-3">
          <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
        </div>
        
        <div v-else-if="episodes.length === 0" class="text-center py-3 text-medium-emphasis">
          <div class="text-body-2">本课程暂无其他视频</div>
        </div>
        
        <v-list v-else density="compact" class="bg-transparent pa-0">
          <v-list-item
            v-for="(episode, index) in episodes"
            :key="episode.id"
            :active="String(episode.id) === String(props.currentVideoId)"
            :class="{'v-list-item--active': String(episode.id) === String(props.currentVideoId)}"
            :data-video-id="String(episode.id)"
            @click="selectEpisode(episode.id)"
            hover
            class="mb-1 rounded pa-2"
            rounded
          >
            <template v-slot:prepend>
              <div class="mr-2 d-flex align-center justify-center bg-primary-lighten-4 rounded-circle" style="width: 28px; height: 28px;">
                <span class="text-primary font-weight-bold text-caption">P{{ index + 1 }}</span>
              </div>
            </template>
            
            <v-list-item-title class="text-body-2">{{ episode.title }}</v-list-item-title>
            
            <v-list-item-subtitle class="d-flex align-center mt-1">
              <v-icon size="x-small" class="mr-1">mdi-clock-outline</v-icon>
              <span class="text-caption mr-2">{{ formatDuration(episode.duration) }}</span>
              
              <v-icon size="x-small" class="mr-1">mdi-eye-outline</v-icon>
              <span class="text-caption">{{ episode.viewCount }}次</span>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import courseService from '../api/courseService'
import summaryService from '../api/summaryService'
import knowledgeMapService from '../api/knowledgeMapService'
import { useKeywordNavigation, useKeywordDisplay } from '@/composables/useKeywordNavigation'
import type { VideoKeywordData, VideoSummaryData } from '@/types/keyword'

const props = defineProps<{
  courseId: string
  currentVideoId: string
}>()

const emit = defineEmits(['jump-to-timepoint', 'jump-to-video', 'ask-ai'])

const router = useRouter()
const summary = ref<VideoSummaryData | null>(null)
const summaryLoading = ref(false)
const episodes = ref<any[]>([])
const episodesLoading = ref(false)
const episodesListRef = ref<HTMLElement | null>(null) // 分集列表的DOM引用
const showSectionDetails = ref(false) // 控制是否显示所有章节详情
const expandedSections = ref<number[]>([]) // 跟踪展开的章节索引
const selectedKeyword = ref<VideoKeywordData | null>(null)

// 使用composables
const { handleVideoKeywordClick, goToKnowledgePointDetail } = useKeywordNavigation()
const { getKeywordChipKey } = useKeywordDisplay()

// 加载视频总结
const loadSummary = async () => {
  if (!props.currentVideoId) return
  
  summaryLoading.value = true
  try {
    const response = await summaryService.getVideoSummary(props.currentVideoId)
    console.log('视频总结API响应:', response)  // 添加日志
    if (response.data.code === 200) {
      const summaryData = response.data.data
      
      // 确保数据格式化正确
      if (summaryData) {
        // 如果不存在mainPoints，则使用summary字段
        if (!summaryData.mainPoints && summaryData.summary) {
          summaryData.mainPoints = summaryData.summary
        }
        
        // 确保sections是数组 - 处理JSON格式数据
        if (typeof summaryData.sections === 'string') {
          try {
            summaryData.sections = JSON.parse(summaryData.sections);
          } catch (e) {
            console.error('解析章节JSON数据失败:', e);
            summaryData.sections = [];
          }
        } else if (!Array.isArray(summaryData.sections)) {
          summaryData.sections = [];
        }
        
        // 确保keywordsList是数组，并且每个知识点都有id
        if (!Array.isArray(summaryData.keywordsList)) {
          summaryData.keywordsList = []
        } else {
          // 确保每个知识点都有id
          summaryData.keywordsList = summaryData.keywordsList.map((keyword: any, index: number) => {
            if (!keyword.id && keyword.keyword_id) {
              return { ...keyword, id: keyword.keyword_id }
            }
            return keyword
          })
        }
        
        console.log('处理后的知识点列表:', summaryData.keywordsList)  // 添加日志
        
        summary.value = summaryData
      }
    }
  } catch (err) {
    console.error('获取视频总结失败:', err)
  } finally {
    summaryLoading.value = false
  }
}


// 获取课程视频列表
const fetchEpisodes = async () => {
  if (!props.courseId) return
  
  episodesLoading.value = true
  try {
    const response = await courseService.getCourseDetails(props.courseId)
    if (response.data.code === 200 && response.data.data.videos) {
      episodes.value = response.data.data.videos
    }
  } catch (err) {
    console.error('获取课程视频列表失败:', err)
  } finally {
    episodesLoading.value = false
  }
}

// 选择视频
const selectEpisode = (episodeId: number | string) => {
  // 在发送事件之前，先应用本地选中效果，提高响应速度
  const stringId = String(episodeId)
  
  // 在DOM更新前，先确保视觉反馈给用户
  const items = document.querySelectorAll('.episodes-list .v-list-item')
  items.forEach(item => {
    if (item.getAttribute('data-video-id') === stringId) {
      item.classList.add('v-list-item--active')
    } else {
      item.classList.remove('v-list-item--active')
    }
  })
  
  // 发射事件通知父组件切换视频
  emit('jump-to-video', stringId)
}

// 时间点跳转
const emitJumpToTimepoint = (timePoint: number | undefined) => {
  if (timePoint !== undefined) {
    console.log('跳转到时间点:', timePoint)
    emit('jump-to-timepoint', timePoint)
  } else {
    console.warn('无效的时间点')
  }
}

// 切换章节展开/折叠状态
const toggleSection = (index: number, event: Event) => {
  event.stopPropagation() // 阻止事件冒泡，防止触发跳转
  
  const sectionIndex = expandedSections.value.indexOf(index)
  if (sectionIndex === -1) {
    // 如果不在数组中，添加它（展开）
    expandedSections.value.push(index)
  } else {
    // 如果已在数组中，移除它（折叠）
    expandedSections.value.splice(sectionIndex, 1)
  }
}

// 检查章节是否展开
const isSectionExpanded = (index: number): boolean => {
  return expandedSections.value.includes(index)
}

// 格式化时间
const formatTime = (seconds: number | undefined): string => {
  if (seconds === undefined) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化视频时长
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 处理知识点点击
const handleKeywordClick = async (keyword: VideoKeywordData) => {
  // 如果点击的是同一个知识点，则切换显示状态
  if (selectedKeyword.value && selectedKeyword.value.id === keyword.id) {
    selectedKeyword.value = null
    return
  }
  
  console.log('点击的知识点数据:', keyword)  // 添加日志
  
  // 使用composable中的方法获取相关视频
  const keywordWithVideos = await handleVideoKeywordClick(keyword)
  if (keywordWithVideos) {
    selectedKeyword.value = keywordWithVideos
  } else {
    // 使用基础信息作为fallback
    selectedKeyword.value = {
      ...keyword,
      description: `这是关于 ${keyword.name} 的详细描述`,
      relatedVideos: []
    }
  }
}

// 添加askAI函数
const askAI = (keyword: any) => {
  if (!keyword) return
  
  // 直接对当前视频提问
  emit('ask-ai', {
    videoId: props.currentVideoId,
    keyword: keyword.name
  })
}

// goToKnowledgePointDetail 函数已从 useKeywordNavigation composable 中导入

onMounted(() => {
  console.log('VideoSummary组件已挂载，当前视频ID:', props.currentVideoId)
  loadSummary()
  fetchEpisodes()
})

// 当视频ID变化时重新加载总结
watch(() => props.currentVideoId, (newId) => {
  if (newId) {
    console.log('VideoSummary - 当前视频ID变化为:', newId)
    loadSummary()
    
    // 更新视频列表选中状态
    updateSelectedState(newId)
  }
})

// 更新视频列表选中状态
const updateSelectedState = (videoId: string) => {
  if (!episodes.value || episodes.value.length === 0) return
  
  console.log('更新视频选中状态，当前视频ID:', videoId)
  
  // 强制刷新选中状态
  nextTick(() => {
    // 使用data-video-id属性直接更新DOM元素
    const items = document.querySelectorAll('.episodes-list .v-list-item')
    items.forEach(item => {
      if (item.getAttribute('data-video-id') === videoId) {
        item.classList.add('v-list-item--active')
      } else {
        item.classList.remove('v-list-item--active')
      }
    })
    
    // 确保列表滚动到选中项
    const selectedItem = document.querySelector(`.episodes-list .v-list-item[data-video-id="${videoId}"]`)
    if (selectedItem) {
      selectedItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}
</script>

<style scoped>
.video-summary {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.summary-section {
  background-color: #f8faff;
  border-radius: 8px;
  margin-bottom: 4px;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.summary-content {
  overflow-y: auto;
  flex: 1;
  padding-right: 4px;
}

.main-points {
  background-color: white;
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.keywords .v-chip {
  margin: 1px;
}

.keyword-chip {
  cursor: pointer;
  transition: all 0.2s ease;
}

.keyword-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.sections-container {
  max-height: 250px;
  overflow-y: auto;
  padding-right: 8px;
}

.sections .v-list-item {
  transition: background-color 0.2s;
  padding: 4px;
  margin-bottom: 2px;
}

.sections .v-list-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
  cursor: pointer;
}

.episodes-section {
  margin-top: 0;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.episodes-list {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.episodes-list .v-list-item.v-list-item--active {
  background-color: rgba(var(--v-theme-primary), 0.1);
  position: relative;
}

.episodes-list .v-list-item.v-list-item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 0 2px 2px 0;
}

/* 章节列表样式 */
.sections-container {
  max-height: 250px;
  overflow-y: auto;
  border-radius: 6px;
  background-color: white;
  padding: 4px;
  box-shadow: inset 0 0 3px rgba(0, 0, 0, 0.05);
  transition: max-height 0.3s ease;
}

.section-title {
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 展开时的章节内容样式 */
.section-content-expanded {
  color: rgba(0, 0, 0, 0.7);
  line-height: 1.4;
  background-color: rgba(var(--v-theme-primary), 0.02);
  padding: 4px 6px;
  border-radius: 3px;
  white-space: pre-line;
}

/* 章节展开/折叠相关样式 */
.section-item {
  transition: all 0.3s;
}

.section-expanded {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.section-title-expanded {
  -webkit-line-clamp: unset !important;
  line-clamp: unset !important;
  display: block !important;
  font-weight: 500;
}

/* 添加刷新状态辅助类 */
.episodes-list .v-list.refreshing {
  animation: refresh 0.01s;
}

@keyframes refresh {
  0% { opacity: 0.99; }
  100% { opacity: 1; }
}

/* 自定义滚动条 - 更细 */
.summary-content::-webkit-scrollbar,
.episodes-list::-webkit-scrollbar,
.sections-container::-webkit-scrollbar {
  width: 4px;
}

.summary-content::-webkit-scrollbar-track,
.episodes-list::-webkit-scrollbar-track,
.sections-container::-webkit-scrollbar-track {
  background: transparent;
}

.summary-content::-webkit-scrollbar-thumb,
.episodes-list::-webkit-scrollbar-thumb,
.sections-container::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.15);
  border-radius: 2px;
}

.summary-content::-webkit-scrollbar-thumb:hover,
.episodes-list::-webkit-scrollbar-thumb:hover,
.sections-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.25);
}
</style>