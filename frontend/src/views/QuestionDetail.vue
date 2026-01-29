<template>
  <div class="question-detail-page">
    <v-container>
      <!-- 返回按钮 -->
      <v-row class="mb-4">
        <v-col>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-arrow-left"
            @click="goBack()"
            class="mb-4"
          >
            返回
          </v-btn>
        </v-col>
      </v-row>

      <!-- 加载状态 -->
      <v-row v-if="loading" class="justify-center">
        <v-col cols="12" class="text-center">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
          <p class="mt-4">加载中...</p>
        </v-col>
      </v-row>

      <!-- 错误状态 -->
      <v-row v-else-if="error" class="justify-center">
        <v-col cols="12" md="8">
          <v-alert type="error" variant="tonal">
            {{ error }}
          </v-alert>
        </v-col>
      </v-row>

      <!-- 题目内容 -->
      <v-row v-else-if="question && !isUnmounted" class="justify-center">
        <v-col cols="12" md="10" lg="8">
          <v-card class="elevation-2">
            <v-card-title class="bg-primary text-white">
              <div class="d-flex align-center justify-space-between w-100">
                <div class="d-flex align-center">
                  <v-chip
                    :color="getTypeColor(question.type)"
                    variant="elevated"
                    size="small"
                    class="mr-3"
                  >
                    {{ getTypeText(question.type) }}
                  </v-chip>
                  <v-chip
                    :color="getDifficultyColor(question.difficulty)"
                    variant="elevated"
                    size="small"
                    class="mr-3"
                  >
                    {{ getDifficultyText(question.difficulty) }}
                  </v-chip>
                  <span class="text-body-2">分值: {{ question.maxScore || 100 }}分</span>
                </div>
              </div>
            </v-card-title>

            <v-card-text class="pa-6">
              <!-- 题目内容 -->
              <div class="mb-6">
                <h3 class="text-h6 mb-4">题目内容</h3>
                <div 
                  class="question-content text-body-1 mb-4" 
                  v-html="formatQuestionContent(question.content)"
                ></div>
              </div>

              <!-- 选择题选项 -->
              <div v-if="['single', 'multiple'].includes(question.type) && !isUnmounted" class="mb-6">
                <h4 class="text-subtitle-1 mb-3">选项</h4>
                <v-list class="pa-0">
                  <v-list-item
                    v-for="(option, index) in question.options"
                    :key="index"
                    class="option-item mb-2 pa-3"
                    :class="{ 'selected-option': selectedAnswers.includes(index) }"
                    @click="toggleAnswer(index)"
                  >
                    <template v-slot:prepend>
                      <div class="option-label mr-3">
                        {{ String.fromCharCode(65 + index) }}
                      </div>
                    </template>
                    <v-list-item-title class="text-body-1">
                      {{ cleanOptionText(option, index) }}
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </div>

              <!-- 填空题/问答题输入框 -->
              <div v-else-if="['blank', 'essay'].includes(question.type) && !isUnmounted" class="mb-6">
                <h4 class="text-subtitle-1 mb-3">请输入答案</h4>
                <v-textarea
                  v-model="textAnswer"
                  variant="outlined"
                  :placeholder="question.type === 'blank' ? '请输入填空答案' : '请输入详细答案'"
                  :rows="question.type === 'blank' ? 3 : 6"
                  counter
                  clearable
                ></v-textarea>
              </div>

              <!-- 操作按钮 -->
              <div class="d-flex flex-wrap gap-3 mb-4">
                <v-btn
                  color="primary"
                  variant="elevated"
                  :disabled="!hasAnswer"
                  @click="submitAnswer"
                >
                  提交答案
                </v-btn>
                <v-btn
                  color="secondary"
                  variant="outlined"
                  @click="clearAnswer"
                >
                  清空答案
                </v-btn>
                <v-btn
                  v-if="showExplanation"
                  color="info"
                  variant="outlined"
                  @click="toggleExplanation"
                >
                  {{ explanationVisible ? '隐藏解析' : '查看解析' }}
                </v-btn>
                <v-btn
                  v-if="['blank', 'essay'].includes(question.type) && hasAnswer"
                  color="purple"
                  variant="outlined"
                  :loading="aiAnalysisLoading"
                  @click="getAIAnalysis"
                >
                  AI解析
                </v-btn>
                <!-- 上一题按钮 -->
                <v-btn
                  v-if="hasPreviousQuestion && !isUnmounted"
                  :key="`prev-btn-${forceUpdateKey}`"
                  color="orange"
                  variant="elevated"
                  prepend-icon="mdi-arrow-left"
                  @click="goToPreviousQuestion"
                >
                  上一题 ({{ currentQuestionIndex + 1 }}/{{ recommendedQuestions.length }})
                </v-btn>
                <!-- 下一题按钮 -->
                <v-btn
                  v-if="hasNextQuestion && !isUnmounted"
                  :key="`next-btn-${forceUpdateKey}`"
                  color="success"
                  variant="elevated"
                  prepend-icon="mdi-arrow-right"
                  @click="goToNextQuestion"
                >
                  下一题 ({{ currentQuestionIndex + 1 }}/{{ recommendedQuestions.length }})
                </v-btn>
              </div>

              <!-- 题目解析 -->
              <v-expand-transition>
                <v-card
                  v-if="explanationVisible && question && question.explanation && !isUnmounted"
                  class="explanation-card mt-4"
                  variant="tonal"
                  color="info"
                >
                  <v-card-title class="text-h6">
                    <v-icon class="mr-2">mdi-lightbulb-outline</v-icon>
                    题目解析
                  </v-card-title>
                  <v-card-text>
                    <div v-html="question.explanation"></div>
                  </v-card-text>
                </v-card>
              </v-expand-transition>

              <!-- 相关知识点 -->
              <div v-if="question && question.keywords && question.keywords.length > 0 && !isUnmounted" class="mt-6">
                <h4 class="text-subtitle-1 mb-3">
                  相关知识点
                  <span v-if="question.keywords.length > 8 && !showAllKeywordsFlag" class="text-caption text-grey">
                    (显示前8个，共{{ question.keywords.length }}个)
                  </span>
                  <span v-else-if="question.keywords.length > 8 && showAllKeywordsFlag" class="text-caption text-grey">
                    (共{{ question.keywords.length }}个)
                  </span>
                </h4>
                <div class="d-flex flex-wrap gap-2">
                  <v-chip
                    v-for="keyword in displayedKeywords"
                    :key="keyword.id"
                    :color="getKeywordTagColor(keyword.category)"
                    variant="outlined"
                    size="small"
                    class="cursor-pointer"
                    @click="navigateToKeyword(keyword.id)"
                  >
                    {{ keyword.name }}
                  </v-chip>
                  <v-chip
                    v-if="question.keywords.length > 8 && !showAllKeywordsFlag"
                    color="grey"
                    variant="outlined"
                    size="small"
                    class="cursor-pointer"
                    @click="showAllKeywords"
                  >
                    +{{ question.keywords.length - 8 }}个更多
                  </v-chip>
                </div>
              </div>

              <!-- 所属课程 -->
              <div v-if="question && question.course && !isUnmounted" class="mt-4">
                <h4 class="text-subtitle-1 mb-3">所属课程</h4>
                <v-chip
                  color="primary"
                  variant="outlined"
                  class="cursor-pointer"
                  @click="navigateToCourse(question.course.id)"
                >
                  {{ question.course.name }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- 答案结果弹窗 -->
    <v-dialog v-model="resultDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="text-h5 d-flex align-center">
          <v-icon 
            :color="answerResult?.correct ? 'success' : 'error'" 
            class="mr-2"
            size="large"
          >
            {{ answerResult?.correct ? 'mdi-check-circle' : 'mdi-close-circle' }}
          </v-icon>
          {{ answerResult?.correct ? '答案正确' : '答案错误' }}
        </v-card-title>
        
        <v-card-text>
          <div class="mb-4">
            <p class="text-body-1 mb-2">{{ answerResult?.message }}</p>
            
            <!-- 显示得分 -->
            <div v-if="answerResult?.score !== undefined" class="mb-3">
              <v-chip 
                :color="getScoreColor(answerResult.score, answerResult.maxScore || 100)"
                variant="elevated"
              >
                得分: {{ answerResult.score }} / {{ answerResult.maxScore || 100 }}
              </v-chip>
            </div>
            
            <!-- 显示评语 -->
            <div v-if="answerResult?.comment" class="mb-3">
              <h4 class="text-subtitle-2 mb-2">评语:</h4>
              <p class="text-body-2">{{ answerResult.comment }}</p>
            </div>
            
            <!-- 显示解析 -->
            <div v-if="answerResult?.explanation" class="mb-3">
              <h4 class="text-subtitle-2 mb-2">解析:</h4>
              <div class="text-body-2" v-html="answerResult.explanation"></div>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="resultDialog = false">
            确定
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- AI解析弹窗 -->
    <v-dialog v-model="aiAnalysisDialog" max-width="800" persistent>
      <v-card>
        <v-card-title class="text-h5 d-flex align-center">
          <v-icon color="purple" class="mr-2" size="large">
            mdi-robot
          </v-icon>
          AI智能解析
        </v-card-title>
        
        <v-card-text>
          <div v-if="aiAnalysisLoading" class="text-center py-8">
            <v-progress-circular indeterminate color="purple" size="48"></v-progress-circular>
            <p class="mt-4 text-body-1">AI正在分析您的答案，请稍候...</p>
          </div>
          
          <div v-else-if="aiAnalysisResult">
            <!-- 显示得分 -->
            <div class="mb-4">
              <v-chip 
                :color="getScoreColor(aiAnalysisResult.score, question?.maxScore || 100)"
                variant="elevated"
                size="large"
              >
                AI评分: {{ aiAnalysisResult.score }} / {{ question?.maxScore || 100 }}
              </v-chip>
            </div>
            
            <!-- 显示反馈 -->
            <div v-if="aiAnalysisResult.feedback" class="mb-4">
              <h4 class="text-subtitle-1 mb-2">AI反馈:</h4>
              <v-card variant="tonal" color="info" class="pa-3">
                <p class="text-body-2 mb-0">{{ aiAnalysisResult.feedback }}</p>
              </v-card>
            </div>
            
            <!-- 显示建议 -->
            <div v-if="aiAnalysisResult.suggestions" class="mb-4">
              <h4 class="text-subtitle-1 mb-2">改进建议:</h4>
              <v-card variant="tonal" color="warning" class="pa-3">
                <p class="text-body-2 mb-0">{{ aiAnalysisResult.suggestions }}</p>
              </v-card>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="aiAnalysisDialog = false">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import questionBankService from '@/api/questionBankService'
import assignmentService from '@/api/assignmentService'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(true)
const error = ref('')
const question = ref<any>(null)
const selectedAnswers = ref<number[]>([])
const textAnswer = ref('')
const explanationVisible = ref(false)
const resultDialog = ref(false)
const answerResult = ref<any>(null)
const aiAnalysisDialog = ref(false)
const aiAnalysisResult = ref<any>(null)
const aiAnalysisLoading = ref(false)

// 组件卸载标志
const isUnmounted = ref(false)

// 个性化推荐相关数据
const recommendedQuestions = ref<any[]>([])
const currentQuestionIndex = ref(-1)
const forceUpdateKey = ref(0) // 添加强制更新键

// 知识点显示相关
const showAllKeywordsFlag = ref(false)

// 计算属性
const hasAnswer = computed(() => {
  if (isUnmounted.value || !question.value) return false
  
  if (['single', 'multiple'].includes(question.value?.type)) {
    return selectedAnswers.value.length > 0
  } else if (['blank', 'essay'].includes(question.value?.type)) {
    return textAnswer.value.trim().length > 0
  }
  return false
})

const showExplanation = computed(() => {
  if (isUnmounted.value || !question.value) return false
  return question.value?.explanation && question.value.explanation.trim().length > 0
})

const hasNextQuestion = computed(() => {
  if (isUnmounted.value) return false
  
  const hasQuestions = recommendedQuestions.value.length > 0
  const validIndex = currentQuestionIndex.value >= 0
  const hasNext = currentQuestionIndex.value < recommendedQuestions.value.length - 1
  
  return hasQuestions && validIndex && hasNext
})

const hasPreviousQuestion = computed(() => {
  if (isUnmounted.value) return false
  
  const hasQuestions = recommendedQuestions.value.length > 0
  const validIndex = currentQuestionIndex.value >= 0
  const hasPrev = currentQuestionIndex.value > 0
  
  return hasQuestions && validIndex && hasPrev
})

// 显示的知识点（限制数量）
const displayedKeywords = computed(() => {
  if (!question.value?.keywords) return []
  
  // 如果显示全部或者总数不超过8个，返回全部
  if (showAllKeywordsFlag.value || question.value.keywords.length <= 8) {
    return question.value.keywords
  }
  
  // 否则只返回前8个
  return question.value.keywords.slice(0, 8)
})

// 工具方法 - 移到前面定义
const getTypeColor = (type: string): string => {
  const colors: Record<string, string> = {
    single: 'blue',
    multiple: 'green',
    blank: 'orange',
    essay: 'purple'
  }
  return colors[type] || 'grey'
}

const getTypeText = (type: string): string => {
  const texts: Record<string, string> = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '问答题'
  }
  return texts[type] || type
}

const getDifficultyColor = (difficulty: string): string => {
  if (!difficulty) return 'grey'
  
  const normalizedDifficulty = difficulty.toLowerCase()
  const colors: Record<string, string> = {
    easy: 'green',
    medium: 'orange',
    hard: 'red',
    '简单': 'green',
    '中等': 'orange',
    '困难': 'red',
    '1': 'green',
    '2': 'orange', 
    '3': 'red',
    'low': 'green',
    'middle': 'orange',
    'high': 'red'
  }
  return colors[normalizedDifficulty] || 'grey'
}

const getDifficultyText = (difficulty: string): string => {
  if (!difficulty) return '未知'
  
  const normalizedDifficulty = difficulty.toLowerCase()
  const texts: Record<string, string> = {
    easy: '简单',
    medium: '中等',
    hard: '困难',
    '简单': '简单',
    '中等': '中等', 
    '困难': '困难',
    '1': '简单',
    '2': '中等',
    '3': '困难',
    'low': '简单',
    'middle': '中等',
    'high': '困难'
  }
  return texts[normalizedDifficulty] || difficulty
}

const formatQuestionContent = (content: string): string => {
  if (!content) return ''
  // 处理填空题的空格显示
  return content.replace(/_+/g, '<span class="blank-placeholder">_____</span>')
}

const cleanOptionText = (option: any, index: number): string => {
  if (!option) return ''
  
  // 处理不同的数据格式
  let optionStr = ''
  if (typeof option === 'string') {
    optionStr = option
  } else if (typeof option === 'object' && option.text) {
    optionStr = option.text
  } else if (typeof option === 'object' && option.content) {
    optionStr = option.content
  } else {
    optionStr = String(option)
  }
  
  const optionLetter = String.fromCharCode(65 + index)
  const patterns = [
    new RegExp(`^${optionLetter}\.\s*`, 'i'),
    new RegExp(`^${optionLetter}\\)\s*`, 'i'),
    new RegExp(`^${optionLetter}\s+`, 'i'),
    new RegExp(`^\(${optionLetter}\)\s*`, 'i'),
    new RegExp(`^\[${optionLetter}\]\s*`, 'i'),
    new RegExp(`^${index + 1}\.\s*`, 'i'),
    new RegExp(`^${index + 1}\\)\s*`, 'i')
  ]
  
  let cleaned = optionStr
  for (const pattern of patterns) {
    cleaned = cleaned.replace(pattern, '')
  }
  
  return cleaned.trim()
}

const getScoreColor = (score: number, maxScore: number): string => {
  const percentage = (score / maxScore) * 100
  if (percentage >= 90) return 'success'
  if (percentage >= 70) return 'warning'
  return 'error'
}

const goBack = (): void => {
  if (window.history.length > 1) {
    router.go(-1)
  } else {
    router.push('/')
  }
}

// 方法
const loadQuestionDetail = async (): Promise<void> => {
  if (isUnmounted.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    const questionId = route.params.id as string
    
    if (isUnmounted.value) return
    const response = await questionBankService.getQuestionDetail(questionId)
  
  if (isUnmounted.value) return
  if (response.data.code === 200) {
    question.value = response.data.data
    console.log('题目详情加载完成:', question.value?.title)
  } else {
    error.value = response.data.message || '获取题目详情失败'
  }
} catch (err: any) {
  console.error('获取题目详情失败:', err)
  if (isUnmounted.value) return
  error.value = err.response?.data?.message || '获取题目详情失败，请稍后重试'
} finally {
  if (!isUnmounted.value) {
    loading.value = false
  }
}
}

const toggleAnswer = (index: number): void => {
  if (isUnmounted.value || !question.value) return
  
  if (question.value?.type === 'single') {
    // 单选题：如果点击的是已选择的选项，则取消选择；否则选择该选项
    if (selectedAnswers.value.includes(index)) {
      selectedAnswers.value = [] // 取消选择
    } else {
      selectedAnswers.value = [index] // 选择新选项
    }
  } else if (question.value?.type === 'multiple') {
    const currentIndex = selectedAnswers.value.indexOf(index)
    if (currentIndex === -1) {
      selectedAnswers.value.push(index)
    } else {
      selectedAnswers.value.splice(currentIndex, 1)
    }
  }
}

const clearAnswer = (): void => {
  if (isUnmounted.value) return
  
  selectedAnswers.value = []
  textAnswer.value = ''
  explanationVisible.value = false
  answerResult.value = null
}

const submitAnswer = async (): Promise<void> => {
  if (!question.value || isUnmounted.value) return
  
  explanationVisible.value = true
  
  // 根据题目类型调用不同的接口
  if (['single', 'multiple'].includes(question.value?.type)) {
    // 选择题：调用选择题批改接口
    if (isUnmounted.value) return
    await handleChoiceQuestion()
  } else if (['blank', 'essay'].includes(question.value?.type)) {
    // 简答题：使用AI分析
    if (isUnmounted.value) return
    aiAnalysisLoading.value = true
    await getAIAnalysis()
    if (!isUnmounted.value) {
      aiAnalysisLoading.value = false
    }
  }
}

const toggleExplanation = (): void => {
  if (isUnmounted.value) return
  explanationVisible.value = !explanationVisible.value
}

const navigateToKeyword = (keywordId: string): void => {
  if (isUnmounted.value) return
  router.push(`/knowledge-point/${keywordId}`)
}

const navigateToCourse = (courseId: string): void => {
  if (isUnmounted.value) return
  router.push(`/course/${courseId}`)
}

const showAllKeywords = (): void => {
  showAllKeywordsFlag.value = true
}

// 根据知识点级别获取标签颜色
const getKeywordTagColor = (category: string): string => {
  switch (category) {
    case 'core_concept':
      return '#ff6b6b';  // 一级知识点 - 红色
    case 'main_module':
      return '#4ecdc4';  // 二级知识点 - 青色
    case 'specific_point':
      return '#45b7d1';  // 三级知识点 - 蓝色
    default:
      return '#cccccc';  // 默认颜色
  }
}

const goToNextQuestion = (): void => {
  if (isUnmounted.value) {
    console.log('组件已卸载，取消跳转')
    return
  }
  
  console.log('点击下一题按钮')
  console.log('hasNextQuestion:', hasNextQuestion.value)
  console.log('currentQuestionIndex:', currentQuestionIndex.value)
  console.log('recommendedQuestions length:', recommendedQuestions.value.length)
  console.log('recommendedQuestions:', recommendedQuestions.value)
  
  if (!hasNextQuestion.value) {
    console.log('没有下一题，退出')
    return
  }
  
  const nextIndex = currentQuestionIndex.value + 1
  const nextQuestion = recommendedQuestions.value[nextIndex]
  
  console.log('nextIndex:', nextIndex)
  console.log('nextQuestion:', nextQuestion)
  
  if (nextQuestion && !isUnmounted.value) {
    // 清空当前答案状态
    clearAnswer()
    
    // 确保推荐列表已保存到sessionStorage
    sessionStorage.setItem('recommendedQuestions', JSON.stringify(recommendedQuestions.value))
    
    console.log('准备跳转到:', `/question/${nextQuestion.id}`)
    console.log('跳转参数: from=personalized (推荐列表已保存到sessionStorage)')
    
    // 跳转到下一题，只传递from参数，推荐列表从sessionStorage获取
    router.push({
      path: `/question/${nextQuestion.id}`,
      query: {
        from: 'personalized'
      }
    }).then(() => {
      if (!isUnmounted.value) {
        console.log('路由跳转成功')
      }
    }).catch((error) => {
      if (!isUnmounted.value) {
        console.error('路由跳转失败:', error)
      }
    })
  } else {
    console.log('nextQuestion 为空或组件已卸载，无法跳转')
  }
}

const goToPreviousQuestion = (): void => {
  if (isUnmounted.value) {
    console.log('组件已卸载，取消跳转')
    return
  }
  
  console.log('点击上一题按钮')
  console.log('hasPreviousQuestion:', hasPreviousQuestion.value)
  console.log('currentQuestionIndex:', currentQuestionIndex.value)
  console.log('recommendedQuestions length:', recommendedQuestions.value.length)
  console.log('recommendedQuestions:', recommendedQuestions.value)
  
  if (!hasPreviousQuestion.value) {
    console.log('没有上一题，退出')
    return
  }
  
  const prevIndex = currentQuestionIndex.value - 1
  const prevQuestion = recommendedQuestions.value[prevIndex]
  
  console.log('prevIndex:', prevIndex)
  console.log('prevQuestion:', prevQuestion)
  
  if (prevQuestion && !isUnmounted.value) {
    // 清空当前答案状态
    clearAnswer()
    
    // 确保推荐列表已保存到sessionStorage
    sessionStorage.setItem('recommendedQuestions', JSON.stringify(recommendedQuestions.value))
    
    console.log('准备跳转到:', `/question/${prevQuestion.id}`)
    console.log('跳转参数: from=personalized (推荐列表已保存到sessionStorage)')
    
    // 跳转到上一题，只传递from参数，推荐列表从sessionStorage获取
    router.push({
      path: `/question/${prevQuestion.id}`,
      query: {
        from: 'personalized'
      }
    }).then(() => {
      if (!isUnmounted.value) {
        console.log('路由跳转成功')
      }
    }).catch((error) => {
      if (!isUnmounted.value) {
        console.error('路由跳转失败:', error)
      }
    })
  } else {
    console.log('prevQuestion 为空或组件已卸载，无法跳转')
  }
}

const handleChoiceQuestion = async (): Promise<void> => {
  if (!hasAnswer.value || isUnmounted.value) return
  
  try {
    // 准备选择题答案数据
    let studentAnswer
    if (question.value?.type === 'single') {
      studentAnswer = selectedAnswers.value[0] // 单选题取第一个选中的选项
    } else {
      studentAnswer = selectedAnswers.value // 多选题取所有选中的选项
    }
    
    // 处理options格式，确保包含isCorrect字段
    let formattedOptions = []
    if (question.value?.options) {
      formattedOptions = question.value.options.map((option: any, index: number) => {
        if (typeof option === 'string') {
          // 如果是字符串格式，需要根据answers字段确定正确答案
          const correctAnswers = question.value?.answers || ''
          const optionLetter = String.fromCharCode(65 + index) // A, B, C, D...
          
          // 处理多种答案格式："A"、"A,B"、"AB"等
          let isCorrect = false
          if (correctAnswers && correctAnswers.trim()) {
            // 移除空格并转为大写
            const cleanAnswers = correctAnswers.replace(/\s/g, '').toUpperCase()
            // 检查是否包含当前选项字母
            isCorrect = cleanAnswers.includes(optionLetter) || 
                       cleanAnswers.split(',').includes(optionLetter) ||
                       cleanAnswers.split('').includes(optionLetter)
          }
          
          return {
            content: option,
            isCorrect: isCorrect
          }
        } else if (typeof option === 'object') {
          // 如果已经是对象格式，直接使用
          // 确保对象包含必要的字段
          return {
            content: option.content || option.text || option,
            isCorrect: option.isCorrect || option.is_correct || false
          }
        }
        return { content: option, isCorrect: false }
      })
    }
    
    // 检查是否有正确答案
    const hasCorrectAnswer = formattedOptions.some(option => option.isCorrect)
    if (!hasCorrectAnswer) {
      // 如果没有正确答案，显示错误信息
      if (isUnmounted.value) return
      answerResult.value = {
        correct: false,
        message: '题目配置错误：未找到正确答案',
        explanation: question.value?.explanation || '',
        comment: '该题目的正确答案配置有误，请联系管理员',
        score: 0,
        maxScore: question.value?.maxScore || 100
      }
      resultDialog.value = true
      return
    }
    
    if (isUnmounted.value) return
    const response = await assignmentService.gradeChoiceQuestion({
      question_type: question.value?.type,
      options: formattedOptions,
      student_answer: studentAnswer,
      max_score: question.value?.maxScore || 100
    })
    
    if (isUnmounted.value) return
    if (response.data.code === 200) {
      const result = response.data.data
      // 显示选择题结果弹窗，包含正确答案信息
      answerResult.value = {
        correct: result.is_correct || false,
        message: result.is_correct ? '恭喜您，答案正确！' : '很遗憾，答案不正确。',
        explanation: question.value?.explanation || '',
        comment: result.comment || '', // 包含正确答案的评语
        score: result.score || 0,
        maxScore: question.value?.maxScore || 100
      }
      resultDialog.value = true
    }
  } catch (err: any) {
    console.error('批改选择题失败:', err)
    // 显示错误信息
    if (!isUnmounted.value) {
      answerResult.value = {
        correct: false,
        message: '批改失败，请稍后重试',
        comment: '系统错误，请稍后重试'
      }
      resultDialog.value = true
    }
  }
}

const getAIAnalysis = async (): Promise<void> => {
  if (!hasAnswer.value || isUnmounted.value) return
  
  // 显示AI解析弹窗
  aiAnalysisDialog.value = true
  
  try {
    let userAnswer = ''
    if (['single', 'multiple'].includes(question.value?.type)) {
      userAnswer = selectedAnswers.value.map(index => 
        String.fromCharCode(65 + index)
      ).join(', ')
    } else {
      userAnswer = textAnswer.value
    }
    
    if (isUnmounted.value) return
    const response = await assignmentService.gradeAnswer({
      question: question.value?.content || '',
      standard_answer: question.value?.answers || '',
      student_answer: userAnswer,
      score_full: question.value?.maxScore || 100,
      question_id: question.value?.id
    })
    
    if (isUnmounted.value) return
    if (response.data.code === 200) {
      aiAnalysisResult.value = {
        score: response.data.data.score || 0,
        feedback: response.data.data.feedback || response.data.data.comment || '',
        suggestions: response.data.data.suggestions || ''
      }
    }
  } catch (err: any) {
    console.error('获取AI解析失败:', err)
    // 发生错误时关闭弹窗
    if (!isUnmounted.value) {
      aiAnalysisDialog.value = false
    }
  }
}

// 处理推荐列表的通用函数
const handleRecommendedQuestions = () => {
  if (isUnmounted.value) return
  
  if (route.query.from === 'personalized') {
    try {
      // 从sessionStorage获取推荐列表
      const stored = sessionStorage.getItem('recommendedQuestions')
      
      if (stored) {
        const questions = JSON.parse(stored)
        recommendedQuestions.value = questions
        const currentId = route.params.id as string
        
        // 支持字符串和数字ID的匹配
        currentQuestionIndex.value = questions.findIndex((q: any) => {
          return String(q.id) === String(currentId) || q.id === currentId
        })
        
        console.log('推荐列表加载完成，当前索引:', currentQuestionIndex.value, '总数:', questions.length)
        
        // 强制触发组件更新
        nextTick(() => {
          if (!isUnmounted.value) {
            forceUpdateKey.value++
          }
        })
      }
    } catch (error) {
      console.error('从sessionStorage解析推荐题目列表失败:', error)
    }
  } else {
    // 清除推荐列表
    recommendedQuestions.value = []
    currentQuestionIndex.value = -1
    sessionStorage.removeItem('recommendedQuestions')
  }
}

// 监听路由变化
const stopWatchingRoute = watch(
  () => route.params.id,
  (newId, oldId) => {
    if (isUnmounted.value) return
    if (newId && newId !== oldId) {
      console.log('路由参数变化，重新加载题目:', newId)
      // 先处理推荐列表，再加载题目详情
      handleRecommendedQuestions()
      loadQuestionDetail()
    }
  }
)

// 监听路由查询参数变化
const stopWatchingQuery = watch(
  () => route.query.from,
  (newFrom, oldFrom) => {
    if (isUnmounted.value) return
    if (newFrom !== oldFrom) {
      console.log('路由from参数变化，重新处理推荐列表')
      handleRecommendedQuestions()
    }
  }
)

// 生命周期
onMounted(() => {
  console.log('组件挂载，开始处理推荐列表和加载题目详情')
  
  // 如果没有推荐列表且不是从个性化推荐进入，创建一个测试用的推荐列表
  if (!route.query.from && !sessionStorage.getItem('recommendedQuestions')) {
    console.log('创建测试用的推荐列表')
    const currentId = route.params.id as string
    
    // 根据当前ID类型生成测试推荐列表
    let testRecommendedQuestions
    if (/^\d+$/.test(currentId)) {
      // 如果是纯数字ID
      const numId = parseInt(currentId)
      testRecommendedQuestions = [
        { id: numId - 1, title: '上一题测试', content: '测试上一题内容' },
        { id: numId, title: '当前题目', content: '当前题目内容' },
        { id: numId + 1, title: '下一题测试', content: '测试下一题内容' }
      ]
    } else {
      // 如果是UUID或其他格式ID，使用当前ID作为中间项
      testRecommendedQuestions = [
        { id: 'prev-' + currentId, title: '上一题测试', content: '测试上一题内容' },
        { id: currentId, title: '当前题目', content: '当前题目内容' },
        { id: 'next-' + currentId, title: '下一题测试', content: '测试下一题内容' }
      ]
    }
    
    sessionStorage.setItem('recommendedQuestions', JSON.stringify(testRecommendedQuestions))
    console.log('生成的测试推荐列表:', testRecommendedQuestions)
    
    // 更新路由查询参数为个性化推荐
    router.replace({
      path: route.path,
      query: { ...route.query, from: 'personalized' }
    })
  }
  
  // 先处理推荐列表
  handleRecommendedQuestions()
  // 再加载题目详情
  loadQuestionDetail()
})

// 组件卸载前清理
onBeforeUnmount(() => {
  isUnmounted.value = true
  // 停止所有watch监听器
  stopWatchingRoute()
  stopWatchingQuery()
})
</script>

<style scoped>
.question-detail-page {
  background: #f5f7fa;
  min-height: 100vh;
  padding-bottom: 40px;
}

.option-item {
  border: 2px solid transparent;
  border-radius: 8px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.option-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.selected-option {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-color: rgba(var(--v-theme-primary), 0.5);
}

.option-label {
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.blank-placeholder {
  color: #1976d2;
  font-weight: bold;
  text-decoration: underline;
  text-decoration-style: dashed;
}

.explanation-card {
  border-left: 4px solid #2196f3;
}

.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  opacity: 0.8;
}
</style>
