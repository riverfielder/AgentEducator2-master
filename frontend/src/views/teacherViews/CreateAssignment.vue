<template>
  <v-container fluid class="create-assignment pa-0">
    <!-- 顶部基础信息区 -->
    <v-card class="mb-4">
      <v-card-text class="d-flex align-center flex-wrap gap-4">
        <!-- 返回按钮 -->
        <v-btn
          icon
          variant="text"
          class="me-2"
          @click="router.push('/assignments')"
        >
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <!-- 作业标题 -->
        <v-text-field
          v-model="assignment.title"
          label="作业标题"
          placeholder="如：Vue.js 组件实践作业"
          
          class="flex-grow-1"
          hide-details="auto"
          density="comfortable"
        ></v-text-field>

        <!-- 关联课程 -->
        <v-select
          v-model="assignment.courseId"
          :items="courses"
          item-title="name"
          item-value="id"
          label="关联课程"
          
          :loading="loadingCourses"
          class="flex-grow-1"
          hide-details="auto"
          density="comfortable"
        ></v-select>

        <!-- 截止日期 -->
        <v-menu
          v-model="showDatePicker"
          :close-on-content-click="false"
        >
          <template v-slot:activator="{ props }">
            <v-text-field
              :model-value="assignment.dueDate ? formatDateTime(assignment.dueDate) : ''"
              label="截止日期"
              readonly
              v-bind="props"
              hide-details="auto"
              density="comfortable"
              class="flex-grow-1"
              prepend-inner-icon="mdi-calendar-clock"
            ></v-text-field>
          </template>
          <v-card min-width="300">
            <v-date-picker
              v-model="tempDueDate"
              @update:model-value="() => {}"
            ></v-date-picker>
            <v-divider></v-divider>
            <v-card-text class="pa-3">
              <v-text-field
                v-model="tempDueTime"
                type="time"
                label="截止时间"
                hide-details
                density="comfortable"
                class="mb-3"
              ></v-text-field>
            </v-card-text>
            <v-card-actions class="pa-3">
              <v-spacer></v-spacer>
              <v-btn
                variant="text"
                @click="showDatePicker = false"
              >
                取消
              </v-btn>
              <v-btn
                color="primary"
                @click="confirmDueDateTime"
              >
                确定
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-menu>

        <!-- 操作按钮 -->
        <div class="d-flex gap-2">
          <v-btn
            color="primary"
            variant="outlined"
            :loading="saving"
            @click="saveAsDraft"
          >
            保存草稿
          </v-btn>
          <v-btn
            color="warning"
            variant="outlined"
            @click="showScheduleDialog = true"
            prepend-icon="mdi-clock-outline"
          >
            定时发布
          </v-btn>
          <v-btn
            color="primary"
            :loading="publishing"
            @click="publishAssignment()"
          >
            立即发布
          </v-btn>
          <v-btn
            color="info"
            variant="outlined"
            prepend-icon="mdi-database-import"
            @click="showImportFromBank = true"
          >
            从题库导入
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <!-- 主体内容区 -->
    <div class="d-flex gap-4">
      <!-- 左侧题目创建区 -->
      <div class="question-creation flex-grow-1">
        <v-row>
          <!-- 题型选择栏 -->
          <v-col cols="2">
            <v-card>
              <v-list density="compact" nav>
                <v-list-item
                  v-for="type in questionTypes"
                  :key="type.value"
                  :value="type.value"
                  :active="currentQuestionType === type.value"
                  @click="handleQuestionTypeChange(type.value)"
                  class="question-type-item"
                >
                  <template v-slot:prepend>
                    <v-icon :icon="type.icon"></v-icon>
                  </template>
                  <v-list-item-title>{{ type.title }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card>
          </v-col>

          <!-- 题目编辑区 -->
          <v-col cols="10">
            <v-card class="question-editor">
              <v-card-text>
                <!-- 单选/多选题编辑器 -->
                <template v-if="['single', 'multiple'].includes(currentQuestionType)">
                  <v-textarea
                    v-model="currentQuestion.content"
                    label="题干"
                    placeholder="请输入题目描述"
                    class="mb-4"
                    auto-grow
                    rows="2"
                    max-rows="8"
                  ></v-textarea>

                  <!-- 选项列表 -->
                  <div v-for="(option, index) in currentQuestion.options" :key="index" class="d-flex align-center mb-2">
                    <span class="option-label me-2">{{ String.fromCharCode(65 + index) }}</span>
                    <v-text-field
                      v-model="option.content"
                      placeholder="请输入选项内容"
                      hide-details
                      class="flex-grow-1 me-2"
                      density="comfortable"
                    ></v-text-field>
                    <v-checkbox
                      v-model="currentQuestion.options[index].isCorrect"
                      :disabled="currentQuestionType === 'single' && someOtherOptionIsCorrect(index)"
                      hide-details
                      density="compact"
                      class="ma-0"
                    ></v-checkbox>
                    <v-btn
                      icon="mdi-delete"
                      variant="text"
                      size="small"
                      color="error"
                      @click="removeOption(index)"
                      class="ms-2"
                    ></v-btn>
                  </div>

                  <!-- 添加选项按钮 -->
                  <v-btn
                    prepend-icon="mdi-plus"
                    variant="text"
                    class="mt-2 mb-4"
                    @click="addOption"
                  >
                    添加选项
                  </v-btn>
                </template>

                <!-- 填空题编辑器 -->
                <template v-else-if="currentQuestionType === 'blank'">
                  <v-textarea
                    v-model="currentQuestion.content"
                    label="题干"
                    placeholder="请输入题目描述，使用 ____ 表示填空位置"
                    rows="3"
                    class="mb-4"
                    auto-grow
                    max-rows="8"
                  ></v-textarea>

                  <v-textarea
                    v-model="currentQuestion.answers"
                    label="答案"
                    placeholder="请输入答案，多个答案请用换行分隔"
                    rows="3"
                    class="mb-4"
                    auto-grow
                    max-rows="8"
                  ></v-textarea>
                </template>

                <!-- 大题编辑器 -->
                <template v-else-if="currentQuestionType === 'essay'">
                  <v-textarea
                    v-model="currentQuestion.content"
                    label="题干"
                    placeholder="请输入题目要求"
                    rows="3"
                    class="mb-4"
                    auto-grow
                    max-rows="8"
                  ></v-textarea>

                  <v-textarea
                    v-model="currentQuestion.reference"
                    label="答案/评分参考"
                    placeholder="请输入参考答案或评分标准"
                    rows="4"
                    class="mb-4"
                    auto-grow
                    max-rows="8"
                  ></v-textarea>
                </template>

                <!-- 通用解析 -->
                <v-textarea
                  v-model="currentQuestion.explanation"
                  label="答案解析（选填）"
                  placeholder="请输入答案解析"
                  rows="2"
                  class="mb-4"
                  auto-grow
                  max-rows="8"
                ></v-textarea>

                <!-- 难度设置 -->
                <v-select
                  v-model="currentQuestion.difficulty"
                  :items="difficultyOptions"
                  item-title="label"
                  item-value="value"
                  label="题目难度"
                  class="mb-4"
                  style="max-width: 200px"
                  hide-details
                  density="comfortable"
                ></v-select>

                <!-- 分数设置 -->
                <v-text-field
                  v-model.number="currentQuestion.maxScore"
                  label="满分分数"
                  type="number"
                  min="0"
                  step="0.5"
                  style="max-width: 200px"
                  class="mb-4"
                  hide-details
                ></v-text-field>                <!-- 题目操作区 -->
                <div class="d-flex justify-space-between align-center mt-4">
                  <div class="d-flex gap-2">
                    <v-btn
                      prepend-icon="mdi-arrow-up"
                      variant="outlined"
                      :disabled="!canMoveUp || !isEditingExistingQuestion"
                      @click="moveQuestion('up')"
                    >
                      上移
                    </v-btn>
                    <v-btn
                      prepend-icon="mdi-arrow-down"
                      variant="outlined"
                      :disabled="!canMoveDown || !isEditingExistingQuestion"
                      @click="moveQuestion('down')"
                    >
                      下移
                    </v-btn>
                    <v-btn
                      prepend-icon="mdi-delete"
                      variant="outlined"
                      color="error"
                      :disabled="!isEditingExistingQuestion"
                      @click="deleteQuestion"
                    >
                      删除题目
                    </v-btn>
                  </div>
                  <div class="d-flex gap-2">
                    <!-- 编辑模式下的按钮 -->
                    <template v-if="isEditingExistingQuestion">
                      <v-btn
                        color="warning"
                        variant="outlined"
                        prepend-icon="mdi-cancel"
                        @click="cancelEdit"
                      >
                        取消编辑
                      </v-btn>
                      <v-btn
                        color="success"
                        prepend-icon="mdi-content-save"
                        @click="saveQuestionEdit"
                      >
                        保存修改
                      </v-btn>
                    </template>
                    <!-- 创建模式下的按钮 -->
                    <template v-else>
                      <v-btn
                        color="primary"
                        prepend-icon="mdi-plus"
                        @click="addQuestion"
                      >
                        添加新题
                      </v-btn>
                    </template>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- 右侧预览区 -->
      <v-card class="preview-section" width="400">
        <v-card-title class="d-flex align-center">
          <v-icon start>mdi-eye</v-icon>
          作业预览
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="preview-content">
          <!-- 基本信息预览 -->
          <div class="preview-header mb-4">
            <h3 class="text-h6">{{ assignment.title || '作业标题' }}</h3>
            <p class="text-body-2 text-medium-emphasis">
              课程：{{ getCurrentCourseName }}
            </p>
            <p class="text-body-2 text-medium-emphasis">
              截止日期：{{ assignment.dueDate || '未设置' }}
            </p>
          </div>          <!-- 题目列表预览 -->
          <div class="questions-preview">
            <div
              v-for="(question, index) in assignment.questions"
              :key="index"
              class="question-preview-item mb-6 clickable-question"
              :class="{ 'editing-question': isEditingExistingQuestion && currentQuestionIndex === index }"
              @click="selectQuestion(index)"
            >
              <div class="d-flex align-start">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  :color="isEditingExistingQuestion && currentQuestionIndex === index ? 'error' : (currentQuestionIndex === index ? 'primary' : 'grey')"
                  class="question-number me-2"
                  @click.stop="selectQuestion(index)"
                >
                  {{ index + 1 }}
                </v-btn>
                <div class="flex-grow-1">
                  <!-- 题型标识 -->
                  <v-chip
                    size="small"
                    :color="getQuestionTypeColor(question.type)"
                    class="mb-2"
                  >
                    {{ getQuestionTypeText(question.type) }}
                  </v-chip>

                  <!-- 难度标识 -->
                  <v-chip
                    size="small"
                    :color="getDifficultyColor(question.difficulty)"
                    class="mb-2 ms-2"
                  >
                    {{ getDifficultyText(question.difficulty) }}
                  </v-chip>

                  <!-- 题干 -->
                  <p class="text-body-1 mb-4" v-if="!['blank'].includes(question.type)">{{ question.content }}</p>

                  <!-- 选项（单选/多选） -->
                  <template v-if="['single', 'multiple'].includes(question.type)">
                    <v-radio-group
                      v-if="question.type === 'single'"
                      :model-value="null"
                      disabled
                    >
                      <v-radio
                        v-for="(option, optIndex) in question.options"
                        :key="optIndex"
                        :label="String.fromCharCode(65 + optIndex) + '. ' + option.content"
                        :value="optIndex"
                      ></v-radio>
                    </v-radio-group>

                    <v-radio-group
                      v-else
                      :model-value="[]"
                      disabled
                      multiple
                    >
                      <v-radio
                        v-for="(option, optIndex) in question.options"
                        :key="optIndex"
                        :label="String.fromCharCode(65 + optIndex) + '. ' + option.content"
                        :value="optIndex"
                      ></v-radio>
                    </v-radio-group>
                  </template>

                  <!-- 填空 -->
                  <template v-else-if="question.type === 'blank'">
                    <div class="blank-preview" v-html="formatBlankQuestion(question.content)"></div>
                  </template>

                  <!-- 大题 -->
                  <template v-else-if="question.type === 'essay'">
                    <v-textarea
                      disabled
                      placeholder="在此作答..."
                      rows="4"
                      variant="outlined"
                      density="comfortable"
                    ></v-textarea>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- 定时发布对话框 -->
    <v-dialog v-model="showScheduleDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          定时发布
          <v-spacer></v-spacer>
          <v-btn icon @click="showScheduleDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <p class="text-body-1 mb-4">请选择作业发布时间：</p>
          <v-card variant="outlined">
            <v-date-picker
              v-model="scheduleDate"
              @update:model-value="() => {}"
              class="border-0"
            ></v-date-picker>
            <v-divider></v-divider>
            <v-card-text class="pa-3">
              <v-text-field
                v-model="scheduleTime"
                type="time"
                label="发布时间"
                hide-details
                density="comfortable"
                prepend-inner-icon="mdi-clock-outline"
              ></v-text-field>
            </v-card-text>
          </v-card>
          <div class="d-flex align-center mt-4">
            <v-icon icon="mdi-clock-check" class="me-2" color="primary"></v-icon>
            <span class="text-body-2">预计发布时间：{{ scheduleDate  +" " + scheduleTime || '未设置' }}</span>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="showScheduleDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="publishAssignment(true)"
            :disabled="!isValidScheduleTime"
          >
            确定
          </v-btn>
        </v-card-actions>
        <div v-if="!isValidScheduleTime" class="text-caption text-error px-4 pb-4">
          {{ scheduleTimeErrorMessage }}
        </div>
      </v-card>
    </v-dialog>

    <!-- 题库导入弹窗 -->
    <QuestionBankSelectDialog
      v-model:show="showImportFromBank"
      :courseOptions="courseOptions"
      @import-questions="handleImportQuestionsFromBank"
    />
  </v-container>

  <!-- 通知提示 -->
  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    timeout="3000"
    location="top right"
  >
    {{ snackbar.message }}
    <template v-slot:actions>
      <v-btn icon @click="snackbar.show = false">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../stores/userStore';
import courseService from '../../api/courseService';
import assignmentService from '../../api/assignmentService';
import QuestionBankSelectDialog from './components/QuestionBankSelectDialog.vue';

const router = useRouter();
const userStore = useUserStore();

const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
})

// 设置页面布局
defineOptions({
  layout: 'teacher'
});

// 基础数据
const showDatePicker = ref(false);
const loadingCourses = ref(false);
const saving = ref(false);
const publishing = ref(false);

// 课程列表
const courses = ref<Array<{ id: string; name: string }>>([]);

// 课程选项（用于题库导入）
const courseOptions = computed(() => courses.value.map((c:any) => ({ title: c.name, value: c.id })));

// 定义Question接口
interface Question {
  type: 'single' | 'multiple' | 'blank' | 'essay';
  content: string;
  options: Array<{ content: string; isCorrect: boolean }>;
  answers?: string;
  reference?: string;
  explanation?: string;
  maxScore: number;
  difficulty?: string;  // 添加难度字段
  courseId?: string;  // 添加courseId字段，表示题目所属课程ID
}

// 作业数据
const assignment = ref<{
  title: string;
  courseId: string | null;
  dueDate: string;
  publishTime?: string;
  questions: Question[];
}>({
  title: '',
  courseId: null,
  dueDate: '',
  questions: []
});

// 题型定义
const questionTypes = [
  { title: '单选题', value: 'single' as const, icon: 'mdi-radiobox-marked' },
  { title: '多选题', value: 'multiple' as const, icon: 'mdi-checkbox-marked' },
  { title: '填空题', value: 'blank' as const, icon: 'mdi-form-textbox' },
  { title: '问答题', value: 'essay' as const, icon: 'mdi-text' }
];

// 难度选项定义
const difficultyOptions = [
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' }
];

// 当前编辑的题型和题目
const currentQuestionType = ref('single');
const currentQuestion = ref({
  type: 'single',
  content: '',
  options: [] as { content: string; isCorrect: boolean }[],
  answers: '',
  reference: '',
  explanation: '',
  maxScore: 5,  // 修改默认分数为5分
  difficulty: 'medium'  // 添加默认难度
});

// 当前编辑状态：是否正在编辑已有题目
const isEditingExistingQuestion = ref(false);
const editingQuestionIndex = ref(-1);

function showSnackbar(message: string, color: string = 'success') {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

// 获取当前选中课程名称
const getCurrentCourseName = computed(() => {
  const course = courses.value.find(c => c.id === assignment.value.courseId);
  return course ? course.name : '未选择课程';
});

// 题目移动控制
const currentQuestionIndex = ref(0);
const canMoveUp = computed(() => currentQuestionIndex.value > 0);
const canMoveDown = computed(() => {
  return currentQuestionIndex.value < assignment.value.questions.length - 1;
});

// 截止日期相关
const tempDueDate = ref('');
const tempDueTime = ref(new Date().toTimeString().substr(0, 5));

// 修复时区问题：创建本地时间格式化函数
const formatLocalDateTime = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  const second = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
};

// 格式化日期时间显示
const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return '';
  const dateTime = new Date(dateTimeStr);
  const date = dateTime.toISOString().split('T')[0];
  const time = dateTime.toTimeString().substr(0, 5);
  return `${date} ${time}`;
};

// 确认截止日期和时间
const confirmDueDateTime = () => {
  if (tempDueDate.value && tempDueTime.value) {
    const [hours, minutes] = tempDueTime.value.split(':').map(Number);
    const dueDateTime = new Date(tempDueDate.value);
    dueDateTime.setHours(hours, minutes, 0, 0);
    
    // 修复时区问题：直接使用本地时间字符串，避免UTC转换
    const year = dueDateTime.getFullYear();
    const month = String(dueDateTime.getMonth() + 1).padStart(2, '0');
    const day = String(dueDateTime.getDate()).padStart(2, '0');
    const hour = String(dueDateTime.getHours()).padStart(2, '0');
    const minute = String(dueDateTime.getMinutes()).padStart(2, '0');
    const second = String(dueDateTime.getSeconds()).padStart(2, '0');
    
    assignment.value.dueDate = `${year}-${month}-${day} ${hour}:${minute}:${second}`;
    showDatePicker.value = false;
  }
};

// 加载课程列表
const loadCourses = async () => {
  loadingCourses.value = true;
  try {
    const response = await courseService.getCourses()
    if (response.data && response.data.code === 200) {
      courses.value = response.data.data.list || []
    }
  } catch (error) {
    console.error('获取课程列表失败:', error)
    showSnackbar('获取课程列表失败', 'error')
  } finally {
    loadingCourses.value = false;
  }
};

// 选项操作
const addOption = () => {
  currentQuestion.value.options.push({
    content: '',
    isCorrect: false
  });
};

const removeOption = (index: number) => {
  currentQuestion.value.options.splice(index, 1);
};

const someOtherOptionIsCorrect = (currentIndex: number) => {
  return currentQuestion.value.options.some((opt, idx) => idx !== currentIndex && opt.isCorrect);
};

// 题目操作
const addQuestion = () => {
  // 验证是否选择了课程
  if (!assignment.value.courseId) {
    showSnackbar('请先选择关联课程', 'error');
    return;
  }

  const question = {
    type: currentQuestionType.value as 'single' | 'multiple' | 'blank' | 'essay',
    content: currentQuestion.value.content,
    options: currentQuestionType.value === 'single' || currentQuestionType.value === 'multiple'
      ? [...currentQuestion.value.options]
      : [],
    answers: currentQuestionType.value === 'blank' ? currentQuestion.value.answers : '',
    reference: currentQuestionType.value === 'essay' ? currentQuestion.value.reference : '',
    explanation: currentQuestion.value.explanation,
    maxScore: Number(currentQuestion.value.maxScore) || 5,  // 确保是数字类型
    difficulty: currentQuestion.value.difficulty, // 保持难度
    courseId: assignment.value.courseId || undefined
  };
  console.log(currentQuestion);
  if(currentQuestion.value.content === ''){
    showSnackbar('请输入题干内容', 'error');
    console.log('请输入题目内容');
    return;
  }
  if(currentQuestion.value.options.length === 0 && (currentQuestionType.value === 'single' || currentQuestionType.value === 'multiple')){
    showSnackbar('请添加选项', 'error');
    console.log('请添加选项');
    return;
  }
  if(currentQuestion.value.answers === '' && currentQuestionType.value === 'blank'){
    showSnackbar('请输入答案', 'error');
    console.log('请输入答案');
    return;
  }
  if(currentQuestion.value.options.some(opt => opt.isCorrect) === false && (currentQuestionType.value === 'single' || currentQuestionType.value === 'multiple')){
    showSnackbar('请选择正确答案', 'error');
    console.log('请选择正确答案');
    return;
  }

  assignment.value.questions.push(question);
  // 打印所有题目数据
  console.log('所有题目数据:', assignment.value.questions);
  // 新增：打印当前题目的知识点（本地暂不可用，后端保存后可通过接口获取）
// 移除不存在的keywords属性的打印
  // 新增：保存题目后打印题目内容、选项、答案等详细信息
  console.log('题目内容:', question.content);
  console.log('题目选项:', question.options);
  console.log('题目答案:', question.answers);
  console.log('题目分数:', question.maxScore);
  
  // 重置当前题目
  currentQuestion.value = {
    type: currentQuestionType.value,
    content: '',
    options: [] as { content: string; isCorrect: boolean }[],
    answers: '',
    reference: '',
    explanation: '',
    maxScore: 5,  // 保持默认分数
    difficulty: 'medium' // 保持默认难度
  };
};

// 保存题目编辑
const saveQuestionEdit = () => {
  // 验证题目内容
  if(currentQuestion.value.content === ''){
    showSnackbar('请输入题干内容', 'error');
    return;
  }
  if(currentQuestion.value.options.length === 0 && (currentQuestionType.value === 'single' || currentQuestionType.value === 'multiple')){
    showSnackbar('请添加选项', 'error');
    return;
  }
  if(currentQuestion.value.answers === '' && currentQuestionType.value === 'blank'){
    showSnackbar('请输入答案', 'error');
    return;
  }
  if(currentQuestion.value.options.some(opt => opt.isCorrect) === false && (currentQuestionType.value === 'single' || currentQuestionType.value === 'multiple')){
    showSnackbar('请选择正确答案', 'error');
    return;
  }

  // 更新题目数据
  const updatedQuestion = {
    type: currentQuestionType.value as 'single' | 'multiple' | 'blank' | 'essay',
    content: currentQuestion.value.content,
    options: currentQuestionType.value === 'single' || currentQuestionType.value === 'multiple'
      ? [...currentQuestion.value.options]
      : [],
    answers: currentQuestionType.value === 'blank' ? currentQuestion.value.answers : '',
    reference: currentQuestionType.value === 'essay' ? currentQuestion.value.reference : '',
    explanation: currentQuestion.value.explanation,
    maxScore: Number(currentQuestion.value.maxScore) || 5,
    difficulty: currentQuestion.value.difficulty, // 保持难度
    courseId: assignment.value.courseId || undefined
  };

  assignment.value.questions[editingQuestionIndex.value] = updatedQuestion;
  
  showSnackbar('题目修改成功', 'success');
  
  // 退出编辑模式
  cancelEdit();
};

// 取消编辑
const cancelEdit = () => {
  isEditingExistingQuestion.value = false;
  editingQuestionIndex.value = -1;
  currentQuestionIndex.value = -1;
  
  // 重置编辑器
  currentQuestion.value = {
    type: currentQuestionType.value,
    content: '',
    options: [] as { content: string; isCorrect: boolean }[],
    answers: '',
    reference: '',
    explanation: '',
    maxScore: 5,
    difficulty: 'medium' // 保持默认难度
  };
};

const moveQuestion = (direction: 'up' | 'down') => {
  if (!isEditingExistingQuestion.value) return;
  
  const questions = assignment.value.questions;
  const newIndex = direction === 'up'
    ? currentQuestionIndex.value - 1
    : currentQuestionIndex.value + 1;

  if (newIndex >= 0 && newIndex < questions.length) {
    const temp = questions[currentQuestionIndex.value];
    questions[currentQuestionIndex.value] = questions[newIndex];
    questions[newIndex] = temp;
    currentQuestionIndex.value = newIndex;
    editingQuestionIndex.value = newIndex;
  }
};

const deleteQuestion = () => {
  if (!isEditingExistingQuestion.value) return;
  
  assignment.value.questions.splice(currentQuestionIndex.value, 1);
  showSnackbar('题目删除成功', 'success');
  
  // 退出编辑模式
  cancelEdit();
};

// 格式化填空题显示
const formatBlankQuestion = (content: string) => {
  return content.replace(/____/g, '<span class="blank-line">________</span>');
};

// 获取题型文本和颜色
const getQuestionTypeText = (type: 'single' | 'multiple' | 'blank' | 'essay') => {
  const typeMap = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '大题'
  } as const;
  return typeMap[type];
};

const getQuestionTypeColor = (type: 'single' | 'multiple' | 'blank' | 'essay') => {
  const colorMap = {
    single: 'primary',
    multiple: 'success',
    blank: 'info',
    essay: 'warning'
  } as const;
  return colorMap[type];
};

// 获取难度文本和颜色
const getDifficultyText = (difficulty: string | undefined) => {
  const difficultyMap = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  } as const;
  return difficultyMap[difficulty || 'medium'];
};

const getDifficultyColor = (difficulty: string | undefined) => {
  const colorMap = {
    easy: 'success',
    medium: 'info',
    hard: 'error'
  } as const;
  return colorMap[difficulty || 'medium'];
};

// 保存和发布
const validateAssignment = () => {
  const errors: string[] = [];
  
  if (!assignment.value.title) {
    console.log('请输入作业标题');
    showSnackbar('请输入作业标题', 'error');
    return false;
  }
  if (!assignment.value.courseId) {
    console.log('请选择关联课程');
    showSnackbar('请选择关联课程', 'error');
    return false;
  }
  if (!assignment.value.dueDate) {
    showSnackbar('请选择截止日期', 'error');
    return false;
  }
  if (assignment.value.questions.length === 0) {
    showSnackbar('请至少添加一道题目', 'error');
    return false;
  }

  // 检查每道题目
  assignment.value.questions.forEach((question, index) => {
    if (!question.content) {
      errors.push(`第 ${index + 1} 题题干不能为空`);
    }
    if (['single', 'multiple'].includes(question.type)) {
      if (!question.options.length) {
        errors.push(`第 ${index + 1} 题至少需要一个选项`);
      }
      if (question.type === 'single' && !question.options.some(opt => opt.isCorrect)) {
        errors.push(`第 ${index + 1} 题未设置正确答案`);
      }
    }
    if (question.type === 'blank' && !question.answers) {
      errors.push(`第 ${index + 1} 题未设置答案`);
    }
  });

  if (errors.length > 0) {
    showSnackbar(errors[0], 'error');
    return false;
  }
  return true;
};

const saveAsDraft = async () => {
  if (!validateAssignment()) return;

  saving.value = true;
  try {
    console.log('保存草稿数据:', {
      title: assignment.value.title,
      courseId: assignment.value.courseId,
      dueDate: assignment.value.dueDate,
      questions: assignment.value.questions
    });

    const response = await assignmentService.createDraft({
      title: assignment.value.title,
      courseId: String(assignment.value.courseId),
      dueDate: assignment.value.dueDate,
      questions: assignment.value.questions,
      teacherId: userStore.userId,
      publishTime: undefined
    });

    if (response.data && response.data.code === 200) {
      console.log('发布成功，返回数据:', response.data);
      // 新增：遍历题目ID，获取并打印每题关联知识点
      const assignmentData = response.data.data;
      if (assignmentData && assignmentData.questions && Array.isArray(assignmentData.questions)) {
        for (const q of assignmentData.questions) {
          if (q.id) {
            assignmentService.getExtractedKeywords(q.id).then((res: any) => {
              const keywords = res.data?.data?.extracted_keywords || [];
              console.log(`[作业题目] 题目ID: ${q.id}, 关联知识点:`, keywords, '题目信息:', q);
            }).catch((e: Error) => {
              console.error(`[作业题目] 题目ID: ${q.id} 关联知识点获取失败`, e);
            });
          }
        }
      }
      showSnackbar(assignment.value.publishTime ? '作业已设置定时发布' : '发布成功', 'success');
      router.push('/assignments');
    } else {
      showSnackbar(response.data?.message || '保存失败', 'error');
    }
  } catch (error: any) {
    console.error('保存草稿失败:', error);
    showSnackbar(error.response?.data?.message || '保存失败，请稍后重试', 'error');
  } finally {
    saving.value = false;
  }
};

// 定时发布相关
const showScheduleDialog = ref(false);
const showScheduleDatePicker = ref(false);
const scheduleDate = ref(new Date().toISOString().split('T')[0]);
const scheduleTime = ref(new Date().toTimeString().substr(0, 5));

const scheduleTimeErrorMessage = computed(() => {
  if (!scheduleDate.value || !scheduleTime.value) {
    return '请选择发布时间';
  }

  try {
    const now = new Date();
    const [scheduleHours, scheduleMinutes] = scheduleTime.value.split(':').map(Number);
    const scheduledDateTime = new Date(scheduleDate.value);
    scheduledDateTime.setHours(scheduleHours, scheduleMinutes, 0, 0);

    // 检查是否在当前时间之后
    if (scheduledDateTime <= now) {
      return '发布时间必须在当前时间之后';
    }

    // 检查是否在截止时间之前
    if (assignment.value.dueDate) {
      const dueDateTime = new Date(assignment.value.dueDate);
      if (scheduledDateTime >= dueDateTime) {
        return '发布时间必须在截止时间之前';
      }
    }

    return '';
  } catch (error) {
    console.error('时间验证出错:', error);
    return '时间格式错误';
  }
});

const isValidScheduleTime = computed(() => {
  return scheduleTimeErrorMessage.value === '';
});

const publishAssignment = async (isScheduled = false) => {
  if (!validateAssignment()) {
    return;
  }

  publishing.value = true;
  try {
    // 不需要转换courseId为数字类型，保持字符串UUID
    const courseId = assignment.value.courseId;
    if (!courseId) {
      showSnackbar('请选择关联课程', 'error');
      return;
    }

    // 设置发布时间
    if (isScheduled) {
      const [scheduleHours, scheduleMinutes] = scheduleTime.value.split(':').map(Number);
      const scheduledDateTime = new Date(scheduleDate.value);
      scheduledDateTime.setHours(scheduleHours, scheduleMinutes, 0, 0);
      assignment.value.publishTime = formatLocalDateTime(scheduledDateTime);
      showScheduleDialog.value = false;
    } else {
      assignment.value.publishTime = undefined; // 后端会自动使用服务器当前时间
    }

    // 打印发送的数据
    const requestData = {
      title: assignment.value.title,
      courseId: courseId,
      dueDate: assignment.value.dueDate,
      publishTime: assignment.value.publishTime,
      questions: assignment.value.questions,
      teacherId: userStore.userId
    };

    const response = await assignmentService.publishAssignment(requestData);

    if (response.data && response.data.code === 200) {
      console.log('发布成功，返回数据:', response.data);
      showSnackbar(isScheduled ? '作业已设置定时发布' : '发布成功', 'success');
      router.push('/assignments');
    } else {
      showSnackbar(response.data?.message || '发布失败', 'error');
    }
  } catch (error) {
    console.error('发布作业失败:', error);
    showSnackbar('发布失败，请稍后重试', 'error');
  } finally {
    publishing.value = false;
  }
};

// 题型切换处理
const handleQuestionTypeChange = (newType: 'single' | 'multiple' | 'blank' | 'essay') => {
  // 如果正在编辑已有题目，且题型发生变化，则清空输入框
  if (isEditingExistingQuestion.value && currentQuestion.value.type !== newType) {
    currentQuestion.value = {
      type: newType,
      content: '',
      options: [] as { content: string; isCorrect: boolean }[],
      answers: '',
      reference: '',
      explanation: '',
      maxScore: 5,
      difficulty: 'medium' // 保持默认难度
    };
  } else if (!isEditingExistingQuestion.value && currentQuestion.value.type !== newType) {
    // 如果是新建题目且题型发生变化，也清空输入框
    currentQuestion.value = {
      type: newType,
      content: '',
      options: [] as { content: string; isCorrect: boolean }[],
      answers: '',
      reference: '',
      explanation: '',
      maxScore: 5,
      difficulty: 'medium' // 保持默认难度
    };
  }
  currentQuestionType.value = newType;
};

// 题目选择
const selectQuestion = (index: number) => {
  currentQuestionIndex.value = index;
  // 进入编辑模式
  isEditingExistingQuestion.value = true;
  editingQuestionIndex.value = index;
  
  // 同时更新当前编辑的题目类型和内容
  const selectedQuestion = assignment.value.questions[index];
  currentQuestionType.value = selectedQuestion.type;
  currentQuestion.value = {
    type: selectedQuestion.type,
    content: selectedQuestion.content,
    options: selectedQuestion.type === 'single' || selectedQuestion.type === 'multiple'
      ? [...selectedQuestion.options]
      : [],
    answers: selectedQuestion.type === 'blank' ? selectedQuestion.answers || '' : '',
    reference: selectedQuestion.type === 'essay' ? selectedQuestion.reference || '' : '',
    explanation: selectedQuestion.explanation || '',
    maxScore: selectedQuestion.maxScore || 5,  // 保持分数
    difficulty: selectedQuestion.difficulty || 'medium' // 保持难度
  };
};

// 题库导入相关
const showImportFromBank = ref(false);

// 清理选项内容，去除重复的前缀
function cleanOptionContent(option: string, index: number): string {
  if (!option || typeof option !== 'string') return option;
  
  // 定义可能的前缀模式
  const expectedPrefix = String.fromCharCode(65 + index) + '.'; // A., B., C., D.
  const expectedPrefixWithSpace = String.fromCharCode(65 + index) + '. '; // A. , B. , C. , D. 
  
  // 如果选项以期望的前缀开头，就去除它
  if (option.startsWith(expectedPrefixWithSpace)) {
    return option.substring(expectedPrefixWithSpace.length).trim();
  } else if (option.startsWith(expectedPrefix)) {
    return option.substring(expectedPrefix.length).trim();
  }
  
  // 也处理其他可能的前缀格式，如 "A)"、"(A)"等
  const otherPrefixes = [
    String.fromCharCode(65 + index) + ')',
    String.fromCharCode(65 + index) + ') ',
    '(' + String.fromCharCode(65 + index) + ')',
    '(' + String.fromCharCode(65 + index) + ') '
  ];
  
  for (const prefix of otherPrefixes) {
    if (option.startsWith(prefix)) {
      return option.substring(prefix.length).trim();
    }
  }
  
  return option.trim();
}

function handleImportQuestionsFromBank(selectedQuestions: any[]) {
  // 将题库题目转为作业题目格式并批量添加
  if (!selectedQuestions || !selectedQuestions.length) return;
  
  console.log('导入题目数据:', selectedQuestions); // 调试日志
  
  selectedQuestions.forEach((q, qIndex) => {
    const questionType = q.question_type;    // 根据题型从正确的字段获取答案
    let correctAnswerField = '';
    if (questionType === 'blank') {
      // 填空题：答案存储在 reference 字段中
      correctAnswerField = q.reference || '';
      console.log(`填空题答案检查: reference="${q.reference}"`);
    } else if (questionType === 'essay') {
      // 问答题：参考答案存储在 reference 字段中
      correctAnswerField = q.reference || '';
      console.log(`问答题答案检查: reference="${q.reference}"`);
    } else if (questionType === 'single') {
      // 单选题：答案存储在 answer 字段中
      correctAnswerField = q.answer || q.correct_answer || '';
      console.log(`单选题答案检查: answer="${q.answer}", correct_answer="${q.correct_answer}"`);
    } else if (questionType === 'multiple') {
      // 多选题：答案存储在 answers 字段中
      correctAnswerField = q.answers || q.correct_answer || '';
      console.log(`多选题答案检查: answers="${q.answers}", correct_answer="${q.correct_answer}"`);
    }
      console.log(`题目 ${qIndex + 1} 完整数据:`, q);
    console.log(`题目 ${qIndex + 1} 答案字段映射结果:`, {
      questionType: questionType,
      字段映射策略: {
        填空题: 'reference',
        问答题: 'reference', 
        单选题: 'answer',
        多选题: 'answers'
      },
      数据库字段值: {
        reference: q.reference,
        answer: q.answer,
        answers: q.answers,
        correct_answer: q.correct_answer
      },
      最终使用答案: correctAnswerField,
      hasOptions: !!(q.options && q.options.length)
    });
    
    // 处理选项和正确答案
    let processedOptions: { content: string; isCorrect: boolean }[] = [];
    
    if (['single', 'multiple'].includes(questionType) && q.options && q.options.length > 0) {
      // 如果是选择题且有选项，处理正确答案标记
      processedOptions = q.options.map((opt: string, index: number) => {
        let isCorrect = false;
        
        if (correctAnswerField) {
          if (questionType === 'single') {
            // 单选题：答案可能是 "A"、"0"、"D"，或者选项内容
            let correctIndex = -1;
            
            console.log(`单选题答案解析: "${correctAnswerField}", 类型: ${typeof correctAnswerField}`);
            
            // 确保答案字段是字符串类型
            const answerStr = String(correctAnswerField || '').trim();
            
            // 先尝试解析为数字索引
            const numIndex = parseInt(answerStr);
            if (!isNaN(numIndex)) {
              correctIndex = numIndex;
            } else if (answerStr.length === 1 && /^[A-Za-z]$/.test(answerStr)) {
              // 单个字母格式："A", "B", "C", "D"
              correctIndex = answerStr.toUpperCase().charCodeAt(0) - 65;
            } else {
              // 尝试作为选项内容查找对应索引
              const foundIndex = q.options.findIndex((option: string) => {
                const cleanOption = cleanOptionContent(option, 0);
                return cleanOption === answerStr;
              });
              if (foundIndex >= 0) {
                correctIndex = foundIndex;
                console.log(`单选题答案选项内容 "${answerStr}" 对应索引: ${correctIndex}`);
              } else {
                console.warn(`无效的单选题答案: "${answerStr}"`);
              }
            }
            
            isCorrect = correctIndex === index;
            console.log(`单选题选项 ${index}: ${opt}, 正确答案索引: ${correctIndex}, 是否正确: ${isCorrect}`);} else if (questionType === 'multiple') {
            // 多选题：答案可能是 "AB"、"0,1"、"A,C"，或者选项内容数组
            let correctIndices: number[] = [];
            
            console.log(`多选题答案解析: "${correctAnswerField}", 类型: ${typeof correctAnswerField}`);
            
            // 处理数组格式的答案（选项内容数组）
            if (Array.isArray(correctAnswerField)) {
              console.log(`多选题答案为数组格式:`, correctAnswerField);
              correctIndices = correctAnswerField.map((answerContent: string) => {
                // 在选项中查找匹配的内容
                const foundIndex = q.options.findIndex((option: string) => {
                  const cleanOption = cleanOptionContent(option, 0);
                  const cleanAnswer = String(answerContent).trim();
                  return cleanOption === cleanAnswer;
                });
                if (foundIndex >= 0) {
                  console.log(`找到答案选项 "${answerContent}" 对应索引: ${foundIndex}`);
                  return foundIndex;
                } else {
                  console.warn(`未找到答案选项 "${answerContent}" 对应的索引`);
                  return -1;
                }
              }).filter(idx => idx >= 0);            } else {
              // 处理字符串格式的答案
              const answerStr = String(correctAnswerField || '').trim();
              
              // 优先检查连续字母格式（新格式）："AB"、"ACD"等
              if (/^[A-Za-z]+$/.test(answerStr) && answerStr.length <= 10) {
                correctIndices = answerStr.split('').map((char: string) => {
                  if (/^[A-Za-z]$/.test(char)) {
                    return char.toUpperCase().charCodeAt(0) - 65;
                  }
                  return -1;
                }).filter(idx => idx >= 0);
                console.log(`字母格式解析成功: "${answerStr}" -> 索引:`, correctIndices);
              }
              // 如果字母格式解析没有结果，尝试作为选项内容处理（逗号分隔的选项内容）
              else if (answerStr.includes(',') && answerStr.length > 3) {
                const parts = answerStr.split(',').map((s: string) => s.trim()).filter(s => s);
                console.log(`尝试解析为选项内容:`, parts);
                
                // 尝试将每部分作为选项内容查找索引
                const contentIndices = parts.map((part: string) => {
                  const foundIndex = q.options.findIndex((option: string) => {
                    const cleanOption = cleanOptionContent(option, 0);
                    return cleanOption === part;
                  });
                  return foundIndex >= 0 ? foundIndex : -1;
                }).filter(idx => idx >= 0);
                
                if (contentIndices.length > 0) {
                  correctIndices = contentIndices;
                  console.log(`选项内容解析成功:`, correctIndices);
                } else {
                  // 如果选项内容解析失败，回退到传统的索引解析
                  console.log(`选项内容解析失败，回退到索引解析`);
                  correctIndices = parts.map((part: string) => {
                    // 先检查是否是纯数字
                    const numIndex = parseInt(part);
                    if (!isNaN(numIndex)) {
                      return numIndex;
                    }
                    
                    // 检查是否是单个字母
                    if (part.length === 1 && /^[A-Za-z]$/.test(part)) {
                      return part.toUpperCase().charCodeAt(0) - 65;
                    }
                    
                    console.warn(`无效的答案部分: "${part}"`);
                    return -1;
                  }).filter(idx => idx >= 0);
                }
              } else {
                // 连续字母格式："ABC" 或 数字格式："123"
                correctIndices = answerStr.split('').map((char: string) => {
                  // 先检查是否是纯数字
                  const numIndex = parseInt(char);
                  if (!isNaN(numIndex)) {
                    return numIndex;
                  }
                  
                  // 检查是否是单个字母
                  if (/^[A-Za-z]$/.test(char)) {
                    return char.toUpperCase().charCodeAt(0) - 65;
                  }
                  
                  console.warn(`无效的答案字符: "${char}"`);
                  return -1;
                }).filter(idx => idx >= 0);
              }
            }
            
            isCorrect = correctIndices.includes(index);
            console.log(`多选题选项 ${index}: ${opt}, 正确答案索引: ${correctIndices}, 是否正确: ${isCorrect}`);
          }
        }
        
        // 清理选项内容，去除可能的前缀
        const cleanedContent = cleanOptionContent(opt, index);
        
        return { content: cleanedContent, isCorrect };
      });
      
      console.log(`题目 ${qIndex + 1} 处理后的选项:`, processedOptions);
    } else if (['single', 'multiple'].includes(questionType)) {
      // 如果是选择题但没有选项，创建默认的空选项（避免重复）
      processedOptions = [
        { content: '', isCorrect: false },
        { content: '', isCorrect: false },
        { content: '', isCorrect: false },
        { content: '', isCorrect: false }
      ];
    }
    
    const newQuestion = {
      type: questionType,
      content: q.content,
      options: processedOptions,      answers: (() => {
        // 根据题型处理答案字段
        if (questionType === 'blank') {
          // 填空题：从 reference 字段获取答案，存储到 answers 字段（前端统一使用 answers 字段）
          return q.reference || '';
        } else if (questionType === 'single') {
          // 单选题：从 answer 字段获取答案，存储到 answers 字段
          return q.answer || q.correct_answer || '';
        } else if (questionType === 'multiple') {
          // 多选题：从 answers 字段获取答案，存储到 answers 字段
          return q.answers || q.correct_answer || '';
        } else {
          return '';
        }
      })(),
      reference: questionType === 'essay' ? (q.reference || '') : '',
      explanation: q.explanation || '',
      maxScore: 5,
      difficulty: q.difficulty || 'medium', // 从题库导入时也保持难度
      courseId: assignment.value.courseId || undefined
    };
    
    console.log(`题目 ${qIndex + 1} 最终数据:`, newQuestion);
    assignment.value.questions.push(newQuestion);
  });
    // 统计刚导入的题目中正确设置答案的数量
  const importedQuestions = assignment.value.questions.slice(-selectedQuestions.length);
  let correctlySetCount = 0;
  
  importedQuestions.forEach(q => {
    if (['single', 'multiple'].includes(q.type)) {
      // 选择题：检查是否有正确选项
      if (q.options.some(opt => opt.isCorrect)) {
        correctlySetCount++;
      }
    } else if (q.type === 'blank') {
      // 填空题：检查是否有答案
      if (q.answers && q.answers.trim()) {
        correctlySetCount++;
      }
    } else if (q.type === 'essay') {
      // 问答题：检查是否有参考答案
      if (q.reference && q.reference.trim()) {
        correctlySetCount++;
      }
    }
  });
  
  showSnackbar(`已导入${selectedQuestions.length}道题目，其中${correctlySetCount}道题目答案已自动设置`, 'success');
}

// 生命周期
onMounted(() => {
  loadCourses();
});
</script>

<style scoped>
.create-assignment {
  height: calc(100vh - 64px); /* 减去顶部导航栏的高度 */
  overflow-y: auto;
  padding: 16px;
}

.question-type-item {
  cursor: pointer;
  border-radius: 4px;
  margin: 4px 0;
}

.question-type-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.option-label {
  min-width: 24px;
  text-align: center;
}

.preview-section {
  height: calc(100vh - 200px);
  overflow-y: auto;
}

.preview-content {
  padding: 16px;
}

.question-number {
  width: 28px !important;
  height: 28px !important;
  min-width: unset !important;
  border-radius: 50%;
  font-weight: 500;
  font-size: 14px;
}

.question-number:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.blank-line {
  display: inline-block;
  min-width: 100px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.6);
  margin: 0 4px;
}

:deep(.v-card-text) {
  padding: 24px;
}

.editing-question {
  border: 2px solid rgba(var(--v-theme-warning), 0.5);
  border-radius: 8px;
  padding: 12px;
  background-color: rgba(var(--v-theme-warning), 0.05);
}

.clickable-question {
  cursor: pointer;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.clickable-question:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.clickable-question:hover .question-number {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>