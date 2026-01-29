<template>
  <v-app>
    <!-- 根据路由决定是否显示Header -->
    <Header v-if="!isVideoPlayerRoute" />
    <v-main :class="{ 'video-player-main': isVideoPlayerRoute }">
      <!-- 根据路由元数据选择正确的布局 -->
      <component :is="layoutComponent">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </component>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DefaultLayout from './layouts/DefaultLayout.vue'
import TeacherLayout from './layouts/TeacherLayout.vue'
import BlankLayout from './layouts/BlankLayout.vue'
import Header from './components/Header.vue'

const route = useRoute()

// 检查当前路由是否为视频播放页面
const isVideoPlayerRoute = computed(() => {
  return route.name === 'VideoPlayer' || route.path.includes('/video/')
})

// 根据路由元数据确定使用哪个布局
const layoutComponent = computed(() => {
  if (isVideoPlayerRoute.value) {
    return BlankLayout
  }
  
  const layout = route.meta.layout || 'default'
  switch(layout) {
    case 'teacher':
      return TeacherLayout
    case 'blank':
      return BlankLayout
    default:
      return DefaultLayout
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: auto;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f4f4f4;
  color: #333;
}

.v-application {
  height: 100%;
  min-height: 100vh;
}

/* 确保v-main正确处理app-bar的偏移 */
:deep(.v-main) {
  padding-top: 0 !important;
}

:deep(.v-main .v-main__wrap) {
  padding-top: 56px; /* 为app-bar留出空间 */
}

.cursor-pointer {
  cursor: pointer;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c0c0c0;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 确保v-container内容可以滚动 */
.v-container {
  max-height: 100%;
  overflow-y: auto;
}

/* 视频播放页面的特殊样式 */
.video-player-main {
  padding: 0 !important;
}

.video-player-main .v-main__wrap {
  padding: 0 !important;
  min-height: 100vh !important;
}

/* 移动端视频播放优化 */
@media (max-width: 768px) {
  .video-player-main {
    overflow-x: hidden;
  }
}
</style>