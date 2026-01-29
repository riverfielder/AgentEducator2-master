<template>
  <v-navigation-drawer
    v-model="isOpen"
    :rail="isCollapsed"
    permanent
    app
    class="sidebar"
    :width="200"
    :rail-width="56"
    :expand-on-hover="false"
  >
    <!-- 侧边栏头部Logo区域 -->
    <div class="sidebar-header">
      <div v-if="!isCollapsed" class="sidebar-logo">
        <div class="logo-container">
          <svg class="logo-icon-svg" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path d="M888.3 279.8v412.5l-378 146.6-377.9-146.6V279.8H66.1v436.1c-0.1 13.9 8.3 26.5 21.2 31.6l411.1 159.3c3.8 1.3 7.9 2 11.9 2 4.1 0.1 8.1-0.6 11.9-2l411.1-159.3c12.8-5.3 21.2-17.8 21.2-31.6V279.8h-66.2z" fill="currentColor"></path>
            <path d="M233.4 620.7l263.9 110.8c4 2 8.5 2.9 13 2.7 6.9 0.1 13.6-2.1 19.1-6.2 9.4-6.5 15.1-17.2 15-28.7V276.8l195.6-82V566l-151.3 63.3c-1 0.4-1.9 0.9-2.8 1.4l29.6 61.1 171.7-71.1c12.8-5.2 21.2-17.6 21.2-31.5V143.4c0.2-11.5-5.5-22.3-15-28.7-9.7-6-21.6-7-32.1-2.7l-264 110.8c-12.8 5.2-21.2 17.6-21.2 31.5v393.9l-195.6-82.1V194.8l114.7 58c0.2 0.1 0.4 0.1 0.6 0.2l28.7-61.3c-1.1-0.6-2.1-1.2-3.3-1.7l-161.8-78c-10.5-4.6-22.6-3.6-32.1 2.7-9.4 6.5-15.1 17.2-15 28.7v445.7c-0.1 14 8.3 26.4 21.1 31.6z" fill="currentColor"></path>
          </svg>
          <div class="logo-text-container">
            <div class="logo-text">闻道</div>
            <div class="logo-subtitle">学习平台</div>
          </div>
        </div>
      </div>
      <div v-else class="sidebar-logo-collapsed">
        <div class="logo-icon">
          <svg class="logo-icon-svg-small" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
            <path d="M888.3 279.8v412.5l-378 146.6-377.9-146.6V279.8H66.1v436.1c-0.1 13.9 8.3 26.5 21.2 31.6l411.1 159.3c3.8 1.3 7.9 2 11.9 2 4.1 0.1 8.1-0.6 11.9-2l411.1-159.3c12.8-5.3 21.2-17.8 21.2-31.6V279.8h-66.2z" fill="currentColor"></path>
            <path d="M233.4 620.7l263.9 110.8c4 2 8.5 2.9 13 2.7 6.9 0.1 13.6-2.1 19.1-6.2 9.4-6.5 15.1-17.2 15-28.7V276.8l195.6-82V566l-151.3 63.3c-1 0.4-1.9 0.9-2.8 1.4l29.6 61.1 171.7-71.1c12.8-5.2 21.2-17.6 21.2-31.5V143.4c0.2-11.5-5.5-22.3-15-28.7-9.7-6-21.6-7-32.1-2.7l-264 110.8c-12.8 5.2-21.2 17.6-21.2 31.5v393.9l-195.6-82.1V194.8l114.7 58c0.2 0.1 0.4 0.1 0.6 0.2l28.7-61.3c-1.1-0.6-2.1-1.2-3.3-1.7l-161.8-78c-10.5-4.6-22.6-3.6-32.1 2.7-9.4 6.5-15.1 17.2-15 28.7v445.7c-0.1 14 8.3 26.4 21.1 31.6z" fill="currentColor"></path>
          </svg>
        </div>
      </div>
    </div>

    <v-divider class="sidebar-divider"></v-divider>

    <v-list density="compact" nav class="sidebar-nav">
      <v-list-item
        v-for="(item, index) in currentNavItems"
        :key="index"
        :to="item.path"
        :title="item.title"
        :prepend-icon="convertIcon(item.icon)"
        :active="item.path === router.currentRoute.value.path"
        @click="navigateToPage(item.path)"
        class="sidebar-item"
      ></v-list-item>
    </v-list>
    
    <v-btn
      block
      icon
      @click="toggleSidebar"
      class="collapse-btn"
    >
      <v-icon>{{ isCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
    </v-btn>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { teacherNavItems } from '../config/navigation';

const isOpen = ref(true);
const isCollapsed = ref(false);
const router = useRouter();
const route = useRoute();

// 学生端导航菜单项
const studentNavItems = [
  { id: 1, title: '首页', icon: 'fas fa-book-open', path: '/' },
  { id: 2, title: 'AI学习助手', icon: 'fas fa-robot', path: '/ai-assistant' },
  { id: 3, title: '个性化推荐', icon: 'fas fa-star', path: '/personalized' },
  { id: 4, title: '知识图谱', icon: 'fas fa-mind-share', path: '/knowledge-map' },
  { id: 5, title: '作业', icon: 'mdi-clipboard-text', path: '/student-assignments' },
  { id: 6, title: '笔记本', icon: 'fas fa-notebook', path: '/notebook' },
];

// 根据当前路由的布局类型确定显示哪个导航菜单
const currentNavItems = computed(() => {
  const layout = route.meta.layout;
  return layout === 'teacher' ? teacherNavItems : studentNavItems;
});

// 将 Font Awesome 图标转换为 Material Design 图标
const convertIcon = (iconName: string) => {
  // 如果图标是 fas fa- 开头，转换为对应的 mdi- 前缀
  if (iconName && iconName.startsWith('fas fa-')) {
    const iconPart = iconName.replace('fas fa-', '');
    const iconMap: {[key: string]: string} = {
      'home': 'mdi-home',
      'book': 'mdi-book',
      'video': 'mdi-video',
      'user-graduate': 'mdi-account-school',
      'tasks': 'mdi-clipboard-check',
      'chart-line': 'mdi-chart-line',
      'clipboard-list': 'mdi-clipboard-list',
      'cog': 'mdi-cog',
      'book-open': 'mdi-book-open-variant',
      'notebook': 'mdi-notebook',
      'robot': 'mdi-robot',
      'mind-share': 'mdi-graph',
    };
    
    return iconMap[iconPart] || `mdi-${iconPart}`;
  }
  
  return iconName; // 如果已经是 mdi 图标，直接返回
};

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

const navigateToPage = (path: string) => {
  if (path !== router.currentRoute.value.path) {
    router.push(path);
  }
};
</script>

<style scoped>
.sidebar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #5a67d8 100%);
  color: white;
  position: relative;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

/* 添加装饰背景 */
.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(240, 147, 251, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: 1;
}

/* 侧边栏头部区域 */
.sidebar-header {
  position: relative;
  z-index: 2;
  padding: 20px 16px 16px;
  text-align: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.logo-icon-svg {
  width: 28px;
  height: 28px;
  color: rgba(255, 255, 255, 0.95);
  filter: drop-shadow(0 2px 4px rgba(255, 255, 255, 0.2));
  flex-shrink: 0;
}

.logo-text-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  line-height: 1.2;
}

.logo-text {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 1.5px;
  background: linear-gradient(135deg, #fff 0%, rgba(255, 255, 255, 0.85) 50%, #fff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
  margin-bottom: 2px;
  line-height: 1.1;
}

.logo-subtitle {
  font-size: 12px;
  opacity: 0.85;
  letter-spacing: 0.8px;
  font-weight: 500;
  line-height: 1.2;
}

.sidebar-logo-collapsed {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: all 0.3s ease;
}

.logo-icon:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.15));
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
}

.logo-icon-svg-small {
  width: 22px;
  height: 22px;
  color: white;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.2));
}

.sidebar-divider {
  border-color: rgba(255, 255, 255, 0.15);
  margin: 0 12px;
}

.sidebar-nav {
  position: relative;
  z-index: 2;
  padding: 8px 0;
}

.sidebar-item {
  position: relative;
  margin: 4px 12px;
  border-radius: 12px;
  min-height: 44px;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow: hidden;
}

.sidebar-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 12px;
}

.sidebar-item:hover::before {
  opacity: 1;
}

.sidebar-item:hover {
  transform: translateX(3px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

/* 活动状态样式 */
:deep(.v-list-item--active) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transform: translateX(3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

:deep(.v-list-item--active .v-list-item__prepend .v-icon) {
  color: white;
  text-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
}

:deep(.v-list-item--active .v-list-item-title) {
  color: white;
  font-weight: 600;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

/* 默认图标和文字样式 */
:deep(.v-list-item .v-list-item__prepend .v-icon) {
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

:deep(.v-list-item-title) {
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
  letter-spacing: 0.3px;
  transition: all 0.3s ease;
}

:deep(.v-list) {
  padding: 4px 0;
  background: transparent;
}

.collapse-btn {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  height: 36px;
  width: 36px;
  min-width: 0;
  padding: 0;
  margin: 0;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  z-index: 2;
}

.collapse-btn:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.2));
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

/* 为折叠状态的侧边栏调整按钮位置 */
:deep(.v-navigation-drawer--rail) .collapse-btn {
  left: 50%;
  transform: translateX(-50%);
}

/* 为图标添加过渡效果 */
.collapse-btn .v-icon {
  transition: transform 0.3s ease;
  color: white;
}

.collapse-btn:hover .v-icon {
  transform: scale(1.1);
}

/* 折叠状态下的样式调整 */
:deep(.v-navigation-drawer--rail) .sidebar-item {
  margin: 4px 8px;
}

:deep(.v-navigation-drawer--rail) .sidebar-header {
  padding: 16px 8px 12px;
}
</style>