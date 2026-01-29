<template>
  <div class="mobile-video-player">
    <!-- 顶部状态栏 -->
    <div class="mobile-status-bar">
      <v-btn
        icon
        size="small"
        variant="text"
        color="white"
        @click="goBack"
        class="back-btn"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      
      <div class="status-title">
        <span class="text-white text-truncate">{{ videoTitle }}</span>
      </div>
      
      <v-btn
        icon
        size="small"
        variant="text"
        color="white"
        @click="showMenu = !showMenu"
      >
        <v-icon>mdi-dots-vertical</v-icon>
      </v-btn>
    </div>

    <!-- 视频播放器 -->
    <div class="mobile-video-container" :class="{ 'fullscreen': isFullscreen }">
      <video 
        ref="videoRef" 
        class="mobile-video-player-element" 
        controls 
        autoplay 
        @timeupdate="handleTimeUpdate"
        @fullscreenchange="handleFullscreenChange"
        :style="{ height: isFullscreen ? '100vh' : '40vh' }"
      >
        <source :src="videoUrl" type="video/mp4">
        您的浏览器不支持HTML5视频
      </video>
    </div>

    <!-- 视频信息 -->
    <div class="mobile-video-info" v-show="!isFullscreen">
      <v-card flat class="pa-3">
        <h2 class="text-h6 mb-2">{{ videoTitle }}</h2>
        <div class="d-flex align-center text-caption text-medium-emphasis">
          <v-icon size="14" class="me-1">mdi-eye</v-icon>
          <span class="me-3">{{ videoDetail?.viewCount || 0 }} 次观看</span>
          <v-icon size="14" class="me-1">mdi-calendar</v-icon>
          <span>{{ formatDate(videoDetail?.uploadTime) }}</span>
        </div>
      </v-card>
    </div>

    <!-- 底部导航 -->
    <div class="mobile-bottom-nav" v-show="!isFullscreen">
      <v-bottom-navigation 
        v-model="activeTab"
        height="60"
        bg-color="white"
        border
        elevation="8"
      >
        <v-btn value="summary" class="nav-btn">
          <v-icon>mdi-file-document</v-icon>
          <span class="nav-label">总结</span>
        </v-btn>
        
        <v-btn value="ai" class="nav-btn">
          <v-icon>mdi-robot</v-icon>
          <span class="nav-label">问答</span>
        </v-btn>
        
        <v-btn value="comments" class="nav-btn">
          <v-icon>mdi-comment-outline</v-icon>
          <span class="nav-label">评论</span>
        </v-btn>
      </v-bottom-navigation>
    </div>

    <!-- 内容面板 -->
    <div class="mobile-content-panel" v-show="!isFullscreen && activeTab">
      <div class="panel-header">
        <div class="panel-title">
          {{ getTabName(activeTab) }}
        </div>
        <v-btn
          icon
          size="small"
          variant="text"
          @click="activeTab = null"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </div>
      
      <div class="panel-content">
        <!-- 视频总结 -->
        <div v-if="activeTab === 'summary'" class="content-wrapper">
          <VideoSummary 
            :course-id="courseId" 
            :current-video-id="videoId" 
            @jump-to-timepoint="jumpToTimepoint"
            @jump-to-video="navigateToVideo" 
          />
        </div>

        <!-- AI问答 -->
        <div v-if="activeTab === 'ai'" class="content-wrapper">
          <AIChat 
            :video-id="videoId" 
            :course-id="courseId" 
            @jump-to-timepoint="jumpToTimepoint" 
            @jump-to-video-timepoint="jumpToVideoTimepoint" 
          />
        </div>

        <!-- 评论 -->
        <div v-if="activeTab === 'comments'" class="content-wrapper">
          <Comments 
            :video-id="videoId" 
            :current-time="currentTime" 
            @jump-to-timepoint="jumpToTimepoint" 
          />
        </div>
      </div>
    </div>

    <!-- 菜单 -->
    <v-menu v-model="showMenu" location="top end" offset="10">
      <v-list density="compact">
        <v-list-item @click="shareVideo">
          <template v-slot:prepend>
            <v-icon>mdi-share</v-icon>
          </template>
          <v-list-item-title>分享</v-list-item-title>
        </v-list-item>
        <v-list-item @click="toggleFullscreen">
          <template v-slot:prepend>
            <v-icon>{{ isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen' }}</v-icon>
          </template>
          <v-list-item-title>{{ isFullscreen ? '退出全屏' : '全屏播放' }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- 加载状态 -->
    <v-overlay v-model="loading" class="d-flex align-center justify-center">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </v-overlay>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import VideoSummary from '../components/VideoSummary.vue'
import AIChat from '../components/AIChat.vue'
import Comments from '../components/Comments.vue'
import videoService from '../api/videoService'

const router = useRouter()
const route = useRoute()
const videoRef = ref<HTMLVideoElement | null>(null)
const activeTab = ref<string | null>(null)
const videoDetail = ref<any>(null)
const loading = ref(true)
const currentTime = ref(0)
const updateInterval = ref<number | null>(null)
const isFullscreen = ref(false)
const showMenu = ref(false)

// 从路由参数中获取课程ID和视频ID
const courseId = (route.params.courseId || 0) as string
const startTime = route.query.t ? Number(route.query.t) : 0
const videoId = computed(() => (route.params.videoId || 0) as string)

// 计算属性
const videoUrl = computed(() => videoDetail.value?.videoUrl || '')
const videoTitle = computed(() => videoDetail.value?.title || '加载中...')

// 获取标签名称
const getTabName = (tab: string) => {
  const names = {
    summary: '视频总结',
    ai: 'AI问答',
    comments: '评论'
  }
  return names[tab] || tab
}

// 获取视频信息
const fetchVideoInfo = async () => {
  if (!videoId.value) return

  loading.value = true
  try {
    const response = await videoService.getVideoDetail(videoId.value)
    if (response.data.code === 200) {
      videoDetail.value = response.data.data

      if (videoRef.value) {
        videoRef.value.load()
      }

      setVideoTime(startTime || videoDetail.value.lastWatchTime || 0)
    }
  } catch (err: any) {
    console.error('获取视频信息失败:', err)
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

// 处理视频时间更新
const handleTimeUpdate = () => {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
  }
}

// 处理全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// 切换全屏
const toggleFullscreen = () => {
  if (!videoRef.value) return

  if (!document.fullscreenElement) {
    videoRef.value.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// 跳转到指定时间点
const jumpToTimepoint = (seconds: number) => {
  if (videoRef.value) {
    videoRef.value.currentTime = seconds
    videoRef.value.play().catch(err => console.error('视频播放失败:', err))
  }
  // 关闭面板，返回视频
  activeTab.value = null
}

// 跳转到视频时间点
const jumpToVideoTimepoint = (toVideoId: string, seconds: number) => {
  if (toVideoId === videoId.value) {
    jumpToTimepoint(seconds)
  } else {
    navigateToVideo(toVideoId, seconds)
  }
}

// 导航到其他视频
const navigateToVideo = async (videoIdNow: string, targetTime?: number) => {
  if (videoId.value === videoIdNow) {
    if (targetTime !== undefined) {
      jumpToTimepoint(targetTime)
    }
    return
  }

  try {
    const response = await videoService.getVideoDetail(videoIdNow)
    if (response.data.code === 200) {
      const query = targetTime !== undefined ? { ...route.query, t: targetTime } : route.query
      router.push({
        path: `/mobile/course/${response.data.data.courseId}/video/${videoIdNow}`,
        query
      })
    }
  } catch (err) {
    console.error('导航到新视频时出错:', err)
  }
}

// 分享视频
const shareVideo = () => {
  if (navigator.share) {
    navigator.share({
      title: videoTitle.value,
      url: window.location.href
    })
  } else {
    // 复制链接到剪贴板
    navigator.clipboard.writeText(window.location.href)
    // TODO: 显示提示消息
  }
}

// 返回
const goBack = () => {
  if (courseId) {
    router.push(`/course/${courseId}`)
  } else {
    router.back()
  }
}

// 格式化日期
const formatDate = (dateString: string | undefined) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })
}

// 监听路由参数变化
watch(() => route.params.videoId, (newValue, oldValue) => {
  if (newValue && newValue !== oldValue) {
    fetchVideoInfo()
  }
}, { immediate: true })

onMounted(() => {
  fetchVideoInfo()
})

onBeforeUnmount(() => {
  if (updateInterval.value) {
    clearInterval(updateInterval.value)
  }
})
</script>

<style scoped>
.mobile-video-player {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #000;
  overflow: hidden;
}

/* 状态栏 */
.mobile-status-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 44px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  padding: 0 8px;
  z-index: 1000;
}

.status-title {
  flex: 1;
  text-align: center;
  padding: 0 16px;
}

/* 视频容器 */
.mobile-video-container {
  width: 100%;
  background: #000;
  position: relative;
  margin-top: 44px;
}

.mobile-video-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  margin-top: 0;
}

.mobile-video-player-element {
  width: 100%;
  height: 40vh;
  object-fit: cover;
  background: #000;
}

/* 视频信息 */
.mobile-video-info {
  background: white;
  border-top: 1px solid #e0e0e0;
}

/* 底部导航 */
.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.nav-btn {
  flex-direction: column;
  height: 60px;
  min-width: auto;
  padding: 4px 8px;
}

.nav-label {
  font-size: 0.7rem;
  margin-top: 2px;
  text-transform: none;
}

/* 内容面板 */
.mobile-content-panel {
  position: fixed;
  bottom: 60px;
  left: 0;
  right: 0;
  top: 0;
  background: white;
  z-index: 200;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.panel-header {
  height: 56px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  padding: 0 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.panel-title {
  flex: 1;
  font-size: 1.1rem;
  font-weight: 500;
}

.panel-content {
  flex: 1;
  overflow: hidden;
  background: #f5f5f5;
}

.content-wrapper {
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* 修复组件在移动端面板中的显示 */
.content-wrapper :deep(.video-summary),
.content-wrapper :deep(.ai-chat-container),
.content-wrapper :deep(.comments-container) {
  height: 100% !important;
  background: #f5f5f5 !important;
}

.content-wrapper :deep(.comments-list-container),
.content-wrapper :deep(.chat-messages-container) {
  height: calc(100% - 100px) !important;
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch !important;
}

/* 横屏模式优化 */
@media (orientation: landscape) {
  .mobile-video-player-element {
    height: 100vh;
  }
  
  .mobile-video-info {
    display: none;
  }
  
  .mobile-bottom-nav {
    display: none;
  }
  
  .mobile-content-panel {
    bottom: 0;
  }
}

/* 超小屏幕优化 */
@media (max-width: 360px) {
  .nav-label {
    font-size: 0.65rem;
  }
  
  .panel-title {
    font-size: 1rem;
  }
}

/* 确保视频控件在移动端正常显示 */
.mobile-video-player-element::-webkit-media-controls {
  display: flex !important;
}

.mobile-video-player-element::-webkit-media-controls-panel {
  background: rgba(0, 0, 0, 0.8);
}

/* 防止页面缩放 */
.mobile-video-player {
  touch-action: manipulation;
}

/* 优化触摸体验 */
.nav-btn,
.back-btn {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
</style>
