<template>
  <div class="video-player-page">
    <!-- 返回按钮 -->
    <div class="back-button-container">
      <v-btn
        icon
        size="small"
        variant="elevated"
        color="white"
        @click="goBack"
        class="back-btn"
      >
        <v-icon color="primary">mdi-arrow-left</v-icon>
      </v-btn>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <!-- 主内容 -->
    <div v-else class="main-layout">
      <!-- 视频区域 -->
      <div class="video-section" :class="{ 'video-collapsed': sidebarExpanded }">
        <div class="video-container">
          <div class="video-wrapper">
            <video 
              ref="videoRef" 
              class="video-player" 
              controls 
              autoplay 
              @timeupdate="handleTimeUpdate"
            >
              <source :src="videoUrl" type="video/mp4">
              您的浏览器不支持HTML5视频
            </video>
          </div>
        </div>
        
        <!-- 视频信息面板 -->
        <div class="video-info-panel">
          <div class="video-details">
            <h1 class="video-title">{{ videoTitle }}</h1>
            <div class="video-meta">
              <div class="meta-item">
                <v-icon size="16" color="text-secondary">mdi-eye</v-icon>
                <span>{{ videoDetail?.viewCount || 0 }} 次观看</span>
              </div>
              <div class="meta-divider"></div>
              <div class="meta-item">
                <v-icon size="16" color="text-secondary">mdi-calendar</v-icon>
                <span>{{ formatDate(videoDetail?.uploadTime) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 分隔条和切换按钮 -->
      <div class="separator-container">
        <div class="separator-line"></div>
        <v-btn
          icon
          size="small"
          variant="elevated"
          color="primary"
          @click="toggleSidebar"
          class="toggle-button"
          :class="{ 'toggle-rotated': sidebarExpanded }"
        >
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
      </div>

      <!-- 侧边栏 -->
      <div class="sidebar-section" :class="{ 'sidebar-expanded': sidebarExpanded }">
        <!-- 顶部导航 -->
        <div class="sidebar-header">
          <v-tabs 
            v-model="currentTab" 
            density="compact" 
            color="primary"
            slider-color="primary"
            grow
          >
            <v-tab 
              v-for="tab in tabs" 
              :key="tab.id" 
              :value="tab.id"
              class="sidebar-tab"
            >
              <v-icon size="18" class="tab-icon">{{ tab.icon }}</v-icon>
              <span class="tab-label">{{ tab.name }}</span>
            </v-tab>
          </v-tabs>
        </div>

        <!-- 内容区域 -->
        <div class="sidebar-content">
          <v-window v-model="currentTab" class="content-window">
            <v-window-item value="summary" class="window-item">
              <VideoSummary 
                :course-id="courseId" 
                :current-video-id="videoId" 
                @jump-to-timepoint="jumpToTimepoint"
                @jump-to-video="navigateToVideo" 
                @ask-ai="handleAskAI"
              />
            </v-window-item>

            <v-window-item value="ai" class="window-item">
              <AIChat 
                :video-id="videoId" 
                :course-id="courseId" 
                v-model:auto-prompt="autoPrompt"
                @jump-to-timepoint="jumpToTimepoint" 
                @jump-to-video-timepoint="jumpToVideoTimepoint" 
              />
            </v-window-item>

            <v-window-item value="comments" class="window-item">
              <Comments 
                :video-id="videoId" 
                :current-time="currentTime" 
                @jump-to-timepoint="jumpToTimepoint" 
              />
            </v-window-item>
          </v-window>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import VideoSummary from '../components/VideoSummary.vue'
import AIChat from '../components/AIChat.vue'
import Comments from '../components/Comments.vue'
import videoService from '../api/videoService'

const router = useRouter()
const route = useRoute()
const videoRef = ref<HTMLVideoElement | null>(null)
const currentTab = ref('summary')
const videoDetail = ref<any>(null)
const loading = ref(true)
const currentTime = ref(0)
const updateInterval = ref<number | null>(null)
const error = ref<string | null>(null)

// 用户相关状态
const showDropdown = ref(false)
const username = computed(() => localStorage.getItem('wendao_user_name') || 'User')
const userAvatar = ref('')
const isLoggedIn = computed(() => !!localStorage.getItem('wendao_token'))

// 菜单控制
const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

// 退出登录
const logout = () => {
  localStorage.removeItem('wendao_token')
  localStorage.removeItem('wendao_user_id')
  localStorage.removeItem('wendao_user_name')
  localStorage.removeItem('wendao_user_role')
  router.push('/login')
}

// 从路由参数中获取课程ID和视频ID
const courseId = (route.params.courseId || 0) as string
const startTime = route.query.t ? Number(route.query.t) : 0

// 将videoId改为计算属性，以便随路由参数变化而自动更新
const videoId = computed(() => (route.params.videoId || 0) as string)

// 其他计算属性
console.log('视频ID:', videoId.value)
console.log('课程ID:', courseId, '开始时间:', startTime, videoDetail.value)
const videoUrl = computed(() => videoDetail.value?.videoUrl || '')
const videoTitle = computed(() => videoDetail.value?.title || '加载中...')

const tabs = [
  { id: 'summary', name: '总结', icon: 'mdi-file-document' },
  { id: 'ai', name: '问答', icon: 'mdi-robot' },
  { id: 'comments', name: '评论', icon: 'mdi-comment-outline' }
]

// 获取视频信息
const fetchVideoInfo = async () => {
  if (!videoId.value) return

  loading.value = true
  error.value = null
  try {
    const response = await videoService.getVideoDetail(videoId.value)
    if (response.data.code === 200) {
      videoDetail.value = response.data.data

      // 强制刷新 video src，确保每次都能正确加载
      if (videoRef.value) {
        videoRef.value.load()
      }

      // 设置初始播放时间
      setVideoTime(startTime || videoDetail.value.lastWatchTime || 0)
    } else {
      error.value = response.data.message || '获取视频信息失败'
    }
  } catch (err: any) {
    console.error('获取视频信息失败:', err)
    error.value = err.message || '获取视频信息失败'
  } finally {
    loading.value = false
  }
}

// 设置视频播放时间
const setVideoTime = (seconds: number) => {
  if (videoRef.value && seconds > 0) {
    videoRef.value.currentTime = seconds
  }
}

// 监听路由参数变化
watch(() => route.params.videoId,
  (newValue, oldValue) => {
    if (newValue && newValue !== oldValue) {
      console.log(`视频ID从 ${oldValue} 变更为 ${newValue}，重新获取视频信息`)

      if (videoDetail.value && String(videoDetail.value.id) === String(newValue)) {
        console.log('视频信息已存在，无需重新获取')
        return
      }

      fetchVideoInfo()
    }
  },
  { immediate: true } // 确保组件首次加载时也会执行
)

// 处理视频时间更新
const handleTimeUpdate = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
  }
}

// 定期保存观看进度
const startProgressUpdates = () => {
  // 每30秒保存一次进度
  updateInterval.value = window.setInterval(() => {
    if (videoRef.value) {
      saveProgress()
    }
  }, 30000)
}

// 保存观看进度到服务器
const saveProgress = async () => {
  if (!videoId.value || !videoRef.value) return

  try {
    const currentTime = videoRef.value.currentTime
    const duration = videoRef.value.duration
    const completed = currentTime / duration > 0.9 // 观看超过90%视为完成

    await videoService.updateProgress(videoId.value, {
      currentTime,
      duration,
      completed
    })
  } catch (err) {
    console.error('保存观看进度失败:', err)
  }
}

// 跳转到指定时间点
const jumpToTimepoint = (seconds: number) => {
  if (videoRef.value) {
    videoRef.value.currentTime = seconds
    videoRef.value.play().catch(err => console.error('视频播放失败:', err))
  }
}

const jumpToVideoTimepoint = (toVideoId: string, seconds: number) => {
  console.log('跳转到视频时间点:', videoId, seconds)
  
  if (toVideoId === videoId.value) {
    // 如果是当前视频，直接跳转时间
    jumpToTimepoint(seconds)
  } else {
    // 如果是不同视频，先切换视频再跳转时间
    navigateToVideo(toVideoId, seconds)
  }
}

// 导航到视频页面 - 这个函数适用于在同一课程内切换视频
const navigateToVideo = async (videoIdNow: string, targetTime?: number) => {
  // 在切换视频前保存当前视频的进度
  saveProgress()

  if (videoId.value === videoIdNow) {
    console.log('已经在当前视频页面')
    if (targetTime !== undefined) {
      jumpToTimepoint(targetTime)
    }
    return
  }

  try {
    // 直接获取新视频的详细信息
    const response = await videoService.getVideoDetail(videoIdNow)
    if (response.data.code === 200) {
      // 更新本地视频详情，无需等待路由变化触发
      videoDetail.value = response.data.data
      
      // 更新视频源并等待加载完成
      if (videoRef.value) {
        const video = videoRef.value
        
        // 创建一个Promise来等待视频加载完成
        const waitForVideoLoad = new Promise<void>((resolve) => {
          const handleLoadedData = () => {
            video.removeEventListener('loadeddata', handleLoadedData)
            resolve()
          }
          video.addEventListener('loadeddata', handleLoadedData)
        })
        
        video.src = response.data.data.videoUrl
        video.load() // 强制重新加载视频
        
        // 等待视频加载完成后设置时间和播放
        waitForVideoLoad.then(() => {
          if (targetTime !== undefined && targetTime > 0) {
            video.currentTime = targetTime
          } else {
            video.currentTime = 0
          }
          
          // 尝试播放视频
          video.play().catch(err => console.error('视频播放失败:', err))
        })
      }

      // 导航到新视频的URL - 这会触发路由参数变化
      const query = targetTime !== undefined ? { ...route.query, t: targetTime } : route.query
      router.push({
        path: `/course/${response.data.data.courseId}/video/${videoIdNow}`,
        query
      })

    } else {
      console.error('获取新视频信息失败:', response.data.message)
    }
  } catch (err) {
    console.error('导航到新视频时出错:', err)
  }
}

// 新增移动端检测和重定向
const checkMobileAndRedirect = () => {
  const isMobile = window.innerWidth <= 768 || /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  
  if (isMobile) {
    // 重定向到移动端视频播放器
    const currentPath = route.path
    const mobilePath = currentPath.replace('/course/', '/mobile/course/')
    router.replace({ path: mobilePath, query: route.query })
    return true
  }
  return false
}

onMounted(() => {
  // 在加载视频前先检查是否需要重定向
  if (checkMobileAndRedirect()) {
    return
  }
  
  fetchVideoInfo()
  startProgressUpdates()

  // 检查是否需要自动触发AI对话
  const askAI = route.query.askAI
  const keyword = route.query.keyword
  if (askAI === 'true' && keyword) {
    // 等待视频信息加载完成后再触发AI对话
    nextTick(() => {
      currentTab.value = 'ai'
      handleAskAI({
        videoId: videoId.value,
        keyword: keyword as string
      })
    })
  }
})

// 组件卸载前清理资源
onBeforeUnmount(() => {
  // 保存最终进度
  saveProgress()

  // 清除定时器
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
})

const goBack = () => {
  // 保存进度
  saveProgress()
  router.back()
}

// 格式化日期
const formatDate = (dateString: string | undefined) => {
  if (!dateString) return '-'

  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 添加侧边栏展开状态
const sidebarExpanded = ref(false)

// 添加切换侧边栏展开/收起的方法
const toggleSidebar = () => {
  sidebarExpanded.value = !sidebarExpanded.value
}

// 在script部分添加autoPrompt状态
const autoPrompt = ref<string>('')

// 修改handleAskAI函数
const handleAskAI = (data: { videoId: string, keyword: string }) => {
  // 如果是不同视频，先跳转
  if (data.videoId !== videoId.value) {
    navigateToVideo(data.videoId)
  }
  
  // 切换到AI对话标签页
  currentTab.value = 'ai'
  
  // 设置自动对话的提示词
  autoPrompt.value = `请找出本视频中关于"${data.keyword}"的表述，并解释这个概念。`
}
</script>

<style scoped>
.video-player-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #f8f9fb 100%);
  position: relative;
  overflow: hidden;
}

.back-button-container {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 1001;
}

.back-btn {
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #fafafa;
}

.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 视频区域 */
.video-section {
  flex: 2.5;
  display: flex;
  flex-direction: column;
  background: #000;
  transition: flex 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 400px;
}

.video-collapsed {
  flex: 1;
  min-width: 300px;
}

.video-container {
  flex: 1;
  position: relative;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #000;
}

.video-info-panel {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-top: 1px solid #e9ecef;
  padding: 20px 24px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.video-details {
  max-width: 100%;
}

.video-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 12px;
  line-height: 1.4;  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #64748b;
  font-size: 0.875rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-divider {
  width: 1px;
  height: 16px;
  background: #cbd5e0;
}

/* 分隔条 */
.separator-container {
  position: relative;
  width: 2px;
  background: linear-gradient(to bottom, #e2e8f0, #f1f5f9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.separator-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 1px;
  background: #cbd5e0;
  transform: translateX(-50%);
}

.toggle-button {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 2px solid #ffffff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 20;
}

.toggle-button:hover {
  transform: translate(-50%, -50%) scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.toggle-rotated {
  transform: translate(-50%, -50%) rotate(180deg);
}

.toggle-rotated:hover {
  transform: translate(-50%, -50%) rotate(180deg) scale(1.1);
}

/* 侧边栏 */
.sidebar-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-left: 1px solid #e2e8f0;
  transition: flex 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 320px;
  max-width: 480px;
  overflow: hidden;
}

.sidebar-expanded {
  flex: 1.5;
  min-width: 400px;
  max-width: 600px;
}

.sidebar-header {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.sidebar-tab {
  text-transform: none;
  font-weight: 500;
  padding: 12px 16px;
}

.tab-icon {
  margin-right: 8px;
}

.tab-label {
  font-size: 0.875rem;
  letter-spacing: 0.025em;
}

.sidebar-content {
  flex: 1;
  overflow: hidden;
  background: #ffffff;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-window {
  height: 100%;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.window-item {
  height: 100%;
  width: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 确保组件内容可以正常滚动，减少内边距 */
.window-item :deep(.v-window-item__content) {
  height: 100% !important;
  overflow: auto !important;
  display: flex !important;
  flex-direction: column !important;
  flex: 1 !important;
}

/* 针对各个组件的样式优化 - 减少内边距 */
.window-item :deep(.video-summary),
.window-item :deep(.ai-chat),
.window-item :deep(.comments) {
  height: 100% !important;
  overflow-y: auto !important;
  padding: 8px 12px !important;
  box-sizing: border-box !important;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .window-item :deep(.video-summary),
  .window-item :deep(.ai-chat),
  .window-item :deep(.comments) {
    padding: 6px 10px !important;
  }
}

@media (max-width: 480px) {
  .window-item :deep(.video-summary),
  .window-item :deep(.ai-chat),
  .window-item :deep(.comments) {
    padding: 4px 8px !important;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .window-item :deep(.video-summary),
  .window-item :deep(.ai-chat),
  .window-item :deep(.comments) {
    background: #2d3748 !important;
  }
}

.video-player {
  will-change: transform;
}

.toggle-button {
  will-change: transform;
}

/* 无障碍支持 */
@media (prefers-reduced-motion: reduce) {
  .video-section,
  .sidebar-section,
  .toggle-button {
    transition: none;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .video-player-page {
    background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
  }
  
  .video-info-panel {
    background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
    border-top-color: #4a5568;
  }
  
  .video-title {
    color: #f7fafc;
  }
  
  .video-meta {
    color: #a0aec0;
  }
  
  .meta-divider {
    background: #4a5568;
  }
  
  .sidebar-section {
    background: #2d3748;
    border-left-color: #4a5568;
  }
  
  .sidebar-header {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    border-bottom-color: #4a5568;
  }
  
  .content-panel {
    background: #2d3748;
  }
}
</style>