<template>
  <div class="assignment-list-container">
    <v-container class="py-6">
      <!-- 页面标题 -->
      <div class="page-header mb-6">
        <h1 class="page-title">我的作业</h1>
        <p class="page-subtitle">查看和完成您的课程作业</p>
      </div>

      <!-- 筛选和搜索区域 -->
      <div class="filter-section mb-8">
        <v-card class="filter-card" elevation="0">
          <v-card-text class="pa-8">
            <!-- 筛选标题 -->
            <div class="filter-header mb-6">
              <!-- <h2 class="filter-title">筛选条件</h2>
              <p class="filter-subtitle">快速找到您需要的作业</p> -->
            </div>
            
            <!-- 筛选控件 -->
            <div class="filter-controls">
              <v-row class="filter-row" no-gutters>
                <!-- 搜索框 -->
                <v-col cols="12" lg="4" class="filter-col">
                  <div class="filter-item search-item">
                    <div class="filter-icon-wrapper">
                      <v-icon class="filter-icon">mdi-magnify</v-icon>
                    </div>
                    <v-text-field
                      v-model="searchQuery"
                      variant="solo-filled"
                      density="comfortable"
                      clearable
                      placeholder="搜索作业标题..."
                      hide-details
                      class="search-input"
                      flat
                    />
                  </div>
                </v-col>
                
                <!-- 课程筛选 -->
                <v-col cols="12" sm="6" lg="2" class="filter-col">
                  <div class="filter-item select-item">
                    <v-select
                      v-model="selectedCourse"
                      :items="courseOptions"
                      :loading="coursesLoading"
                      variant="solo-filled"
                      density="comfortable"
                      clearable
                      placeholder="课程"
                      hide-details
                      class="filter-select"
                      flat
                    >
                      <template #prepend-inner>
                        <v-icon class="select-icon">mdi-book-outline</v-icon>
                      </template>
                    </v-select>
                  </div>
                </v-col>
                
                <!-- 老师筛选 -->
                <v-col cols="12" sm="6" lg="2" class="filter-col">
                  <div class="filter-item select-item">
                    <v-select
                      v-model="selectedTeacher"
                      :items="teacherOptions"
                      :loading="teachersLoading"
                      variant="solo-filled"
                      density="comfortable"
                      clearable
                      placeholder="老师"
                      hide-details
                      class="filter-select"
                      flat
                    >
                      <template #prepend-inner>
                        <v-icon class="select-icon">mdi-account-outline</v-icon>
                      </template>
                    </v-select>
                  </div>
                </v-col>
                
                <!-- 状态筛选 -->
                <v-col cols="12" sm="6" lg="3" class="filter-col">
                  <div class="filter-item select-item">
                    <v-select
                      v-model="tab"
                      :items="tabItems"
                      item-title="text"
                      item-value="value"
                      variant="solo-filled"
                      density="comfortable"
                      hide-details
                      class="filter-select"
                      flat
                    >
                      <template #prepend-inner>
                        <v-icon class="select-icon">mdi-format-list-bulleted</v-icon>
                      </template>
                    </v-select>
                  </div>
                </v-col>
                
                <!-- 重置按钮 -->
                <v-col cols="12" sm="6" lg="1" class="filter-col">
                  <div class="filter-item reset-item">
                    <v-btn
                      @click="resetFilters"
                      variant="elevated"
                      color="primary"
                      class="reset-btn"
                      size="large"
                      icon
                    >
                      <v-icon>mdi-refresh</v-icon>
                      <v-tooltip activator="parent" location="bottom">
                        重置筛选
                      </v-tooltip>
                    </v-btn>
                  </div>
                </v-col>
              </v-row>
            </div>
          </v-card-text>
        </v-card>
      </div>
    
      <!-- 作业卡片列表 -->
      <div v-if="loading" class="loading-container">
        <div class="text-center py-12">
          <v-progress-circular
            indeterminate
            color="primary"
            size="64"
            width="6"
          ></v-progress-circular>
          <div class="mt-4 text-h6 text-grey-600">正在加载作业列表...</div>
        </div>
      </div>
      
      <div v-else class="assignments-grid">
        <v-row v-if="filteredAssignments.length > 0" class="assignment-cards">
          <v-col v-for="assignment in filteredAssignments" :key="assignment.id" cols="12" sm="6" md="6" lg="6" xl="4">
            <AssignmentCard
              :assignment="assignment"
              :statusText="statusMap[assignment.status].text"
              :statusColor="statusMap[assignment.status].color"
              @action="goToDetail"
              @view="goToDetail"
              @ai="onAIAgent"
              class="assignment-card-item"
            />
          </v-col>
        </v-row>
        
        <!-- 空状态 -->
        <v-card v-else class="empty-state" elevation="0">
          <v-card-text class="text-center pa-12">
            <div class="empty-icon mb-4">
              <v-icon size="80" color="grey-lighten-2">mdi-clipboard-text-outline</v-icon>
            </div>
            <h3 class="empty-title mb-3">暂无作业</h3>
            <p class="empty-subtitle">当前筛选条件下没有找到作业，请尝试调整筛选条件</p>
          </v-card-text>
        </v-card>
      </div>
    </v-container>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AssignmentCard from '../components/AssignmentCard.vue'
import assignmentService from '../api/assignmentService'
import courseService from '../api/courseService'
import userService from '../api/userService'

// 筛选项
const tab = ref('all')
const tabItems = [
  { text: '全部', value: 'all' },
  { text: '未完成', value: 'not_completed' },
  { text: '已完成', value: 'completed' },
  { text: '已过期', value: 'overdue' }
]

// 定义课程和老师接口
interface Course {
  id: string;
  name: string;
  courseName?: string;
  [key: string]: any;
}

interface Teacher {
  id: string;
  name: string;
}

// 搜索和筛选
const searchQuery = ref('')
const selectedCourse = ref<string | null>(null)
const selectedTeacher = ref<string | null>(null)
const courses = ref<Course[]>([])
const teachers = ref<Teacher[]>([])

// 加载状态
const loading = ref(false)
const coursesLoading = ref(false)
const teachersLoading = ref(false)

// 课程选项
const courseOptions = computed(() => {
  if (!Array.isArray(courses.value)) {
    console.log('courses.value不是数组:', courses.value)
    return []
  }
  const options = courses.value.map(course => ({
    title: course.name,
    value: course.id
  }))
  console.log('生成的课程选项:', options)
  return options
})

// 老师选项
const teacherOptions = computed(() => {
  if (!Array.isArray(teachers.value)) {
    return []
  }
  return teachers.value.map(teacher => ({
    title: teacher.name,
    value: teacher.id
  }))
})

// 定义状态类型
type AssignmentStatus = '未完成' | '已提交' | '已截止';

// 状态映射
const statusMap: Record<AssignmentStatus, { text: string, color: string }> = {
  '未完成': { text: '未完成', color: 'primary' },
  '已提交': { text: '已提交', color: 'info' },
  '已截止': { text: '已截止', color: 'success' }
}

// 作业数据
interface Assignment {
  id: string;
  title: string;
  status: AssignmentStatus;
  studentStatus?: string;
  dueDate: string;
  [key: string]: any;
}

const assignments = ref<Assignment[]>([])

// 判断作业是否已过期
const isOverdue = (dueDate: string) => {
  const due = new Date(dueDate);
  return new Date() > due;
};

// 重置筛选条件
const resetFilters = () => {
  searchQuery.value = ''
  selectedCourse.value = null
  selectedTeacher.value = null
  tab.value = 'all'
}

// 获取课程列表
const loadCourses = async () => {
  try {
    coursesLoading.value = true
    const res = await courseService.getStudentCourses()
    if (res.data && res.data.code === 200) {
      courses.value = res.data.data.list || []
      console.log('加载的课程列表:', courses.value)
    }
  } catch (error) {
    console.error('获取课程列表失败:', error)
    courses.value = [] // 确保在错误时设置为空数组
  } finally {
    coursesLoading.value = false
  }
}

/**
 * 从作业数据中提取唯一的老师信息
 * 这个函数依赖于assignments中的teacherId和teacherName字段
 */
const loadTeachers = async () => {
  try {
    teachersLoading.value = true
    // 使用Map来确保老师ID的唯一性
    const uniqueTeachers = new Map<string, Teacher>()
    
    // 遍历所有作业，提取老师信息
    assignments.value.forEach(assignment => {
      // 确保teacherId和teacherName都存在
      if (assignment.teacherId && assignment.teacherName) {
        uniqueTeachers.set(assignment.teacherId, {
          id: assignment.teacherId,
          name: assignment.teacherName
        })
      }
    })
    
    // 将Map转换为数组并更新teachers引用
    teachers.value = Array.from(uniqueTeachers.values())
    console.log('加载的老师列表:', teachers.value)
  } catch (error) {
    console.error('获取老师列表失败:', error)
    teachers.value = [] // 确保在错误时设置为空数组
  } finally {
    teachersLoading.value = false
  }
}

// 封装加载作业列表的函数
const loadAssignments = async () => {
  try {
    loading.value = true
    
    const res = await assignmentService.getAssignmentList({ status: 'published' })
    let list: any[] = []
    if (res.data && res.data.code === 200) {
      list = res.data.data.list || []
    }
    
    assignments.value = list.map((item: any) => {
      // 使用后端返回的studentStatus来确定前端状态
      let status: AssignmentStatus = '未完成';
      
      if (item.studentStatus === 'expired') {
        status = '已截止';
      } else if (item.studentStatus === 'submitted') {
        status = '已提交';
      } else {
        status = '未完成';
      }
      
      return {
        ...item,
        status
      };
    });
    
    // 获取老师列表
    await loadTeachers()
  } catch (error) {
    console.error('加载作业列表失败:', error)
    assignments.value = [] // 确保在错误时设置为空数组
  } finally {
    loading.value = false
  }
}

// 页面加载时获取作业列表，只获取已发布的作业
onMounted(async () => {
  // 先获取课程列表
  await loadCourses()
  // 然后加载作业列表
  await loadAssignments()
});

// 页面激活时刷新数据（当从其他页面返回时）
onActivated(async () => {
  console.log('页面激活，刷新作业列表数据')
  await loadAssignments()
})

const filteredAssignments = computed(() => {
  if (!Array.isArray(assignments.value)) {
    return []
  }
  
  let filtered = assignments.value
  
  // 按状态筛选
  if (tab.value !== 'all') {
    filtered = filtered.filter(a => {
      const currentTime = new Date()
      const dueTime = new Date(a.dueDate)
      
      switch (tab.value) {
        case 'not_completed':
          return a.studentStatus !== 'submitted' && a.studentStatus !== 'graded' && a.studentStatus !== 'expired' && currentTime < dueTime
        case 'completed':
          return a.studentStatus === 'submitted' || a.studentStatus === 'graded'
        case 'overdue':
          return a.studentStatus === 'expired' || (currentTime > dueTime && a.studentStatus !== 'submitted' && a.studentStatus !== 'graded')
        default:
          return true
      }
    })
  }
  
  // 按搜索关键词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(a => 
      a.title && a.title.toLowerCase().includes(query)
    )
  }
  
  // 按课程筛选
  if (selectedCourse.value) {
    filtered = filtered.filter(a => a.courseId === selectedCourse.value)
  }
  
  // 按老师筛选
  if (selectedTeacher.value) {
    filtered = filtered.filter(a => a.teacherId === selectedTeacher.value)
  }
  
  return filtered
})

const router = useRouter()
const goToDetail = async (assignment: any) => {
  try {
    // 根据作业状态决定跳转逻辑
    if (assignment.status === '已截止') {
      // 已截止的作业跳转到只读的评分查看页面
      router.push(`/student-assignments/${assignment.id}/graded`)
    } else if (assignment.status === '已提交') {
      // 已提交但未批改完成的作业，学生可以继续编辑
      router.push(`/student-assignments/${assignment.id}`)
    } else {
      // 未完成的作业，学生可以编辑
      router.push(`/student-assignments/${assignment.id}`)
    }
  } catch (error) {
    console.error('跳转作业详情失败:', error);
    // 出错时默认跳转到编辑页面
    router.push(`/student-assignments/${assignment.id}`)
  }
}

// AI Agent 事件处理
const onAIAgent = (assignment: any) => {
  // 这里可以弹窗、跳转AI问答页等
  ElMessage.info(`你可以就作业"${assignment.title}"向AI提问！`)
}
</script>

<style scoped>
.assignment-list-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
}

/* 页面标题样式 */
.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 0.5rem;
  letter-spacing: -0.025em;
}

.page-subtitle {
  font-size: 1.125rem;
  color: #64748b;
  margin: 0;
  font-weight: 400;
}

/* 筛选区域样式 */
.filter-section {
  position: relative;
}

.filter-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: hidden;
}

.filter-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* 筛选标题样式 */
.filter-header {
  text-align: center;
  margin-bottom: 2rem;
}

.filter-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a202c;
  margin-bottom: 0.5rem;
  letter-spacing: -0.025em;
}

.filter-subtitle {
  font-size: 1rem;
  color: #64748b;
  margin: 0;
  font-weight: 400;
}

/* 筛选控件布局 */
.filter-controls {
  position: relative;
}

.filter-row {
  gap: 1rem;
  align-items: center;
}

.filter-col {
  padding: 0 0.5rem;
}

.filter-item {
  position: relative;
  height: 56px;
  display: flex;
  align-items: center;
}

/* 搜索框样式 */
.search-item {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-radius: 16px;
  padding: 0 1rem;
  transition: all 0.3s ease;
}

.search-item:hover {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  transform: translateY(-1px);
}

.filter-icon-wrapper {
  margin-right: 0.75rem;
}

.filter-icon {
  color: #64748b;
  font-size: 1.25rem;
}

.search-input :deep(.v-field) {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.search-input :deep(.v-field__input) {
  padding: 0;
  min-height: auto;
}

.search-input :deep(.v-field__field) {
  padding: 0;
}

/* 选择器样式 */
.select-item {
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  transition: all 0.3s ease;
  overflow: hidden;
}

.select-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  transform: translateY(-1px);
}

.filter-select :deep(.v-field) {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.filter-select :deep(.v-field__input) {
  padding: 0 1rem;
  min-height: 52px;
}

.filter-select :deep(.v-field__field) {
  padding: 0;
}

.select-icon {
  color: #64748b;
  margin-right: 0.5rem;
  font-size: 1.125rem;
}

/* 重置按钮样式 */
.reset-item {
  display: flex;
  justify-content: center;
  align-items: center;
}

.reset-btn {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
}

.reset-btn:hover {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
  transform: translateY(-2px) scale(1.05);
}

.reset-btn .v-icon {
    font-size: 1.25rem;
    color: white;
  }

/* 状态筛选样式 */
.status-section {
  margin-top: 2rem;
}

.status-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  overflow: hidden;
}

.status-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.status-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.status-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 0.25rem;
  letter-spacing: -0.025em;
}

.status-subtitle {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0;
  font-weight: 400;
}

.status-select-wrapper {
  max-width: 300px;
  margin: 0 auto;
}

.status-select-item {
  background: #ffffff;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  transition: all 0.3s ease;
  overflow: hidden;
}

.status-select-item:hover {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  transform: translateY(-1px);
}

.status-select :deep(.v-field) {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.status-select :deep(.v-field__input) {
  padding: 0 1rem;
  min-height: 52px;
  text-align: center;
}

.status-select :deep(.v-field__field) {
  padding: 0;
}

.status-select :deep(.v-select__selection) {
  font-weight: 500;
  color: #1a202c;
}

.status-icon {
  color: #10b981;
  margin-right: 0.5rem;
  font-size: 1.125rem;
}

/* 作业列表样式 */
.assignments-grid {
  margin-top: 1rem;
}

.assignment-cards {
  margin: -8px;
}

.assignment-cards .v-col {
  padding: 8px;
}

.assignment-card-item {
  transition: transform 0.2s ease;
  height: 100%;
}

.assignment-card-item:hover {
  transform: translateY(-2px);
}

/* 响应式卡片间距调整 */
@media (max-width: 768px) {
  .assignment-cards {
    margin: -6px;
  }
  
  .assignment-cards .v-col {
    padding: 6px;
  }
}

@media (max-width: 480px) {
  .assignment-cards {
    margin: -4px;
  }
  
  .assignment-cards .v-col {
    padding: 4px;
  }
}

/* 加载状态样式 */
.loading-container {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

/* 空状态样式 */
.empty-state {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.empty-icon {
  opacity: 0.6;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.75rem;
}

.empty-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .filter-col {
    padding: 0.25rem;
  }
  
  .filter-row {
    gap: 0.5rem;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }
  
  .filter-title {
    font-size: 1.25rem;
  }
  
  .filter-subtitle {
    font-size: 0.875rem;
  }
  
  .filter-card {
    border-radius: 20px;
  }
  
  .filter-col {
    padding: 0.25rem 0;
    margin-bottom: 0.5rem;
  }
  
  .filter-item {
    height: 48px;
  }
  
  .search-item {
    border-radius: 12px;
    padding: 0 0.75rem;
  }
  
  .select-item {
    border-radius: 12px;
  }
  
  .filter-select :deep(.v-field__input) {
    padding: 0 0.75rem;
    min-height: 44px;
  }
  
  .reset-btn {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }
  
  .reset-btn .v-icon {
    font-size: 1.125rem;
  }
  
  .status-card {
    border-radius: 16px;
  }
  
  .status-title {
    font-size: 1.125rem;
  }
  
  .status-subtitle {
    font-size: 0.8rem;
  }
  
  .status-select-wrapper {
    max-width: 280px;
  }
  
  .status-select-item {
    border-radius: 12px;
  }
  
  .status-select :deep(.v-field__input) {
    padding: 0 0.75rem;
    min-height: 44px;
  }
}

@media (max-width: 480px) {
  .filter-header {
    margin-bottom: 1.5rem;
  }
  
  .filter-title {
    font-size: 1.125rem;
  }
  
  .filter-subtitle {
    font-size: 0.8rem;
  }
  
  .filter-col {
    margin-bottom: 0.75rem;
  }
  
  .search-item {
    padding: 0 0.5rem;
  }
  
  .filter-select :deep(.v-field__input) {
    padding: 0 0.5rem;
  }
  
  .status-section {
    margin-top: 1.5rem;
  }
  
  .status-header {
    margin-bottom: 1rem;
  }
  
  .status-title {
    font-size: 1rem;
  }
  
  .status-subtitle {
    font-size: 0.75rem;
  }
  
  .status-select-wrapper {
    max-width: 250px;
  }
  
  .status-select :deep(.v-field__input) {
    padding: 0 0.5rem;
    min-height: 40px;
  }
}
</style>