<template>
  <div class="personalized-recommend">
    <v-container fluid class="pa-4">
      <!-- 主标题和操作区 -->
      <div class="d-flex align-center mb-6">
        <div>
          <h1 class="text-h4 font-weight-bold mb-2">个性化学习路径推荐</h1>
          <p class="text-body-1 text-medium-emphasis">
            基于AI分析为您量身定制的学习推荐和成长路径
          </p>
        </div>
        <v-spacer></v-spacer>
        
        <!-- 缓存信息和刷新按钮 -->
        <div v-if="isLoggedIn" class="d-flex align-center gap-4">
          <div v-if="cacheInfo" class="text-center">
            <div class="text-caption text-medium-emphasis">
              <v-icon size="small" class="mr-1">{{ cacheInfo.is_from_cache ? 'mdi-clock-outline' : 'mdi-refresh' }}</v-icon>
              {{ formatCacheTime(cacheInfo.created_at) }}
            </div>
            <div v-if="cacheInfo.expires_in_seconds > 0" class="text-caption text-medium-emphasis">
              {{ formatExpiryTime(cacheInfo.expires_in_seconds) }}后过期
            </div>
          </div>
          
          <!-- 刷新按钮 -->
          <v-btn
            color="primary"
            variant="outlined"
            :loading="refreshing"
            @click="refreshRecommendations"
            prepend-icon="mdi-refresh"
          >
            重新推荐
          </v-btn>
        </div>
      </div>

      <!-- 标签页导航 -->
      <v-card class="content-card">
        <v-tabs 
          v-model="activeTab" 
          color="primary" 
          align-tabs="start"
          class="px-4"
        >
          <v-tab value="overview">
            <v-icon start>mdi-view-dashboard</v-icon>
            学习概览
          </v-tab>
          <v-tab value="growth-path">
            <v-icon start>mdi-map-marker-path</v-icon>
            学习路径
          </v-tab>
          <v-tab value="resources">
            <v-icon start>mdi-book-open-variant</v-icon>
            资源推荐
          </v-tab>
          <v-tab value="study-plan">
            <v-icon start>mdi-calendar-check</v-icon>
            学习计划
          </v-tab>
        </v-tabs>
        <v-divider></v-divider>

        <!-- 标签页内容 -->
        <v-window v-model="activeTab">
          <!-- 学习概览 Tab -->
          <v-window-item value="overview">
            <v-card-text class="pa-6">
              <!-- 用户掌握度概览 -->
              <v-row v-if="isLoggedIn && userMasteryOverview">
                <v-col cols="12">
                  <h3 class="text-h6 mb-4">
                    <v-icon start color="primary">mdi-chart-line</v-icon>
                    学习概况统计
                  </h3>
                </v-col>
                <!-- 学习进度统计 -->
                <v-col cols="12">
                  <v-row dense class="stats-flow">
                    <v-col cols="6" sm="3" class="stat-col">
                      <v-card class="stat-card" elevation="1" hover>
                        <v-card-text class="stat-card-content">
                          <div class="d-flex align-center">
                            <div class="stat-icon purple me-3">
                              <v-icon>mdi-book-open-page-variant</v-icon>
                            </div>
                            <div>
                              <div class="text-h5">{{ progressStats.activeCourses }}</div>
                              <div class="text-caption text-medium-emphasis">在学课程</div>
                            </div>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>

                    <v-col cols="6" sm="3" class="stat-col">
                      <v-card class="stat-card" elevation="1" hover>
                        <v-card-text class="stat-card-content">
                          <div class="d-flex align-center">
                            <div class="stat-icon blue me-3">
                              <v-icon>mdi-clock-outline</v-icon>
                            </div>
                            <div>
                              <div class="text-h5">{{ progressStats.studyHours }}</div>
                              <div class="text-caption text-medium-emphasis">学习时长(小时)</div>
                            </div>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>

                    <v-col cols="6" sm="3" class="stat-col">
                      <v-card class="stat-card" elevation="1" hover>
                        <v-card-text class="stat-card-content">
                          <div class="d-flex align-center">
                            <div class="stat-icon green me-3">
                              <v-icon>mdi-lightbulb-outline</v-icon>
                            </div>
                            <div>
                              <div class="text-h5">{{ progressStats.totalKnowledgePoints }}</div>
                              <div class="text-caption text-medium-emphasis">已学知识点</div>
                            </div>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>

                    <v-col cols="6" sm="3" class="stat-col">
                      <v-card class="stat-card" elevation="1" hover>
                        <v-card-text class="stat-card-content">
                          <div class="d-flex align-center">
                            <div class="stat-icon orange me-3">
                              <v-icon>mdi-chart-line</v-icon>
                            </div>
                            <div>
                              <div class="text-h5">{{ progressStats.avgMasteryLevel || '-' }}%</div>
                              <div class="text-caption text-medium-emphasis">平均掌握程度</div>
                            </div>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-col>
                  </v-row>
                </v-col>

                <!-- 课程进度列表 -->
                <v-col cols="12" v-if="progressCourses.length > 0" class="mt-4">
                  <v-card class="mb-4">
                    <v-card-title class="d-flex align-center py-4 px-6">
                      当前学习进度
                      <v-spacer></v-spacer>
                      <v-chip v-if="filteredProgressCourses.length > 0" size="small" color="primary" variant="tonal">
                        {{ filteredProgressCourses.length }} 门课程
                      </v-chip>
                    </v-card-title>
                    <v-divider></v-divider>
                    <v-card-text class="pa-6">
                      <v-text-field
                        v-model="searchProgress"
                        prepend-inner-icon="mdi-magnify"
                        label="搜索课程"
                        single-line
                        hide-details
                        density="compact"
                        variant="outlined"
                        class="search-field mb-4"
                        style="max-width: 300px"
                      ></v-text-field>

                      <v-list>
                        <v-list-item v-for="course in filteredProgressCourses" :key="course.id" class="mb-4">
                          <template v-slot:prepend>
                            <v-avatar size="48" color="grey-lighten-2">
                              <v-img v-if="course.image" :src="course.image" cover></v-img>
                              <v-icon v-else>mdi-book-open-variant</v-icon>
                            </v-avatar>
                          </template>
                          <v-list-item-title class="text-h6 mb-1">{{ course.name }}</v-list-item-title>
                          <v-list-item-subtitle>
                            <div class="progress-info d-flex align-center justify-space-between mb-2">
                              <span class="text-body-2">已完成 {{ course.completedLessons }}/{{ course.totalLessons }} 课时</span>
                              <span class="text-primary font-weight-bold">{{ course.progress }}%</span>
                            </div>
                            <v-progress-linear
                              :model-value="course.progress"
                              height="8"
                              rounded
                              :color="course.progress >= 80 ? 'success' : 'primary'"
                              bg-color="primary-lighten-4"
                            ></v-progress-linear>
                            <div class="course-meta d-flex align-center mt-2">
                              <v-chip size="small" class="mr-2" color="primary-lighten-4">
                                <v-icon start size="16">mdi-clock-outline</v-icon>
                                {{ course.lastStudyTime }}
                              </v-chip>
                              <v-chip v-if="course.remainingDays > 0" size="small" :color="course.remainingDays <= 7 ? 'error' : 'warning'">
                                <v-icon start size="16">mdi-calendar</v-icon>
                                剩余 {{ course.remainingDays }} 天
                              </v-chip>
                              <v-chip v-else size="small" color="success">
                                <v-icon start size="16">mdi-check-circle</v-icon>
                                长期有效
                              </v-chip>
                              <v-spacer></v-spacer>
                              <v-btn
                                color="primary"
                                variant="text"
                                @click="continueLearning(course.id)"
                              >
                                继续学习
                                <v-icon end>mdi-arrow-right</v-icon>
                              </v-btn>
                            </div>
                          </v-list-item-subtitle>
                        </v-list-item>
                      </v-list>
                    </v-card-text>
                  </v-card>
                </v-col>

                <v-col cols="12" md="8">
                </v-col>
                <v-col cols="12" md="4">
                </v-col>
              </v-row>

              <!-- 未登录状态 -->
              <div v-if="!isLoggedIn" class="text-center py-8">
                <v-icon size="80" color="grey-lighten-1" class="mb-4">mdi-account-circle</v-icon>
                <h3 class="text-h5 mb-4">开启个性化学习之旅</h3>
                <p class="text-body-1 text-medium-emphasis mb-6">
                  登录后，AI将为您量身定制专属的学习推荐和成长路径
                </p>
                <v-btn color="primary" size="large" @click="$router.push('/login')">
                  立即登录
                </v-btn>
              </div>
            </v-card-text>
          </v-window-item>

          <!-- 成长路径 Tab -->
          <v-window-item value="growth-path">
            <v-card-text class="pa-6">
              <div class="d-flex align-center mb-6">
                <h3 class="text-h6">
                  <v-icon start color="primary">mdi-map-marker-path</v-icon>
                  AI推荐的成长路径
                </h3>
                <v-spacer></v-spacer>
                <v-chip 
                  v-if="learningPaths.length > 0" 
                  color="success" 
                  variant="outlined"
                >
                  {{ learningPaths.length }} 个推荐路径
                </v-chip>
              </div>

              <v-timeline v-if="learningPaths.length > 0" align="start">
                <v-timeline-item
                  v-for="(path, index) in learningPaths"
                  :key="path.id"
                  :dot-color="path.color"
                  size="small"
                >
                  <template v-slot:opposite>
                    <div class="text-caption text-medium-emphasis">{{ path.duration }}</div>
                    <!-- 显示优先级和掌握度信息 -->
                    <div v-if="path.priorityScore" class="text-caption mt-1">
                      <v-chip 
                        size="x-small" 
                        :color="path.priorityScore > 0.7 ? 'error' : path.priorityScore > 0.4 ? 'warning' : 'success'"
                      >
                        {{ path.priorityScore > 0.7 ? '高优先级' : path.priorityScore > 0.4 ? '中优先级' : '低优先级' }}
                      </v-chip>
                    </div>
                    <div v-if="path.currentMastery !== undefined" class="text-caption mt-1">
                      当前掌握度: {{ Math.round(path.currentMastery * 100) }}%
                    </div>
                  </template>
                  
                  <!-- 右侧内容（竖线右边） -->
                  <v-card class="mb-4" :variant="index === 0 ? 'tonal' : 'outlined'" :color="index === 0 ? 'primary' : undefined">
                    <v-card-text class="pa-4">
                      <div class="d-flex align-center mb-2">
                        <div class="text-subtitle-1 font-weight-medium flex-grow-1">{{ path.title }}</div>
                        <v-chip size="small" :color="path.color" variant="outlined">
                          路径 {{ index + 1 }}
                        </v-chip>
                      </div>
                      <p class="text-body-2 text-medium-emphasis mb-3">{{ path.description }}</p>
                      
                      <!-- 学习收益展示 -->
                      <div v-if="path.learning_benefits && path.learning_benefits.length > 0" class="mb-3">
                        <div class="text-caption text-grey mb-2">
                          <v-icon size="small" class="mr-1">mdi-star-outline</v-icon>
                          学习收益:
                        </div>
                        <div class="d-flex flex-wrap gap-1">
                          <v-chip 
                            v-for="(benefit, idx) in path.learning_benefits" 
                            :key="idx"
                            size="small" 
                            color="success" 
                            variant="outlined"
                            class="text-caption"
                          >
                            {{ benefit }}
                          </v-chip>
                        </div>
                      </div>
                      
                      <!-- 显示基础信息 -->
                      <div v-if="path.sourceKeyword" class="text-caption text-grey mb-3">
                        <v-icon size="small" class="mr-1">mdi-school</v-icon>
                        基于已掌握知识点: {{ path.sourceKeyword }}
                        <span v-if="path.masteryLevel" class="ml-2">
                          (掌握度: {{ Math.round(path.masteryLevel * 100) }}%)
                        </span>
                      </div>
                      
                      <!-- 资源统计 -->
                      <div v-if="path.resources" class="d-flex gap-4 mb-3">
                        <div v-if="path.resources.videos.length > 0" class="text-caption">
                          <v-icon size="small" color="red" class="mr-1">mdi-video</v-icon>
                          {{ path.resources.videos.length }} 个视频
                        </div>
                        <div v-if="path.resources.documents.length > 0" class="text-caption">
                          <v-icon size="small" color="blue" class="mr-1">mdi-file-document</v-icon>
                          {{ path.resources.documents.length }} 个文档
                        </div>
                        <div v-if="path.resources.questions.length > 0" class="text-caption">
                          <v-icon size="small" color="green" class="mr-1">mdi-help-circle</v-icon>
                          {{ path.resources.questions.length }} 道练习
                        </div>
                      </div>
                      
                      <!-- 如果有关联的知识点和资源，显示操作按钮 -->
                      <div v-if="path.keywordId" class="d-flex gap-2">
                        <v-btn 
                          size="small" 
                          color="primary" 
                          variant="outlined"
                          @click="viewLearningResources(path)"
                          prepend-icon="mdi-book-open-variant"
                        >
                          查看学习资源
                        </v-btn>
                        <v-btn
                          size="small"
                          color="success"
                          variant="flat"
                          @click="router.push('/dynamic-training?keyword=' + path.title.replace('学习 ', ''))"
                        >
                          生成AI专项训练
                        </v-btn>
                        <v-btn 
                          size="small" 
                          color="success" 
                          variant="outlined"
                          @click="startLearning(path)"
                          prepend-icon="mdi-play"
                        >
                          开始学习
                        </v-btn>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-timeline-item>
              </v-timeline>

              <!-- 无推荐路径时的显示 -->
              <div v-else class="text-center py-8">
                <v-icon size="80" color="grey-lighten-1" class="mb-4">mdi-map-marker-path</v-icon>
                <h3 class="text-h6 mb-4">暂无推荐路径</h3>
                <p class="text-body-1 text-medium-emphasis mb-6">
                  {{ isLoggedIn ? 'AI正在分析您的学习情况，稍后将为您生成个性化路径' : '登录后获取专属学习路径' }}
                </p>
                <v-btn 
                  v-if="!isLoggedIn" 
                  color="primary" 
                  @click="$router.push('/login')"
                >
                  立即登录
                </v-btn>
                <v-btn 
                  v-else 
                  color="primary" 
                  variant="outlined"
                  @click="refreshRecommendations"
                  :loading="refreshing"
                >
                  重新生成推荐
                </v-btn>
              </div>
            </v-card-text>
          </v-window-item>

          <!-- 资源推荐 Tab -->
          <v-window-item value="resources">
            <v-card-text class="pa-6">
              <h3 class="text-h6 mb-6">
                <v-icon start color="primary">mdi-book-open-variant</v-icon>
                个性化资源推荐
              </h3>

              <!-- 资源分类展示 -->
              <v-row>
                <!-- 视频资源 -->
                <v-col cols="12" md="4">
                  <v-card height="300" class="d-flex flex-column">
                    <v-card-title class="bg-red-lighten-4">
                      <v-icon start color="red">mdi-video</v-icon>
                      推荐视频 ({{ getTotalVideos() }})
                    </v-card-title>
                    <v-card-text class="flex-grow-1 overflow-y-auto">
                      <div v-if="getRecommendedVideos().length > 0">
                        <div 
                          v-for="video in getRecommendedVideos().slice(0, 3)" 
                          :key="video.id" 
                          class="mb-3 cursor-pointer"
                          @click="goToVideo(video)"
                        >
                          <div class="text-subtitle-2 font-weight-medium">{{ video.title }}</div>
                          <div class="text-caption text-medium-emphasis">{{ video.course_name || '课程资源' }}</div>
                          <v-divider class="mt-2"></v-divider>
                        </div>
                        <v-btn 
                          v-if="getRecommendedVideos().length > 3"
                          variant="text" 
                          size="small" 
                          @click="activeTab = 'growth-path'"
                        >
                          查看全部 {{ getRecommendedVideos().length }} 个视频
                        </v-btn>
                      </div>
                      <div v-else class="text-center py-4">
                        <v-icon size="48" color="grey">mdi-video-off</v-icon>
                        <p class="text-caption text-grey mt-2">暂无推荐视频</p>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- 文档资源 -->
                <v-col cols="12" md="4">
                  <v-card height="300" class="d-flex flex-column">
                    <v-card-title class="bg-blue-lighten-4">
                      <v-icon start color="blue">mdi-file-document</v-icon>
                      推荐文档 ({{ getTotalDocuments() }})
                    </v-card-title>
                    <v-card-text class="flex-grow-1 overflow-y-auto">
                      <div v-if="getRecommendedDocuments().length > 0">
                        <div 
                          v-for="doc in getRecommendedDocuments().slice(0, 3)" 
                          :key="doc.id" 
                          class="mb-3 cursor-pointer"
                          @click="goToDocument(doc)"
                        >
                          <div class="text-subtitle-2 font-weight-medium">{{ doc.title }}</div>
                          <div class="text-caption text-medium-emphasis">{{ doc.course_name || '学习文档' }}</div>
                          <v-divider class="mt-2"></v-divider>
                        </div>
                        <v-btn 
                          v-if="getRecommendedDocuments().length > 3"
                          variant="text" 
                          size="small" 
                          @click="activeTab = 'growth-path'"
                        >
                          查看全部 {{ getRecommendedDocuments().length }} 个文档
                        </v-btn>
                      </div>
                      <div v-else class="text-center py-4">
                        <v-icon size="48" color="grey">mdi-file-document-off</v-icon>
                        <p class="text-caption text-grey mt-2">暂无推荐文档</p>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- 练习题 -->
                <v-col cols="12" md="4">
                  <v-card height="300" class="d-flex flex-column">
                    <v-card-title class="bg-green-lighten-4">
                      <v-icon start color="green">mdi-help-circle</v-icon>
                      配套练习 ({{ getTotalQuestions() }})
                    </v-card-title>
                    <v-card-text class="flex-grow-1 overflow-y-auto">
                      <div v-if="getRecommendedQuestions().length > 0">
                        <div 
                          v-for="question in getRecommendedQuestions().slice(0, 3)" 
                          :key="question.id" 
                          class="mb-3 cursor-pointer"
                          @click="goToQuestion(question)"
                        >
                          <div class="text-subtitle-2 font-weight-medium">
                            {{ question.title || question.content?.substring(0, 30) + '...' || '练习题' }}
                          </div>
                          <div class="text-caption text-medium-emphasis">
                            {{ question.difficulty || question.difficulty_level || '难度适中' }}
                          </div>
                          <v-divider class="mt-2"></v-divider>
                        </div>
                        <v-btn 
                          v-if="getRecommendedQuestions().length > 3"
                          variant="text" 
                          size="small" 
                          @click="activeTab = 'growth-path'"
                        >
                          查看全部 {{ getRecommendedQuestions().length }} 道练习
                        </v-btn>
                      </div>
                      <div v-else class="text-center py-4">
                        <v-icon size="48" color="grey">mdi-help-circle-outline</v-icon>
                        <p class="text-caption text-grey mt-2">暂无配套练习</p>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-window-item>

          <!-- 学习计划 Tab -->
          <v-window-item value="study-plan">
            <v-card-text class="pa-6">
              <h3 class="text-h6 mb-6">
                <v-icon start color="primary">mdi-calendar-check</v-icon>
                个人学习计划
              </h3>

              <!-- 学习计划内容 -->
              <v-row>
                <v-col cols="12" md="6">
                  <v-card>
                    <v-card-title>
                      <v-icon start>mdi-target</v-icon>
                      学习目标设置
                    </v-card-title>
                    <v-card-text>
                      <div class="mb-4">
                        <v-select
                          label="每天学习时长"
                          v-model="studyPlanSettings.dailyTime"
                          :items="[
                            { title: '15分钟', value: 15 },
                            { title: '20分钟', value: 20 },
                            { title: '30分钟', value: 30 },
                            { title: '45分钟', value: 45 },
                            { title: '60分钟', value: 60 },
                            { title: '90分钟', value: 90 },
                            { title: '120分钟', value: 120 },
                          ]"
                          item-title="title"
                          item-value="value"
                          variant="outlined"
                          density="compact"
                          class="mb-3"
                        ></v-select>
                        
                        <v-checkbox
                          v-model="studyPlanSettings.weekdays"
                          label="工作日学习"
                          class="my-0"
                          density="compact"
                        ></v-checkbox>
                        
                        <v-checkbox
                          v-model="studyPlanSettings.weekends"
                          label="双休日学习"
                          class="my-0"
                          density="compact"
                        ></v-checkbox>
                        

                        
                        <v-progress-linear 
                          :model-value="calculatePlanCompletion()"
                          color="primary"
                          height="8"
                          rounded
                          class="mb-2"
                        ></v-progress-linear>
                        
                        <div class="text-caption text-grey text-end">
                          可学习 {{ calculateCompletedResources() }}/{{ calculateTotalResources() }} 个资源
                        </div>
                      </div>
                      

                    </v-card-text>
                  </v-card>
                </v-col>
                <v-col cols="12" md="6">
                  <v-card v-if="studyPlan">
                    <v-card-title>
                      <v-icon start>mdi-calendar-check</v-icon>
                      智能分配学习计划
                      <v-chip class="ml-2" size="small" color="success">{{ studyPlan.totalDays }}天</v-chip>
                      <v-chip class="ml-2" size="small" color="info">{{ calculateTotalResources() }}个资源</v-chip>
                    </v-card-title>
                    <v-card-text style="max-height: 400px; overflow-y: auto;">
                      <v-timeline density="compact">
                        <v-timeline-item
                          v-for="(day, index) in studyPlan.dailyPlans"
                          :key="index"
                          size="small"
                          :dot-color="day.dayOfWeek.includes('周六') || day.dayOfWeek.includes('周日') ? 'orange' : 'primary'"
                        >
                          <div class="d-flex align-start mb-2">
                            <div>
                              <div class="text-subtitle-2 font-weight-medium">第{{ day.day }}天：{{ day.date }} {{ day.dayOfWeek }}</div>
                              <div class="text-caption text-medium-emphasis mb-2">
                                总时长：{{ day.totalTime }}分钟
                              </div>
                            </div>
                            <v-spacer></v-spacer>
                            <v-chip size="x-small" :color="day.dayOfWeek.includes('周六') || day.dayOfWeek.includes('周日') ? 'orange' : 'primary'">
                              {{ day.resources.length }}个资源
                            </v-chip>
                          </div>
                          <v-list density="compact" class="bg-grey-lighten-5 rounded">
                            <v-list-item
                              v-for="(resource, rIndex) in day.resources"
                              :key="`${index}-${rIndex}`"
                              density="compact"
                            >
                              <template v-slot:prepend>
                                <v-icon size="small" :color="resource.type === 'video' ? 'red' : resource.type === 'document' ? 'blue' : 'green'">
                                  {{ resource.type === 'video' ? 'mdi-video' : resource.type === 'document' ? 'mdi-file-document' : 'mdi-help-circle' }}
                                </v-icon>
                              </template>
                              <v-list-item-title class="text-body-2">
                                {{ resource.title }}
                                <v-chip 
                                  v-if="resource.isPartial" 
                                  size="x-small" 
                                  color="warning-lighten-4" 
                                  class="ml-2"
                                >
                                  分段学习
                                </v-chip>
                              </v-list-item-title>
                              <v-list-item-subtitle v-if="resource.partialInfo" class="text-caption">
                                {{ resource.partialInfo }}
                              </v-list-item-subtitle>
                              <template v-slot:append>
                                <v-chip size="x-small" :color="resource.type === 'video' ? 'red-lighten-4' : resource.type === 'document' ? 'blue-lighten-4' : 'green-lighten-4'">
                                  {{ resource.estimatedTime }}分钟
                                </v-chip>
                              </template>
                            </v-list-item>
                          </v-list>
                        </v-timeline-item>
                      </v-timeline>
                    </v-card-text>
                  </v-card>
                  <v-card v-else>
                    <v-card-title>
                      <v-icon start>mdi-calendar-check</v-icon>
                      计划预览
                    </v-card-title>
                    <v-card-text class="text-center py-12">
                      <v-icon size="64" color="grey-lighten-2">mdi-calendar-blank</v-icon>
                      <p class="text-medium-emphasis mt-4">
                        请设置学习目标并生成学习计划
                      </p>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-window-item>

        </v-window>
      </v-card>
    </v-container>

    <!-- 加载状态 -->
    <v-overlay :model-value="loading" class="d-flex align-center justify-center">
      <v-progress-circular
        indeterminate
        color="primary"
        size="64"
      ></v-progress-circular>
    </v-overlay>

    <!-- 学习资源对话框 -->
    <v-dialog v-model="resourceDialog" max-width="800px">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-book-open-variant</v-icon>
          学习资源 - {{ selectedPath?.title }}
        </v-card-title>
        
        <v-card-text>
          <div v-if="selectedPath?.resources">
            <!-- 视频资源 -->
            <div v-if="selectedPath?.resources?.videos && selectedPath.resources.videos.length > 0" class="mb-4">
              <h4 class="mb-2">
                <v-icon class="mr-1">mdi-video</v-icon>
                推荐视频 ({{ selectedPath.resources.videos.length }})
              </h4>
              <v-list>
                <v-list-item
                  v-for="video in selectedPath.resources.videos"
                  :key="video.id"
                  @click="goToVideo(video)"
                  class="cursor-pointer"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-play-circle</v-icon>
                  </template>
                  <v-list-item-title>{{ video.title }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <div v-if="video.course_name" class="text-caption">课程: {{ video.course_name }}</div>
                    <div class="d-flex align-center gap-2">
                      <span v-if="video.duration">时长: {{ formatDuration(video.duration) }}</span>
                      <span v-if="video.progress !== undefined" class="text-success">
                        已学习: {{ Math.round(video.progress * 100) }}%
                      </span>
                    </div>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </div>
            
            <!-- 文档资源 -->
            <div v-if="selectedPath?.resources?.documents && selectedPath.resources.documents.length > 0" class="mb-4">
              <h4 class="mb-2">
                <v-icon class="mr-1">mdi-file-document</v-icon>
                推荐文档 ({{ selectedPath.resources.documents.length }})
              </h4>
              <v-list>
                <v-list-item
                  v-for="doc in selectedPath.resources.documents"
                  :key="doc.id"
                  @click="goToDocument(doc)"
                  class="cursor-pointer"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-file-document-outline</v-icon>
                  </template>
                  <v-list-item-title>{{ doc.title }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <div v-if="doc.course_name" class="text-caption">课程: {{ doc.course_name }}</div>
                    <div v-if="doc.file_type" class="text-caption">类型: {{ doc.file_type }}</div>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </div>
            
            <!-- 练习题 -->
            <div v-if="selectedPath?.resources?.questions && selectedPath.resources.questions.length > 0">
              <h4 class="mb-2">
                <v-icon class="mr-1">mdi-help-circle</v-icon>
                配套练习 ({{ selectedPath.resources.questions.length }})
              </h4>
              <v-list>
                <v-list-item
                  v-for="question in selectedPath.resources.questions"
                  :key="question.id"
                  @click="goToQuestion(question)"
                  class="cursor-pointer"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-help-circle-outline</v-icon>
                  </template>
                  <v-list-item-title>{{ question.title || question.content?.substring(0, 50) + '...' || '练习题' }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <div v-if="question.difficulty || question.difficulty_level" class="text-caption">
                      难度: {{ question.difficulty || question.difficulty_level }}
                    </div>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </div>
          </div>
          
          <div v-else class="text-center py-4">
            <v-icon size="48" color="grey">mdi-book-open-variant</v-icon>
            <p class="text-grey mt-2">暂无学习资源</p>
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="resourceDialog = false">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted, onActivated, onDeactivated, watch } from 'vue'
import { useRouter } from 'vue-router'
import { personalizedRecommendationService } from '../api/personalizedRecommendationService'
import courseService from '../api/courseService'

interface LearningPath {
  id: number
  title: string
  description: string
  duration: string
  color: string
  keywordId?: number
  sourceKeyword?: string
  masteryLevel?: number
  currentMastery?: number
  priorityScore?: number
  learning_benefits?: string[]
  resources: {
    videos: Array<{ id: number; title: string; description?: string; duration?: number; course_name?: string; course_id?: number; progress?: number }>
    documents: Array<{ id: number; title: string; description?: string; file_type?: string; course_name?: string; course_id?: number }>
    questions: Array<{ id: number; title?: string; content?: string; difficulty?: string; difficulty_level?: string; type?: string; assignment_title?: string; assignment_id?: string; is_completed?: boolean; is_correct?: boolean }>
  } | undefined
}

// 学习计划设置接口
interface StudyPlanSettings {
  dailyTime: number; // 每天学习分钟数
  weekdays: boolean; // 工作日学习
  weekends: boolean; // 双休日学习
}

// 学习计划结果接口
interface StudyPlan {
  totalDays: number;
  dailyPlans: Array<{
    day: number;
    date: string;
    dayOfWeek: string;
    resources: Array<{
      type: string; // 'video', 'document', 'question'
      id: number;
      title: string;
      estimatedTime: number; // 分钟
      isPartial?: boolean; // 是否为分段学习
      partialInfo?: string; // 分段学习信息
    }>;
    totalTime: number; // 分钟
  }>;
}

const router = useRouter()
const loading = ref(false)
const error = ref<string | null>(null)

// 标签页状态
const activeTab = ref('overview')

const learningPaths = ref<LearningPath[]>([])
const userMasteryOverview = ref<any>(null)
const isLoggedIn = computed(() => !!localStorage.getItem('wendao_token'))

// 缓存相关状态
const cacheInfo = ref<any>(null)
const refreshing = ref(false)

// 学习资源对话框相关
const resourceDialog = ref(false)
const selectedPath = ref<LearningPath | null>(null)

// 学习进度相关状态
const progressStats = ref({
  activeCourses: 0,
  studyHours: 0,
  totalKnowledgePoints: 0,
  avgMasteryLevel: 0,
  masteredPoints: 0
})
const progressCourses = ref<any[]>([])
const loadingProgress = ref(false)
const progressError = ref<string | null>(null)
const searchProgress = ref('')

// 学习计划相关状态
const studyPlanSettings = ref<StudyPlanSettings>({
  dailyTime: 20, // 默认每天学习20分钟
  weekdays: true, // 默认工作日学习
  weekends: false // 默认双休日不学习
})
const studyPlan = ref<StudyPlan | null>(null)
const generatingPlan = ref(false)

// 过滤课程（基于搜索）
const filteredProgressCourses = computed(() => {
  if (!searchProgress.value) {
    return progressCourses.value
  }
  
  const query = searchProgress.value.toLowerCase()
  return progressCourses.value.filter(course => 
    course.name.toLowerCase().includes(query)
  )
})

// 统计方法
const getTotalVideos = () => {
  return learningPaths.value.reduce((total, path) => {
    return total + (path.resources?.videos?.length || 0)
  }, 0)
}

const getTotalDocuments = () => {
  return learningPaths.value.reduce((total, path) => {
    return total + (path.resources?.documents?.length || 0)
  }, 0)
}

const getTotalQuestions = () => {
  return learningPaths.value.reduce((total, path) => {
    return total + (path.resources?.questions?.length || 0)
  }, 0)
}

// 获取推荐资源
const getRecommendedVideos = () => {
  const videos: any[] = []
  learningPaths.value.forEach(path => {
    if (path.resources?.videos) {
      videos.push(...path.resources.videos)
    }
  })
  return videos
}

const getRecommendedDocuments = () => {
  const documents: any[] = []
  learningPaths.value.forEach(path => {
    if (path.resources?.documents) {
      documents.push(...path.resources.documents)
    }
  })
  return documents
}

const getRecommendedQuestions = () => {
  const questions: any[] = []
  learningPaths.value.forEach(path => {
    if (path.resources?.questions) {
      questions.push(...path.resources.questions)
    }
  })
  return questions
}

// 生成学习计划
const generateStudyPlan = () => {
  generatingPlan.value = true
  try {
    if (!studyPlanSettings.value.weekdays && !studyPlanSettings.value.weekends) {
      console.warn('未选择任何学习日，无法生成计划')
      generatingPlan.value = false
      return
    }
    const resources = getAllResources()
    const availableDaysPerWeek = getAvailableDaysPerWeek()
    const dailyTimeMinutes = studyPlanSettings.value.dailyTime || 20
    if (resources.length === 0 || availableDaysPerWeek === 0) {
      console.warn('没有资源或没有选择学习日')
      generatingPlan.value = false
      return
    }
    
    console.log(`开始生成学习计划：${resources.length}个资源，每日${dailyTimeMinutes}分钟`)
    
    // 按优先级排序
    resources.sort((a, b) => {
      const pathPriorityA = a.pathPriority || 0
      const pathPriorityB = b.pathPriority || 0
      return pathPriorityB - pathPriorityA
    })
    
    const dailyPlans = []
    let dayCount = 0
    let currentDate = new Date()
    const maxDays = 365
    let dayCounter = 0
    
    // 创建资源队列，支持分割学习
    const resourceQueue = resources.map(resource => ({
      ...resource,
      remainingTime: resource.estimatedTime, // 剩余学习时间
      isPartial: false, // 是否是分割的资源
      originalResource: resource // 保存原始资源引用
    }))
    
    while (resourceQueue.length > 0 && dayCounter < maxDays) {
      dayCounter++
      if (isAvailableDay(currentDate)) {
        dayCount++
        const dayPlan = {
          day: dayCount,
          date: formatDate(currentDate),
          dayOfWeek: getDayOfWeek(currentDate),
          resources: [] as any[],
          totalTime: 0
        }
        
        // 分配当天的学习资源
        let remainingDailyTime = dailyTimeMinutes
        
        while (resourceQueue.length > 0 && remainingDailyTime > 0) {
          const currentResourceItem = resourceQueue[0]
          
          if (currentResourceItem.remainingTime <= remainingDailyTime) {
            // 资源能在当天完成
            const resource = resourceQueue.shift()!
            dayPlan.resources.push({
              type: resource.type,
              id: resource.id,
              title: resource.isPartial ? 
                `${resource.title}（完成）` : resource.title,
              estimatedTime: resource.remainingTime,
              isPartial: resource.isPartial,
              partialInfo: resource.isPartial ? `完成学习` : undefined
            })
            dayPlan.totalTime += resource.remainingTime
            remainingDailyTime -= resource.remainingTime
            
            console.log(`第${dayCount}天：完成资源"${resource.title}"，用时${resource.remainingTime}分钟`)
          } else {
            // 资源需要分割到多天学习
            const timeToAllocate = remainingDailyTime
            
            // 计算当前是第几天学习这个资源
            const originalTime = currentResourceItem.originalResource.estimatedTime
            const completedTime = originalTime - currentResourceItem.remainingTime
            const dailyTime = studyPlanSettings.value.dailyTime || 20
            const currentPartialDay = Math.floor(completedTime / dailyTime) + 1
            
            currentResourceItem.remainingTime -= timeToAllocate
            currentResourceItem.isPartial = true
            
            dayPlan.resources.push({
              type: currentResourceItem.type,
              id: currentResourceItem.id,
              title: `${currentResourceItem.title}（第${currentPartialDay}天）`,
              estimatedTime: timeToAllocate,
              isPartial: true,
              partialInfo: `剩余${currentResourceItem.remainingTime}分钟`
            })
            dayPlan.totalTime += timeToAllocate
            remainingDailyTime = 0
            
            console.log(`第${dayCount}天：学习资源"${currentResourceItem.title}"${timeToAllocate}分钟，剩余${currentResourceItem.remainingTime}分钟`)
          }
        }
        
        if (dayPlan.resources.length > 0) {
          dailyPlans.push(dayPlan)
        }
      }
      
      currentDate.setDate(currentDate.getDate() + 1)
      
      if (dayCounter % 20 === 0) {
        console.log(`计划生成中...已处理${dayCounter}天，剩余资源：${resourceQueue.length}`)
      }
    }
    
    if (resourceQueue.length > 0) {
      console.warn(`达到最大计划天数限制(${maxDays}天)，仍有${resourceQueue.length}个资源未完全分配`)
    } else {
      console.log('所有资源已成功分配到学习计划中')
    }
    
    studyPlan.value = {
      totalDays: dayCount,
      dailyPlans: dailyPlans
    }
    
    console.log(`学习计划生成完成：总天数${dayCount}天，原始资源${resources.length}个`)
  } catch (error) {
    console.error('生成学习计划失败:', error)
  } finally {
    generatingPlan.value = false
  }
}


// 获取所有可用资源，并计算估计学习时间
const getAllResources = () => {
  const resources: Array<{
    type: string;
    id: number;
    title: string;
    estimatedTime: number;
    pathPriority?: number;
  }> = []
  
  // 记录处理的资源数量，用于调试
  let videoCount = 0
  let docCount = 0
  let questionCount = 0
  
  // 遍历学习路径
  learningPaths.value.forEach((path, pathIndex) => {
    if (!path.resources) return
    
    // 计算路径优先级 (0-1)，越接近1优先级越高
    const pathPriority = path.priorityScore !== undefined ? path.priorityScore : (1 - pathIndex / learningPaths.value.length)
    
    // 处理视频资源
    if (Array.isArray(path.resources.videos)) {
      path.resources.videos.forEach(video => {
        // 安全获取视频时长
        let duration = 15 // 默认15分钟
        if (video.duration && typeof video.duration === 'number' && video.duration > 0) {
          // 视频时长（秒）转为分钟，向上取整
          const videoDurationMinutes = Math.ceil(video.duration / 60)
          // 对于长视频，考虑学习效率，可能需要更多时间（暂停、回看等）
          if (videoDurationMinutes > 30) {
            duration = Math.ceil(videoDurationMinutes * 1.2) // 长视频增加20%时间
          } else {
            duration = videoDurationMinutes
          }
          // 确保合理范围 (5分钟到4小时)
          duration = Math.max(5, Math.min(240, duration))
        }
        
        resources.push({
          type: 'video',
          id: video.id || Math.random(),
          title: video.title || `视频 ${++videoCount}`,
          estimatedTime: duration,
          pathPriority
        })
      })
    }
    
    // 处理文档资源
    if (Array.isArray(path.resources.documents)) {
      path.resources.documents.forEach(doc => {
        resources.push({
          type: 'document',
          id: doc.id || Math.random(),
          title: doc.title || `文档 ${++docCount}`,
          estimatedTime: 10, // 每个文档默认10分钟，按需求设置
          pathPriority
        })
      })
    }
    
    // 处理练习题
    if (Array.isArray(path.resources.questions)) {
      path.resources.questions.forEach(question => {
        resources.push({
          type: 'question',
          id: question.id || Math.random(),
          title: question.title || (question.content ? question.content.substring(0, 30) + '...' : `练习题 ${++questionCount}`),
          estimatedTime: 5, // 每道题默认5分钟，按需求设置
          pathPriority
        })
      })
    }
  })
  
  return resources
}

// 获取每周可用学习天数
const getAvailableDaysPerWeek = () => {
  let days = 0
  if (studyPlanSettings.value.weekdays) days += 5 // 周一至周五
  if (studyPlanSettings.value.weekends) days += 2 // 周六和周日
  return days
}

// 判断日期是否是可学习日（工作日或周末，取决于设置）
const isAvailableDay = (date: Date) => {
  const day = date.getDay()
  const isWeekend = day === 0 || day === 6 // 0是周日，6是周六
  
  if (isWeekend) {
    return studyPlanSettings.value.weekends
  } else {
    return studyPlanSettings.value.weekdays
  }
}

// 格式化日期为 YYYY-MM-DD 格式
const formatDate = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 获取星期几
const getDayOfWeek = (date: Date) => {
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[date.getDay()]
}

// 计算学习计划中的总学习小时数
const calculateTotalStudyHours = () => {
  const totalMinutes = calculateTotalLearningMinutes()
  return (totalMinutes / 60).toFixed(1)
}

// 计算学习计划中的总学习分钟数
const calculateTotalLearningMinutes = () => {
  const resources = getAllResources()
  
  return resources.reduce((total, resource) => {
    return total + resource.estimatedTime
  }, 0)
}

// 计算预计学习周期（天）
const calculateStudyPeriod = () => {
  const totalMinutes = calculateTotalLearningMinutes()
  const dailyTime = studyPlanSettings.value.dailyTime
  const availableDaysPerWeek = getAvailableDaysPerWeek()
  
  if (dailyTime <= 0 || availableDaysPerWeek === 0) return 0
  
  // 计算总天数
  const totalDays = Math.ceil(totalMinutes / dailyTime)
  
  // 转换为实际日历天数（考虑到不是每天都学习）
  const calendarDays = Math.ceil(totalDays * (7 / availableDaysPerWeek))
  
  return calendarDays
}

// 计算计划完成百分比
const calculatePlanCompletion = () => {
  // 默认返回0%
  if (!studyPlanSettings.value.dailyTime) return 0
  
  const dailyTimeMinutes = studyPlanSettings.value.dailyTime
  const totalResourcesTime = calculateTotalLearningMinutes()
  
  // 获取30天内可学习的总时间
  const availableDaysPerWeek = getAvailableDaysPerWeek()
  if (availableDaysPerWeek === 0) return 0
  
  const daysIn30Days = 30 * (availableDaysPerWeek / 7)
  const availableTimeIn30Days = daysIn30Days * dailyTimeMinutes
  
  // 计算30天内可以完成的百分比
  const completion = (availableTimeIn30Days / totalResourcesTime) * 100
  
  // 如果可以在30天内完成，则返回实际百分比，否则按比例计算
  return Math.min(100, completion)
}

// 计算已完成资源数（可在30天内学习完的资源数）
const calculateCompletedResources = () => {
  const resources = getAllResources()
  const dailyTimeMinutes = studyPlanSettings.value.dailyTime
  
  // 获取30天内可学习的总时间
  const availableDaysPerWeek = getAvailableDaysPerWeek()
  if (availableDaysPerWeek === 0) return 0
  
  const daysIn30Days = 30 * (availableDaysPerWeek / 7)
  const availableTimeIn30Days = daysIn30Days * dailyTimeMinutes
  
  let timeUsed = 0
  let count = 0
  
  for (const resource of resources) {
    if (timeUsed + resource.estimatedTime <= availableTimeIn30Days) {
      timeUsed += resource.estimatedTime
      count++
    } else {
      break
    }
  }
  
  return count
}

// 计算总资源数
const calculateTotalResources = () => {
  return getAllResources().length
}

// 查看学习资源
const viewLearningResources = (path: LearningPath) => {
  selectedPath.value = path
  resourceDialog.value = true
}

// 开始学习
const startLearning = (path: LearningPath) => {
if (path.resources && path.resources.videos.length > 0) {
    // 如果有视频资源，直接跳转到第一个视频
    const firstVideo = path.resources.videos[0]
    goToVideo(firstVideo)
  } else if (path.resources && path.resources.documents.length > 0) {
    // 如果有文档资源，跳转到第一个文档
    const firstDoc = path.resources.documents[0]
    goToDocument(firstDoc)
  } else if (path.resources && path.resources.questions.length > 0) {
    // 如果有练习题，跳转到第一道题
    const firstQuestion = path.resources.questions[0]
    goToQuestion(firstQuestion)
  } else {
    // 没有具体资源，显示提示
    console.log('暂无可用的学习资源')
  }
}

// 导航到视频
const goToVideo = (video: any) => {
  // 关闭模态框
  resourceDialog.value = false
  
  if (video.course_id) {
    router.push(`/course/${video.course_id}/video/${video.id}`)
  } else {
    router.push(`/video/${video.id}`)
  }
}

// 导航到文档
const goToDocument = (doc: any) => {
  // 关闭模态框
  resourceDialog.value = false
  
  if (doc.course_id) {
    router.push(`/course/${doc.course_id}/document/${doc.id}`)
  } else {
    router.push(`/document/${doc.id}`)
  }
}

// 导航到练习题
const goToQuestion = (question: any) => {
  // 关闭模态框
  resourceDialog.value = false
  
  // 获取所有推荐的练习题
  const allQuestions = getRecommendedQuestions()
  
  // 将推荐题目列表保存到sessionStorage，避免URL过长
  sessionStorage.setItem('recommendedQuestions', JSON.stringify(allQuestions))
  
  // 跳转到题目详情页，只传递from参数
  router.push({
    path: `/question/${question.id}`,
    query: {
      from: 'personalized'
    }
  })
}

// 继续学习课程
const continueLearning = (courseId: string) => {
  router.push(`/course/${courseId}`)
}

// 格式化时长
const formatDuration = (seconds: number) => {
  if (!seconds) return '未知时长'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`
  }
  return `${remainingSeconds}秒`
}

// 格式化缓存时间
const formatCacheTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
  
  if (diffMinutes < 1) {
    return '刚刚生成'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前生成`
  } else {
    const diffHours = Math.floor(diffMinutes / 60)
    return `${diffHours}小时前生成`
  }
}

// 格式化过期时间
const formatExpiryTime = (seconds: number) => {
  if (seconds <= 0) return '已过期'
  
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}小时${remainingMinutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟`
  } else {
    return `${remainingSeconds}秒`
  }
}

// 刷新推荐
const refreshRecommendations = async () => {
  if (refreshing.value || !isLoggedIn.value) return
  
  refreshing.value = true
  try {
    // 调用API时使用force_refresh参数
    const data = await personalizedRecommendationService.getNextSteps(true) // force_refresh = true
    console.log('刷新推荐数据:', data)
    
    // 更新缓存信息
    if (data && data.cache_info) {
      cacheInfo.value = data.cache_info
    }
    
    // 转换为学习路径格式（与loadRecommendations相同的逻辑）
    if (data && Array.isArray(data.learning_path_recommendations)) {
      userMasteryOverview.value = data.user_mastery_overview || null
      
      learningPaths.value = data.learning_path_recommendations.map((step: any) => ({
        id: step.recommended_keyword?.id || Math.random(),
        title: `学习 ${step.recommended_keyword?.name || '未知知识点'}`,
        description: step.recommendation_reason || '暂无推荐理由',
        duration: step.resources?.videos?.length > 0 ? 
          `${step.resources.videos.length}个视频, ${step.resources.documents?.length || 0}个文档, ${step.resources.questions?.length || 0}道练习` :
          '暂无具体时长',
        color: step.priority_score > 0.7 ? 'primary' : step.priority_score > 0.4 ? 'success' : 'info',
        keywordId: step.recommended_keyword?.id,
        sourceKeyword: step.source_keyword?.name || '',
        masteryLevel: step.source_keyword?.mastery_level || 0,
        currentMastery: step.recommended_keyword?.current_mastery || 0,
        priorityScore: step.priority_score || 0,
        resources: {
          videos: Array.isArray(step.resources?.videos) ? step.resources.videos : [],
          documents: Array.isArray(step.resources?.documents) ? step.resources.documents : [],
          questions: Array.isArray(step.resources?.questions) ? step.resources.questions : []
        }
      }))
    } else if (data && Array.isArray(data.next_steps)) {
      userMasteryOverview.value = data.user_mastery_summary || null
      
      learningPaths.value = data.next_steps.map((step: any) => ({
        id: step.recommended_keyword?.id || Math.random(),
        title: `推荐学习 ${step.to_keyword} （基于${step.from_keyword}的掌握情况）`,
        description: step.reason || '暂无推荐理由',
        learning_benefits: step.learning_benefits || [],
        duration: `${step.resources_summary?.videos || 0}个视频, ${step.resources_summary?.documents || 0}个文档, ${step.resources_summary?.questions || 0}道练习`,
        color: step.priority_score > 0.7 ? 'primary' : step.priority_score > 0.4 ? 'success' : 'info',
        keywordId: step.recommended_keyword?.id,
        sourceKeyword: step.from_keyword || '',
        masteryLevel: 0,
        currentMastery: step.recommended_keyword?.current_mastery || 0,
        priorityScore: step.priority_score || 0,
        resources: {
          videos: Array.isArray(step.resources?.videos) ? step.resources.videos : [],
          documents: Array.isArray(step.resources?.documents) ? step.resources.documents : [],
          questions: Array.isArray(step.resources?.questions) ? step.resources.questions : []
        }
      }))
    }
    
    // 显示成功提示
    console.log('推荐数据刷新成功')
    
    // 刷新后自动重新生成学习计划
    const result = autoGenerateStudyPlan()
    console.log('学习计划自动生成结果:', result ? '成功' : '失败')
  } catch (error) {
    console.error('刷新推荐失败:', error)
  } finally {
    refreshing.value = false
  }
}

// 加载个性化推荐数据
const loadRecommendations = async () => {
  loading.value = true
  try {
    if (isLoggedIn.value) {
      // 调用个性化推荐API
      const data = await personalizedRecommendationService.getNextSteps()
      console.log('推荐数据:', data)
      
      // 更新缓存信息
      if (data && data.cache_info) {
        cacheInfo.value = data.cache_info
      }
      
      // 转换为学习路径格式
      if (data && Array.isArray(data.learning_path_recommendations)) {
        // 存储用户掌握度概览
        userMasteryOverview.value = data.user_mastery_overview || null
        
        learningPaths.value = data.learning_path_recommendations.map((step: any) => ({
          id: step.recommended_keyword?.id || Math.random(),
          title: `学习 ${step.recommended_keyword?.name || '未知知识点'}`,
          description: step.recommendation_reason || '暂无推荐理由',
          duration: step.resources?.videos?.length > 0 ? 
            `${step.resources.videos.length}个视频, ${step.resources.documents?.length || 0}个文档, ${step.resources.questions?.length || 0}道练习` :
            '暂无具体时长',
          color: step.priority_score > 0.7 ? 'primary' : step.priority_score > 0.4 ? 'success' : 'info',
          keywordId: step.recommended_keyword?.id,
          sourceKeyword: step.source_keyword?.name || '',
          masteryLevel: step.source_keyword?.mastery_level || 0,
          currentMastery: step.recommended_keyword?.current_mastery || 0,
          priorityScore: step.priority_score || 0,
          resources: {
            videos: Array.isArray(step.resources?.videos) ? step.resources.videos : [],
            documents: Array.isArray(step.resources?.documents) ? step.resources.documents : [],
            questions: Array.isArray(step.resources?.questions) ? step.resources.questions : []
          }
        }))
      } else if (data && Array.isArray(data.next_steps)) {
        // 处理next_steps格式的数据
        // 存储用户掌握度概览
        userMasteryOverview.value = data.user_mastery_summary || null
        
        learningPaths.value = data.next_steps.map((step: any) => ({
          id: step.recommended_keyword?.id || Math.random(),
          title: `推荐学习 ${step.to_keyword} （基于${step.from_keyword}的掌握情况）`,
          description: step.reason || '暂无推荐理由',
          learning_benefits: step.learning_benefits || [],
          duration: `${step.resources_summary?.videos || 0}个视频, ${step.resources_summary?.documents || 0}个文档, ${step.resources_summary?.questions || 0}道练习`,
          color: step.priority_score > 0.7 ? 'primary' : step.priority_score > 0.4 ? 'success' : 'info',
          keywordId: step.recommended_keyword?.id,
          sourceKeyword: step.from_keyword || '',
          masteryLevel: 0,
          currentMastery: step.recommended_keyword?.current_mastery || 0,
          priorityScore: step.priority_score || 0,
          resources: {
            videos: Array.isArray(step.resources?.videos) ? step.resources.videos : [],
            documents: Array.isArray(step.resources?.documents) ? step.resources.documents : [],
            questions: Array.isArray(step.resources?.questions) ? step.resources.questions : []
          }
        }))
      } else {
        // 如果没有推荐数据，使用默认路径
        learningPaths.value = getDefaultLearningPaths()
      }
    } else {
      learningPaths.value = getDefaultLearningPaths()
    }
  } catch (error) {
    console.error('加载推荐失败:', error)
    learningPaths.value = getDefaultLearningPaths()
  } finally {
    loading.value = false
  }
  
  // 确保总是返回一个Promise以便链式调用
  return Promise.resolve(learningPaths.value)
}

// 获取默认学习路径
const getDefaultLearningPaths = () => {
  if (!isLoggedIn.value) {
    return [
      {
        id: 1,
        title: '体验个性化学习',
        description: '登录后，系统将根据您的学习历史和掌握情况，智能推荐最适合的学习内容',
        duration: '立即开始',
        color: 'primary',
        resources: {
          videos: [],
          documents: [],
          questions: []
        }
      },
      {
        id: 2,
        title: '智能学习路径',
        description: '基于知识图谱和AI分析，为您制定个性化的学习计划',
        duration: '持续优化',
        color: 'success',
        resources: {
          videos: [],
          documents: [],
          questions: []
        }
      },
      {
        id: 3,
        title: '实时学习反馈',
        description: '系统会根据您的学习进度和表现，动态调整推荐内容',
        duration: '即时响应',
        color: 'info',
        resources: {
          videos: [],
          documents: [],
          questions: []
        }
      }
    ]
  }
  
  return [
    {
      id: 1,
      title: '正在分析您的学习情况',
      description: '系统正在基于您的学习历史生成个性化推荐，请稍后...',
      duration: '分析中',
      color: 'warning',
      resources: {
        videos: [],
        documents: [],
        questions: []
      }
    }
  ]
}

// 获取学习进度数据
const fetchLearningProgress = async () => {
  if (!isLoggedIn.value) return;
  
  loadingProgress.value = true;
  progressError.value = null;
  
  try {
    const response = await courseService.getLearningProgress();
    
    if (response.data.code === 200) {
      const data = response.data.data;
      progressStats.value = data.stats;
      progressCourses.value = data.courses;
    } else {
      progressError.value = response.data.message || '获取学习进度失败';
      console.error(progressError.value);
    }
  } catch (err: unknown) {
    const errorObj = err as Error;
    progressError.value = errorObj.message || '获取学习进度出错';
    console.error('获取学习进度失败:', errorObj);
  } finally {
    loadingProgress.value = false;
  }
};

// 在加载推荐后自动生成学习计划
const autoGenerateStudyPlan = () => {
  // 检查推荐路径是否有效
  if (!learningPaths.value || learningPaths.value.length === 0) {
    console.log('没有可用的学习路径，无法生成学习计划')
    return false
  }
  
  try {
    // 检查学习设置是否有效
    if (!studyPlanSettings.value.weekdays && !studyPlanSettings.value.weekends) {
      console.log('未选择任何学习日，设置默认值为工作日学习')
      studyPlanSettings.value.weekdays = true // 默认设置为工作日学习
    }
    
    generateStudyPlan()
    return true
  } catch (error) {
    console.error('自动生成学习计划失败:', error)
    return false
  }
}

// 监听学习计划设置变化，自动重新生成计划
watch(() => studyPlanSettings.value, (newSettings, oldSettings) => {
  // 防止初始化时触发
  if (oldSettings && learningPaths.value.length > 0) {
    console.log('学习计划设置发生变化，自动重新生成计划')
    autoGenerateStudyPlan()
  }
}, { deep: true })

// 监听学习路径变化，自动生成计划
watch(() => learningPaths.value, (newPaths, oldPaths) => {
  if (newPaths && newPaths.length > 0 && (!oldPaths || oldPaths.length === 0)) {
    console.log('学习路径数据加载完成，自动生成计划')
    autoGenerateStudyPlan()
  }
}, { deep: true })

onMounted(() => {
  // 使用Promise链来确保按顺序执行
  loadRecommendations()
    .then(() => {
      console.log('推荐数据加载完成，准备生成学习计划')
      return autoGenerateStudyPlan()
    })
    .catch(error => {
      console.error('加载推荐或生成学习计划失败:', error)
    })
  
  fetchLearningProgress()
})

// 添加组件卸载时的清理
onUnmounted(() => {
  // 清理状态
  learningPaths.value = []
  userMasteryOverview.value = null
  loading.value = false
  error.value = null
  progressCourses.value = []
  progressStats.value = {
    activeCourses: 0,
    studyHours: 0,
    totalKnowledgePoints: 0,
    avgMasteryLevel: 0,
    masteredPoints: 0
  }
})

// 确保在组件激活时重新加载数据
onActivated(() => {
  // 使用Promise链确保按顺序执行
  loadRecommendations()
    .then(() => {
      console.log('组件激活：推荐数据加载完成')
      return autoGenerateStudyPlan()
    })
    .catch(error => {
      console.error('组件激活：加载推荐或生成学习计划失败:', error)
    })
  
  fetchLearningProgress()
})

// 组件停用时清理
onDeactivated(() => {
  learningPaths.value = []
  userMasteryOverview.value = null
  loading.value = false
  error.value = null
  progressCourses.value = []
  progressStats.value = {
    activeCourses: 0,
    studyHours: 0,
    totalKnowledgePoints: 0,
    avgMasteryLevel: 0,
    masteredPoints: 0
  }
})
</script>

<style scoped>
.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* 自定义标签样式 */
:deep(.v-chip) {
  margin: 4px;
}

:deep(.v-chip--selected) {
  background-color: #6f23d1 !important;
  color: white !important;
}

.text-body-2{
  margin: auto;
}

.text-subtitle-1{
  margin: auto;
}

.personalized-recommend {
  min-height: 100vh;
  width: 100%;
}

.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

/* 学习进度统计卡片样式 */
.stats-flow {
  margin-bottom: 20px;
}

.stat-col {
  padding: 4px;
}

.stat-card {
  transition: all 0.2s;
  border-radius: 8px;
  height: 100%;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
}

.stat-card-content {
  padding: 12px !important;
}

.stat-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.blue {
  background-color: #3498db;
  color: white;
}

.stat-icon.green {
  background-color: #2ecc71;
  color: white;
}

.stat-icon.orange {
  background: linear-gradient(135deg, #ff9800, #f57c00);
  color: white;
}

.stat-icon.purple {
  background: linear-gradient(135deg, #9c27b0, #7b1fa2);
  color: white;
}

/* 确保卡片高度自适应 */
.text-h5 {
  line-height: 1.2;
  margin-bottom: 2px;
  font-weight: 600;
}

.search-field {
  max-width: 300px;
}

/* 确保课程列表能够滚动 */
:deep(.v-card-text) {
  max-height: none;
  overflow-y: visible;
}

/* 针对课程卡片外层容器的滚动设置 */
:deep(.v-list) {
  max-height: 400px;
  overflow-y: auto;
  padding: 0;
}
</style>
