<template>
  <v-container fluid class="pa-4 home-container"> <!-- 从上次中断的地方继续 - 条状物设计 -->
    <v-card v-if="isLoggedIn && homepageData.recentVideos && homepageData.recentVideos.length > 0"
      class="content-card mb-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="warning">mdi-restore</v-icon>
        从上次中断的地方继续
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-4">
        <div class="continue-learning-list">
          <div v-for="video in homepageData.recentVideos" :key="video.videoId" class="continue-learning-item"
            @click="navigateToVideo(video)">
            <div class="video-thumbnail">
              <v-img :src="video.coverUrl || '/default-video.jpg'" width="120" height="68" cover class="rounded">
                <div class="play-overlay">
                  <v-icon color="white" size="24">mdi-play-circle</v-icon>
                </div>
              </v-img>
            </div>
            <div class="video-info">
              <div class="video-title">{{ video.title }}</div>
              <div class="video-course">{{ video.courseName }}</div>
              <div class="video-progress-info">
                <span class="progress-text">{{ video.progressPercent }}% 完成</span>
                <span class="duration-text">{{ video.durationFormatted }}</span>
              </div>
              <v-progress-linear :model-value="video.progressPercent" color="warning" height="3" class="mt-2"
                rounded></v-progress-linear>
            </div>
            <div class="continue-action">
              <v-btn color="warning" variant="flat" size="small" @click.stop="navigateToVideo(video)">
                继续观看
              </v-btn>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 大家都在学 -->
    <v-card v-if="homepageData.popularCourses && homepageData.popularCourses.length > 0" class="content-card mb-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="primary">mdi-trending-up</v-icon>
        大家都在学
        <v-spacer></v-spacer>
        <v-progress-circular v-if="loading" indeterminate color="primary" size="24"></v-progress-circular>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-row>
          <v-col v-for="course in homepageData.popularCourses" :key="course.id" cols="12" sm="6" md="4" lg="3"> <v-card
              class="course-card" elevation="2" hover>
              <v-img :src="course.imageUrl || '/default-course.jpg'" height="280" cover>
                <div class="course-overlay">
                  <v-chip size="small" color="primary" class="ma-2">
                    {{ course.learnerCount }}人在学
                  </v-chip>
                </div>
              </v-img>
              <v-card-text class="pa-4">
                <div class="text-h6 mb-2">{{ course.name }}</div>
                <div class="text-body-2 text-grey mb-2">{{ course.teacherInfo.name }}</div>
                <div class="d-flex align-center justify-space-between">
                  <v-chip size="small" color="orange" variant="outlined">
                    <v-icon start size="16">mdi-account-group</v-icon>
                    {{ course.learnerCount }}人学习
                  </v-chip>
                  <v-btn color="primary" variant="text" size="small" :to="`/course/${course.id}`">
                    查看课程
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>    <!-- 我选修的课程 - 增强显示 -->
    <v-card v-if="isLoggedIn && homepageData.continueLearningCourses && homepageData.continueLearningCourses.length > 0"
      class="content-card mb-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="success">mdi-school</v-icon>
        我选修的课程
        <v-spacer></v-spacer>
        <v-chip size="small" color="success" variant="tonal">
          {{ homepageData.continueLearningCourses.length }} 门课程
        </v-chip>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <v-row>
          <v-col v-for="course in homepageData.continueLearningCourses" :key="course.id" cols="12" sm="6" md="4" lg="4">
            <v-card class="enrolled-course-card" elevation="3" hover>
              <v-img :src="course.imageUrl || '/default-course.jpg'" height="200" cover>
                <div class="course-progress-overlay">
                  <v-progress-circular
                    :model-value="course.progressPercent"
                    :size="60"
                    :width="4"
                    color="white"
                    class="progress-indicator"
                  >
                    <span class="text-white font-weight-bold">{{ course.progressPercent }}%</span>
                  </v-progress-circular>
                </div>
              </v-img>
              
              <v-card-text class="pa-4">
                <div class="text-h6 mb-2 course-title">{{ course.name }}</div>                <div class="d-flex align-center mb-2">
                  <v-avatar size="24" class="mr-2" color="grey-lighten-3">
                    <img 
                      v-if="course.teacherInfo.avatar && !course.avatarLoadError" 
                      :src="course.teacherInfo.avatar" 
                      @error="handleAvatarError($event, course)"
                      @load="handleAvatarLoad($event, course)"
                      style="width: 100%; height: 100%; object-fit: cover;" 
                    />
                    <div v-else-if="course.teacherInfo.name && course.teacherInfo.name.trim()" 
                         class="letter-avatar" 
                         :style="getLetterAvatarStyle(course.teacherInfo.name)">
                      {{ course.teacherInfo.name.charAt(0).toUpperCase() }}
                    </div>
                    <v-icon v-else size="16">mdi-account</v-icon>
                  </v-avatar>
                  <span class="text-body-2 text-grey">{{ course.teacherInfo.name }}</span>
                </div>
                
                <!-- 学习进度条 -->
                <div class="mb-3">
                  <div class="d-flex justify-space-between align-center mb-1">
                    <span class="text-caption text-grey">学习进度</span>
                    <span class="text-caption font-weight-bold text-success">{{ course.progressPercent }}%</span>
                  </div>
                  <v-progress-linear
                    :model-value="course.progressPercent"
                    height="6"
                    rounded
                    color="success"
                    bg-color="grey-lighten-3"
                  ></v-progress-linear>
                </div>
                
                <!-- 学习统计 -->
                <div class="study-stats mb-3">
                  <div class="d-flex justify-space-between">
                    <div class="stat-item">
                      <v-icon size="16" color="primary" class="mr-1">mdi-clock-outline</v-icon>
                      <span class="text-caption">已学{{ course.userWatchTime }}小时，{{ course.watchedVideos }}个视频</span>
                    </div>
                    <div class="stat-item">
                      <v-icon size="16" color="green" class="mr-1">mdi-account-group</v-icon>
                      <span class="text-caption">{{ course.studentCount }}人学习</span>
                    </div>
                  </div>
                </div>
                
                <!-- 最后学习时间 -->
                <div class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <v-icon size="16" color="grey" class="mr-1">mdi-update</v-icon>
                    <span class="text-caption text-grey">
                      {{ course.lastStudyTime ? formatLastStudyTime(course.lastStudyTime) : '暂无记录' }}
                    </span>
                  </div>
                </div>
                
                <!-- 操作按钮 -->
                <div class="d-flex gap-2">
                  <v-btn
                    color="success"
                    variant="flat"
                    size="small"
                    block
                    :to="`/course/${course.id}`"
                    prepend-icon="mdi-play"
                  >
                    继续学习
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card><!-- 全部课程 -->
    <v-card class="content-card">
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon class="mr-2" color="info">mdi-book-multiple</v-icon>
        全部课程
        <v-spacer></v-spacer>
        <v-progress-circular v-if="loading" indeterminate color="primary" size="24"></v-progress-circular>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-6">
        <!-- 分类筛选栏 -->
        <div class="d-flex flex-wrap align-center mb-6 gap-4">
          <div class="d-flex flex-wrap align-center gap-2">
            <v-btn
              v-for="cat in categories"
              :key="cat"
              :color="selectedCategories.includes(cat) ? 'primary' : 'grey-lighten-2'"
              class="ma-1"
              variant="elevated"
              @click="toggleCategory(cat)"
            >
              {{ cat }}
            </v-btn>
            <v-btn
              :color="selectedCategories.length === 0 ? 'primary' : 'grey-lighten-2'"
              class="ma-1"
              variant="elevated"
              @click="clearCategories"
            >
              全部
            </v-btn>
          </div>
        </div>
        <!-- 课程列表 -->
        <v-row v-if="!loading && filteredCourses.length > 0">
          <v-col v-for="course in filteredCourses" :key="course.id" cols="12" sm="6" md="4" lg="3" xl="2">
            <CourseCard 
              :id="course.id" 
              :thumbnail="course.thumbnail" 
              :title="course.title" 
              :duration="course.duration"
              :students="course.students" 
              :teacher="course.teacher" 
              :teacherInfo="course.teacherInfo"
              :category="course.category"
              :description="course.description" 
            />
          </v-col>
          <!-- 所有课程占位方块 -->
          <v-col cols="12" sm="6" md="4" lg="3" xl="2">
            <v-card class="all-courses-placeholder" elevation="2" hover @click="navigateToAllCourses">
              <v-card-text class="d-flex flex-column align-center justify-center pa-6" style="height: 300px;">
                <v-icon size="64" color="primary" class="mb-4">mdi-view-grid-plus</v-icon>
                <div class="text-h6 text-center text-primary">查看所有课程</div>
                <div class="text-body-2 text-center text-grey mt-2">探索更多精彩内容</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        <v-row v-else-if="!loading && filteredCourses.length === 0" class="fill-height align-center justify-center">
          <v-col cols="12" class="text-center">
            <v-icon size="64" color="grey">mdi-book-off</v-icon>
            <div class="text-h6 mt-4 text-grey">暂无可访问的课程</div>
            <div class="text-body-1 mt-2 text-grey">
              {{ isLoggedIn ? '可能需要教师授予访问权限' : '请登录以查看更多课程' }}
            </div>
            <v-btn v-if="!isLoggedIn" color="primary" class="mt-4" to="/login">
              去登录
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import CourseCard from '../components/CourseCard.vue'
import courseService from '../api/courseService'
import userService from '../api/userService'
import { useCourseStore } from '../stores/courseStore'
import type { AxiosResponse } from 'axios'
import type { TeacherInfo } from '../types/course'
import { parseCourseDescription } from '../utils/courseUtils'
import { getCategories } from '@/api/categoryService'

// 定义接口
interface MenuItem {
  title: string
  icon: string
  path: string
}

interface Course {
  id: string
  thumbnail: string
  title: string
  duration: string
  students: number
  teacher: string
  teacherInfo?: TeacherInfo
  category: string[]
  avatarLoadError?: boolean // 添加头像错误标记
}

interface ApiResponse<T> {
  code: number
  message: string
  data: {
    list: T[]
  }
}

interface PopularCourse {
  id: string
  name: string
  code: string
  imageUrl: string
  hours: number
  studentCount: number
  teacherInfo: {
    id: string
    name: string
    avatar?: string | null
  }
  totalWatchTime: number
  learnerCount: number
  category: string
}

interface ContinueLearningCourse {
  id: string
  name: string
  code: string
  imageUrl: string
  hours: number
  studentCount: number
  teacherInfo: {
    id: string
    name: string
    avatar?: string | null
  }
  userWatchTime: number
  watchedVideos: number
  lastStudyTime: string | null
  progressPercent: number
  category: string
  avatarLoadError?: boolean // 添加头像错误标记
}

interface RecentVideo {
  videoId: string
  courseId: string
  title: string
  courseName: string
  coverUrl: string
  duration: number
  durationFormatted: string
  lastPosition: number
  lastPositionFormatted: string
  progressPercent: number
  lastWatchTime: string | null
  watchUrl: string
}

interface HomepageData {
  popularCourses: PopularCourse[]
  continueLearningCourses: ContinueLearningCourse[]
  recentVideos: RecentVideo[]
}

const router = useRouter()
const route = useRoute()
const courseStore = useCourseStore()
const loading = ref(true)
const error = ref<string | null>(null)
const homepageData = ref<HomepageData>({
  popularCourses: [],
  continueLearningCourses: [],
  recentVideos: []
})

const menuItems: MenuItem[] = [
  { title: '推荐课程', icon: 'mdi-book-open-variant', path: '/' },
  { title: '学习进度', icon: 'mdi-progress-check', path: '/learning-progress' },
  { title: '笔记本', icon: 'mdi-notebook', path: '/notebook' },
  { title: 'AI助手', icon: 'mdi-robot', path: '/ai-assistant' }
]

// 添加路由导航方法
const navigateToPage = (path: string) => {
  router.push(path)
}

// 导航到所有课程页面
const navigateToAllCourses = () => {
  router.push('/all-courses')
}

// 导航到视频播放页面
const navigateToVideo = (video: RecentVideo) => {
  router.push(`/course/${video.courseId}/video/${video.videoId}`)
}

// 格式化最后学习时间
const formatLastStudyTime = (timeString: string) => {
  const now = new Date()
  const studyTime = new Date(timeString)
  const diffInMinutes = Math.floor((now.getTime() - studyTime.getTime()) / (1000 * 60))
  
  if (diffInMinutes < 60) {
    return `${diffInMinutes}分钟前`
  } else if (diffInMinutes < 1440) { // 24小时
    const hours = Math.floor(diffInMinutes / 60)
    return `${hours}小时前`
  } else if (diffInMinutes < 10080) { // 7天
    const days = Math.floor(diffInMinutes / 1440)
    return `${days}天前`
  } else {
    return studyTime.toLocaleDateString('zh-CN', { 
      month: '2-digit', 
      day: '2-digit' 
    })
  }
}

// 检查用户是否已登录
const isLoggedIn = computed(() => {
  return !!localStorage.getItem('wendao_token')
})

// 格式化最后观看时间
const formatLastWatchTime = (lastWatchTime: string | null): string => {
  if (!lastWatchTime) return '未知时间'

  const now = new Date()
  const watchTime = new Date(lastWatchTime)
  const diffInSeconds = Math.floor((now.getTime() - watchTime.getTime()) / 1000)

  if (diffInSeconds < 60) return '刚刚'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}分钟前`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}小时前`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}天前`

  return watchTime.toLocaleDateString()
}

// 加载首页数据
const fetchHomepageData = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await courseService.getHomepageData()

    if (response.data.code === 200) {
      homepageData.value = response.data.data
    } else {
      error.value = response.data.message || '获取首页数据失败'
      console.error(error.value)
    }
  } catch (err: unknown) {
    const errorObj = err as Error
    error.value = errorObj.message || '获取首页数据出错'
    console.error('获取首页数据失败:', errorObj)
  } finally {
    loading.value = false
  }
}

// 加载课程数据
const fetchCourses = async () => {
  try {
    loading.value = true
    error.value = null
    let response;
    if (isLoggedIn.value) {
      response = await courseService.getStudentCourses()
    } else {
      response = await courseService.getStudentCourses({ public: true })
    }
    if (response.data.code === 200) {
      const courseList = response.data.data.list.map((course: any) => {
        const descObj = parseCourseDescription(course.description)
        return {
          id: String(course.id),
          thumbnail: course.imageUrl,
          title: course.name,
          duration: `${course.hours}课时`,
          students: course.studentCount || 0,
          rating: 4.5,
          teacher: course.teacherInfo?.name || '未知教师',
          teacherInfo: course.teacherInfo,
          category: descObj.category || [],
          description: descObj.description || ''
        }
      })
      courseStore.setCourses(courseList)
    } else {
      error.value = response.data.data.message || '获取课程失败'
      console.error(error.value)
    }
  } catch (err: unknown) {
    const errorObj = err as Error
    error.value = errorObj.message || '获取课程出错'
    console.error('获取课程列表失败:', errorObj)
  } finally {
    loading.value = false
  }
}

const categories = ref<string[]>([])
const selectedCategories = ref<string[]>([])

const toggleCategory = (cat: string) => {
  const idx = selectedCategories.value.indexOf(cat)
  if (idx === -1) {
    selectedCategories.value.push(cat)
  } else {
    selectedCategories.value.splice(idx, 1)
  }
}
const clearCategories = () => {
  selectedCategories.value = []
}

const filteredCourses = computed(() => {
  let filtered = courseStore.courses
  if (selectedCategories.value.length > 0) {
    filtered = filtered.filter(course =>
      course.category.some(cat => selectedCategories.value.includes(cat))
    )
  }
  return filtered
})

onMounted(async () => {
  // 并行加载首页数据和推荐课程
  await Promise.all([
    fetchHomepageData(),
    fetchCourses()
  ])
  try {
    const res = await getCategories()
    categories.value = res.data || []
  } catch (e) {
    categories.value = []
  }
})

// 头像处理方法
const getRandomColor = (username: string): string => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#16a085'
  ]
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const getLetterAvatarStyle = (username: string) => {
  if (!username || !username.trim()) {
    return {
      backgroundColor: '#95a5a6',
      color: 'white',
      fontSize: '14px',
      fontWeight: 'bold',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100%'
    }
  }
  
  const bgColor = getRandomColor(username)
  return {
    backgroundColor: bgColor,
    color: 'white',
    fontSize: '14px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    height: '100%'
  }
}

const handleAvatarError = (event: Event, course: ContinueLearningCourse) => {
  console.log('Avatar load error for course:', course.name)
  course.avatarLoadError = true
}

const handleAvatarLoad = (event: Event, course: ContinueLearningCourse) => {
  console.log('Avatar loaded successfully for course:', course.name)
  course.avatarLoadError = false
}
</script>

<style scoped>
/* 主页容器 */
.home-container {
  background: transparent;
  min-height: 100%;
}

/* 内容卡片 */
.content-card {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.8);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  margin-bottom: 24px;
  overflow: hidden;
  position: relative;
}

.content-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  opacity: 0.8;
}

.content-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 12px 48px rgba(0, 0, 0, 0.15),
    0 4px 16px rgba(0, 0, 0, 0.1);
}

/* 卡片标题区域 */
:deep(.content-card .v-card-title) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.03));
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  font-weight: 700;
  color: #2d3748;
  letter-spacing: 0.5px;
}

:deep(.content-card .v-card-title .v-icon) {
  margin-right: 12px;
  opacity: 0.8;
}

/* 继续学习项目 */
.continue-learning-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.continue-learning-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.continue-learning-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(4px);
  border-color: rgba(102, 126, 234, 0.2);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
}

.video-thumbnail {
  position: relative;
  margin-right: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.3);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.continue-learning-item:hover .play-overlay {
  background: rgba(102, 126, 234, 0.8);
  transform: translate(-50%, -50%) scale(1.1);
}

.video-info {
  flex: 1;
}

.video-title {
  font-weight: 600;
  font-size: 16px;
  color: #2d3748;
  margin-bottom: 4px;
}

.video-course {
  font-size: 14px;
  color: #64748b;
  margin-bottom: 8px;
}

.video-progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.continue-action {
  margin-left: 16px;
}

/* 课程卡片优化 */
.course-card {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: 1px solid rgba(102, 126, 234, 0.1);
  overflow: hidden;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.2);
}

.course-overlay {
  position: absolute;
  top: 0;
  right: 0;
}

/* "查看所有课程"占位卡片 */
.all-courses-placeholder {
  border: 2px dashed rgba(102, 126, 234, 0.3);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.03));
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
}

.all-courses-placeholder:hover {
  border-color: rgba(102, 126, 234, 0.5);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.05));
  transform: translateY(-4px);
}

/* 加载动画 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.content-card {
  animation: fadeInUp 0.6s ease-out;
}

.content-card:nth-child(1) {
  animation-delay: 0.1s;
}

.content-card:nth-child(2) {
  animation-delay: 0.2s;
}

.content-card:nth-child(3) {
  animation-delay: 0.3s;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .continue-learning-item {
    flex-direction: column;
    text-align: center;
  }

  .video-thumbnail {
    margin-right: 0;
    margin-bottom: 12px;
  }
  .continue-action {
    margin-left: 0;
    margin-top: 12px;
  }
}

/* 选修课程卡片样式 */
.enrolled-course-card {
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: 1px solid rgba(102, 126, 234, 0.1);
  overflow: hidden;
  position: relative;
}

.enrolled-course-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.2);
}

.course-progress-overlay {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 50%;
  padding: 8px;
  backdrop-filter: blur(10px);
}

.progress-indicator {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.course-title {
  font-weight: 600;
  color: #2d3748;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.study-stats {
  background: rgba(102, 126, 234, 0.05);
  border-radius: 8px;
  padding: 8px 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #64748b;
}

.stat-item .v-icon {
  opacity: 0.8;
}

/* 课程分类导航样式 */
.course-categories {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.primary-categories {
  margin-bottom: 12px;
}

.primary-category-chip {
  font-weight: 500;
  font-size: 14px;
  padding: 0 16px;
  height: 36px;
  margin-right: 8px;
  transition: all 0.3s ease;
}

.primary-category-chip:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.primary-selected {
  background-color: rgb(var(--v-theme-primary)) !important;
  color: white !important;
}

.secondary-categories {
  padding-top: 8px;
  border-top: 1px dashed rgba(0, 0, 0, 0.1);
}

.secondary-category-chip {
  font-size: 13px;
  margin-right: 8px;
  transition: all 0.3s ease;
}

.secondary-category-chip:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.secondary-selected {
  background-color: rgba(var(--v-theme-primary), 0.1) !important;
  color: rgb(var(--v-theme-primary)) !important;
  font-weight: 500;
}

.text-truncate-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  line-height: 1.5;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 字母头像样式 */
.letter-avatar {
  border-radius: 50%;
  background: linear-gradient(135deg, var(--bg-color, #3498db), var(--bg-color-light, #5dade2));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  cursor: pointer;
}

.letter-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>