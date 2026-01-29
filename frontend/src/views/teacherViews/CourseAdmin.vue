<template>
  <v-container fluid class="pa-4 course-admin-container">
    <v-card class="content-card">
      <v-card-title class="d-flex align-center py-4 px-6">
        课程管理
        <v-spacer></v-spacer>
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="搜索课程名称、编号或描述..."
          placeholder="输入关键词进行搜索"
          single-line
          hide-details
          density="compact"
          class="search-field"
          clearable
          @input="filterCourses"
        ></v-text-field>
      </v-card-title>
      <v-divider></v-divider>
      
      <v-card-text class="pa-4">
        <!-- 操作栏 -->
        <v-row class="mb-4">
          <v-col cols="12">
            <!-- 第一行：创建按钮 -->
            <div class="d-flex flex-wrap align-center mb-3">
              <v-btn
                color="primary"
                prepend-icon="mdi-plus-circle"
                class="me-3 mb-2"
                size="default"
                variant="elevated"
                @click="showAddCourseModal"
              >
                <v-icon left>mdi-school</v-icon>
                创建新课程
              </v-btn>
            </div>
            
            <!-- 第二行：筛选器 -->
            <v-row class="align-center">
              <v-col cols="12" sm="6" md="4" lg="3">
                <v-select
                  v-model="statusFilter"
                  :items="statusOptions"
                  item-title="title"
                  item-value="value"
                  label="按状态筛选"
                  prepend-inner-icon="mdi-chart-timeline-variant"
                  density="compact"
                  hide-details
                  clearable
                  variant="outlined"
                  @update:model-value="filterCourses"
                ></v-select>
              </v-col>
              
              <v-col cols="12" sm="6" md="8" lg="9">
                <v-select
                  v-model="semesterFilter"
                  :items="semesterOptions"
                  item-title="title"
                  item-value="value"
                  label="按学期筛选"
                  prepend-inner-icon="mdi-calendar-range"
                  density="compact"
                  hide-details
                  clearable
                  variant="outlined"
                  @update:model-value="filterCourses"
                ></v-select>
              </v-col>
              
              <v-col cols="12" class="d-flex justify-end align-center">
                <span class="text-caption me-2">视图模式：</span>
                <v-btn-toggle v-model="viewMode" mandatory density="comfortable">
                  <v-tooltip text="网格视图" location="top">
                    <template #activator="{ props }">
                      <v-btn icon value="grid" v-bind="props">
                        <v-icon>mdi-view-grid</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                  <v-tooltip text="列表视图" location="top">
                    <template #activator="{ props }">
                      <v-btn icon value="list" v-bind="props">
                        <v-icon>mdi-view-list</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </v-btn-toggle>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
        
        <!-- 统计卡片 -->
        <v-row class="mb-6">
          <v-col v-for="(stat, index) in statsItems" :key="index" cols="12" sm="6" md="3">
            <v-card :color="stat.color" variant="flat" class="stat-card">
              <v-card-text>
                <div class="d-flex align-center">
                  <v-icon size="32" :icon="stat.icon" class="me-3"></v-icon>
                  <div>
                    <div class="text-subtitle-2 text-medium-emphasis">{{ stat.title }}</div>
                    <div class="text-h4 font-weight-bold">{{ stat.value }}</div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 网格视图 -->
        <v-row v-if="viewMode === 'grid' && filteredCourses.length > 0">
          <v-col            v-for="course in filteredCourses"
            :key="course.id?.toString() || ''"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <v-card class="course-card" @click="manageCourseMaterials(course)" style="cursor: pointer;" hover>
              <div class="status-indicator" :class="course.status"></div>
              <!-- 点击提示 -->
              <div class="click-hint">
                <v-icon size="small">mdi-mouse</v-icon>
                <span class="text-caption">点击进入课程管理</span>
              </div>
              <v-img
                :src="course.image || 'https://picsum.photos/400/200?random=' + course.id"
                height="180"
                cover
              ></v-img>
              
              <v-card-item>
                <v-card-title class="text-h6 mb-1">{{ course.name }}</v-card-title>
                <v-card-subtitle>课程编码: {{ course.code }}</v-card-subtitle>
              </v-card-item>
              
              <v-card-text>
                <div class="d-flex mb-2">
                  <v-icon size="small" class="me-1">mdi-account-group</v-icon>
                  <span class="text-body-2 me-3">{{ course.studentCount }}人</span>
                  <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                  <span class="text-body-2">{{ course.hours }}学时</span>
                </div>
                <div class="text-body-2 text-truncate-3">{{ course.description }}</div>
                <div class="mt-2 d-flex align-center">
                  <v-icon size="small" class="me-1">mdi-calendar</v-icon>
                  <span class="text-caption">{{ course.startDate }} ~ {{ course.endDate }}</span>
                </div>
              </v-card-text>
              
              <v-card-actions>
                <v-spacer></v-spacer>
                <v-tooltip text="编辑课程信息" location="top">
                  <template #activator="{ props }">
                    <v-btn icon variant="text" v-bind="props" @click.stop="editCourse(course)">
                      <v-icon>mdi-pencil-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="查看知识图谱" location="top">
                  <template #activator="{ props }">
                    <v-btn icon variant="text" v-bind="props" @click.stop="viewCourseKnowledgeGraph(course)">
                      <v-icon>mdi-graph-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="管理课程资料" location="top">
                  <template #activator="{ props }">
                    <v-btn icon variant="text" v-bind="props" @click.stop="manageCourseMaterials(course)">
                      <v-icon>mdi-folder-open-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="删除课程" location="top">
                  <template #activator="{ props }">
                    <v-btn icon variant="text" v-bind="props" @click.stop="confirmDeleteCourse(course)">
                      <v-icon>mdi-delete-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-spacer></v-spacer>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 列表视图 -->
        <v-table
          v-if="viewMode === 'list' && filteredCourses.length > 0"
          density="comfortable"
        >
          <thead>
            <tr>
              <th class="text-left">
                <v-icon size="small" class="me-1">mdi-book</v-icon>
                课程名称
              </th>
              <th class="text-left">
                <v-icon size="small" class="me-1">mdi-identifier</v-icon>
                课程编号
              </th>
              <th class="text-left">
                <v-icon size="small" class="me-1">mdi-calendar-range</v-icon>
                学期
              </th>
              <th class="text-left">
                <v-icon size="small" class="me-1">mdi-calendar-start</v-icon>
                开始日期
              </th>
              <th class="text-left">
                <v-icon size="small" class="me-1">mdi-calendar-end</v-icon>
                结束日期
              </th>
              <th class="text-center">
                <v-icon size="small" class="me-1">mdi-account-group</v-icon>
                学生数
              </th>
              <th class="text-center">
                <v-icon size="small" class="me-1">mdi-chart-timeline-variant</v-icon>
                状态
              </th>
              <th class="text-center">
                <v-icon size="small" class="me-1">mdi-cog</v-icon>
                操作
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="course in filteredCourses" :key="course.id?.toString() || ''">
              <td class="font-weight-medium">{{ course.name }}</td>
              <td>
                <v-chip size="small" variant="outlined" color="primary">
                  {{ course.code }}
                </v-chip>
              </td>
              <td>{{ course.semester }}</td>
              <td>{{ course.startDate }}</td>
              <td>{{ course.endDate }}</td>
              <td class="text-center">
                <v-chip size="small" variant="tonal" color="info">
                  {{ course.studentCount }}人
                </v-chip>
              </td>
              <td class="text-center">
                <v-chip
                  :color="getStatusColor(course.status)"
                  size="small"
                  label
                >
                  {{ getStatusText(course.status) }}
                </v-chip>
              </td>
              <td class="text-center">
                <div class="d-flex gap-1 justify-center">
                  <v-tooltip text="编辑课程信息" location="top">
                    <template #activator="{ props }">
                      <v-btn icon="mdi-pencil-outline" size="small" variant="text" 
                             color="primary" v-bind="props" @click="editCourse(course)"></v-btn>
                    </template>
                  </v-tooltip>
                  
                  <v-tooltip text="查看知识图谱" location="top">
                    <template #activator="{ props }">
                      <v-btn icon="mdi-graph-outline" size="small" variant="text" 
                             color="info" v-bind="props" @click="viewCourseKnowledgeGraph(course)"></v-btn>
                    </template>
                  </v-tooltip>
                  
                  <v-tooltip text="管理课程资料" location="top">
                    <template #activator="{ props }">
                      <v-btn icon="mdi-folder-open-outline" size="small" variant="text" 
                             color="success" v-bind="props" @click="manageCourseMaterials(course)"></v-btn>
                    </template>
                  </v-tooltip>
                  
                  <v-tooltip text="删除课程" location="top">
                    <template #activator="{ props }">
                      <v-btn icon="mdi-delete-outline" size="small" variant="text" 
                             color="error" v-bind="props" @click="confirmDeleteCourse(course)"></v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </td>
            </tr>
          </tbody>
        </v-table>
        
        <!-- 空状态 -->
        <v-row v-if="filteredCourses.length === 0" class="fill-height align-center justify-center">
          <v-col cols="12" class="text-center pa-12">
            <v-icon size="64" color="grey">mdi-book-off</v-icon>
            <div class="text-h6 mt-4 text-grey">暂无符合条件的课程</div>
            <div class="text-body-1 mt-2 text-grey">
              您可以点击"创建新课程"按钮创建一门新课程
            </div>
            <v-btn
              color="primary"
              prepend-icon="mdi-plus-circle"
              class="mt-4"
              size="large"
              variant="elevated"
              @click="showAddCourseModal"
            >
              <v-icon left>mdi-school</v-icon>
              创建新课程
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 新增/编辑课程对话框 -->
    <v-dialog
      v-model="showModal"
      max-width="700px"
    >
      <v-card>
        <v-card-title class="text-h5 pa-4">
          {{ isEditing ? '编辑课程' : '新建课程' }}
          <v-spacer></v-spacer>
          <v-btn icon @click="closeModal">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="form" @submit.prevent="saveCourse">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="courseForm.name"
                  label="课程名称"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="courseForm.code"
                  label="课程编号"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="courseForm.startDate"
                  label="开始日期"
                  type="date"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="courseForm.endDate"
                  label="结束日期"
                  type="date"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model.number="courseForm.hours"
                  label="学时数"
                  type="number"
                  min="1"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="courseForm.semester"
                  :items="getFormSemesterOptions()"
                  item-title="title"
                  item-value="value"
                  label="学期"
                  prepend-inner-icon="mdi-calendar-range"
                  required
                  variant="outlined"
                  density="comfortable"
                >
                  <template #selection="{ item }">
                    <span>{{ item.title }}</span>
                  </template>
                </v-select>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="courseForm.status"
                  :items="[
                    { title: '🔵 即将开始', value: 'upcoming' },
                    { title: '🟢 进行中', value: 'active' },
                    { title: '⚪ 已结束', value: 'completed' }
                  ]"
                  item-title="title"
                  item-value="value"
                  label="课程状态"
                  prepend-inner-icon="mdi-chart-timeline-variant"
                  required
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
              <v-col cols="12">
                <v-file-input
                  label="课程封面图"
                  accept="image/*"
                  show-size
                  @change="handleImageInputChange"
                  variant="outlined"
                  density="comfortable"
                ></v-file-input>
                <v-img
                  v-if="courseForm.image"
                  :src="courseForm.image"
                  max-height="200"
                  contain
                  class="mt-2"
                ></v-img>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="courseForm.description"
                  label="课程描述"
                  rows="4"
                  variant="outlined"
                  density="comfortable"
                ></v-textarea>
              </v-col>
              <v-col cols="12">
                <v-checkbox
                  v-model="courseForm.isPublic"
                  label="公开课程"
                  density="comfortable"
                ></v-checkbox>
              </v-col>
              <v-col cols="12">
                <v-select
                  v-model="courseForm.category"
                  :items="categoryList"
                  label="课程分类"
                  clearable
                  multiple
                  variant="outlined"
                  density="comfortable"
                >
                  <template #append>
                    <v-btn text small @click="showAddCategoryDialog = true">新增分类</v-btn>
                  </template>
                </v-select>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeModal"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="saveCourse"
          >
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 删除确认对话框 -->
    <v-dialog
      v-model="showDeleteModal"
      max-width="400px"
    >
      <v-card>
        <v-card-title class="text-h5 pa-4">
          确认删除
          <v-spacer></v-spacer>
          <v-btn icon @click="closeDeleteModal">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="error"
            size="64"
            class="mb-4"
          >
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要删除课程 <strong>{{ courseToDelete?.name }}</strong> 吗？
          </div>
          <div class="text-caption text-error mt-2">
            此操作无法撤销，课程的所有相关数据也将被删除。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="closeDeleteModal"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            @click="deleteCourse"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 新增分类对话框 -->
    <v-dialog v-model="showAddCategoryDialog" max-width="400">
      <v-card>
        <v-card-title>新增课程分类</v-card-title>
        <v-card-text>
          <v-text-field v-model="newCategoryName" label="分类名称"></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddCategoryDialog = false">取消</v-btn>
          <v-btn color="primary" @click="addCategory">添加</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 知识图谱弹框 -->
    <v-dialog
      v-model="showKnowledgeMapDialog"
      max-width="1200px"
    >
      <v-card>
        <v-card-title class="text-h5 pa-4">
          课程知识图谱
          <v-spacer></v-spacer>
          <v-btn icon @click="showKnowledgeMapDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <KnowledgeMap v-if="selectedCourseForKnowledgeMap" :course-id="selectedCourseForKnowledgeMap.id ?? undefined" />
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import courseService from '../../api/courseService'
import uploadService from '../../api/uploadService'
import categoryService from '../../api/categoryService'
import { useUserStore } from '../../stores/userStore'
import KnowledgeMap from '../../views/KnowledgeMap.vue'
import { parseCourseDescription } from '../../utils/courseUtils' 

// 定义接口
interface Course {
  id: string | null
  name: string
  code: string
  description: string
  image: string
  startDate: string
  endDate: string
  hours: number
  studentCount: number
  status: string
  semester: string
  isPublic: boolean // 新增是否公开属性
  category: string[] // 修复：加上分类字段
  teacher_id: string // 只在Course接口定义
}

interface CourseForm {
  id: string | null
  name: string
  code: string
  description: string
  image: string
  startDate: string
  endDate: string
  hours: number
  studentCount: number
  status: string
  semester: string
  isPublic: boolean
  category: string[]
  // teacher_id 不需要在CourseForm中定义
}

// 路由相关
const router = useRouter()
const userStore = useUserStore()

// 状态管理
const viewMode = ref('grid')
const searchQuery = ref('')
const statusFilter = ref('all')
const semesterFilter = ref('all')
const courses = ref<Course[]>([])
const filteredCourses = ref<Course[]>([])
const imageFile = ref<File | null>(null)
const showModal = ref(false)
const isEditing = ref(false)
const showDeleteModal = ref(false)
const courseToDelete = ref<Course | null>(null)
const showKnowledgeMapDialog = ref(false)
const selectedCourseForKnowledgeMap = ref<Course | null>(null)

// 筛选选项
const statusOptions = ref([
  { title: '全部状态', value: 'all' },
  { title: '🟢 进行中', value: 'active' },
  { title: '🔵 即将开始', value: 'upcoming' },
  { title: '⚪ 已结束', value: 'completed' }
])

const semesterOptions = ref([
  { title: '全部学期', value: 'all' }
])

// 课程表单
const courseForm = reactive<CourseForm>({
  id: null,
  name: '',
  code: '',
  description: '',
  image: '',
  startDate: getTodayDate(),
  endDate: '',
  hours: 40,
  studentCount: 0,
  status: 'upcoming',
  semester: '2025-fall',
  isPublic: true,
  category: []
})

// 分类数据
const categoryList = ref<string[]>([])

// 获取分类列表
const fetchCategoryList = async () => {
  const res = await categoryService.getCategoryList()
  categoryList.value = res.data
}

// 新增分类相关
const showAddCategoryDialog = ref(false)
const newCategoryName = ref('')

// 新增分类
const addCategory = async () => {
  if (newCategoryName.value && !categoryList.value.includes(newCategoryName.value)) {
    categoryList.value.push(newCategoryName.value) // 立即本地添加
    courseForm.category.push(newCategoryName.value)
    // 不直接保存到后端分类表，而是保存课程时带上新分类
    // 保存课程后刷新分类列表
    // await fetchCategoryList() // 不再立即刷新，等保存后统一刷新
  }
  showAddCategoryDialog.value = false
  newCategoryName.value = ''
}

// 统计信息计算属性 - 基于当前用户的课程
const statsItems = computed(() => {
  // 首先过滤出当前用户的课程
  const userCourses = courses.value.filter(course => course.teacher_id === userStore.userId)
  
  return [
    {
      title: '总课程数',
      value: userCourses.length,
      icon: 'mdi-book-multiple',
      color: 'bg-primary-lighten-4'
    },
    {
      title: '进行中',
      value: userCourses.filter(c => c.status === 'active').length,
      icon: 'mdi-play-circle',
      color: 'bg-success-lighten-4'
    },
    {
      title: '即将开始',
      value: userCourses.filter(c => c.status === 'upcoming').length,
      icon: 'mdi-clock-outline',
      color: 'bg-info-lighten-4'
    },
    {
      title: '已结束',
      value: userCourses.filter(c => c.status === 'completed').length,
      icon: 'mdi-check-circle',
      color: 'bg-grey-lighten-3'
    }
  ]
})

// 方法
function getTodayDate() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 管理课程视频
function manageCourseVideos(course: Course) {
  if (!course.id) return
  router.push(`/CourseVideoManage/${course.id}`)
}

// 管理课程详情（新的功能）
function manageCourseMaterials(course: Course) {
  if (!course.id) return
  router.push(`/course-detail-manage/${course.id}`)
}

// 格式化时间戳为日期格式
function formatTimestampToDate(timestamp: number) {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toISOString().split('T')[0]; // 返回YYYY-MM-DD格式
}

// 筛选课程
function filterCourses() {
  let filtered = [...courses.value]
  
  // 只显示自己创建的课程
  filtered = filtered.filter(course => course.teacher_id === userStore.userId)
  
  // 搜索筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(course => 
      course.name.toLowerCase().includes(query) || 
      course.code.toLowerCase().includes(query) ||
      course.description.toLowerCase().includes(query)
    )
  }
  
  // 状态筛选
  if (statusFilter.value !== 'all') {
    filtered = filtered.filter(course => course.status === statusFilter.value)
  }
  
  // 学期筛选
  if (semesterFilter.value !== 'all') {
    filtered = filtered.filter(course => course.semester === semesterFilter.value)
  }
  
  // 保证每个对象都带有 category 字段
  filteredCourses.value = filtered.map(course => ({
    ...course,
    category: Array.isArray(course.category) ? course.category : []
  }))
}

// 获取状态文本
function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    'active': '进行中',
    'upcoming': '即将开始',
    'completed': '已结束'
  }
  return statusMap[status] || status
}

// 获取状态颜色
function getStatusColor(status: string) {
  const colorMap: Record<string, string> = {
    'active': 'success',
    'upcoming': 'info',
    'completed': 'grey'
  }
  return colorMap[status] || 'primary'
}

// 获取表单用的学期选项（不包含"全部学期"选项）
function getFormSemesterOptions() {
  // 返回除了"全部学期"之外的所有选项，再加上一些常用选项
  const dynamicOptions = semesterOptions.value.filter(option => option.value !== 'all')
  
  // 如果没有动态选项，提供一些默认选项
  if (dynamicOptions.length === 0) {
    const currentYear = new Date().getFullYear()
    return [
      { title: `📅 ${currentYear}年春季`, value: `${currentYear}-spring` },
      { title: `📅 ${currentYear}年秋季`, value: `${currentYear}-fall` },
      { title: `📅 ${currentYear + 1}年春季`, value: `${currentYear + 1}-spring` },
      { title: `📅 ${currentYear + 1}年秋季`, value: `${currentYear + 1}-fall` }
    ]
  }
  
  return dynamicOptions
}

// 打开新建课程模态框
function showAddCourseModal() {
  isEditing.value = false
  Object.assign(courseForm, {
    id: null,
    name: '',
    code: '',
    description: '',
    image: '',
    startDate: getTodayDate(),
    endDate: '',
    hours: 40,
    studentCount: 0,
    status: 'upcoming',
    semester: '2023-fall',
    isPublic: true,
    category: []
  })
  imageFile.value = null
  showModal.value = true
}

// 打开编辑课程模态框
function editCourse(course: any) {
  isEditing.value = true
  const descObj = parseCourseDescription(course.description)
  // 保证当前课程的分类都在categoryList中
  if (descObj.category && Array.isArray(descObj.category)) {
    descObj.category.forEach((cat: string) => {
      if (cat && !categoryList.value.includes(cat)) {
        categoryList.value.push(cat)
      }
    })
  }
  // 直接赋值，不再过滤
  Object.assign(courseForm, {
    ...course,
    description: descObj.description || '',
    category: Array.isArray(descObj.category) ? [...descObj.category] : []
  })
  showModal.value = true
  // 调试输出
  console.log('categoryList:', categoryList.value)
  console.log('courseForm.category:', courseForm.category)
}

// 关闭模态框
function closeModal() {
  showModal.value = false
}

// 处理图片上传
function handleImageInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    imageFile.value = target.files[0]
    
    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target) {
        courseForm.image = e.target.result as string
      }
    }
    reader.readAsDataURL(imageFile.value)
  }
}

// 保存课程
async function saveCourse() {
  // 表单验证
  if (!courseForm.name || !courseForm.code || !courseForm.startDate || !courseForm.endDate) {
    ElMessage.warning('请填写所有必填字段')
    return
  }
  try {
    // 转换日期为时间戳
    const dateToTimestamp = (dateStr: string | null): number => {
      if (!dateStr) return 0;
      return new Date(dateStr).getTime();
    };
    // 打包 description 和 category
    const packedDesc = JSON.stringify({
      description: courseForm.description,
      category: courseForm.category
    })
    const courseData = {
      name: courseForm.name,
      code: courseForm.code,
      description: packedDesc, // 存储打包后的 JSON 字符串
      imageUrl: courseForm.image,
      startDate: dateToTimestamp(courseForm.startDate),
      endDate: dateToTimestamp(courseForm.endDate),
      hours: courseForm.hours,
      status: mapStatusToInt(courseForm.status),
      semester: courseForm.semester,
      isPublic: courseForm.isPublic
      // category 字段不再单独传递
    }
    // 如果有选择图片文件，先上传图片
    if (imageFile.value) {
      try {
        const uploadResponse = await uploadService.uploadImage(imageFile.value)
        if (uploadResponse.data.code === 200) {
          courseData.imageUrl = uploadResponse.data.data.imageUrl
        } else {
          throw new Error(uploadResponse.data.message || '图片上传失败')
        }
      } catch (uploadError: any) {
        console.error('图片上传错误:', uploadError)
        ElMessage.error('图片上传失败: ' + (uploadError.message || '未知错误'))
        return
      }
    }
    // 发送创建/更新课程请求
    let response
    if (isEditing.value && courseForm.id) {
      response = await courseService.updateCourse(courseForm.id, courseData)
    } else {
      response = await courseService.createCourse(courseData)
    }
    if (response.data.code === 200) {
      ElMessage.success(isEditing.value ? '课程更新成功' : '课程创建成功')
      closeModal()
      fetchCourses() // 刷新课程列表
    } else {
      throw new Error(response.data.message || (isEditing.value ? '更新课程失败' : '创建课程失败'))
    }
  } catch (error: any) {
    console.error(isEditing.value ? '更新课程错误:' : '创建课程错误:', error)
    ElMessage.error(error.message || '操作失败，请重试')
  }
}

// 状态转换函数
function mapStatusToInt(status: string) {
  const statusMap: Record<string, number> = {
    'upcoming': 0,   // 即将开始
    'active': 1,     // 进行中
    'completed': 2   // 已结束
  }
  return statusMap[status] ?? 0
}

// 数字状态转字符串状态
function mapIntToStatus(statusInt: number): string {
  const statusMap: Record<number, string> = {
    0: 'upcoming',    // 即将开始
    1: 'active',      // 进行中
    2: 'completed'    // 已结束
  }
  return statusMap[statusInt] ?? 'upcoming'
}

// 打开删除确认框
function confirmDeleteCourse(course: Course) {
  courseToDelete.value = course
  showDeleteModal.value = true
}

// 关闭删除确认框
function closeDeleteModal() {
  showDeleteModal.value = false
  courseToDelete.value = null
}

// 删除课程
async function deleteCourse() {
  if (!courseToDelete.value || !courseToDelete.value.id) return
  
  try {
    const response = await courseService.deleteCourse(courseToDelete.value.id)
    
    if (response.data.code === 200) {
      // 删除成功后更新本地数据
      courses.value = courses.value.filter(c => c.id !== courseToDelete.value?.id)
      filterCourses() // 重新应用筛选
      
      ElMessage.success('课程删除成功')
    } else {
      throw new Error(response.data.message || '删除课程失败')
    }
  } catch (error: any) {
    console.error('删除课程错误:', error)
    ElMessage.error('删除课程失败: ' + (error.message || '未知错误'))
  } finally {
    closeDeleteModal()
  }
}

// 查看课程详情
function viewCourseKnowledgeGraph(course: Course) {
  selectedCourseForKnowledgeMap.value = course
  showKnowledgeMapDialog.value = true
}

// 跳转到知识图谱页面
function goToKnowledgeMap(courseId: string | null) {
  if (!courseId) return
  router.push({
    name: 'KnowledgeMap', // 需在路由配置中定义该名称
    params: { courseId }
  })
}

// 退出登录
function logout() {
  userStore.clearUserInfo()
  router.push('/login')
}

// 获取课程列表
async function fetchCourses() {
  try {
    const response = await courseService.getCourses()
    if (response.data.code === 200) {
      // 更新课程列表
      courses.value = response.data.data.list.map((course: any) => {
        const descObj = parseCourseDescription(course.description)
        return {
          id: course.id,
          name: course.name,
          code: course.code,
          description: descObj.description || '',
          image: course.imageUrl,
          startDate: formatTimestampToDate(course.startDate),
          endDate: formatTimestampToDate(course.endDate),
          hours: course.hours,
          studentCount: course.studentCount || 0,
          // 将数字状态转换为字符串状态
          status: mapIntToStatus(course.status),
          semester: course.semester,
          isPublic: course.isPublic !== undefined ? course.isPublic : true,
          category: descObj.category || [],
          teacher_id: course.teacher_id // 新增字段
        }
      })
      // 分类记忆：自动聚合所有课程的分类
      const allCategories = new Set<string>()
      courses.value.forEach(course => {
        (course.category || []).forEach((cat: string) => {
          if (cat) allCategories.add(cat)
        })
      })
      categoryList.value = Array.from(allCategories)
      
      // 动态更新学期选项：从实际课程数据中提取
      const allSemesters = new Set<string>()
      courses.value.forEach(course => {
        if (course.semester) {
          allSemesters.add(course.semester)
        }
      })
      
      // 构建学期选项，按时间排序
      const semesterList = Array.from(allSemesters).sort((a, b) => {
        // 简单排序：假设格式为 YYYY-season，将较新的学期排在前面
        const [yearA, seasonA] = a.split('-')
        const [yearB, seasonB] = b.split('-')
        if (yearA !== yearB) {
          return parseInt(yearB) - parseInt(yearA) // 年份降序
        }
        // 同年的话，spring < fall
        const seasonOrder = { 'spring': 1, 'fall': 2 }
        return (seasonOrder[seasonB as keyof typeof seasonOrder] || 0) - (seasonOrder[seasonA as keyof typeof seasonOrder] || 0)
      })
      
      // 更新学期选项
      semesterOptions.value = [
        { title: '全部学期', value: 'all' },
        ...semesterList.map(semester => {
          // 将学期代码转换为友好的显示文本
          const [year, season] = semester.split('-')
          const seasonMap = {
            'spring': '春季',
            'fall': '秋季',
            'summer': '夏季',
            'winter': '冬季'
          }
          const seasonText = seasonMap[season as keyof typeof seasonMap] || season
          return {
            title: `📅 ${year}年${seasonText}`,
            value: semester
          }
        })
      ]
      
      // 应用过滤器重新显示课程
      filterCourses()
    } else {
      throw new Error(response.data.message || '获取课程列表失败')
    }
  } catch (error: any) {
    console.error('获取课程列表失败:', error)
    ElMessage.error('获取课程列表失败: ' + (error.message || '未知错误'))
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchCourses()
  fetchCategoryList()
})
</script>

<style scoped>
.course-admin-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.content-card > .v-card-text {
  overflow-y: auto;
  flex: 1;
}

.search-field {
  max-width: 300px;
}

.stat-card {
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.course-card {
  position: relative;
  transition: all 0.3s ease;
  height: 100%;
  overflow: hidden;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.status-indicator {
  position: absolute;
  top: 0;
  right: 0;
  width: 50px;
  height: 5px;
  z-index: 2;
}

.status-indicator.active {
  background-color: rgb(76, 175, 80);
}

.status-indicator.upcoming {
  background-color: rgb(33, 150, 243);
}

.status-indicator.completed {
  background-color: rgb(158, 158, 158);
}

.click-hint {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(25, 118, 210, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  display: none;
  align-items: center;
  gap: 4px;
  z-index: 3;
  font-size: 11px;
}

.course-card:hover .click-hint {
  display: flex;
}

.text-truncate-3 {  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 600px) {
  .pa-4 {
    padding: 8px !important;
  }
  
  .pa-6 {
    padding: 12px !important;
  }
}
</style>