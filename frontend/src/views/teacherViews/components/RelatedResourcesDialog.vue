<template>
  <v-dialog v-model="dialog" max-width="800px">
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between pa-6">
        <div class="d-flex align-center">
          <v-icon :color="getResourceIconColor(resourceType)" size="large" class="mr-3">
            {{ getResourceIcon(resourceType) }}
          </v-icon>
          <span class="text-h5 font-weight-bold">{{ dialogTitle }}</span>
        </div>
        <v-btn icon @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-6">
        <!-- 视频资源列表 -->
        <div v-if="resourceType === 'video' && resources.length > 0">
          <v-list>
            <v-list-item
              v-for="video in resources"
              :key="video.id"
              class="mb-3 rounded-lg"
              variant="outlined"
              @click="navigateToVideo(video.id)"
            >
              <template #prepend>
                <v-avatar color="info" size="48">
                  <v-icon color="white">mdi-video</v-icon>
                </v-avatar>
              </template>
              
              <v-list-item-title class="font-weight-medium mb-1">
                {{ video.title || video.name }}
              </v-list-item-title>
              
              <v-list-item-subtitle class="text-caption">
                <div class="d-flex align-center mb-1">
                  <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
                  <span>{{ formatDuration(video.duration) }}</span>
                  <v-divider vertical class="mx-2"></v-divider>
                  <v-icon size="small" class="mr-1">mdi-eye</v-icon>
                  <span>{{ video.view_count || 0 }} 次观看</span>
                </div>
                <div v-if="video.description" class="text-truncate">
                  {{ video.description }}
                </div>
              </v-list-item-subtitle>
              
              <template #append>
                <v-btn icon variant="text" color="primary">
                  <v-icon>mdi-arrow-right</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
        </div>

        <!-- 文档资源列表 -->
        <div v-if="resourceType === 'document' && resources.length > 0">
          <v-list>
            <v-list-item
              v-for="document in resources"
              :key="document.id"
              class="mb-3 rounded-lg"
              variant="outlined"
              @click="navigateToDocument(document.id)"
            >
              <template #prepend>
                <v-avatar color="secondary" size="48">
                  <v-icon color="white">mdi-file-document</v-icon>
                </v-avatar>
              </template>
              
              <v-list-item-title class="font-weight-medium mb-1">
                {{ document.title || document.name }}
              </v-list-item-title>
              
              <v-list-item-subtitle class="text-caption">
                <div class="d-flex align-center mb-1">
                  <v-icon size="small" class="mr-1">mdi-file</v-icon>
                  <span>{{ getFileType(document.file_name || document.title) }}</span>
                  <v-divider vertical class="mx-2"></v-divider>
                  <v-icon size="small" class="mr-1">mdi-download</v-icon>
                  <span>{{ document.download_count || 0 }} 次下载</span>
                </div>
                <div v-if="document.description" class="text-truncate">
                  {{ document.description }}
                </div>
              </v-list-item-subtitle>
              
              <template #append>
                <v-btn icon variant="text" color="primary">
                  <v-icon>mdi-arrow-right</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
        </div>

        <!-- 题目资源列表 -->
        <div v-if="resourceType === 'question' && resources.length > 0">
          <v-list>
            <v-list-item
              v-for="(question, index) in resources"
              :key="question.id"
              class="mb-4 rounded-lg"
              variant="outlined"
              @click="showQuestionDetail(question)"
            >
              <template #prepend>
                <v-avatar color="warning" size="48">
                  <span class="text-white font-weight-bold">{{ index + 1 }}</span>
                </v-avatar>
              </template>
              
              <v-list-item-title class="font-weight-medium mb-2">
                {{ getQuestionTypeText(question.type || question.question_type) }}
              </v-list-item-title>
              
              <v-list-item-subtitle>
                <div class="question-content mb-2">
                  {{ truncateText(question.content || question.question_content, 100) }}
                </div>
                <div class="d-flex align-center text-caption">
                  <v-icon size="small" class="mr-1">mdi-star</v-icon>
                  <span>分值：{{ question.max_score || 0 }}分</span>
                  <v-divider vertical class="mx-2"></v-divider>
                  <v-icon size="small" class="mr-1">mdi-account-group</v-icon>
                  <span>{{ question.attempt_count || 0 }} 人作答</span>
                  <v-divider vertical class="mx-2"></v-divider>
                  <v-icon size="small" class="mr-1">mdi-book-open-variant</v-icon>
                  <span>{{ question.assignment_title || '未知作业' }}</span>
                </div>
              </v-list-item-subtitle>
              
              <template #append>
                <v-btn 
                  v-if="question.assignment_id"
                  icon 
                  variant="text" 
                  color="secondary"
                  @click.stop="navigateToAssignment(question.assignment_id)"
                  title="查看作业"
                >
                  <v-icon>mdi-book-open-variant</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
        </div>

        <!-- 空状态 -->
        <div v-if="resources.length === 0" class="text-center pa-8">
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-inbox-outline</v-icon>
          <div class="text-h6 text-grey-darken-1 mb-2">暂无{{ getResourceTypeName(resourceType) }}</div>
          <div class="text-body-2 text-grey">该知识点暂无相关{{ getResourceTypeName(resourceType) }}资源</div>
        </div>
      </v-card-text>

      <v-card-actions class="pa-6 pt-0">
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="outlined" @click="closeDialog">
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- 题目详情弹窗 -->
    <v-dialog v-model="questionDetailDialog" max-width="600px">
      <v-card v-if="selectedQuestion">
        <v-card-title class="d-flex align-center justify-space-between pa-4">
          <div class="d-flex align-center">
            <v-icon color="warning" class="mr-2">mdi-help-circle</v-icon>
            <span class="text-h6">{{ getQuestionTypeText(selectedQuestion.type || selectedQuestion.question_type || 'essay') }}</span>
          </div>
          <v-btn icon @click="questionDetailDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-card-text class="pa-4">
          <!-- 题目内容 -->
          <div class="mb-4">
            <div class="text-subtitle-1 font-weight-medium mb-2">题目内容：</div>
            <div class="text-body-1 pa-3 bg-grey-lighten-5 rounded">
              {{ selectedQuestion.content || selectedQuestion.question_content }}
            </div>
          </div>

          <!-- 参考答案 -->
          <div v-if="selectedQuestion.reference_answer" class="mb-4">
            <div class="text-subtitle-1 font-weight-medium mb-2">参考答案：</div>
            <div class="text-body-1 pa-3 bg-success-lighten-5 rounded">
              {{ selectedQuestion.reference_answer }}
            </div>
          </div>

          <!-- 解析 -->
          <div v-if="selectedQuestion.explanation" class="mb-4">
            <div class="text-subtitle-1 font-weight-medium mb-2">解析：</div>
            <div class="text-body-1 pa-3 bg-info-lighten-5 rounded">
              {{ selectedQuestion.explanation }}
            </div>
          </div>

          <!-- 题目信息 -->
          <v-divider class="my-4"></v-divider>
          <div class="d-flex justify-space-between text-caption text-grey-darken-1">
            <span>分值：{{ selectedQuestion.max_score || 0 }}分</span>
            <span>难度：{{ getDifficultyText(selectedQuestion.difficulty || selectedQuestion.difficulty_level || 1) }}</span>
            <span>{{ selectedQuestion.attempt_count || 0 }} 人作答</span>
          </div>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="outlined" @click="questionDetailDialog = false">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 定义题目类型接口
interface Question {
  id: string
  question_type?: 'single' | 'multiple' | 'blank' | 'essay'
  type?: 'single' | 'multiple' | 'blank' | 'essay'
  question_content?: string
  content?: string
  reference_answer?: string
  explanation?: string
  max_score?: number
  difficulty?: number
  difficulty_level?: number
  attempt_count?: number
  assignment_id?: string
  assignment_title?: string
  course_id?: string
  course_name?: string
  weight?: number
  user_answer?: {
    answered: boolean
    is_correct?: boolean
    score?: number
    submit_time?: string
  }
}

// Props
interface Props {
  modelValue: boolean
  resourceType: 'video' | 'document' | 'question'
  resources: any[]
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  resourceType: 'video',
  resources: () => []
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

// 响应式数据
const questionDetailDialog = ref(false)
const selectedQuestion = ref<Question | null>(null)

// 计算属性
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => {
  const count = props.resources.length
  const typeName = getResourceTypeName(props.resourceType)
  return `${count}个${typeName}资源`
})

// 方法
const closeDialog = () => {
  dialog.value = false
}

const getResourceIcon = (type: string) => {
  const icons: Record<string, string> = {
    'video': 'mdi-video',
    'document': 'mdi-file-document',
    'question': 'mdi-help-circle'
  }
  return icons[type] || 'mdi-help-circle'
}

const getResourceIconColor = (type: string) => {
  const colors: Record<string, string> = {
    'video': 'info',
    'document': 'secondary',
    'question': 'warning'
  }
  return colors[type] || 'primary'
}

const getResourceTypeName = (type: string) => {
  const names: Record<string, string> = {
    'video': '视频',
    'document': '文档',
    'question': '题目'
  }
  return names[type] || '未知'
}

const getQuestionTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '问答题'
  }
  return typeMap[type] || '未知题型'
}

const getDifficultyText = (difficulty: number) => {
  if (difficulty <= 1) return '简单'
  if (difficulty <= 2) return '中等'
  return '困难'
}

const formatDuration = (seconds: number) => {
  if (!seconds) return '未知时长'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const getFileType = (fileName: string) => {
  if (!fileName) return '未知类型'
  const extension = fileName.split('.').pop()?.toLowerCase()
  const typeMap: Record<string, string> = {
    'pdf': 'PDF文档',
    'doc': 'Word文档',
    'docx': 'Word文档',
    'ppt': 'PowerPoint',
    'pptx': 'PowerPoint',
    'xls': 'Excel表格',
    'xlsx': 'Excel表格',
    'txt': '文本文件'
  }
  return typeMap[extension || ''] || `${extension?.toUpperCase()}文件`
}

const truncateText = (text: string, maxLength: number) => {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const navigateToVideo = (videoId: string) => {
  // 检查当前路由，如果是教师界面，跳转到教师视频页面
  const currentPath = router.currentRoute.value.path
  const currentRoute = router.currentRoute.value
  
  // 尝试从当前路由获取课程ID
  let courseId = currentRoute.params.courseId || currentRoute.query.course_id
  
  // 如果路由中没有课程ID，尝试从视频数据中获取
  if (!courseId) {
    const video = props.resources.find(v => v.id === videoId)
    if (video && video.course_id) {
      courseId = video.course_id
      console.log('从视频数据中获取到课程ID:', courseId)
    }
  }
  
  console.log('视频跳转调试信息:', {
    videoId,
    currentPath,
    courseId,
    isTeacher: currentPath.includes('/teacher')
  })
  
  if (courseId) {
    // 有课程ID，跳转到视频播放页面（教师端和学生端都使用相同的播放页面）
    console.log('跳转到视频播放页面:', `/course/${courseId}/video/${videoId}`)
    router.push(`/course/${courseId}/video/${videoId}`)
  } else {
    // 没有课程ID，跳转到课程首页
    console.log('没有课程ID，跳转到课程首页')
    router.push('/all-courses')
  }
  closeDialog()
}

const navigateToDocument = (documentId: string) => {
  // 检查当前路由，如果是教师界面，跳转到教师文档页面
  const currentPath = router.currentRoute.value.path
  const currentRoute = router.currentRoute.value
  
  // 尝试从当前路由获取课程ID
  let courseId = currentRoute.params.courseId || currentRoute.query.course_id
  
  // 如果路由中没有课程ID，尝试从文档数据中获取
  if (!courseId) {
    const document = props.resources.find(d => d.id === documentId)
    if (document && document.course_id) {
      courseId = document.course_id
      console.log('从文档数据中获取到课程ID:', courseId)
    }
  }
  
  console.log('文档跳转调试信息:', {
    documentId,
    currentPath,
    courseId,
    isTeacher: currentPath.includes('/teacher')
  })
  
  if (courseId) {
    // 有课程ID，跳转到文档查看页面（教师端和学生端都使用相同的查看页面）
    console.log('跳转到课程文档页面:', `/course/${courseId}/document/${documentId}`)
    router.push(`/course/${courseId}/document/${documentId}`)
  } else {
    // 没有课程ID，跳转到文档查看页面
    console.log('跳转到文档查看页面:', `/document/${documentId}`)
    router.push(`/document/${documentId}`)
  }
  closeDialog()
}

const showQuestionDetail = (question: Question) => {
  selectedQuestion.value = question
  questionDetailDialog.value = true
}

const navigateToAssignment = (assignmentId: string) => {
  console.log('作业跳转调试信息:', {
    assignmentId,
    currentPath: router.currentRoute.value.path
  })
  
  // 跳转到作业批改页面
  console.log('跳转到作业批改页面:', `/assignments/${assignmentId}/mark`)
  router.push(`/assignments/${assignmentId}/mark`)
  closeDialog()
}
</script>

<style scoped>
.question-content {
  line-height: 1.6;
  color: var(--v-text-primary);
}
</style> 