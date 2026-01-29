<template>
  <v-dialog :model-value="show" @update:modelValue="(val:boolean) => emit('update:show', val)" max-width="1200px">
    <v-card>
      <v-card-title>从题库导入题目</v-card-title>
      <v-card-text>
        <!-- 筛选栏 -->
        <div class="filter-bar mb-3">
          <v-text-field v-model="search" label="关键词" dense clearable style="min-width: 150px" @keyup.enter="fetchQuestions" />
          <v-select v-model="filterType" :items="typeOptions" label="题型" dense clearable style="min-width: 120px" @change="fetchQuestions" />
          <v-select v-model="filterDifficulty" :items="difficultyOptions" label="难度" dense clearable style="min-width: 120px" @change="fetchQuestions" />
          <v-select v-model="filter_course_id" :items="courseOptions" item-title="title" item-value="value" label="课程" dense clearable style="min-width: 120px" @change="fetchQuestions" />
          <v-select v-model="filterTag" :items="tagOptions" label="标签" dense clearable style="min-width: 120px" @change="fetchQuestions" />
          <v-spacer></v-spacer>
          <span class="selected-count">已选：{{ selected.length }} 题</span>
        </div>
        
        <!-- 题目表格 -->
        <v-data-table
          :headers="headers"
          :items="questions"
          :loading="loading"
          :items-per-page="8"
          :page.sync="page"
          :server-items-length="total"
          item-key="id"
          v-model:selected="selected"
          class="elevation-1 compact-table"
          density="compact"
          @click:row="toggleSelect"
          :row-props="getRowProps"
          hide-default-footer
        >
          <template v-slot:item.content="{ item }">
            <div class="content-cell" :class="{ 'selected-content': selected.some(q => q.id === item.id) }">
              {{ item.content }}
            </div>
          </template>
          <template v-slot:item[headers[0].value]="{ item }">
            <div class="d-flex align-center" :class="{ 'selected-cell': selected.some(q => q.id === item.id) }">
            <v-checkbox
              :model-value="selected.some(q => q.id === item.id)"
              @click.stop="toggleSelectCheckbox(item)"
              class="mr-2"
              density="compact"
                color="primary"
            />
            <span class="content-cell">{{ item.content }}</span>
              <div 
                v-if="selected.some(q => q.id === item.id)"
                class="ms-2 selected-indicator-group d-flex align-center"
              >
                <v-chip
                  color="primary"
                  size="x-small"
                  variant="flat"
                  class="selected-number me-1"
                >
                  第{{ getSelectedIndex(item) }}题
                </v-chip>
                <v-icon 
                  color="primary" 
                  size="16"
                  class="selected-check"
                >
                  mdi-check-circle
                </v-icon>
              </div>
            </div>
          </template>
          <template v-slot:item.question_type="{ item }">
            <v-chip 
              :color="typeColor(item.question_type)" 
              size="x-small" 
              class="type-chip"
              :variant="selected.some(q => q.id === item.id) ? 'flat' : 'tonal'"
            >
              {{ typeLabel(item.question_type) }}
            </v-chip>
          </template>
          <template v-slot:item.difficulty="{ item }">
            <v-chip 
              :color="difficultyColor(item.difficulty)" 
              size="x-small" 
              class="type-chip"
              :variant="selected.some(q => q.id === item.id) ? 'flat' : 'tonal'"
            >
              {{ difficultyLabel(item.difficulty) }}
            </v-chip>
          </template>
          <template v-slot:item.tags="{ item }">
            <div class="tags-cell" :class="{ 'selected-tags': selected.some(q => q.id === item.id) }">
              <v-chip 
                v-if="item.tags && item.tags.length" 
                :color="difficultyColor(item.difficulty)" 
                size="x-small" 
                class="mr-1"
                :variant="selected.some(q => q.id === item.id) ? 'flat' : 'tonal'"
              >
                {{ item.tags[0] }}
              </v-chip>
              <span v-if="item.tags && item.tags.length > 1" class="more-tags">+{{ item.tags.length - 1 }}</span>
            </div>
          </template>
          <template v-slot:item.remark="{ item }">
            <div class="remark-cell" :class="{ 'selected-remark': selected.some(q => q.id === item.id) }">
              {{ item.remark || '—' }}
            </div>
          </template>
          <template v-slot:item.course_id="{ item }">
            <span :class="{ 'selected-text': selected.some(q => q.id === item.id) }">
              {{ getCourseName(item.course_id) || '—' }}
            </span>
          </template>
        </v-data-table>
        
        <!-- 分页器 -->
        <div class="d-flex justify-center mt-2">
          <v-pagination v-model="page" :length="Math.ceil(total/pageSize)" color="primary" />
        </div>
        
        <!-- 已选题目胶囊展示区 -->
        <div v-if="selected.length > 0" class="selected-questions-section mt-4">
          <div class="selected-header d-flex align-center mb-3">
            <v-icon color="primary" class="me-2">mdi-check-circle</v-icon>
            <span class="selected-title">已选择的题目</span>
            <v-chip 
              color="primary" 
              size="small" 
              variant="tonal"
              class="ms-2"
            >
              {{ selected.length }} 题
            </v-chip>
            <v-spacer></v-spacer>
            <v-btn 
              variant="text" 
              size="small" 
              color="error"
              prepend-icon="mdi-delete-sweep"
              @click="clearAllSelected"
            >
              清空所有
            </v-btn>
          </div>
          
          <!-- 胶囊型题目列表 -->
          <div class="selected-questions-chips">
            <v-chip
              v-for="(question, index) in selected"
              :key="question.id"
              :color="typeColor(question.question_type)"
              variant="tonal"
              closable
              class="question-chip ma-1"
              @click:close="removeFromSelected(question)"
            >
              <v-icon 
                :icon="getQuestionTypeIcon(question.question_type)" 
                size="16" 
                class="me-1"
              ></v-icon>
              <span class="question-chip-text">
                第{{ index + 1 }}题 {{ typeLabel(question.question_type) }}
              </span>
              <template v-slot:append>
                <v-tooltip text="点击查看完整题目" location="top">
                  <template v-slot:activator="{ props }">
                    <v-icon 
                      v-bind="props"
                      size="14" 
                      class="ms-1 preview-icon"
                      @click.stop="showQuestionPreview(question)"
                    >
                      mdi-eye
                    </v-icon>
                  </template>
                </v-tooltip>
              </template>
            </v-chip>
          </div>
          
          <!-- 题目预览卡片 -->
          <v-expand-transition>
            <v-card 
              v-if="previewQuestion" 
              class="preview-card mt-3" 
              variant="outlined"
            >
              <v-card-text class="pa-3">
                <div class="d-flex align-center mb-2">
                  <v-chip 
                    :color="typeColor(previewQuestion.question_type)" 
                    size="small"
                    variant="tonal"
                    class="me-2"
                  >
                    {{ typeLabel(previewQuestion.question_type) }}
                  </v-chip>
                  <v-chip 
                    :color="difficultyColor(previewQuestion.difficulty)" 
                    size="small"
                    variant="outlined"
                    class="me-2"
                  >
                    {{ difficultyLabel(previewQuestion.difficulty) }}
                  </v-chip>
                  <v-spacer></v-spacer>
                  <v-btn 
                    icon="mdi-close" 
                    variant="text" 
                    size="small"
                    @click="previewQuestion = null"
                  ></v-btn>
                </div>
                <div class="question-preview-content">
                  <strong>题目内容：</strong>{{ previewQuestion.content }}
                </div>
                
                <!-- 显示选项（单选题和多选题） -->
                <div v-if="previewQuestion.options && previewQuestion.options.length > 0" class="question-preview-options mt-3">
                  <strong>选项：</strong>
                  <div class="options-list mt-2">
                    <div 
                      v-for="(option, index) in previewQuestion.options" 
                      :key="index"
                      class="option-item d-flex align-center mb-1"
                      :class="{ 'correct-option': option.isCorrect }"
                    >
                      <span class="option-label me-2">{{ String.fromCharCode(65 + index) }}.</span>
                      <span class="option-content">{{ cleanOptionText(option, index) }}</span>
                      <v-icon 
                        v-if="isCorrectOption(previewQuestion, index)"
                        color="success" 
                        size="16" 
                        class="ms-2"
                      >
                        mdi-check-circle
                      </v-icon>
                    </div>
                  </div>
                </div>
                  <!-- 显示答案（填空题和问答题） -->
                <div v-if="getCorrectAnswerByType(previewQuestion) && ['blank', 'essay'].includes(previewQuestion.question_type)" class="question-preview-answer mt-3">
                  <strong>参考答案：</strong>
                  <div class="answer-content mt-1">{{ getCorrectAnswerByType(previewQuestion) }}</div>
                </div>
                
                <div v-if="previewQuestion.remark" class="question-preview-remark mt-2">
                  <strong>备注：</strong>{{ previewQuestion.remark }}
                </div>
              </v-card-text>
            </v-card>
          </v-expand-transition>
        </div>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="emit('update:show', false)">取消</v-btn>
        <v-btn color="primary" :disabled="!selected.length" @click="importSelected">导入所选题目</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
import questionBankService from '../../../api/questionBankService';
const props = defineProps({ 
  show: { type: Boolean, default: false },
  courseOptions: { type: Array as () => Array<{title: string, value: string}>, default: () => [] }
});
const emit = defineEmits(['update:show', 'import-questions']);
const questions = ref<any[]>([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(8);
const total = ref(0);
const selected = ref<any[]>([]);
const search = ref('');
const filterType = ref('');
const filterDifficulty = ref('');
const filter_course_id = ref('');
const filterTag = ref('');
const tagOptions = ref<string[]>([]);
const previewQuestion = ref<any>(null);
const headers = [
  { text: '题干', value: 'content', align: 'start', width: 280, sortable: false },
  { text: '题型', value: 'question_type', align: 'center', width: 70, sortable: false },
  { text: '难度', value: 'difficulty', align: 'center', width: 70, sortable: false },
  { text: '标签', value: 'tags', align: 'center', width: 80, sortable: false },
  { text: '课程', value: 'course_id', align: 'center', width: 80, sortable: false },
  { text: '备注', value: 'remark', align: 'start', width: 120, sortable: false }
];
const typeOptions = [
  { title: '全部', value: '' },
  { title: '单选题', value: 'single' },
  { title: '多选题', value: 'multiple' },
  { title: '填空题', value: 'blank' },
  { title: '问答题', value: 'essay' }
];
const difficultyOptions = [
  { title: '全部', value: '' },
  { title: '简单', value: 'easy' },
  { title: '普通', value: 'medium' },
  { title: '困难', value: 'hard' }
];
function getCourseName(course_id: string | undefined): string | undefined {
  if (!course_id) return undefined;
  const course = props.courseOptions.find(c => c.value === course_id);
  return course ? course.title : course_id;
}
async function fetchQuestions() {
  loading.value = true;
  try {
    const res = await questionBankService.getQuestionsPaginated({
      page: page.value,
      pageSize: pageSize.value,
      type: filterType.value,
      difficulty: filterDifficulty.value,
      course_id: filter_course_id.value,
      tag: filterTag.value,
      keyword: search.value
    });
    questions.value = res.data.list;
    total.value = res.data.total;
    // 自动聚合所有标签
    const set = new Set<string>();
    res.data.list.forEach((q: any) => {
      if (Array.isArray(q.tags)) q.tags.forEach((t: string) => set.add(t));
    });
    tagOptions.value = Array.from(set);
  } catch (error) {
    console.error('获取题目列表失败:', error);
  } finally {
    loading.value = false;
  }
}
function importSelected() {
  // 强制赋值course_id为当前筛选课程ID
  const course_id = filter_course_id.value;
  const selectedWithCourse = selected.value.map(q => ({ ...q, course_id }));
  emit('import-questions', selectedWithCourse);
  emit('update:show', false);
}
function typeLabel(type: string) {
  const map: any = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '问答题'
  };
  return map[type] || type;
}
function typeColor(type: string) {
  return type === 'single' ? 'primary' : type === 'multiple' ? 'success' : type === 'blank' ? 'info' : type === 'essay' ? 'warning' : 'grey';
}
function difficultyLabel(diff: string) {
  const map: any = { easy: '简单', medium: '普通', hard: '困难' };
  return map[diff] || diff || '—';
}
function difficultyColor(diff: string) {
  return diff === 'easy' ? 'success' : diff === 'medium' ? 'info' : diff === 'hard' ? 'error' : 'grey';
}

// 新增：获取题型对应的图标
function getQuestionTypeIcon(type: string) {
  const iconMap: any = {
    single: 'mdi-radiobox-marked',
    multiple: 'mdi-checkbox-multiple-marked',
    blank: 'mdi-form-textbox',
    essay: 'mdi-text-box-outline'
  };
  return iconMap[type] || 'mdi-help-circle-outline';
}

// 新增：清空所有选中的题目
function clearAllSelected() {
  selected.value = [];
  previewQuestion.value = null;
}

// 新增：移除单个选中的题目
function removeFromSelected(question: any) {
  const index = selected.value.findIndex(q => q.id === question.id);
  if (index !== -1) {
    selected.value.splice(index, 1);
  }
  // 如果移除的是正在预览的题目，关闭预览
  if (previewQuestion.value && previewQuestion.value.id === question.id) {
    previewQuestion.value = null;
  }
}

// 新增：显示题目预览
function showQuestionPreview(question: any) {
  previewQuestion.value = previewQuestion.value?.id === question.id ? null : question;
}

// 新增：判断选项是否为正确答案
function isCorrectOption(question: any, optionIndex: number) {
  if (!question || !question.correct_answer) return false;
  
  // 处理单选题答案（如 "A" 或 "0"）
  if (question.question_type === 'single') {
    const correctIndex = question.correct_answer.charCodeAt(0) - 65; // A=0, B=1, C=2, D=3
    return correctIndex === optionIndex;
  }
  
  // 处理多选题答案（如 "AB" 或 "AC"）
  if (question.question_type === 'multiple') {
    const correctOptions = question.correct_answer.split('').map((char: string) => char.charCodeAt(0) - 65);
    return correctOptions.includes(optionIndex);
  }
  
  return false;
}

// 新增：清理选项文本，去除重复的前缀
function cleanOptionText(option: string, index: number) {
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

// 根据题型获取正确的答案字段显示
function getCorrectAnswerByType(item: any): string {
  if (!item) return '';
  
  if (item.question_type === 'blank') {
    // 填空题：从 reference 字段获取答案
    return item.reference || '';
  } else if (item.question_type === 'essay') {
    // 问答题：从 reference 字段获取答案
    return item.reference || '';
  } else if (item.question_type === 'single') {
    // 单选题：从 answer 字段获取答案
    return item.answer || item.correct_answer || '';
  } else if (item.question_type === 'multiple') {
    // 多选题：从 answers 字段获取答案
    const answers = item.answers || item.correct_answer || '';
    return Array.isArray(answers) ? answers.join(', ') : answers;
  }
  
  // 兜底逻辑：使用原来的 answer 字段
  return Array.isArray(item.answer) ? item.answer.join(', ') : (item.answer || '');
}

// 新增：为表格行设置样式属性
function getRowProps(props: any) {
  const item = props.item;
  const isSelected = selected.value.some(q => q.id === item.id);
  return {
    class: isSelected ? 'selected-row' : '',
    style: isSelected ? 'background-color: #e3f2fd !important; border-left: 4px solid #1976d2;' : ''
  };
}

// 新增：获取选中题目的序号
function getSelectedIndex(item: any) {
  const index = selected.value.findIndex(q => q.id === item.id);
  return index !== -1 ? index + 1 : 0;
}
// 新增：点击整行切换选中，点击多选框也能切换
function toggleSelect(event: any, row: any) {
  // 如果点击的是多选框本身，交给v-data-table默认逻辑
  if (event?.target?.closest('.v-simple-checkbox, .v-checkbox')) return;
  if (!row || !row.item) return;
  const item = row.item;
  const idx = selected.value.findIndex((q: any) => q.id === item.id);
  if (idx === -1) {
    selected.value.push(item);
  } else {
    selected.value.splice(idx, 1);
  }
}
// 新增：多选框点击逻辑
function toggleSelectCheckbox(item: any) {
  const idx = selected.value.findIndex((q: any) => q.id === item.id);
  if (idx === -1) {
    selected.value.push(item);
  } else {
    selected.value.splice(idx, 1);
  }
}
watch(() => props.show, val => { if (val) fetchQuestions(); });
watch([page, pageSize, search, filterType, filterDifficulty, filter_course_id, filterTag], fetchQuestions);
watch(selected, (val) => {
  console.log('勾选后selected:', val);
});
</script>
<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  flex-wrap: wrap;
}
.selected-count {
  font-weight: 600;
  color: #1976d2;
  font-size: 14px;
}
.compact-table {
  font-size: 14px;
}
.compact-table :deep(thead) {
  display: table-header-group !important;
}
.compact-table :deep(th) {
  display: table-cell !important;
  height: 40px !important;
  background: #f7f8fa;
  font-weight: 600;
  color: #222;
}
.compact-table :deep(td) {
  vertical-align: middle !important;
  padding-top: 6px !important;
  padding-bottom: 6px !important;
  font-size: 13px;
}
.compact-table :deep(tr:hover) {
  background: #f0f6ff !important;
}

/* 选中行样式 */
.compact-table :deep(.selected-row) {
  background: #e3f2fd !important;
  border-left: 4px solid #1976d2 !important;
  box-shadow: inset 0 0 0 1px rgba(25, 118, 210, 0.2) !important;
}

.compact-table :deep(.selected-row:hover) {
  background: #bbdefb !important;
}

.selected-content {
  font-weight: 600 !important;
  color: #1976d2 !important;
}

.selected-cell {
  background: rgba(25, 118, 210, 0.05);
  border-radius: 4px;
  padding: 4px 8px;
}

.selected-indicator-group {
  animation: checkPulse 0.3s ease-in-out;
}

.selected-number {
  font-size: 10px !important;
  height: 18px !important;
  font-weight: 600 !important;
}

.selected-check {
  animation: checkBounce 0.3s ease-in-out;
}

@keyframes checkBounce {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes checkPulse {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 选中状态的其他元素样式 */
.selected-text {
  font-weight: 600 !important;
  color: #1976d2 !important;
}

.selected-remark {
  font-weight: 500 !important;
  color: #1976d2 !important;
}

.selected-tags .more-tags {
  font-weight: 600 !important;
  color: #1976d2 !important;
}
.content-cell {
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
}
.remark-cell {
  max-width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
}
.type-chip {
  font-size: 11px;
  height: 20px;
}
.tags-cell {
  display: flex;
  align-items: center;
}
.more-tags {
  font-size: 11px;
  color: #666;
  margin-left: 2px;
}

/* 已选题目区域样式 */
.selected-questions-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e0e0e0;
}

.selected-header {
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.selected-title {
  font-size: 16px;
  font-weight: 600;
  color: #1976d2;
}

.selected-questions-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-start;
}

.question-chip {
  max-width: 280px;
  height: auto !important;
  padding: 8px 12px !important;
  border-radius: 20px !important;
  font-size: 13px;
  transition: all 0.2s ease;
}

.question-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.question-chip-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  font-weight: 500;
}

.preview-icon {
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.preview-icon:hover {
  opacity: 1;
}

.preview-card {
  background: #fff;
  border-left: 4px solid #1976d2;
}

.question-preview-content {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}

.question-preview-remark {
  font-size: 13px;
  color: #666;
  font-style: italic;
}

/* 题目预览选项样式 */
.question-preview-options {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
  border-left: 3px solid #4caf50;
}

.options-list {
  margin-left: 8px;
}

.option-item {
  padding: 4px 0;
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.option-item.correct-option {
  background: rgba(76, 175, 80, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.option-label {
  font-weight: 600;
  color: #333;
  min-width: 24px;
}

.option-content {
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
}

.question-preview-answer {
  background: #e3f2fd;
  border-radius: 6px;
  padding: 12px;
  border-left: 3px solid #2196f3;
}

.answer-content {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
  font-weight: 500;
}
</style>