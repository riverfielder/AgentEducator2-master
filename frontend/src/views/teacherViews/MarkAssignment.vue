<template>
  <v-container fluid class="mark-assignment pa-0">
    <!-- 顶部概览栏 -->
    <v-card class="mb-4">
      <v-card-text class="d-flex align-center flex-wrap gap-4">
        <v-btn
          icon
          variant="text"
          class="me-2"
          @click="router.push('/assignments')"
        >
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>

        <div class="d-flex align-center flex-grow-1">
          <div>
            <h2 class="text-h6 mb-1">{{ assignment.title }}</h2>
            <div class="text-subtitle-2 text-medium-emphasis">
              {{ assignment.courseName }}
            </div>
          </div>

          <v-divider vertical class="mx-4"></v-divider>

          <div class="d-flex align-center">
            <v-icon icon="mdi-calendar" class="me-2" size="small"></v-icon>
            <span class="text-body-2">截止日期：{{ formatDateTime(assignment.dueDate) }}</span>
            <v-divider vertical class="mx-4"></v-divider>
            <div class="d-flex align-center">
              <span class="text-body-2 me-2">批改进度：{{ assignment.markedCount }}/{{ assignment.totalSubmissions }}</span>
              <v-progress-linear
                :model-value="assignment.totalSubmissions ? (assignment.markedCount / assignment.totalSubmissions * 100) : 0"
                color="primary"
                rounded
                class="mt-1"
                style="width: 100px"
              ></v-progress-linear>
            </div>
          </div>

          <v-spacer></v-spacer>          <div class="d-flex gap-2">
            <v-tooltip
              location="bottom"
              text="使用AI智能批改填空题和问答题，自动评分和生成批改建议（请注意甄别AI批改结果）"
            >
              <template v-slot:activator="{ props }">
                <v-btn
                  prepend-icon="mdi-robot"
                  color="info"
                  variant="outlined"
                  :loading="aiGrading"
                  :disabled="aiGrading"
                  v-bind="props"
                  @click="startAIGrading"
                >
                  智能批改
                  <v-icon
                    icon="mdi-information"
                    size="small"
                    class="ms-1"
                  ></v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            <v-menu>
              <template v-slot:activator="{ props }">
                <v-btn
                  prepend-icon="mdi-export"
                  variant="outlined"
                  v-bind="props"
                >
                  导出成绩
                  <v-icon size="small" class="ml-1">mdi-chevron-down</v-icon>
                </v-btn>
              </template>
              <v-list>
                <v-list-item @click="exportGrades('excel')">
                  <template v-slot:prepend>
                    <v-icon color="green">mdi-file-excel</v-icon>
                  </template>
                  <v-list-item-title>导出为 Excel</v-list-item-title>
                  <v-list-item-subtitle>适合数据分析和统计</v-list-item-subtitle>
                </v-list-item>
                <v-list-item @click="exportGrades('word')">
                  <template v-slot:prepend>
                    <v-icon color="blue">mdi-file-word</v-icon>
                  </template>
                  <v-list-item-title>导出为 Word</v-list-item-title>
                  <v-list-item-subtitle>适合打印和存档</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <div class="d-flex gap-4" style="height: calc(100vh - 180px)">
      <!-- 左侧导航栏 -->
      <v-card width="300" class="flex-shrink-0">
        <v-card-text class="pa-0">
          <!-- 搜索框 -->
          <div class="px-4 pt-4 pb-2">
            <v-text-field
              v-model="searchQuery"
              prepend-inner-icon="mdi-magnify"
              label="搜索学生"
              hide-details
              density="comfortable"
              variant="outlined"
              class="mb-2"
            ></v-text-field>
          </div>

          <v-divider></v-divider>

          <!-- 学生列表 -->
          <v-list lines="one" select-strategy="classic">
            <v-list-item
              v-for="student in filteredStudents"
              :key="student.id"
              :value="student.id"
              :active="currentStudent?.id === student.id"
              @click="selectStudent(student)"
            >              <template v-slot:prepend>
                <v-avatar color="grey-lighten-3" size="40">
                  <img 
                    v-if="student.avatar"
                    :src="student.avatar" 
                    @error="handleAvatarError($event, student)"
                    @load="handleAvatarLoad($event, student)"
                    style="width: 100%; height: 100%; object-fit: cover;" 
                  />
                  <div v-else-if="student.name && student.name.trim()" 
                       class="letter-avatar" 
                       :style="getLetterAvatarStyle(student.name)">
                    {{ student.name.charAt(0).toUpperCase() }}
                  </div>
                  <v-icon v-else>mdi-account</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title>{{ student.name }}</v-list-item-title>

              <template v-slot:append>
                <v-chip
                  :color="getStatusColor(student.status)"
                  size="small"
                  class="ms-2"
                >
                  {{ getStatusText(student.status) }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>

      <!-- 中间批改区 -->
      <v-card class="flex-grow-1">
        <v-card-text class="pa-0">
          <!-- 智能批改加载动画 -->
          <div v-if="aiGrading" class="ai-grading-overlay">
            <div class="ai-grading-content">
              <div class="ai-grading-animation">
                <v-progress-circular
                  :size="80"
                  :width="6"
                  color="info"
                  indeterminate
                  class="mb-4"
                >
                  <v-icon size="40" color="info">mdi-robot</v-icon>
                </v-progress-circular>
              </div>
              
              <div class="ai-grading-text">
                <h3 class="text-h5 mb-2 text-info">AI 智能批改中</h3>
                <p class="text-body-1 mb-4 text-grey-darken-1">
                  正在使用人工智能技术批改作业，请稍候...
                </p>
                
                <!-- 进度信息 -->
                <div class="progress-info">
                  <div class="d-flex align-center justify-center mb-3">
                    <v-chip
                      color="info"
                      variant="tonal"
                      prepend-icon="mdi-clock-outline"
                      class="me-2"
                    >
                      批改进行中
                    </v-chip>
                    <v-chip
                      color="success"
                      variant="tonal"
                      prepend-icon="mdi-check-circle"
                    >
                      {{ gradingProgress.completed }}/{{ gradingProgress.total }} 题目
                    </v-chip>
                  </div>
                  
                  <!-- 进度条 -->
                  <v-progress-linear
                    :model-value="gradingProgress.percentage"
                    color="info"
                    height="8"
                    rounded
                    class="mb-3"
                  ></v-progress-linear>
                  
                  <div class="text-center">
                    <p class="text-caption text-grey-darken-1 mb-2">
                      {{ gradingProgress.currentTask }}
                    </p>
                    <div class="d-flex align-center justify-center">
                      <v-icon size="16" color="info" class="me-1">mdi-information</v-icon>
                      <span class="text-caption text-grey-darken-1">
                        AI批改结果仅供参考，请仔细核查
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="px-6 py-4" v-if="currentStudent && !aiGrading">
            <div
              v-for="(answer, index) in currentStudent.answers"
              :key="index"
              class="answer-section mb-6"
            >
              <!-- 题目信息 -->
              <div class="d-flex align-center mb-4">
                <h3 class="text-h6">第 {{ index + 1 }} 题 ({{ answer.totalScore }}分)</h3>
                <v-chip
                  :color="getQuestionTypeColor(answer.type)"
                  size="small"
                  class="ms-2"
                >
                  {{ getQuestionTypeText(answer.type) }}
                </v-chip>
              </div>

              <!-- 题干 -->
              <v-card variant="outlined" class="mb-4">
                <v-card-text>
                  <div class="text-body-1">{{ answer.question }}</div>
                </v-card-text>
              </v-card>

              <!-- 学生答案 -->
              <v-card variant="outlined" class="mb-4">
                <v-card-text>
                  <div class="d-flex align-center mb-2">
                    <v-icon icon="mdi-account" class="me-2"></v-icon>
                    <span class="text-subtitle-2">学生答案</span>
                  </div>

                  <!-- 选择题答案 -->
                  <template v-if="['single', 'multiple'].includes(answer.type)">
                    <div v-if="answer.options && answer.options.length > 0">
                      <div
                        v-for="(option, optIndex) in answer.options"
                        :key="`option-${index}-${optIndex}`"
                        class="d-flex align-center py-1"
                        :class="getOptionClass(answer, optIndex)"
                      >
                        <v-checkbox
                          :model-value="isOptionSelected(answer.type, answer.studentAnswer, optIndex)"
                          readonly
                          density="compact"
                          class="me-2"
                        ></v-checkbox>
                        <span>{{ String.fromCharCode(65 + optIndex) }}. {{ option.content }}</span>
                        
                        <!-- 添加正确/错误标识 -->
                        <v-spacer></v-spacer>
                        <v-icon 
                          v-if="option.isCorrect" 
                          color="success" 
                          size="20" 
                          class="ml-2"
                        >
                          mdi-check-circle
                        </v-icon>
                        <v-icon 
                          v-if="isOptionSelected(answer.type, answer.studentAnswer, optIndex) && !option.isCorrect" 
                          color="error" 
                          size="20" 
                          class="ml-2"
                        >
                          mdi-close-circle
                        </v-icon>
                      </div>
                    </div>
                    <div v-else class="text-grey-darken-1">
                      选项数据缺失
                    </div>
                  </template>

                  <!-- 填空题答案 -->
                  <template v-else-if="answer.type === 'blank'">
                    <div v-if="answer.studentAnswer">
                      <div
                        v-for="(blank, blankIndex) in (Array.isArray(answer.studentAnswer) ? answer.studentAnswer : [answer.studentAnswer])"
                        :key="`blank-${index}-${blankIndex}`"
                        class="d-flex align-center py-1"
                      >
                        <span class="me-2">{{ blankIndex + 1 }}.</span>
                        <span>{{ blank }}</span>
                      </div>
                    </div>
                    <div v-else class="text-grey-darken-1">
                      未作答
                    </div>
                  </template>

                  <!-- 简答题答案 -->
                  <template v-else-if="answer.type === 'essay'">
                    <div class="essay-answer">
                      <v-card-text class="pa-2">
                        <div v-if="answer.studentAnswer" style="white-space: pre-wrap;">{{ answer.studentAnswer }}</div>
                        <div v-else class="text-grey-darken-1">未作答</div>
                      </v-card-text>
                    </div>
                  </template>

                  <!-- 未知题型 -->
                  <template v-else>
                    <div class="text-grey-darken-1">
                      未知题型: {{ answer.type }}
                    </div>
                  </template>
                </v-card-text>
              </v-card>              <!-- 批改操作区 -->
              <div class="grading-section">
                <!-- 得分和操作按钮区 -->
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="d-flex align-center gap-4">
                    <!-- 得分输入框 -->
                    <div class="score-input-container">
                      <v-text-field
                        v-model="answer.score"
                        type="number"
                        label="得分"
                        :max="answer.totalScore"
                        min="0"
                        hide-details
                        density="comfortable"
                        variant="outlined"
                        class="score-input"
                        :class="{ 'score-filled': answer.score !== null && answer.score !== undefined }"
                      >
                        <template v-slot:append-inner>
                          <span class="text-caption text-grey-darken-1">/ {{ answer.totalScore }}</span>
                        </template>
                      </v-text-field>
                    </div>
                    
                    <!-- 得分状态指示器（移到右侧） -->
                    <div v-if="answer.score !== null && answer.score !== undefined" class="score-status-chip">
                      <v-chip
                        :color="getScoreColor(answer.score, answer.totalScore)"
                        size="small"
                        variant="tonal"
                      >
                        <v-icon size="14" class="me-1">
                          {{ getScoreIcon(answer.score, answer.totalScore) }}
                        </v-icon>
                        {{ getScoreText(answer.score, answer.totalScore) }}
                      </v-chip>
                    </div>

                    <!-- 选择题自动批改按钮 -->
                    <v-btn
                      v-if="['single', 'multiple'].includes(answer.type) && answer.score === null"
                      color="primary"
                      variant="outlined"
                      size="small"
                      prepend-icon="mdi-check"
                      @click="autoGradeSingleChoice(answer, index)"
                    >
                      自动批改
                    </v-btn>

                    <!-- 填空题自动批改按钮 -->
                    <v-btn
                      v-if="answer.type === 'blank' && answer.score === null"
                      color="primary"
                      variant="outlined"
                      size="small"
                      prepend-icon="mdi-check"
                      @click="autoGradeFillBlank(answer, index)"
                    >
                      自动批改
                    </v-btn>

                    <!-- 简答题自动批改按钮 -->
                    <v-btn
                      v-if="answer.type === 'essay' && answer.score === null"
                      color="primary"
                      variant="outlined"
                      size="small"
                      prepend-icon="mdi-check"
                      @click="autoGradeEssay(answer, index)"
                    >
                      自动批改
                    </v-btn>
                  </div>

                  <!-- 题目导航按钮 -->
                  <div class="d-flex gap-2">
                    <v-btn
                      variant="text"
                      prepend-icon="mdi-arrow-up"
                      :disabled="index === 0"
                      @click="navigateQuestion('prev')"
                      size="small"
                    >
                      上一题
                    </v-btn>
                    <v-btn
                      variant="text"
                      append-icon="mdi-arrow-down"
                      :disabled="index === currentStudent.answers.length - 1"
                      @click="navigateQuestion('next')"
                      size="small"
                    >
                      下一题
                    </v-btn>
                  </div>
                </div>

                <!-- 批改备注区 -->
                <div class="comment-section">
                  <div class="d-flex align-center mb-2">
                    <v-icon size="20" color="primary" class="me-2">mdi-comment-text</v-icon>
                    <span class="text-subtitle-2 text-primary">批改备注</span>
                    <v-spacer></v-spacer>
                    <v-chip
                      v-if="answer.comment && answer.comment.length > 0"
                      size="x-small"
                      color="info"
                      variant="tonal"
                    >
                      {{ answer.comment.length }} 字符
                    </v-chip>
                  </div>
                  
                  <v-card variant="outlined" class="comment-card">
                    <v-card-text class="pa-3">
                      <v-textarea
                        v-model="answer.comment"
                        placeholder="请输入批改备注，为学生提供详细的反馈和建议..."
                        hide-details
                        rows="3"
                        auto-grow
                        max-rows="8"
                        variant="plain"
                        class="comment-textarea"
                        :class="{ 'has-content': answer.comment && answer.comment.length > 0 }"
                      ></v-textarea>
                    </v-card-text>
                  </v-card>
                </div>
              </div>
            </div>

            <!-- 底部操作栏 -->
            <v-divider class="my-4"></v-divider>
            <div class="d-flex justify-end gap-2">
              <v-btn
                color="primary"
                variant="outlined"
                prepend-icon="mdi-content-save"
                :loading="saving"
                @click="saveMarking"
              >
                暂存
              </v-btn>
              <v-btn
                color="primary"
                prepend-icon="mdi-check"
                :loading="submitting"
                @click="submitMarking"
              >
                提交批改
              </v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- 右侧辅助栏 -->
      <v-card width="300" class="flex-shrink-0">
        <v-card-text>
          <!-- 参考答案区 -->
          <div class="mb-6">
            <div class="d-flex align-center mb-4">
              <v-icon icon="mdi-book" class="me-2"></v-icon>
              <span class="text-h6">参考答案</span>
            </div>

            <div
              v-for="(answer, index) in currentQuestion?.referenceAnswer"
              :key="index"
              class="reference-answer mb-4"
            >
              <div class="text-subtitle-1 mb-2">第 {{ index + 1 }} 题答案</div>
              <v-card variant="outlined">
                <v-card-text>
                  <div style="white-space: pre-wrap;">{{ answer.content }}</div>
                  <div v-if="answer.explanation" class="mt-2 text-medium-emphasis">
                    <div class="text-subtitle-2 mb-1">解析：</div>
                    <div style="white-space: pre-wrap;">{{ answer.explanation }}</div>
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </div>

          <!-- 统计数据 -->
          <div class="mb-6">
            <div class="d-flex align-center mb-4">
              <v-icon icon="mdi-chart-box" class="me-2"></v-icon>
              <span class="text-h6">统计数据</span>
            </div>

            <v-list lines="one">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon icon="mdi-check-circle"></v-icon>
                </template>
                <v-list-item-title>作业平均分</v-list-item-title>
                <v-list-item-subtitle>{{ statistics.averageScore.toFixed(1) }}分</v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon icon="mdi-account-check"></v-icon>
                </template>
                <v-list-item-title>当前学生得分</v-list-item-title>
                <v-list-item-subtitle>{{ statistics.currentStudentScore }}分</v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon icon="mdi-clock-outline"></v-icon>
                </template>
                <v-list-item-title>待批改题目</v-list-item-title>
                <v-list-item-subtitle>{{ statistics.remainingQuestions }}题</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>

          <!-- 快捷工具 -->
          <div>
            <div class="d-flex align-center mb-4">
              <v-icon icon="mdi-tools" class="me-2"></v-icon>
              <span class="text-h6">快捷工具</span>
            </div>

            <div class="d-flex flex-column gap-2">
              <v-btn
                prepend-icon="mdi-check-circle"
                color="success"
                variant="outlined"
                :loading="autoGradingChoices"
                block
                @click="startAutoGradeChoices"
              >
                自动批改选择题
              </v-btn>

              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn
                    prepend-icon="mdi-text-box"
                    variant="outlined"
                    block
                    v-bind="props"
                  >
                    常用评语
                  </v-btn>
                </template>

                <v-list>
                  <v-list-item
                    v-for="(comment, index) in commonComments"
                    :key="index"
                    @click="insertComment(comment)"
                  >
                    <v-list-item-title>{{ comment }}</v-list-item-title>
                    <template v-slot:append>
                      <v-btn
                        icon="mdi-content-copy"
                        size="small"
                        variant="text"
                        @click.stop="copyComment(comment)"
                      >
                      </v-btn>
                    </template>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>
  </v-container>

  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    timeout="3000"
  >
    {{ snackbar.message }}
  </v-snackbar>
</template>

<style scoped>
/* 智能批改加载动画样式 */
.ai-grading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 250, 252, 0.98) 100%);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease-in-out;
}

.ai-grading-content {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  animation: slideUp 0.5s ease-out;
}

.ai-grading-animation {
  position: relative;
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

.ai-grading-animation::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  background: linear-gradient(45deg, #2196F3, #21CBF3, #2196F3);
  border-radius: 50%;
  opacity: 0.2;
  animation: pulse 2s ease-in-out infinite;
}

.ai-grading-text h3 {
  font-weight: 600;
  letter-spacing: 0.5px;
}

.progress-info {
  background: rgba(33, 150, 243, 0.05);
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid rgba(33, 150, 243, 0.1);
}

.progress-info .v-chip {
  font-weight: 500;
  letter-spacing: 0.25px;
}

.progress-info .v-progress-linear {
  box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
}

/* 得分和批改备注样式 */
.grading-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-top: 16px;
  border: 1px solid #e3f2fd;
}

.score-input-container {
  position: relative;
  min-width: 140px;
}

.score-input {
  width: 120px;
  transition: all 0.3s ease;
}

.score-input.score-filled {
  border-color: #4caf50 !important;
}

.score-input.score-filled .v-field__outline {
  border-color: #4caf50 !important;
}

.score-status-chip {
  display: flex;
  align-items: center;
  animation: slideIn 0.3s ease-out;
}

.comment-section {
  margin-top: 16px;
}

.comment-card {
  transition: all 0.3s ease;
  border-color: #e0e0e0;
}

.comment-card:hover {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1);
}

.comment-textarea {
  font-size: 14px;
  line-height: 1.6;
  transition: all 0.3s ease;
}

.comment-textarea.has-content {
  background: rgba(25, 118, 210, 0.02);
  border-radius: 8px;
  padding: 8px;
}



/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.2;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.3;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-grading-content {
    max-width: 90%;
    padding: 1.5rem;
  }
  
  .progress-info {
    padding: 1rem;
  }
  
  .grading-section {
    padding: 16px;
  }
  
  .score-input-container {
    min-width: 120px;
  }
    .score-input {
    width: 100px;
  }
}

/* Letter avatar styles */
.letter-avatar {
  border-radius: 50%;
  text-transform: uppercase;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 14px;
}

.letter-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255,255,255,0.1) 0%, 
    rgba(255,255,255,0) 50%, 
    rgba(0,0,0,0.1) 100%);
  pointer-events: none;
}
</style>

<script setup lang="ts">
import { defineExpose } from 'vue';
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import assignmentService from '@/api/assignmentService';
import courseService from '@/api/courseService';

// 类型定义
interface Option {
  content: string;
  selected: boolean;
  isCorrect: boolean;
}

interface Blank {
  content: string;
  isCorrect: boolean;
}

interface Answer {
  type: 'single' | 'multiple' | 'blank' | 'essay';
  question: string;
  question_id: string;
  options?: Option[];
  blanks?: Blank[];
  content?: string;
  score: number | null;
  totalScore: number;
  comment: string;
  studentAnswer?: any;
  reference?: string;
}

interface Student {
  id: string;
  name: string;
  studentId: string;
  user_number?: string;  // 添加可选的 user_number 字段
  status: 'unmarked' | 'marked' | 'pending';
  avatar: string | null;
  answers: Answer[];
}

interface ReferenceAnswer {
  content: string;
  explanation?: string;
}

// 修改基础数据的类型和初始值
interface AssignmentInfo {
  id: string;
  title: string;
  courseName: string;
  dueDate: string;
  totalQuestions: number;
  totalSubmissions: number;
  markedCount: number;
  questions?: any[]; // 添加questions属性
}

// 设置页面布局
defineOptions({
  layout: 'teacher'
});

const router = useRouter();
const route = useRoute();

// 基础数据
const assignment = ref<AssignmentInfo>({
  id: route.params.id as string,
  title: '',
  courseName: '',
  dueDate: '',
  totalQuestions: 0,
  totalSubmissions: 0,
  markedCount: 0,
  questions: [] // 初始化questions数组
});

const markMode = ref<'student' | 'question'>('student');
const searchQuery = ref('');
const currentStudent = ref<Student | null>(null);
const currentQuestion = ref<{
  referenceAnswer: ReferenceAnswer[];
  comment?: string;
} | null>(null);

const saving = ref(false);
const submitting = ref(false);

const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
});

// 添加智能批改相关状态
const aiGrading = ref(false);
const autoGradingChoices = ref(false);

// 批改进度状态
const gradingProgress = ref({
  completed: 0,
  total: 0,
  percentage: 0,
  currentTask: '准备开始批改...'
});

// 重置批改进度
const resetGradingProgress = () => {
  gradingProgress.value = {
    completed: 0,
    total: 0,
    percentage: 0,
    currentTask: '准备开始批改...'
  };
};

// 更新批改进度
const updateGradingProgress = (completed: number, total: number, currentTask: string) => {
  gradingProgress.value.completed = completed;
  gradingProgress.value.total = total;
  gradingProgress.value.percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  gradingProgress.value.currentTask = currentTask;
};

// 模拟数据
const students = ref<Student[]>([]);  // 清空模拟数据，改为从API获取

// 常用评语
const commonComments = [
  '思路清晰，答案完整',
  '基本概念理解准确',
  '需要补充更多示例',
  '答案错误，建议重新思考'
];

// 计算属性
const filteredStudents = computed(() => {
  if (!searchQuery.value) return students.value;
  const query = searchQuery.value.toLowerCase();
  return students.value.filter(student => 
    student.name.toLowerCase().includes(query) ||
    student.studentId.toLowerCase().includes(query)
  );
});

// 添加统计数据的计算属性
const statistics = computed(() => {
  if (!students.value.length) {
    return {
      averageScore: 0,
      currentStudentScore: 0,
      remainingQuestions: 0
    };
  }

  // 筛选出已完全批改的学生（所有题目都有分数的学生）
  const completedStudents = students.value.filter(student => 
    student.answers.every(answer => answer.score !== null)
  );

  // 计算平均分（只计算已完全批改的学生）
  const averageScore = completedStudents.length > 0
    ? completedStudents.reduce((sum, student) => {
        const studentScore = student.answers.reduce((total, answer) => {
          return total + Number(answer.score);
        }, 0);
        return sum + studentScore;
      }, 0) / completedStudents.length
    : 0;

  // 计算当前学生得分
  const currentStudentScore = currentStudent.value
    ? currentStudent.value.answers.reduce((total, answer) => {
        // 确保使用数字类型进行计算
        const score = answer.score !== null ? Number(answer.score) : 0;
        return total + score;
      }, 0)
    : 0;

  // 计算待批改题目数
  const remainingQuestions = currentStudent.value
    ? currentStudent.value.answers.filter(answer => answer.score === null).length
    : 0;

  return {
    averageScore,
    currentStudentScore,
    remainingQuestions
  };
});

// 方法
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getStatusColor = (status: 'unmarked' | 'marked' | 'pending') => {
  const colorMap = {
    unmarked: 'warning',
    marked: 'success',
    pending: 'info'
  } as const;
  return colorMap[status] || 'grey';
};

const getStatusText = (status: 'unmarked' | 'marked' | 'pending') => {
  const textMap = {
    unmarked: '未批改',
    marked: '已批改',
    pending: '待复批'
  } as const;
  return textMap[status] || '未知';
};

const getQuestionTypeColor = (type: 'single' | 'multiple' | 'blank' | 'essay') => {
  const colorMap = {
    single: 'primary',
    multiple: 'success',
    blank: 'info',
    essay: 'warning'
  } as const;
  return colorMap[type] || 'grey';
};

// 获取题型显示文本
const getQuestionDisplayText = (type: 'single' | 'multiple' | 'blank' | 'essay') => {
  const textMap = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '大题'
  } as const;
  return textMap[type] || '未知';
};

// 得分相关方法
const getScoreColor = (score: number, totalScore: number) => {
  const percentage = (score / totalScore) * 100;
  if (percentage >= 90) return 'success';
  if (percentage >= 70) return 'warning';
  if (percentage >= 60) return 'orange';
  return 'error';
};

const getScoreIcon = (score: number, totalScore: number) => {
  const percentage = (score / totalScore) * 100;
  if (percentage >= 90) return 'mdi-star';
  if (percentage >= 70) return 'mdi-thumb-up';
  if (percentage >= 60) return 'mdi-check';
  return 'mdi-alert-circle';
};

const getScoreText = (score: number, totalScore: number) => {
  const percentage = (score / totalScore) * 100;
  if (percentage >= 90) return '优秀';
  if (percentage >= 70) return '良好';
  if (percentage >= 60) return '及格';
  return '待改进';
};

const selectStudent = (student: Student) => {
  currentStudent.value = student;
};

const navigateQuestion = (direction: 'prev' | 'next') => {
  // TODO: 实现题目导航逻辑
};

const saveMarking = async () => {
  saving.value = true;
  try {
    // TODO: 实现保存批改进度的逻辑
    showSnackbar('保存成功');
  } catch (error) {
    showSnackbar('保存失败', 'error');
  } finally {
    saving.value = false;
  }
};

const submitMarking = async () => {
  if (!currentStudent.value) {
    showSnackbar('请先选择学生', 'warning');
    return;
  }

  const hasEmptyScores = currentStudent.value.answers.some(answer => 
    answer.score === null || answer.score === undefined
  );
  
  if (hasEmptyScores) {
    showSnackbar('还有题目未批改完成', 'warning');
    return;
  }

  submitting.value = true;
  try {
    // 添加调试日志
    console.log('当前学生答案数据:', currentStudent.value.answers);
    
    const submitData = {
      scores: currentStudent.value.answers.map((answer) => ({
        student_id: currentStudent.value!.id,
        question_id: answer.question_id,
        score: Number(answer.score),
        is_correct: Number(answer.score) === answer.totalScore,
        comment: answer.comment
      }))
    };
    console.log('提交的数据:', submitData);
    
    const res = await assignmentService.submitMarking(route.params.id as string, submitData);
    if (res.data.code === 200) {
      showSnackbar('提交成功');
      // 更新学生状态为已批改
      currentStudent.value.status = 'marked';
    } else {
      throw new Error(res.data.message || '提交失败');
    }
  } catch (error: any) {
    console.error('提交失败:', error);
    showSnackbar(error.message || '提交失败，请稍后重试', 'error');
  } finally {
    submitting.value = false;
  }
};

// 获取学生提交状态文本的辅助函数
const getStudentStatusText = (status: string) => {
  switch (status) {
    case 'submitted':
      return '已提交';
    case 'graded':
      return '已批改';
    case 'draft':
      return '草稿';
    case 'not_submitted':
      return '未提交';
    default:
      return '未知状态';
  }
};

const exportGrades = (format: 'excel' | 'word' = 'excel') => {
  if (!assignment.value || !students.value.length) {
    showSnackbar('暂无数据可导出', 'warning');
    return;
  }

  if (format === 'excel') {
    exportToExcel();
  } else if (format === 'word') {
    exportToWord();
  }
};

const exportToExcel = () => {
  try {
    // 动态导入xlsx库
    import('xlsx').then((XLSX) => {
      // 准备导出数据
      const exportData = [];
      
      // 添加表头
      const headers = ['学号', '姓名', '总分', '得分', '得分率'];
      
      // 添加每道题的得分列
      if (assignment.value.questions && assignment.value.questions.length > 0) {
        assignment.value.questions.forEach((question: any, index: number) => {
          headers.push(`第${index + 1}题得分`);
          headers.push(`第${index + 1}题备注`);
        });
      }
      
      exportData.push(headers);
      
      // 添加学生数据
      students.value.forEach(student => {
        const row = [
          student.user_number || '',  // 只使用 user_number 作为学号
          student.name,
          student.answers?.reduce((total, answer) => total + (answer.totalScore || 0), 0) || 0,
          student.answers?.reduce((total, answer) => total + (answer.score || 0), 0) || 0,
          // 计算总分和得分率
          student.answers?.reduce((total, answer) => total + (answer.totalScore || 0), 0) ? 
            `${((student.answers?.reduce((total, answer) => total + (answer.score || 0), 0) / 
            student.answers?.reduce((total, answer) => total + (answer.totalScore || 0), 0)) * 100).toFixed(1)}%` : 
            '0%'
        ];
        
        // 添加每道题的详细得分和备注
        if (student.answers && student.answers.length > 0) {
          student.answers.forEach(answer => {
            row.push(answer.score || 0);
            row.push(answer.comment || '');
          });
        } else if (assignment.value.questions) {
          // 如果学生没有答案，填充空值
          assignment.value.questions.forEach(() => {
            row.push(0);
            row.push('');
          });
        }
        
        exportData.push(row);
      });
      
      // 创建工作簿
      const wb = XLSX.utils.book_new();
      
      // 创建工作表
      const ws = XLSX.utils.aoa_to_sheet(exportData);
      
      // 设置列宽
      const colWidths = [
        { wch: 12 }, // 学号
        { wch: 10 }, // 姓名
        { wch: 8 },  // 总分
        { wch: 8 },  // 得分
        { wch: 10 }  // 得分率
      ];
      
      // 为每道题的得分和备注列设置宽度
      if (assignment.value.questions) {
        assignment.value.questions.forEach(() => {
          colWidths.push({ wch: 10 }); // 题目得分
          colWidths.push({ wch: 20 }); // 题目备注
        });
      }
      
      ws['!cols'] = colWidths;
      
      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, '成绩单');
      
      // 生成文件名
      const fileName = `${assignment.value.title}_成绩单_${new Date().toLocaleDateString().replace(/\//g, '-')}.xlsx`;
      
      // 导出文件
      XLSX.writeFile(wb, fileName);
      
      showSnackbar('Excel文件导出成功', 'success');
    }).catch(error => {
      console.error('导入xlsx库失败:', error);
      showSnackbar('Excel导出功能加载失败', 'error');
    });
  } catch (error) {
    console.error('导出Excel失败:', error);
    showSnackbar('Excel导出失败，请稍后重试', 'error');
  }
};

const exportToWord = () => {
  try {
    // 动态导入docx和file-saver库
    Promise.all([
      import('docx'),
      // 导入 file-saver 并添加类型声明
      import('file-saver') as unknown as Promise<{ default: typeof import('file-saver'); saveAs: typeof import('file-saver') }>
    ]).then(([{ Document, Paragraph, Table, TableRow, TableCell, WidthType, AlignmentType, TextRun, HeadingLevel, Packer }, { saveAs }]) => {
      
      // 创建文档段落
      const children = [];
      
      // 添加标题
      children.push(
        new Paragraph({
          text: `${assignment.value.title} - 成绩单`,
          heading: HeadingLevel.HEADING_1,
          alignment: AlignmentType.CENTER,
        })
      );
      
      // 添加基本信息
      children.push(
        new Paragraph({
          children: [
            new TextRun({ text: `导出时间：${new Date().toLocaleString()}`, break: 1 }),
            new TextRun({ text: `总人数：${students.value.length}人`, break: 1 }),
            new TextRun({ text: `已提交：${students.value.filter(s => s.status === 'unmarked').length}人`, break: 1 }),
            new TextRun({ text: `已批改：${students.value.filter(s => s.status === 'marked').length}人`, break: 1 })
          ]
        })
      );
      
      children.push(new Paragraph({ text: '', spacing: { before: 240 } }));
      
      // 创建表格数据
      const tableRows = [];
      
      // 表头
      const headerCells = [
        new TableCell({ children: [new Paragraph({ text: '学号', alignment: AlignmentType.CENTER })] }),
        new TableCell({ children: [new Paragraph({ text: '姓名', alignment: AlignmentType.CENTER })] }),
        new TableCell({ children: [new Paragraph({ text: '总分', alignment: AlignmentType.CENTER })] }),
        new TableCell({ children: [new Paragraph({ text: '得分', alignment: AlignmentType.CENTER })] }),
        new TableCell({ children: [new Paragraph({ text: '得分率', alignment: AlignmentType.CENTER })] })
      ];
      
      // 添加每道题的列
      if (assignment.value.questions && assignment.value.questions.length > 0) {
        assignment.value.questions.forEach((question: any, index: number) => {
          headerCells.push(
            new TableCell({ children: [new Paragraph({ text: `第${index + 1}题`, alignment: AlignmentType.CENTER })] })
          );
        });
      }
      
      tableRows.push(new TableRow({ children: headerCells }));
      
      // 学生数据行
      students.value.forEach(student => {
        const cells = [
           new TableCell({ children: [new Paragraph({ text: student.user_number || '', alignment: AlignmentType.CENTER })] }),
           new TableCell({ children: [new Paragraph({ text: student.name || '', alignment: AlignmentType.CENTER })] }),
           new TableCell({ children: [new Paragraph({ text: String(student.answers?.reduce((sum, answer) => sum + (answer.totalScore || 0), 0) || 0), alignment: AlignmentType.CENTER })] }),
           new TableCell({ children: [new Paragraph({ text: String(student.answers?.reduce((sum, answer) => sum + (answer.score || 0), 0) || 0), alignment: AlignmentType.CENTER })] }),
           new TableCell({ children: [new Paragraph({ text: student.answers && student.answers.length > 0 ? `${((student.answers.reduce((sum, ans) => sum + (ans.score || 0), 0) / student.answers.reduce((sum, ans) => sum + ans.totalScore, 0)) * 100).toFixed(1)}%` : '0%', alignment: AlignmentType.CENTER })] })
         ];
        
        // 添加每道题的得分
        if (student.answers && student.answers.length > 0) {
          student.answers.forEach(answer => {
            const scoreText = `${answer.score || 0}分`;
            const commentText = answer.comment ? `\n备注：${answer.comment}` : '';
            cells.push(
              new TableCell({ 
                children: [new Paragraph({ 
                  children: [
                    new TextRun({ text: scoreText }),
                    new TextRun({ text: commentText, break: commentText ? 1 : 0, size: 18 })
                  ],
                  alignment: AlignmentType.CENTER 
                })] 
              })
            );
          });
        } else if (assignment.value.questions) {
          // 如果学生没有答案，填充空值
          assignment.value.questions.forEach(() => {
            cells.push(
              new TableCell({ children: [new Paragraph({ text: '0分', alignment: AlignmentType.CENTER })] })
            );
          });
        }
        
        tableRows.push(new TableRow({ children: cells }));
      });
      
      // 创建表格
      const table = new Table({
        rows: tableRows,
        width: {
          size: 100,
          type: WidthType.PERCENTAGE,
        },
      });
      
      children.push(table);
      
      // 创建文档
      const doc = new Document({
        sections: [{
          children: children,
        }],
      });
      
      // 生成并下载文件
      Packer.toBlob(doc).then(blob => {
        const fileName = `${assignment.value.title}_成绩单_${new Date().toLocaleDateString().replace(/\//g, '-')}.docx`;
        saveAs(blob, fileName);
        showSnackbar('Word文档导出成功', 'success');
      });
      
    }).catch(error => {
      console.error('导入docx库失败:', error);
      showSnackbar('Word导出功能加载失败', 'error');
    });
  } catch (error) {
    console.error('导出Word失败:', error);
    showSnackbar('Word导出失败，请稍后重试', 'error');
  }
}

const markAsImportant = () => {
  // TODO: 实现标记重点的逻辑
};

const insertComment = (comment: string) => {
  if (currentStudent.value && currentQuestion.value) {
    currentQuestion.value.comment = comment;
  }
};

const showSnackbar = (message: string, color: string = 'success') => {
  snackbar.value.message = message;
  snackbar.value.color = color;
  snackbar.value.show = true;
};

// 智能批改方法
const startAIGrading = async () => {
  console.log('startAIGrading触发，当前学生：', currentStudent.value);
  if (!currentStudent.value) {
    showSnackbar('请先选择要批改的学生', 'warning');
    return;
  }

  // 重置并开始批改进度
  resetGradingProgress();
  aiGrading.value = true;
  
  try {
    // 获取所有未批改的答案
    const unmarkedAnswers = currentStudent.value.answers.filter(answer => 
      answer.score === null || answer.score === undefined
    );
    console.log('未批改答案：', unmarkedAnswers);
    
    if (unmarkedAnswers.length === 0) {
      showSnackbar('该学生的所有答案已批改完成', 'info');
      return;
    }

    // 初始化进度
    updateGradingProgress(0, unmarkedAnswers.length, '正在分析题目类型...');
    
    // 添加延迟以显示初始状态
    await new Promise(resolve => setTimeout(resolve, 800));

    // 批量批改所有未批改的答案
    for (let i = 0; i < unmarkedAnswers.length; i++) {
      const answer = unmarkedAnswers[i];
      const questionNumber = i + 1;
      
      // 更新当前批改状态
      updateGradingProgress(
        i, 
        unmarkedAnswers.length, 
        `正在批改第 ${questionNumber} 题 (${getQuestionTypeText(answer.type)})...`
      );
      
      // 从作业详情中获取题目信息
      const question = (assignment.value as any).questions?.find((q: any) => q.id === answer.question_id);
      console.log('question信息:', question);
      
      try {
        let result;
        
        // 根据题型调用不同的批改接口
        if (answer.type === 'single' || answer.type === 'multiple') {
          // 选择题批改
          result = await assignmentService.gradeChoiceQuestion({
            question_type: answer.type,
            options: answer.options || [], // 确保options始终是数组类型
            student_answer: answer.studentAnswer,
            max_score: answer.totalScore
          });
        } else if (answer.type === 'blank') {
          // 填空题批改
          result = await assignmentService.gradeFillBlankQuestion({
            question_id: answer.question_id,
            student_answer: answer.studentAnswer
          });
        } else {
          // 简答题等其他题型使用通用批改接口
          result = await assignmentService.gradeAnswer({
            question_id: answer.question_id,
            student_answer: answer.studentAnswer || ''
          });
        }
        
        console.log('AI批改返回：', result.data);
        if (result.data.code === 200) {
          // 兼容后端返回结构，优先取data下的score/comment，否则取顶层
          const gradingResult = result.data.data || result.data;
          
          // 确保不破坏原有数据结构，只更新批改相关字段
          const updatedAnswer = {
            ...answer,
            score: gradingResult.score,
            comment: gradingResult.comment || '',
            is_correct: gradingResult.is_correct
          };
          
          // 找到对应答案在数组中的实际索引
          const answerIndex = currentStudent.value.answers.findIndex(a => a.question_id === answer.question_id);
          if (answerIndex !== -1) {
            // 使用Vue的响应式更新方式
            currentStudent.value.answers[answerIndex] = updatedAnswer;
          }
          
          console.log('更新后的答案：', updatedAnswer);
          
          // 更新完成进度
          updateGradingProgress(
            i + 1, 
            unmarkedAnswers.length, 
            `第 ${questionNumber} 题批改完成 ✓`
          );
        } else {
          // 批改失败，但继续处理其他题目
          updateGradingProgress(
            i + 1, 
            unmarkedAnswers.length, 
            `第 ${questionNumber} 题批改失败，跳过...`
          );
        }
      } catch (questionError) {
        console.error(`第${questionNumber}题批改失败:`, questionError);
        updateGradingProgress(
          i + 1, 
          unmarkedAnswers.length, 
          `第 ${questionNumber} 题批改失败，跳过...`
        );
      }
      
      // 添加题目间的延迟，让用户看到进度变化
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // 显示保存状态
    updateGradingProgress(
      unmarkedAnswers.length, 
      unmarkedAnswers.length, 
      '正在保存批改结果...'
    );
    
    // 保存批改结果
    await saveMarking();
    
    // 更新学生状态为已批改
    currentStudent.value.status = 'marked';
    
    // 显示完成状态
    updateGradingProgress(
      unmarkedAnswers.length, 
      unmarkedAnswers.length, 
      '批改完成！正在整理结果...'
    );
    
    // 延迟显示完成状态
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    console.log('批改结果:', unmarkedAnswers);
    showSnackbar(`已完成${unmarkedAnswers.length}道题目的智能批改`, 'success');
  } catch (error: any) {
    console.error('智能批改失败:', error);
    updateGradingProgress(
      gradingProgress.value.completed, 
      gradingProgress.value.total, 
      '批改过程中出现错误...'
    );
    showSnackbar(error.message || '智能批改失败，请稍后重试', 'error');
  } finally {
    // 延迟关闭加载动画，让用户看到最终状态
    setTimeout(() => {
      aiGrading.value = false;
      resetGradingProgress();
    }, 1500);
  }
};

// 自动批改选择题方法
const startAutoGradeChoices = async () => {
  if (!route.params.id) {
    showSnackbar('作业ID不存在', 'error');
    return;
  }

  autoGradingChoices.value = true;
  try {
    const res = await assignmentService.autoGradeChoices(route.params.id as string);
    if (res.data.code === 200) {
      const data = res.data.data;
      showSnackbar(`自动批改完成！共处理了${data.processed_count}道选择题`, 'success');
      
      // 重新获取提交列表以更新显示
      await fetchSubmissions();
    } else {
      showSnackbar(res.data.message || '自动批改失败', 'error');
    }
  } catch (error: any) {
    console.error('自动批改选择题失败:', error);
    showSnackbar(error.response?.data?.message || '自动批改失败，请稍后重试', 'error');
  } finally {
    autoGradingChoices.value = false;
  }
};

// 自动批改单个选择题
const autoGradeSingleChoice = async (answer: any, index: number) => {
  try {
    const res = await assignmentService.gradeChoiceQuestion({
      question_type: answer.type,
      options: answer.options,
      student_answer: answer.studentAnswer,
      max_score: answer.totalScore
    });
    
    if (res.data.code === 200) {
      const result = res.data.data;
      answer.score = result.score;
      answer.comment = result.comment;
      showSnackbar('自动批改完成', 'success');
    } else {
      showSnackbar(res.data.message || '批改失败', 'error');
    }
  } catch (error: any) {
    console.error('单题批改失败:', error);
    showSnackbar(error.response?.data?.message || '批改失败，请稍后重试', 'error');
  }
};

// 获取题型中文名称
const getQuestionTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '简答题'
  };
  return typeMap[type] || '未知题型';
};

// 自动批改填空题
const autoGradeFillBlank = async (answer: any, index: number) => {
  try {
    const res = await assignmentService.gradeFillBlankQuestion({
      question_id: answer.question_id,
      student_answer: answer.studentAnswer || ''
    });
    
    if (res.data.code === 200) {
      const result = res.data.data;
      answer.score = result.score;
      answer.comment = result.comment;
      showSnackbar('自动批改完成', 'success');
    } else {
      showSnackbar(res.data.message || '批改失败', 'error');
    }
  } catch (error: any) {
    console.error('填空题批改失败:', error);
    showSnackbar(error.response?.data?.message || '批改失败，请稍后重试', 'error');
  }
};

// 自动批改简答题
const autoGradeEssay = async (answer: any, index: number) => {
  try {
    const res = await assignmentService.gradeAnswer({
      question_id: answer.question_id,
      student_answer: answer.studentAnswer || ''
    });
    
    if (res.data.code === 200) {
      const result = res.data.data || res.data;
      answer.score = result.score;
      answer.comment = result.comment;
      showSnackbar('自动批改完成', 'success');
    } else {
      showSnackbar(res.data.message || '批改失败', 'error');
    }
  } catch (error: any) {
    console.error('简答题批改失败:', error);
    showSnackbar(error.response?.data?.message || '批改失败，请稍后重试', 'error');
  }
};

// 添加获取作业详情的函数
const fetchAssignmentDetail = async () => {
  try {
    const res = await assignmentService.getAssignmentDetail(route.params.id as string);
    if (res.data.code === 200) {
      const data = res.data.data;
      
      // 先设置基本信息
      assignment.value = {
        id: data.id,
        title: data.title,
        courseName: '',  // 先置空，等待课程信息
        dueDate: data.dueDate,
        totalQuestions: data.questions?.length || 0,
        totalSubmissions: 0,
        markedCount: 0
      };

      // 获取课程信息
      if (data.courseId) {
        try {
          const courseRes = await courseService.getCourseDetails(data.courseId);
          if (courseRes.data.code === 200) {
            assignment.value.courseName = courseRes.data.data.name;
          }
        } catch (error) {
          console.error('获取课程信息失败:', error);
          assignment.value.courseName = '未知课程';
        }
      }
    }
  } catch (error) {
    console.error('获取作业详情失败:', error);
    showSnackbar('获取作业详情失败', 'error');
  }
};

// 修改fetchSubmissions函数，添加统计信息的更新
const fetchSubmissions = async () => {
  try {
    if (!route.params.id) {
      throw new Error('作业ID不能为空');
    }
    const res = await assignmentService.getStudentSubmissions(route.params.id as string);
    console.log('学生提交列表:', res.data);

    if (res.data.code === 200) {
      const submissions = res.data.data.submissions;
      // 更新提交统计信息
      assignment.value.totalSubmissions = res.data.data.total_students || submissions.length;
      // 修复：基于是否所有题目都已批改来统计
      assignment.value.markedCount = submissions.filter((s: any) => 
        s.questions_and_answers.every((qa: any) => qa.score !== null && qa.score !== undefined)
      ).length;
      
      // 更新学生列表
      students.value = submissions.map((submission: any) => {
        // 检查是否所有题目都已批改（有分数）
        const isMarked = submission.questions_and_answers.every((qa: any) => qa.score !== null && qa.score !== undefined);
        
        return {
          id: submission.student_id,
          name: submission.student_name,
          studentId: submission.student_id,
          user_number: submission.user_number || '',  // 添加 user_number 字段
          status: isMarked ? 'marked' : 'unmarked',
          avatar: null,
          answers: submission.questions_and_answers
            .filter((qa: any, index: number, array: any[]) => {
              // 去重：保留每个question_id的第一个出现
              return array.findIndex(item => item.question_id === qa.question_id) === index;
            })
            .map((qa: any) => {
              const options = qa.options ? JSON.parse(qa.options) : [];
              // 从 API 返回的作业详情中获取题目信息
              const question = (assignment.value as any).questions?.find((q: any) => q.id === qa.question_id || q.question_id === qa.question_id);
              
              // 确保初始化 comment 字段
              const answer = {
                type: qa.question_type,
                question: qa.question_content,
                question_id: qa.question_id,
                options: options,
                score: qa.score !== null && qa.score !== undefined ? qa.score : null,
                totalScore: qa.max_score || 10,
                comment: qa.comment || '', // 初始化为空字符串而不是 null
                studentAnswer: qa.student_answer,
                reference: question?.reference || '',
                is_correct: qa.is_correct || false
              };
              console.log('初始化的答案对象:', answer);
              return answer;
            })
        };
      });

      // 如果没有选中的学生，默认选择第一个
      if (!currentStudent.value && students.value.length > 0) {
        selectStudent(students.value[0]);
      }
    }
  } catch (error) {
    console.error('获取提交列表失败:', error);
    showSnackbar('获取提交列表失败', 'error');
  }
};

// 添加辅助函数
const isOptionSelected = (type: string, studentAnswer: any, optionIndex: number) => {
  if (studentAnswer === null || studentAnswer === undefined) return false;
  
  if (type === 'single') {
    // 单选题：学生答案可能是数字或字符串
    if (typeof studentAnswer === 'number') {
      return studentAnswer === optionIndex;
    } else if (typeof studentAnswer === 'string') {
      return parseInt(studentAnswer) === optionIndex;
    }
    return false;
  } else if (type === 'multiple') {
    // 多选题：学生答案应该是数组
    if (Array.isArray(studentAnswer)) {
      return studentAnswer.includes(optionIndex);
    } else if (typeof studentAnswer === 'string') {
      try {
        const answers = JSON.parse(studentAnswer);
        return Array.isArray(answers) && answers.includes(optionIndex);
      } catch {
        return false;
      }
    }
    return false;
  }
  return false;
};

// 获取选择题选项的样式类
const getOptionClass = (answer: any, optionIndex: number) => {
  const isSelected = isOptionSelected(answer.type, answer.studentAnswer, optionIndex);
  const isCorrect = answer.options[optionIndex]?.isCorrect;
  
  if (isCorrect) {
    // 正确答案显示绿色
    return 'text-success';
  } else if (isSelected) {
    // 学生选择的错误答案显示红色
    return 'text-error';
  } else {
    // 其他选项显示灰色
    return 'text-medium-emphasis';
  }
};

// 在 script setup 部分添加 copyComment 方法
const copyComment = async (comment: string) => {
  try {
    await navigator.clipboard.writeText(comment);
    showSnackbar('评语已复制到剪贴板');
  } catch (err) {
    showSnackbar('复制失败，请手动复制', 'error');
  }
};

// 头像相关方法
const getRandomColor = (seed: string) => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
  ];
  const index = seed.charCodeAt(0) % colors.length;
  return colors[index];
};

const getLetterAvatarStyle = (username: string) => {
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
};

const handleAvatarError = (event: Event, item: any) => {
  console.error('MarkAssignment avatar error for:', item.name || 'unknown');
  item.avatarLoadError = true;
  const target = event.target as HTMLImageElement;
  if (target) {
    target.style.display = 'none';
  }
};

const handleAvatarLoad = (event: Event, item: any) => {
  console.log('MarkAssignment avatar loaded for:', item.name || 'unknown');
  item.avatarLoadError = false;
  const target = event.target as HTMLImageElement;
  if (target) {
    target.style.display = 'block';
  }
};

// 生命周期钩子
onMounted(async () => {
  if (!route.params.id) {
    console.error('没有找到作业ID');
    showSnackbar('没有找到作业ID', 'error');
    return;
  }

  await fetchAssignmentDetail(); // 先获取作业详情
  await fetchSubmissions(); // 再获取提交列表
});

// 导出方法供模板使用
defineExpose({
  getScoreColor,
  getScoreIcon,
  getScoreText
});
</script>

<style scoped>
.mark-assignment {
  height: calc(100vh - 64px);
  overflow-y: auto;
  padding: 16px;
}

.answer-section {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
  padding-bottom: 24px;
}

.answer-section:last-child {
  border-bottom: none;
}

/* 选择题选项样式 */
.text-error {
  color: rgb(var(--v-theme-error)) !important;
}

/* 添加中间栏的滚动样式 */
:deep(.v-card-text) {
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

/* 美化滚动条样式 */
:deep(.v-card-text::-webkit-scrollbar) {
  width: 8px;
}

:deep(.v-card-text::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 4px;
}

:deep(.v-card-text::-webkit-scrollbar-thumb) {
  background: #888;
  border-radius: 4px;
}

:deep(.v-card-text::-webkit-scrollbar-thumb:hover) {
  background: #555;
}
</style>