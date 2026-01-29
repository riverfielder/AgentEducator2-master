<template>
  <div class="knowledge-point-detail-page">
    <v-container fluid>
      <!-- 页面头部 -->
      <div class="d-flex align-center mb-4">
        <v-breadcrumbs :items="breadcrumbs" class="pa-0" style="font-size: 14px;">
          <template v-slot:divider>
            <v-icon>mdi-chevron-right</v-icon>
          </template>
        </v-breadcrumbs>
        <v-spacer></v-spacer>
        
        <!-- 跳转到知识图谱按钮 -->
        <v-btn
          color="primary"
          variant="outlined"
          size="small"
          prepend-icon="mdi-graph"
          @click="goToKnowledgeMap"
          class="mr-2"
        >
          查看知识图谱
        </v-btn>
        
        <v-btn
          color="primary"
          variant="flat"
          @click="refreshMastery"
          :loading="refreshing"
          size="small"
          prepend-icon="mdi-refresh"
        >
          刷新掌握程度
        </v-btn>
      </div>

      <!-- 导航历史 -->
      <div v-if="navigationHistory.length > 1" class="mb-4">
        <v-chip
          v-for="(point, index) in navigationHistory"
          :key="point.id"
          class="mr-2"
          :color="index === navigationHistory.length - 1 ? 'primary' : 'default'"
          label
          @click="navigateToKeyword(point.id)"
        >
          {{ point.name }}
          <v-icon v-if="index < navigationHistory.length - 1" end>mdi-menu-right</v-icon>
        </v-chip>
      </div>

      <!-- 知识点总览卡片 -->
      <v-card class="mb-5" variant="flat" border>
        <v-row no-gutters>
          <!-- 左侧：标题和描述 -->
          <v-col cols="12" md="7">
            <v-card-text class="pa-5">
              <h1 class="text-h4 font-weight-bold mb-3">{{ knowledgePoint?.name }}</h1>
              <v-chip v-if="knowledgePoint?.category" size="small" variant="tonal" color="info" class="mb-4">
                {{ getCategoryName(knowledgePoint.category) }}
              </v-chip>
              <p v-if="knowledgePoint?.description" class="text-body-1 text-medium-emphasis">
                {{ knowledgePoint.description }}
              </p>
            </v-card-text>
          </v-col>

          <!-- 右侧：掌握度分析 -->
          <v-col cols="12" md="5">
             <v-card-text class="d-flex align-center justify-center pa-5" style="height: 100%;">
                <v-progress-circular
                  :model-value="Math.round(((knowledgePoint?.mastery_level ?? masteryInfo?.mastery_level) || 0) * 100)"
                  :size="120"
                  :width="10"
                  :color="getMasteryColor((knowledgePoint?.mastery_level ?? masteryInfo?.mastery_level) || 0)"
                  class="mr-6"
                >
                  <div class="text-center">
                    <div class="text-h5 font-weight-bold">{{ Math.round(((knowledgePoint?.mastery_level ?? masteryInfo?.mastery_level) || 0) * 100) }}%</div>
                    <div class="text-caption">{{ getMasteryLabel((knowledgePoint?.mastery_level ?? masteryInfo?.mastery_level) || 0) }}</div>
                  </div>
                </v-progress-circular>
                <div class="flex-grow-1">
                  <div class="d-flex justify-space-between text-body-2 mb-2">
                    <span>教学材料</span>
                    <strong class="font-weight-medium">{{ Math.round(((knowledgePoint?.material_score ?? masteryInfo?.material_score) || 0) * 100) }}%</strong>
                  </div>
                   <v-progress-linear :model-value="Math.round(((knowledgePoint?.material_score ?? masteryInfo?.material_score) || 0) * 100)" color="blue" height="5" rounded class="mb-3"></v-progress-linear>
                  
                  <div class="d-flex justify-space-between text-body-2 mb-2">
                    <span class="d-flex align-center">
                      练习表现
                      <v-icon 
                        v-if="hasExercises === false" 
                        size="small" 
                        color="grey" 
                        class="ml-1"
                      >
                        mdi-information-outline
                      </v-icon>
                      <v-tooltip 
                        v-if="hasExercises === false"
                        activator="parent" 
                        location="top"
                      >
                        该知识点暂无练习题目，此维度不参与掌握度计算
                      </v-tooltip>
                    </span>
                    <strong class="font-weight-medium" :class="hasExercises === false ? 'text-grey' : ''">
                      {{ hasExercises === false ? '无作业' : Math.round(((knowledgePoint?.exercise_score ?? masteryInfo?.exercise_score) || 0) * 100) + '%' }}
                    </strong>
                  </div>
                  <v-progress-linear 
                    :model-value="hasExercises === false ? 0 : Math.round(((knowledgePoint?.exercise_score ?? masteryInfo?.exercise_score) || 0) * 100)" 
                    :color="hasExercises === false ? 'grey-lighten-3' : 'green'" 
                    height="5" 
                    rounded 
                    class="mb-3"
                  ></v-progress-linear>
                  
                  <div class="d-flex justify-space-between text-body-2 mb-2">
                    <span class="d-flex align-center">
                      子知识点
                      <v-icon 
                        v-if="hasSubKnowledge === false" 
                        size="small" 
                        color="grey" 
                        class="ml-1"
                      >
                        mdi-information-outline
                      </v-icon>
                      <v-tooltip 
                        v-if="hasSubKnowledge === false"
                        activator="parent" 
                        location="top"
                      >
                        该知识点无子知识点，此维度不参与掌握度计算
                      </v-tooltip>
                    </span>
                    <strong class="font-weight-medium" :class="hasSubKnowledge === false ? 'text-grey' : ''">
                      {{ hasSubKnowledge === false ? '无子知识点' : Math.round(((knowledgePoint?.child_contribution ?? masteryInfo?.child_contribution) || 0) * 100) + '%' }}
                    </strong>
                  </div>
                  <v-progress-linear 
                    :model-value="hasSubKnowledge === false ? 0 : Math.round(((knowledgePoint?.child_contribution ?? masteryInfo?.child_contribution) || 0) * 100)" 
                    :color="hasSubKnowledge === false ? 'grey-lighten-3' : 'orange'" 
                    height="5" 
                    rounded 
                    class="mb-3"
                  ></v-progress-linear>
                </div>
            </v-card-text>
          </v-col>
        </v-row>
      </v-card>

      <!-- 标签页内容 -->
      <v-card variant="flat" border>
        <v-tabs v-model="activeTab" color="primary" @update:model-value="handleTabClick">
          <v-tab value="mastery">掌握度详情</v-tab>
          <v-tab value="videos">相关视频</v-tab>
          <v-tab value="documents">相关文档</v-tab>
          <v-tab value="exercises">相关练习</v-tab>
          <v-tab value="relations">知识点关系</v-tab>
        </v-tabs>
        <v-divider></v-divider>
        <v-window v-model="activeTab">
          <!-- 掌握度详情标签页 -->
          <v-window-item value="mastery">
            <v-container fluid class="pa-4">
              <div class="text-h6 mb-4">掌握度计算说明</div>
              <v-alert
                variant="tonal"
                color="info"
                class="mb-4"
              >
                <div class="text-body-2">
                  您的掌握度基于以下维度动态计算，只有包含实际学习数据的维度才会参与计算：
                </div>
              </v-alert>
              
              <v-row>
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-text class="pa-4">
                      <div class="d-flex align-center mb-3">
                        <v-icon color="primary" class="mr-2">mdi-book-open-variant</v-icon>
                        <div class="text-h6">学习材料</div>
                      </div>
                      <div class="text-body-2 mb-2">
                        基于您观看视频和阅读文档的完成情况计算
                      </div>
                      <div class="text-caption text-grey">
                        此维度总是参与掌握度计算
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100" :class="hasExercises ? '' : 'bg-grey-lighten-5'">
                    <v-card-text class="pa-4">
                      <div class="d-flex align-center mb-3">
                        <v-icon :color="hasExercises ? 'success' : 'grey'" class="mr-2">mdi-star</v-icon>
                        <div class="text-h6" :class="hasExercises ? '' : 'text-grey'">作业表现</div>
                        <v-chip 
                          v-if="!hasExercises" 
                          size="x-small" 
                          variant="outlined" 
                          color="grey" 
                          class="ml-2"
                        >
                          不参与计算
                        </v-chip>
                      </div>
                      <div class="text-body-2 mb-2" :class="hasExercises ? '' : 'text-grey'">
                        {{ hasExercises ? '基于您完成作业题目的正确率和得分' : '该知识点暂无对应的作业题目' }}
                      </div>
                      <div class="text-caption text-grey">
                        {{ hasExercises ? '此维度参与掌握度计算' : '此维度不参与掌握度计算' }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
                
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100" :class="hasSubKnowledge ? '' : 'bg-grey-lighten-5'">
                    <v-card-text class="pa-4">
                      <div class="d-flex align-center mb-3">
                        <v-icon :color="hasSubKnowledge ? 'warning' : 'grey'" class="mr-2">mdi-sitemap</v-icon>
                        <div class="text-h6" :class="hasSubKnowledge ? '' : 'text-grey'">子知识点</div>
                        <v-chip 
                          v-if="!hasSubKnowledge" 
                          size="x-small" 
                          variant="outlined" 
                          color="grey" 
                          class="ml-2"
                        >
                          不参与计算
                        </v-chip>
                      </div>
                      <div class="text-body-2 mb-2" :class="hasSubKnowledge ? '' : 'text-grey'">
                        {{ hasSubKnowledge ? `基于 ${childKeywords.length} 个子知识点的掌握情况` : '该知识点无子知识点' }}
                      </div>
                      <div class="text-caption text-grey">
                        {{ hasSubKnowledge ? '此维度参与掌握度计算' : '此维度不参与掌握度计算' }}
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              
              <v-alert
                variant="tonal"
                color="success"
                class="mt-4"
              >
              </v-alert>
            </v-container>
          </v-window-item>
          <v-window-item value="videos">
            <v-container fluid class="pa-4">
              <div v-if="relatedVideos.length === 0" class="text-center pa-8 text-medium-emphasis">
                <v-icon size="48">mdi-video-off-outline</v-icon>
                <p class="mt-4">暂无相关视频</p>
              </div>
              <v-row v-else>
                <v-col v-for="video in relatedVideos" :key="video.id" cols="12" sm="6" md="4" lg="3">
                  <v-card class="video-card" @click="playVideo(video)" hover>
                    <v-img :src="video.cover_url || '/default-video-cover.jpg'" :alt="video.title" height="160" cover class="align-end">
                      <div class="d-flex justify-space-between align-center pa-2 image-overlay">
                        <v-chip size="small" color="black" label>{{ formatDuration(video.duration) }}</v-chip>
                      </div>
                    </v-img>
                    <v-card-text class="pt-3 pb-2">
                      <h3 class="video-title mb-1">{{ video.title }}</h3>
                      <div class="text-caption text-medium-emphasis">{{ video.course_name }}</div>
                    </v-card-text>
                    <v-card-actions class="px-3 pt-0 pb-3">
                       <v-progress-linear :model-value="video.user_progress * 100" height="5" rounded stream color="primary"></v-progress-linear>
                       <span class="text-caption font-weight-medium ml-2">{{ Math.round(video.user_progress * 100) }}%</span>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-window-item>
          
          <!-- 相关文档tab -->
          <v-window-item value="documents">
            <v-container fluid class="pa-4">
              <div v-if="related_documents.length === 0" class="text-center pa-8 text-medium-emphasis">
                <v-icon size="48">mdi-file-document-off-outline</v-icon>
                <p class="mt-4">暂无相关文档</p>
              </div>
              <v-row v-else>
                <v-col v-for="doc in related_documents" :key="doc.id" cols="12" sm="6" md="4" lg="3">
                  <v-card class="document-card" @click="viewDocument(doc)" hover>
                    <v-card-text class="pt-3 pb-2">
                      <h3 class="document-title mb-1">{{ doc.title }}</h3>
                      <div class="text-caption text-medium-emphasis">{{ doc.course_name }}</div>
                      <div class="text-caption">类型: {{ doc.file_type }} | 大小: {{ (doc.file_size / 1024 / 1024).toFixed(2) }}MB</div>
                      <div class="text-caption">上传时间: {{ formatDate(doc.upload_time) }}</div>
                    </v-card-text>
                    <v-card-actions class="px-3 pt-0 pb-3">
                      <v-progress-linear :model-value="doc.user_progress * 100" height="5" rounded stream color="primary"></v-progress-linear>
                      <span class="text-caption font-weight-medium ml-2">{{ Math.round(doc.user_progress * 100) }}%</span>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-window-item>

          <!-- 相关练习tab -->
          <v-window-item value="exercises">
            <v-container fluid class="pa-4">
              <div v-if="relatedQuestions.length === 0" class="text-center pa-8 text-medium-emphasis">
                <v-icon size="48">mdi-clipboard-text-off-outline</v-icon>
                <p class="mt-4">暂无相关练习</p>
              </div>
              <v-row v-else>
                <v-col v-for="question in relatedQuestions" :key="question.id" cols="12" sm="6" md="4" lg="3">
                  <v-card class="exercise-card" @click="viewExercise(question)" hover>
                    <v-card-text class="pt-3 pb-2">
                      <div class="d-flex align-center mb-2">
                        <v-chip size="small" :color="getDifficultyType(question.difficulty_level)" class="mr-2">难度: {{ question.difficulty_level }}</v-chip>
                        <span class="text-caption">{{ question.assignment_title }}</span>
                      </div>
                      <div class="exercise-content mb-2">{{ question.content }}</div>
                      <div class="text-caption text-medium-emphasis">所属课程: {{ question.course_name }}</div>
                      <div class="text-caption">{{ question.user_answer.answered ? (question.user_answer.is_correct ? '已答对' : '已作答') : '未作答' }}</div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-container>
          </v-window-item>

          <!-- 知识点关系实现 -->
          <v-window-item value="relations">
            <v-container fluid class="pa-4">
              <div v-if="parentKeywords.length === 0 && childKeywords.length === 0" class="text-center pa-8 text-medium-emphasis">
                <v-icon size="48">mdi-graph-off</v-icon>
                <p class="mt-4">暂无知识点关系</p>
              </div>
              <div v-else>
                <!-- 父知识点 -->
                <div v-if="parentKeywords.length > 0" class="mb-6">
                  <h3 class="text-h6 font-weight-medium mb-3 d-flex align-center">
                    <v-icon color="blue" class="mr-2">mdi-arrow-up-bold-box-outline</v-icon>
                    父知识点
                  </h3>
                  <v-row>
                    <v-col v-for="keyword in parentKeywords" :key="keyword.id" cols="12" md="6" lg="4">
                      <v-card hover @click="navigateToKeyword(keyword.id)" variant="outlined">
                        <v-card-text>
                          <div class="d-flex justify-space-between align-start mb-2">
                            <h4 class="text-subtitle-1 font-weight-bold">{{ keyword.name }}</h4>
                            <v-chip size="small" variant="tonal" color="blue">{{ keyword.relation_type }}</v-chip>
                          </div>
                          <p class="text-body-2 text-medium-emphasis mb-3" style="min-height: 3em;">{{ keyword.description }}</p>
                          <div class="d-flex align-center">
                            <v-progress-linear :model-value="keyword.mastery_level * 100" height="6" rounded :color="getMasteryColor(keyword.mastery_level)"></v-progress-linear>
                            <span class="text-caption font-weight-medium ml-3">{{ Math.round(keyword.mastery_level * 100) }}%</span>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </div>
                <!-- 子知识点 -->
                <div v-if="childKeywords.length > 0">
                  <h3 class="text-h6 font-weight-medium mb-3 d-flex align-center">
                    <v-icon color="green" class="mr-2">mdi-arrow-down-bold-box-outline</v-icon>
                    子知识点
                  </h3>
                  <v-row>
                    <v-col v-for="keyword in childKeywords" :key="keyword.id" cols="12" md="6" lg="4">
                      <v-card hover @click="navigateToKeyword(keyword.id)" variant="outlined">
                        <v-card-text>
                          <div class="d-flex justify-space-between align-start mb-2">
                            <h4 class="text-subtitle-1 font-weight-bold">{{ keyword.name }}</h4>
                            <v-chip size="small" variant="tonal" color="green">{{ keyword.relation_type }}</v-chip>
                          </div>
                          <p class="text-body-2 text-medium-emphasis mb-3" style="min-height: 3em;">{{ keyword.description }}</p>
                          <div class="d-flex align-center">
                            <v-progress-linear :model-value="keyword.mastery_level * 100" height="6" rounded :color="getMasteryColor(keyword.mastery_level)"></v-progress-linear>
                            <span class="text-caption font-weight-medium ml-3">{{ Math.round(keyword.mastery_level * 100) }}%</span>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </div>
              </div>
            </v-container>
          </v-window-item>
          <!-- 其他标签页内容待实现 -->
        </v-window>
      </v-card>
    </v-container>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import knowledgeMapService from '@/api/knowledgeMapService' // 假设API服务已正确导出
import { useTeacherRole } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(true)
const refreshing = ref(false)
const activeTab = ref('mastery')

const knowledgePoint = ref(null)
const masteryInfo = ref(null)
const relatedVideos = ref([])
const related_documents = ref([])
const relatedQuestions = ref([])
const parentKeywords = ref([])
const childKeywords = ref([])
const learningSuggestions = ref([])
const navigationHistory = ref([])

// 分类映射
const categoryMap = {
  core_concept: '一级知识点',
  main_module: '二级知识点',
  specific_point: '三级知识点'
}

// 判断用户是否为教师
const isTeacher = useTeacherRole()

// 计算属性
const breadcrumbs = computed(() => [
  { title: '知识图谱', to: '/knowledge-map', disabled: false },
  { title: knowledgePoint.value?.name || '...', disabled: true }
])

// 分类名称转换函数
const getCategoryName = (category) => {
  return categoryMap[category] || category
}

// 方法
const loadKnowledgePointDetail = async () => {
  loading.value = true
  try {
    const response = await knowledgeMapService.getKnowledgePointDetail(route.params.id)
    if (response.data && response.data.code === 200) {
      const data = response.data.data
      knowledgePoint.value = data.keyword
      relatedVideos.value = data.related_videos || []
      related_documents.value = data.related_documents || []
      relatedQuestions.value = data.related_questions || []
      parentKeywords.value = data.parent_keywords || []
      childKeywords.value = data.child_keywords || []
      updateNavigationHistory(data.keyword)
      
      // 现在所有掌握程度数据都在一个接口中返回了，无需额外轮询
      console.log('知识点详情加载完成，包含完整掌握程度信息')
    } else {
      console.error('加载知识点详情失败:', response.data?.msg)
    }
  } catch (error) {
    console.error('加载知识点详情异常:', error)
  } finally {
    loading.value = false
  }
}

const loadLearningSuggestions = async () => {
  try {
    const response = await knowledgeMapService.getKnowledgePointLearningPath(route.params.id)
    
    if (response.data && response.data.code === 200) {
      learningSuggestions.value = response.data.data.suggestions || []
    } else {
      console.error('Failed to load learning suggestions:', response.data?.msg)
    }
  } catch (error) {
    console.error('Error loading learning suggestions:', error)
  }
}

const loadKnowledgePointMastery = async () => {
  // 掌握程度信息现在已经包含在详情接口中了
  // 这个方法保留用于手动刷新掌握程度
  try {
    const response = await knowledgeMapService.getKnowledgePointMastery(route.params.id)
    if (response.data && response.data.code === 200) {
      masteryInfo.value = response.data.data
      // 同时更新 knowledgePoint 中的掌握程度信息
      if (knowledgePoint.value) {
        knowledgePoint.value.mastery_level = response.data.data.mastery_level
        knowledgePoint.value.material_score = response.data.data.material_progress
        knowledgePoint.value.exercise_score = response.data.data.exercise_score
        knowledgePoint.value.child_contribution = response.data.data.sub_knowledge_contribution
      }
    } else {
      console.error('加载掌握情况失败:', response.data?.msg)
    }
  } catch (error) {
    console.error('加载掌握情况异常:', error)
  }
}

const refreshMastery = async () => {
  try {
    refreshing.value = true
    
    // 重新加载知识点详情，获取最新的掌握程度信息
    const detailResponse = await knowledgeMapService.getKnowledgePointDetail(route.params.id)
    if (detailResponse.data && detailResponse.data.code === 200) {
      const data = detailResponse.data.data
      // 更新知识点和相关数据
      knowledgePoint.value = data.keyword
      parentKeywords.value = data.parent_keywords || []
      childKeywords.value = data.child_keywords || []
    }
    
    // 也获取掌握程度接口的数据用于兼容
    const masteryResponse = await knowledgeMapService.getKnowledgePointMastery(route.params.id, true)
    if (masteryResponse.data && masteryResponse.data.code === 200) {
      masteryInfo.value = masteryResponse.data.data
    }
  } catch (error) {
    console.error('刷新掌握程度异常:', error)
  } finally {
    refreshing.value = false
  }
}

const handleTabClick = (tab) => {
  if (tab === 'suggestions' && learningSuggestions.value.length === 0) {
    loadLearningSuggestions()
  }
}

const playVideo = (video) => {
  router.push({
    path: `/course/${video.course_id}/video/${video.id}`,
    query: { from: 'knowledge-point' }
  })
}

const viewDocument = (document) => {
  router.push({
    path: `/course/${document.course_id}/document/${document.id}`,
    query: { from: 'knowledge-point' }
  })
}

const viewExercise = (question) => {
  // 跳转到自测界面，传递题目ID
  router.push({
    path: `/question/${question.id}`,
    query: { 
      from: 'knowledge-point',
      knowledgePointId: route.params.id 
    }
  })
}

const navigateToKeyword = (keywordId) => {
  if (route.params.id === keywordId) return
  
  // 根据用户角色跳转到不同的详情页面
  if (isTeacher.value) {
    router.push({ 
      name: 'TeacherKnowledgeDetail', 
      params: { id: keywordId } 
    })
  } else {
    router.push({ 
      name: 'KnowledgePointDetail', 
      params: { id: keywordId } 
    })
  }
}

// 跳转到知识图谱页面，并搜索当前知识点
const goToKnowledgeMap = () => {
  if (knowledgePoint.value?.name) {
    router.push({
      path: '/knowledge-map',
      query: {
        search: knowledgePoint.value.name
      }
    })
  } else {
    router.push('/knowledge-map')
  }
}

const handleSuggestion = (suggestion) => {
  switch (suggestion.type) {
    case 'video':
      router.push({ path: `/video/${suggestion.resource_id}` })
      break
    case 'exercise':
    case 'challenge':
      router.push({ path: `/question/${suggestion.resource_id}` })
      break
    case 'related_knowledge':
      navigateToKeyword(suggestion.resource_id)
      break
    default:
      console.info('功能开发中')
  }
}

const updateNavigationHistory = (point) => {
  if (!point) return
  const existingIndex = navigationHistory.value.findIndex(p => p.id === point.id)
  if (existingIndex !== -1) {
    navigationHistory.value = navigationHistory.value.slice(0, existingIndex + 1)
  } else {
    navigationHistory.value.push({
      id: point.id,
      name: point.name
    })
  }
}

// 工具方法
const getMasteryColor = (level) => {
  if (level >= 0.9) return '#67c23a'
  if (level >= 0.7) return '#409eff'
  if (level >= 0.5) return '#e6a23c'
  if (level >= 0.3) return '#f56c6c'
  return '#909399'
}

const getMasteryLabel = (level) => {
  if (level >= 0.9) return '优秀'
  if (level >= 0.7) return '良好'
  if (level >= 0.5) return '一般'
  if (level >= 0.3) return '较差'
  return '再接再厉'
}

const getDifficultyType = (level) => {
  if (level >= 4) return 'danger'
  if (level >= 3) return 'warning'
  return 'success'
}

const getPriorityType = (priority) => {
  switch (priority) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'info'
  }
}

const getPriorityLabel = (priority) => {
  switch (priority) {
    case 'high': return '高优先级'
    case 'medium': return '中优先级'
    case 'low': return '低优先级'
    default: return '普通'
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '00:00'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatReadingTime = (seconds) => {
  if (!seconds) return '0分钟'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  return `${minutes}分钟`
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 计算属性
const activeVideos = computed(() => relatedVideos.value.filter(video => !video.is_deleted))
const activeDocuments = computed(() => related_documents.value.filter(doc => !doc.is_deleted))

// 判断是否有作业和子知识点
const hasExercises = computed(() => {
  return relatedQuestions.value && relatedQuestions.value.length > 0
})

const hasSubKnowledge = computed(() => {
  return childKeywords.value && childKeywords.value.length > 0
})

// 监听路由参数变化
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId && newId !== oldId) {
      loadKnowledgePointDetail()
      // 掌握程度信息现在包含在详情接口中，无需单独调用
      activeTab.value = 'mastery'
    }
  }
)

onMounted(() => {
  loadKnowledgePointDetail()
  // 掌握程度信息现在包含在详情接口中，无需单独调用
})

// 可选：在组件卸载时清除历史记录
onUnmounted(() => {
  // navigationHistory.value = []
})
</script>

<style scoped>
.knowledge-point-detail-page {
  background-color: #f9fafb; /* 更柔和的背景色 */
}

.video-card {
  transition: all 0.2s ease-in-out;
  border: 1px solid #e0e0e0;
}

.video-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 15px rgba(0,0,0,0.08) !important;
}

.video-title {
  font-size: 1rem;
  font-weight: 500;
  line-height: 1.4;
  min-height: 2.8em; 
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2; /* 标准属性，提供更好的浏览器兼容性 */
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.image-overlay {
  background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 60%);
}
</style>