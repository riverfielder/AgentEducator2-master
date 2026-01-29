<template>
  <div class="layout-container">
    <!-- 装饰背景 -->
    <div class="layout-bg"></div>
    
    <v-row no-gutters class="layout-row">
      <v-col class="sidebar-col" cols="auto">
        <Sidebar />
      </v-col>
      <v-col class="content-col">
        <div class="content-wrapper">
          <router-view v-slot="{ Component }">
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </router-view>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '../components/Sidebar.vue';
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: calc(100vh - 56px);  /* 减去Header高度 */
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  position: relative;
}

/* 装饰背景 */
.layout-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(circle at 20% 20%, rgba(102, 126, 234, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(118, 75, 162, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 40% 60%, rgba(240, 147, 251, 0.02) 0%, transparent 50%);
  pointer-events: none;
  z-index: 1;
}

.layout-row {
  height: calc(100vh - 56px);  /* 减去Header高度 */
  margin: 0 !important;
  position: relative;
  z-index: 2;
}

.sidebar-col {
  padding: 0;
  position: relative;
  z-index: 10;
}

.content-col {
  padding: 0;
  position: relative;
  z-index: 5;
  height: calc(100vh - 56px);  /* 减去Header高度 */
}

.content-wrapper {
  padding: 20px 24px;
  height: calc(100vh - 56px);  /* 减去Header高度 */
  overflow-y: auto;
  overflow-x: hidden;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 20px 0 0 0;
  position: relative;
}

/* 内容区域装饰 */
.content-wrapper::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(circle at 90% 10%, rgba(102, 126, 234, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 10% 90%, rgba(118, 75, 162, 0.03) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
}

/* 自定义滚动条 */
.content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
  border-radius: 3px;
  transition: background 0.3s ease;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.5), rgba(118, 75, 162, 0.5));
}

/* 确保Vuetify组件样式不被覆盖 */
:deep(.v-row) {
  margin: 0;
}

:deep(.v-col) {
  padding: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-wrapper {
    padding: 16px 20px;
    border-radius: 16px 0 0 0;
  }
}

@media (max-width: 600px) {
  .content-wrapper {
    padding: 12px 16px;
    border-radius: 12px 0 0 0;
  }
}

/* 添加过渡动画样式 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
