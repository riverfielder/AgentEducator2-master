<template>
  <div class="teacher-knowledge-detail">
    <v-container fluid class="pa-4">
      <v-fade-transition>
        <v-card class="main-card">
          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            closable
            class="ma-4"
          >
            {{ error }}
          </v-alert>

          <!-- 顶部数据卡片 -->
          <v-row class="ma-0 pa-4">
            <!-- 左侧：知识点详情卡片 -->
            <v-col cols="12" md="8" class="pa-2">
              <v-slide-x-transition>
                <v-card>
                  <v-card-text class="pa-6">
                    <v-row no-gutters>
                      <!-- 左侧：知识点信息 -->
                      <v-col cols="12" md="8" class="pr-md-6">
                        <div class="d-flex flex-column">
                          <h1 class="text-h4 font-weight-bold mb-2">{{ title }}</h1>
                          <div class="d-flex align-center mb-4">
                            <v-chip
                              v-for="(tag, index) in tags"
                              :key="index"
                              class="mr-2"
                              size="small"
                              variant="tonal"
                              :color="tag.color"
                            >
                              {{ tag.text }}
                            </v-chip>
                          </div>
                          <p class="text-body-1 text-medium-emphasis mb-4">{{ description }}</p>
                          
                          <!-- 父知识点 -->
                          <div v-if="parentKeywords.length > 0" class="mb-4">
                            <div class="text-subtitle-1 font-weight-medium mb-2">父知识点</div>
                            <div class="d-flex flex-wrap">
                              <v-chip
                                v-for="(point, index) in displayParentKeywords"
                                :key="index"
                                class="mr-2 mb-2"
                                size="small"
                                variant="outlined"
                                color="success"
                                @click="navigateToPoint(point.id)"
                              >
                                {{ point.name }}
                              </v-chip>
                            </div>
                            <v-btn
                              v-if="parentKeywords.length > 8"
                              variant="text"
                              size="small"
                              color="primary"
                              class="mt-1"
                              @click="toggleParentKeywords"
                            >
                              <v-icon size="small" class="mr-1">
                                {{ showAllParentKeywords ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                              </v-icon>
                              {{ showAllParentKeywords ? '收起' : `展开全部 (${parentKeywords.length}个)` }}
                            </v-btn>
                          </div>

                          <!-- 子知识点 -->
                          <div v-if="childKeywords.length > 0" class="mb-4">
                            <div class="text-subtitle-1 font-weight-medium mb-2">子知识点</div>
                            <div class="d-flex flex-wrap">
                              <v-chip
                                v-for="(point, index) in displayChildKeywords"
                                :key="index"
                                class="mr-2 mb-2"
                                size="small"
                                variant="outlined"
                                color="warning"
                                @click="navigateToPoint(point.id)"
                              >
                                {{ point.name }}
                              </v-chip>
                            </div>
                            <v-btn
                              v-if="childKeywords.length > 8"
                              variant="text"
                              size="small"
                              color="primary"
                              class="mt-1"
                              @click="toggleChildKeywords"
                            >
                              <v-icon size="small" class="mr-1">
                                {{ showAllChildKeywords ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                              </v-icon>
                              {{ showAllChildKeywords ? '收起' : `展开全部 (${childKeywords.length}个)` }}
                            </v-btn>
                          </div>

                          <!-- 相关资源统计 -->
                          <div class="mb-4">
                            <div class="text-subtitle-1 font-weight-medium mb-2">相关资源</div>
                            <div class="d-flex flex-wrap">
                              <v-btn
                                v-if="relatedVideos.length > 0"
                                class="mr-2 mb-2"
                                size="small"
                                variant="tonal"
                                color="info"
                                @click="openResourceDialog('video', relatedVideos)"
                              >
                                <v-icon size="small" class="mr-1">mdi-video</v-icon>
                                {{ relatedVideos.length }} 个视频
                              </v-btn>
                              <v-btn
                                v-if="relatedDocuments.length > 0"
                                class="mr-2 mb-2"
                                size="small"
                                variant="tonal"
                                color="secondary"
                                @click="openResourceDialog('document', relatedDocuments)"
                              >
                                <v-icon size="small" class="mr-1">mdi-file-document</v-icon>
                                {{ relatedDocuments.length }} 个文档
                              </v-btn>
                              <v-btn
                                v-if="relatedQuestions.length > 0"
                                class="mr-2 mb-2"
                                size="small"
                                variant="tonal"
                                color="warning"
                                @click="openResourceDialog('question', relatedQuestions)"
                              >
                                <v-icon size="small" class="mr-1">mdi-help-circle</v-icon>
                                {{ relatedQuestions.length }} 道题目
                              </v-btn>
                              <v-chip
                                v-if="relatedQuestions.length === 0"
                                class="mr-2 mb-2"
                                size="small"
                                variant="outlined"
                                color="grey"
                              >
                                <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
                                暂无作业
                              </v-chip>
                            </div>
                          </div>

                          <!-- 相关资源弹窗 -->
                          <RelatedResourcesDialog
                            v-model="showResourceDialog"
                            :resource-type="currentResourceType"
                            :resources="currentResources"
                          />

                          <!-- 掌握度算法说明 -->
                          <div class="mb-4">
                            <div class="text-subtitle-1 font-weight-medium mb-2">掌握度计算说明</div>
                            <v-alert
                              variant="tonal"
                              color="info"
                              density="compact"
                              class="text-body-2"
                            >
                              <div class="d-flex flex-column">
                                <div class="mb-1">
                                  <v-icon size="small" class="mr-1" color="info">mdi-book-open-variant</v-icon>
                                  <strong>学习材料进度</strong>：基于学生观看视频、阅读文档的完成情况
                                </div>
                                <div class="mb-1" v-if="relatedQuestions.length > 0">
                                  <v-icon size="small" class="mr-1" color="success">mdi-star</v-icon>
                                  <strong>作业表现</strong>：基于学生完成作业题目的正确率和得分
                                </div>
                                <div class="mb-1" v-else>
                                  <v-icon size="small" class="mr-1" color="grey">mdi-minus-circle-outline</v-icon>
                                  <strong>作业表现</strong>：<span class="text-grey">暂无作业，此维度不参与计算</span>
                                </div>
                                <div v-if="childKeywords.length > 0">
                                  <v-icon size="small" class="mr-1" color="warning">mdi-sitemap</v-icon>
                                  <strong>子知识点</strong>：基于 {{ childKeywords.length }} 个子知识点的掌握情况
                                </div>
                                <div v-else>
                                  <v-icon size="small" class="mr-1" color="grey">mdi-minus-circle-outline</v-icon>
                                  <strong>子知识点</strong>：<span class="text-grey">无子知识点，此维度不参与计算</span>
                                </div>
                              </div>
                            </v-alert>
                          </div>
                        </div>
                      </v-col>

                      <!-- 右侧：掌握度环形图 -->
                      <v-col cols="12" md="4" class="d-flex align-center justify-center">
                        <div class="text-center">
                          <div class="position-relative" style="width: 180px; height: 180px">
                            <v-progress-circular
                              :model-value="stats.averageMastery"
                              :color="getMasteryColor(stats.averageMastery)"
                              :width="12"
                              :size="180"
                              class="mb-4"
                            >
                              <div class="text-center">
                                <div class="text-h4 font-weight-bold">{{ stats.averageMastery }}%</div>
                                <div class="text-caption text-medium-emphasis">平均掌握度</div>
                              </div>
                            </v-progress-circular>
                          </div>
                          <div class="mt-4">
                            <div v-for="(item, index) in masteryDistribution" :key="index" class="mb-2">
                              <div class="d-flex justify-space-between align-center mb-1">
                                <div class="d-flex align-center">
                                  <v-icon :color="item.color" size="small" class="mr-2">{{ item.icon }}</v-icon>
                                  <span class="text-caption">{{ item.label }}</span>
                                </div>
                                <span class="text-caption font-weight-medium">{{ item.percentage }}%</span>
                              </div>
                              <v-tooltip location="bottom">
                                <template v-slot:activator="{ props }">
                                  <div v-bind="props">
                                    <v-progress-linear
                                      :model-value="item.percentage"
                                      :color="item.color"
                                      height="4"
                                      rounded
                                    ></v-progress-linear>
                                  </div>
                                </template>
                                <div class="text-body-2">
                                  {{ item.label }}: {{ item.percentage }}% 的学生
                                  <div class="text-caption mt-1">
                                    <template v-if="item.label === '已掌握'">
                                      掌握度达到80%及以上的学生
                                    </template>
                                    <template v-else-if="item.label === '学习中'">
                                      掌握度在40%-80%之间的学生
                                    </template>
                                    <template v-else>
                                      掌握度低于40%的学生
                                    </template>
                                  </div>
                                </div>
                              </v-tooltip>
                            </div>
                          </div>
                        </div>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-slide-x-transition>
            </v-col>

            <!-- 右侧：教学材料完成率 -->
            <v-col cols="12" md="4" class="pa-2">
              <v-slide-x-transition>
                <v-card>
                  <v-card-text class="pa-6">
                    <div class="d-flex justify-space-between align-center mb-6">
                      <div class="text-h6">学习资源完成情况</div>
                      <v-chip size="small" :color="getCompletionColor(stats.averageCompletion)" variant="tonal">
                        {{ stats.averageCompletion }}% 平均
                      </v-chip>
                    </div>
                    
                    <div class="chart-container">
                      <!-- Y轴刻度和虚线 -->
                      <div class="y-axis">
                        <div v-for="value in [100, 75, 50, 25, 0]" :key="value" class="y-axis-label">
                          <span class="label">{{ value }}%</span>
                          <div class="grid-line"></div>
                        </div>
                      </div>

                      <!-- 柱状图 -->
                      <div v-if="resourceCompletionStats.length > 0" class="materials-chart d-flex align-end justify-space-around">
                        <div v-for="(resource, index) in resourceCompletionStats" :key="index" class="chart-bar-wrapper text-center">
                          <div class="chart-bar-container">
                            <v-tooltip location="top">
                              <template v-slot:activator="{ props }">
                                <div 
                                  v-bind="props"
                                  class="chart-bar"
                                  :style="{
                                    height: `calc(${resource.completion}% * 0.8)`,
                                    backgroundColor: getResourceColor(resource.type, resource.completion)
                                  }"
                                >
                                  <div class="chart-value">{{ resource.completion }}%</div>
                                </div>
                              </template>
                              <div class="text-body-2">
                                <div class="font-weight-medium">{{ resource.title }}</div>
                                <div class="text-caption mt-1">
                                  类型: {{ getResourceTypeName(resource.type) }}<br>
                                  完成率: {{ resource.completion }}%<br>
                                  完成人数: {{ resource.completedCount }}/{{ resource.totalStudents }}
                                </div>
                              </div>
                            </v-tooltip>
                          </div>
                          <div class="chart-label">
                            <v-icon size="small" :color="getResourceIconColor(resource.type)" class="mr-1">
                              {{ getResourceIcon(resource.type) }}
                            </v-icon>
                            {{ truncateTitle(resource.title, 8) }}
                          </div>
                        </div>
                      </div>
                      <div v-else class="text-center text-grey pa-8">
                        <v-icon size="40" color="grey">mdi-chart-bar-off</v-icon>
                        <div class="mt-2">暂无学习资源数据</div>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-slide-x-transition>
            </v-col>
          </v-row>

          <!-- 加载提示和学生掌握情况 -->
          <v-slide-y-transition>
            <template v-if="loading">
              <div class="d-flex justify-center align-center pa-4">
                <v-progress-circular indeterminate></v-progress-circular>
              </div>
            </template>
            <v-card v-else class="student-section mx-4 mb-4">
              <v-card-title class="d-flex align-center py-4">
                <div class="text-h6">学生掌握情况</div>
                <v-spacer></v-spacer>
                <v-text-field
                  v-model="search"
                  append-icon="mdi-magnify"
                  label="搜索学生"
                  single-line
                  hide-details
                  density="compact"
                  style="max-width: 300px"
                ></v-text-field>
              </v-card-title>

              <v-divider></v-divider>

              <v-data-table
                :headers="studentHeaders"
                :items="displayStudents"
                :loading="loading"
                :items-per-page="10"
                :items-per-page-options="[5, 10, 20, 50]"
                class="student-table"
                :search="search"
              >                <template v-slot:item.avatar="{ item }">
                  <v-avatar size="40" color="grey-lighten-3">
                    <img 
                      v-if="item.avatar && !item.avatarLoadError" 
                      :src="item.avatar" 
                      @error="handleAvatarError($event, item)"
                      @load="handleAvatarLoad($event, item)"
                      style="width: 100%; height: 100%; object-fit: cover;" 
                    />
                    <div v-else-if="item.name && item.name.trim()" 
                         class="letter-avatar" 
                         :style="getLetterAvatarStyle(item.name)">
                      {{ item.name.charAt(0).toUpperCase() }}
                    </div>
                    <v-icon v-else>mdi-account</v-icon>
                  </v-avatar>
                </template>
                
                <template v-slot:item.name="{ item }">
                  <div class="font-weight-medium">{{ item.name }}</div>
                </template>
                
                <template v-slot:item.mastery="{ item }">
                  <div class="d-flex align-center">
                    <v-progress-linear
                      :model-value="item.mastery"
                      :color="getMasteryColor(item.mastery)"
                      height="8"
                      rounded
                      style="width: 100px"
                    ></v-progress-linear>
                    <span class="ml-2 text-caption">{{ item.mastery }}%</span>
                  </div>
                </template>
                
                <template v-slot:item.materialProgress="{ item }">
                  <div class="d-flex align-center">
                    <v-icon size="small" color="info" class="mr-1">mdi-book-open-variant</v-icon>
                    <span class="text-caption">{{ item.materialProgress || 0 }}%</span>
                  </div>
                </template>
                
                <template v-slot:item.exerciseScore="{ item }">
                  <div class="d-flex align-center">
                    <template v-if="getCalculationDetails(item.id) && !getCalculationDetails(item.id).has_exercises">
                      <v-icon size="small" color="grey" class="mr-1">mdi-minus-circle-outline</v-icon>
                      <span class="text-caption text-grey">无作业</span>
                      <v-tooltip activator="parent" location="top">
                        该知识点暂无对应的作业题目，掌握度计算不包含作业得分
                      </v-tooltip>
                    </template>
                    <template v-else>
                      <v-icon size="small" color="success" class="mr-1">mdi-star</v-icon>
                      <span class="text-caption">{{ item.exerciseScore || 0 }}%</span>
                    </template>
                  </div>
                </template>
                
                <template v-slot:item.status="{ item }">
                  <v-chip
                    :color="getStatusColor(item.status)"
                    size="small"
                    variant="tonal"
                  >
                    {{ item.status }}
                  </v-chip>
                </template>
              </v-data-table>
            </v-card>
          </v-slide-y-transition>
        </v-card>
      </v-fade-transition>
    </v-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import knowledgeMapService from '../../api/knowledgeMapService'
import studentService from '../../api/studentService'
import RelatedResourcesDialog from './components/RelatedResourcesDialog.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref(null)
const search = ref('')

// 基础数据
const title = ref('')
const description = ref('')
const tags = ref([])

// 分类映射
const categoryMap = {
  core_concept: '一级知识点',
  main_module: '二级知识点',
  specific_point: '三级知识点'
}

// 分类名称转换函数
const getCategoryName = (category) => {
  return categoryMap[category] || category
}

// 知识点详情数据
const knowledgePoint = ref(null)
const parentKeywords = ref([])
const childKeywords = ref([])
const relatedVideos = ref([])
const relatedDocuments = ref([])
const relatedQuestions = ref([])
const masteryInfo = ref(null)

// 展开/收起状态
const showAllParentKeywords = ref(false)
const showAllChildKeywords = ref(false)

// 相关资源弹窗相关
const showResourceDialog = ref(false)
const currentResourceType = ref('video')
const currentResources = ref([])

// 学习资源完成度统计
const resourceCompletionStats = ref([])

// 更新stats对象
const stats = ref({
  studentCount: 0,
  averageMastery: 0,
  averageCompletion: computed(() => {
    if (resourceCompletionStats.value.length === 0) return 0
    const total = resourceCompletionStats.value.reduce((sum, item) => sum + item.completion, 0)
    return Math.round(total / resourceCompletionStats.value.length)
  })
})

// 掌握度分布数据
const masteryDistribution = ref([
  { label: '已掌握', percentage: 0, color: 'success', icon: 'mdi-check-circle' },
  { label: '学习中', percentage: 0, color: 'info', icon: 'mdi-progress-clock' },
  { label: '未掌握', percentage: 0, color: 'error', icon: 'mdi-alert-circle' }
])

// 学生数据
const students = ref([])

// 表格头部定义
const studentHeaders = ref([
  { title: '头像', key: 'avatar', sortable: false, width: '80px' },
  { title: '姓名', key: 'name', sortable: true },
  { title: '邮箱', key: 'email', sortable: true },
  { title: '掌握度', key: 'mastery', sortable: true, width: '150px' },
  { title: '材料进度', key: 'materialProgress', sortable: true, width: '120px' },
  { 
    title: relatedQuestions.value && relatedQuestions.value.length > 0 ? '作业得分' : '作业得分 (无)', 
    key: 'exerciseScore', 
    sortable: true, 
    width: '120px' 
  },
  { title: '状态', key: 'status', sortable: true, width: '100px' }
])

// 计算显示的学生列表
const displayStudents = computed(() => {
  if (!search.value) return students.value
  const searchText = search.value.toLowerCase()
  return students.value.filter(student => 
    student.email.toLowerCase().includes(searchText) ||
    student.name.toLowerCase().includes(searchText)
  )
})

// 计算显示的父知识点(16个为分界)
const displayParentKeywords = computed(() => {
  if (showAllParentKeywords.value) {
    return parentKeywords.value
  }
  return parentKeywords.value.slice(0, 16)
})

// 计算显示的子知识点
const displayChildKeywords = computed(() => {
  if (showAllChildKeywords.value) {
    return childKeywords.value
  }
  return childKeywords.value.slice(0, 16)
})

// 获取学生的计算详情
const getCalculationDetails = (studentId) => {
  const resourceDetails = masteryInfo.value?.resource_details?.[studentId]
  if (!resourceDetails) return null
  
  // 检查是否有作业/练习
  const hasExercises = resourceDetails.assignments && resourceDetails.assignments.length > 0
  
  // 检查是否有子知识点
  const hasSubKnowledge = childKeywords.value && childKeywords.value.length > 0
  
  return {
    has_exercises: hasExercises,
    has_sub_knowledge: hasSubKnowledge,
    assignments_count: resourceDetails.assignments ? resourceDetails.assignments.length : 0,
    sub_knowledge_count: childKeywords.value ? childKeywords.value.length : 0
  }
}

// 工具函数
const getMasteryColor = (mastery) => {
  if (mastery >= 80) return 'success'
  if (mastery >= 60) return 'primary'
  if (mastery >= 40) return 'warning'
  return 'error'
}

const getStatusColor = (status) => {
  const colors = {
    '已掌握': 'success',
    '进行中': 'primary',
    '未掌握': 'error'
  }
  return colors[status] || 'grey'
}

// 获取完成率颜色
const getCompletionColor = (completion) => {
  if (completion >= 80) return 'success'
  if (completion >= 60) return 'primary'
  if (completion >= 40) return 'warning'
  return 'error'
}

// 获取资源类型颜色
const getResourceColor = (type, completion) => {
  const baseColors = {
    'video': completion >= 80 ? 'rgb(var(--v-theme-success))' : 'rgb(var(--v-theme-info))',
    'document': completion >= 80 ? 'rgb(var(--v-theme-success))' : 'rgb(var(--v-theme-secondary))',
    'assignment': completion >= 80 ? 'rgb(var(--v-theme-success))' : 'rgb(var(--v-theme-warning))'
  }
  return baseColors[type] || 'rgb(var(--v-theme-primary))'
}

// 获取资源图标
const getResourceIcon = (type) => {
  const icons = {
    'video': 'mdi-video',
    'document': 'mdi-file-document',
    'assignment': 'mdi-clipboard-text'
  }
  return icons[type] || 'mdi-help-circle'
}

// 获取资源图标颜色
const getResourceIconColor = (type) => {
  const colors = {
    'video': 'info',
    'document': 'secondary',
    'assignment': 'warning'
  }
  return colors[type] || 'primary'
}

// 获取资源类型名称
const getResourceTypeName = (type) => {
  const names = {
    'video': '视频',
    'document': '文档',
    'assignment': '作业'
  }
  return names[type] || '未知'
}

// 截断标题
const truncateTitle = (title, maxLength) => {
  if (title.length <= maxLength) return title
  return title.substring(0, maxLength) + '...'
}

// 打开资源弹窗
const openResourceDialog = (resourceType, resources) => {
  currentResourceType.value = resourceType
  currentResources.value = resources
  showResourceDialog.value = true
}

// 切换父知识点展开/收起
const toggleParentKeywords = () => {
  showAllParentKeywords.value = !showAllParentKeywords.value
}

// 切换子知识点展开/收起
const toggleChildKeywords = () => {
  showAllChildKeywords.value = !showAllChildKeywords.value
}

const initData = async () => {
  try {
    loading.value = true
    error.value = null
    
    const keywordId = route.params.id
    if (!keywordId) {
      error.value = '知识点ID不存在'
      return
    }

    // 1. 获取知识点信息
    const knowledgePointSuccess = await fetchKnowledgePointInfo(keywordId)
    console.log('knowledgePointSuccess',knowledgePointSuccess)
    if (!knowledgePointSuccess) {
      return
    }

    // 2. 获取学生掌握度信息
    const courseId = route.query.course_id ? String(route.query.course_id) : undefined
    const response = await knowledgeMapService.getCourseStudentsKnowledgePointMastery(keywordId, courseId, false)
    console.log('aaaaaaaaaaaaaa',response)
    if (!response.data || response.data.code !== 200) {
      error.value = response.data?.msg || '获取学生掌握度失败'
      return
    }

    const { students_mastery = {}, resource_details = {} } = response.data.data

    // 3. 更新学生列表
    students.value = Object.values(students_mastery).map(student => ({
      id: student.id,
      name: student.name,
      email: student.email,
      mastery: student.mastery_level,
      status: student.mastery_level >= 80 ? '已掌握' : 
              student.mastery_level >= 40 ? '进行中' : '未掌握',
      materialProgress: student.material_progress,
      exerciseScore: student.exercise_score
    }))

    // 4. 更新掌握度信息
    masteryInfo.value = {
      student_mastery: {},
      material_progress: {},
      exercise_score: {},
      resource_details: {}
    }

    Object.entries(students_mastery).forEach(([studentId, data]) => {
      masteryInfo.value.student_mastery[studentId] = data.mastery_level
      masteryInfo.value.material_progress[studentId] = data.material_progress
      masteryInfo.value.exercise_score[studentId] = data.exercise_score
    })

    masteryInfo.value.resource_details = resource_details

    // 5. 更新统计数据
    updateStatistics()
    
  } catch (err) {
    console.error('加载失败:', err)
    error.value = '数据加载失败，请刷新页面重试'
  } finally {
    loading.value = false
  }
}

const fetchKnowledgePointInfo = async (keywordId) => {
  try {
    const response = await knowledgeMapService.getKnowledgePointDetail(keywordId)
    if (response.data && response.data.code === 200) {
      const data = response.data.data
      
      // 设置知识点基本信息
      knowledgePoint.value = data.keyword
      title.value = data.keyword?.name || `知识点 ${keywordId}`
      description.value = data.keyword?.description || `这是知识点 ${keywordId} 的详细描述。`
      
      // 设置标签
      if (data.keyword?.category) {
        tags.value = [
          { text: getCategoryName(data.keyword.category), color: 'primary' },
          { text: '知识点', color: 'info' }
        ]
      }
      
      // 设置相关数据
      relatedVideos.value = data.related_videos || []
      relatedDocuments.value = data.related_documents || []
      relatedQuestions.value = data.related_questions || []
      parentKeywords.value = data.parent_keywords || []
      childKeywords.value = data.child_keywords || []

      return true
    } else {
      console.error('加载知识点详情失败:', response.data?.msg)
      error.value = response.data?.msg || '加载知识点详情失败'
      return false
    }
  } catch (err) {
    console.error('加载知识点详情失败:', err)
    error.value = '加载知识点详情失败'
    return false
  }
}

const updateStatistics = () => {
  if (students.value.length > 0) {
    // 计算平均掌握度
    const totalMastery = students.value.reduce((sum, student) => sum + student.mastery, 0)
    stats.value.averageMastery = Math.round(totalMastery / students.value.length)

    console.log('\n=== 统计信息 ===')
    console.log('总学生数:', students.value.length)
    console.log('平均掌握度:', stats.value.averageMastery)

    // 更新掌握度分布
    const mastered = students.value.filter(s => s.mastery >= 80).length
    const learning = students.value.filter(s => s.mastery >= 40 && s.mastery < 80).length
    const notStarted = students.value.filter(s => s.mastery < 40).length

    console.log('\n掌握度分布:')
    console.log('- 已掌握(>=80%):', mastered, '人')
    console.log('- 学习中(40-80%):', learning, '人')
    console.log('- 未掌握(<40%):', notStarted, '人')

    masteryDistribution.value = [
      { 
        label: '已掌握', 
        percentage: Math.round((mastered / students.value.length) * 100), 
        color: 'success', 
        icon: 'mdi-check-circle' 
      },
      { 
        label: '学习中', 
        percentage: Math.round((learning / students.value.length) * 100), 
        color: 'info', 
        icon: 'mdi-progress-clock' 
      },
      { 
        label: '未掌握', 
        percentage: Math.round((notStarted / students.value.length) * 100), 
        color: 'error', 
        icon: 'mdi-alert-circle' 
      }
    ]

    // 处理具体资源完成度数据
    updateResourceCompletionStats()
  }
}

const updateResourceCompletionStats = () => {
  console.log('\n=== 资源完成情况统计 ===')
  
  const allResources = []
  const studentCount = students.value.length
  
  if (studentCount === 0) {
    resourceCompletionStats.value = []
    return
  }

  // 收集所有资源
  const resourceMap = new Map()
  
  students.value.forEach(student => {
    const resourceDetails = masteryInfo.value?.resource_details?.[student.id]
    if (resourceDetails) {
      // 处理视频
      if (resourceDetails.videos) {
        resourceDetails.videos.forEach(video => {
          const key = `video_${video.id}`
          if (!resourceMap.has(key)) {
            resourceMap.set(key, {
              id: video.id,
              title: video.title,
              type: 'video',
              completedCount: 0,
              totalStudents: studentCount,
              totalProgress: 0
            })
          }
          const resource = resourceMap.get(key)
          resource.totalProgress += video.progress * 100
          if (video.completed) {
            resource.completedCount++
          }
        })
      }
      
      // 处理文档
      if (resourceDetails.documents) {
        resourceDetails.documents.forEach(document => {
          const key = `document_${document.id}`
          if (!resourceMap.has(key)) {
            resourceMap.set(key, {
              id: document.id,
              title: document.title,
              type: 'document',
              completedCount: 0,
              totalStudents: studentCount,
              totalProgress: 0
            })
          }
          const resource = resourceMap.get(key)
          resource.totalProgress += document.progress * 100
          if (document.completed) {
            resource.completedCount++
          }
        })
      }
      
      // 处理作业
      if (resourceDetails.assignments) {
        resourceDetails.assignments.forEach(assignment => {
          const key = `assignment_${assignment.id}`
          if (!resourceMap.has(key)) {
            resourceMap.set(key, {
              id: assignment.id,
              title: assignment.title,
              type: 'assignment',
              completedCount: 0,
              totalStudents: studentCount,
              totalProgress: 0
            })
          }
          const resource = resourceMap.get(key)
          resource.totalProgress += (assignment.score_rate || 0) * 100
          if (assignment.completed) {
            resource.completedCount++
          }
        })
      }
    }
  })

  // 计算平均完成率并格式化数据
  resourceCompletionStats.value = Array.from(resourceMap.values()).map(resource => {
    const avgCompletion = Math.round(resource.totalProgress / studentCount)
    
    console.log(`${getResourceTypeName(resource.type)} ${resource.title}:`)
    console.log('- 平均完成度:', avgCompletion + '%')
    console.log('- 完成人数:', resource.completedCount + '/' + resource.totalStudents)
    
    return {
      ...resource,
      completion: avgCompletion
    }
  }).sort((a, b) => b.completion - a.completion) // 按完成率排序
}

onMounted(() => {
  initData()
})

// 头像相关方法
const getRandomColor = (seed) => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
  ];
  const index = seed.charCodeAt(0) % colors.length;
  return colors[index];
}

const getLetterAvatarStyle = (username) => {
  if (!username || typeof username !== 'string' || username.length === 0) {
    return {
      backgroundColor: '#9e9e9e',
      color: 'white',
      fontWeight: 'bold',
      fontSize: '16px',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      width: '100%',
      height: '100%'
    };
  }
  const color = getRandomColor(username);
  return {
    backgroundColor: color,
    color: 'white',
    fontWeight: 'bold',
    fontSize: '16px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    width: '100%',
    height: '100%'
  };
}

const handleAvatarError = (event, item) => {
  console.error('TeacherKnowledgeDetail avatar error for:', item.name || 'unknown');
  item.avatarLoadError = true;
  event.target.style.display = 'none';
}

const handleAvatarLoad = (event, item) => {
  console.log('TeacherKnowledgeDetail avatar loaded for:', item.name || 'unknown');
  item.avatarLoadError = false;
  event.target.style.display = 'block';
}

// 添加路由监听
watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (newId && newId !== oldId) {
      // 重置数据
      loading.value = true
      error.value = null
      students.value = []
      masteryInfo.value = null
      resourceCompletionStats.value = []
      // 重置展开状态
      showAllParentKeywords.value = false
      showAllChildKeywords.value = false
      stats.value = {
        studentCount: 0,
        averageMastery: 0,
        averageCompletion: computed(() => {
          if (resourceCompletionStats.value.length === 0) return 0
          const total = resourceCompletionStats.value.reduce((sum, item) => sum + item.completion, 0)
          return Math.round(total / resourceCompletionStats.value.length)
        })
      }
      
      // 重新加载数据
      await initData()
    }
  },
  { immediate: false }
)

// 修改跳转函数，添加过渡效果
const navigateToPoint = async (pointId) => {
  if (pointId === route.params.id) return
  
  loading.value = true
  try {
    await router.push({
      name: 'TeacherKnowledgeDetail',
      params: { id: pointId }
    })
  } catch (error) {
    console.error('导航失败:', error)
    loading.value = false
  }
}

// 查看学生详情
const viewStudentDetail = (student) => {
  console.log('查看学生详情:', student)
  // TODO: 实现查看学生详情的逻辑
}

// 发送消息给学生
const sendMessage = (student) => {
  console.log('发送消息给学生:', student)
  // TODO: 实现发送消息的逻辑
}
</script>

<style scoped>
.teacher-knowledge-detail {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.pa-4 {
  width: 100%;
}

.main-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
  background-color: white;
}

.main-card > .v-card-text {
  overflow-y: auto;
  flex: 1;
}

/* 顶部卡片行样式 */
.v-row {
  margin: 0;
}

/* 左侧知识点卡片样式 */
.v-col-md-8 .v-card {
  height: 100%;
  margin-bottom: 0;
}

/* 右上角卡片样式 */
.v-col-md-4 .v-card {
  height: 100%;
  margin-bottom: 0;
}

/* 学生部分样式 */
.student-section {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* 学生表格样式 */
.student-table {
  border-radius: 0;
}

:deep(.v-data-table) {
  background-color: transparent;
}

:deep(.v-data-table-header) {
  background-color: #f8f9fa;
}

:deep(.v-data-table-header th) {
  font-weight: 600;
  color: #212529;
  white-space: nowrap;
}

:deep(.v-data-table-footer) {
  background-color: #fff;
}

/* 图表容器样式 */
.chart-container {
  position: relative;
  height: 320px;
  margin-top: 24px;
  padding-left: 40px;
  padding-bottom: 30px;
}

.y-axis {
  position: absolute;
  left: 0;
  top: 0;
  height: 200px;
  width: 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.y-axis-label {
  position: relative;
  width: calc(100% + 280px);
  display: flex;
  align-items: center;
  height: 1px;
}

.y-axis-label .label {
  font-size: 12px;
  color: rgba(0,0,0,0.6);
  min-width: 36px;
  text-align: right;
  padding-right: 8px;
  flex-shrink: 0;
  transform: translateY(-50%);
  white-space: nowrap;
}

.y-axis-label .grid-line {
  flex-grow: 1;
  height: 1px;
  background: rgba(0,0,0,0.08);
  border: none;
}

.materials-chart {
  height: 200px;
  position: relative;
  z-index: 1;
  margin-bottom: 0;
  display: flex;
  align-items: flex-end;
  padding: 0 20px;
  gap: 4px;
}

.chart-bar-wrapper {
  flex: 1;
  min-width: 30px;
  max-width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.chart-bar-container {
  width: 16px;
  height: 200px;
  position: relative;
  display: flex;
  align-items: flex-end;
  margin: 0 auto;
}

.chart-bar {
  position: absolute;
  bottom: 0;
  width: 100%;
  border-radius: 8px 8px 0 0;
  transition: height 0.3s ease;
}

.chart-value {
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  color: rgba(0,0,0,0.87);
}

.chart-label {
  position: absolute;
  bottom: -60px;
  width: 100%;
  text-align: center;
  color: rgba(0,0,0,0.6);
  font-weight: 500;
  font-size: 12px;
  line-height: 1.4;
  white-space: normal;
  word-break: break-word;
  padding: 0 2px;
  max-height: none;
  overflow: visible;
}

/* 响应式优化 */
@media (max-width: 600px) {
  :deep(.v-data-table) {
    width: 100%;
    overflow-x: auto;
  }
}

/* 添加过渡动画样式 */
.v-fade-transition-enter-active,
.v-fade-transition-leave-active {
  transition: opacity 0.3s ease;
}

.v-fade-transition-enter-from,
.v-fade-transition-leave-to {
  opacity: 0;
}

.v-slide-x-transition-enter-active,
.v-slide-x-transition-leave-active {
  transition: transform 0.3s ease-in-out;
}

.v-slide-x-transition-enter-from {
  transform: translateX(-20px);
  opacity: 0;
}

.v-slide-x-transition-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

.v-slide-y-transition-enter-active,
.v-slide-y-transition-leave-active {
  transition: transform 0.3s ease-in-out;
}

.v-slide-y-transition-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.v-slide-y-transition-leave-to {
  transform: translateY(-20px);
  opacity: 0;
}

/* 字母头像样式 */
.letter-avatar {
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  transition: all 0.3s ease;
}

.letter-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* 展开/收起按钮样式 */
.v-btn--variant-text {
  text-transform: none;
  font-weight: 500;
  transition: all 0.2s ease;
}

.v-btn--variant-text:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

/* 知识点标签样式优化 */
.v-chip--variant-outlined {
  cursor: pointer;
  transition: all 0.2s ease;
}

.v-chip--variant-outlined:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>