<template>
  <v-container fluid class="pa-4 question-bank-container">
    <v-card class="content-card">
      <v-card-title class="d-flex align-center py-4 px-6">
        题库管理
        <v-spacer></v-spacer>
        <!-- 这里可加搜索框等 -->
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-4">        <QuestionBankToolbar
          :courseOptions="courseOptions"
          v-model:filterCourseId="filter_course_id"
          :tagOptions="tagOptions"
          v-model:filterTag="filterTag"
          @update:type="val => filterType = val"
          @update:difficulty="val => filterDifficulty = val"
          @add="openAddDialog"
          @import="showImportDialog = true"
        /><QuestionBankTable
          :headers="headers"
          :questions="questionsTableData"
          :loading="loading"
          :courseOptions="courseOptions"
          @show-detail="showDetail"
          @edit="editQuestion"
          @delete="deleteQuestion"
        />
          <!-- 加载更多按钮 -->
        <div v-if="!loading && hasMoreQuestions" class="text-center mt-4">
          <v-btn 
            color="primary" 
            variant="outlined"
            :loading="loadingMore"
            @click="loadMoreQuestions"
            prepend-icon="mdi-download"
            class="mb-2"
          >
            {{ loadingMore ? '加载中...' : getLoadMoreButtonText() }}
          </v-btn>
          
          <!-- 自动加载提示 -->
          <div class="text-caption text-grey">
            <v-icon size="14">mdi-information</v-icon>
            滚动到底部时将自动加载更多题目
          </div>
        </div>
        
        <!-- 全部加载完成提示 -->
        <div v-if="!loading && !hasMoreQuestions && questions.length > 0" class="text-center mt-4">
          <v-chip color="success" variant="tonal">
            <v-icon start>mdi-check-circle</v-icon>
            {{ getCompletionText() }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>
    <QuestionBankFormDialog
      v-model:show="showAddDialog"
      :editMode="editMode"
      :form="form"
      :questionTypes="questionTypes"
      :difficultyOptions="difficultyOptions"
      :courseOptions="courseOptions"
      @submit="submitForm"
      @cancel="showAddDialog = false"
      @type-change="onTypeChange"
      @add-option="addOption"
      @remove-option="removeOption"
    />
    <QuestionBankDetailDialog
      v-model:show="showDetailDialog"
      :detailItem="detailItem"
      :getTypeLabel="getTypeLabel"
      :getDifficultyLabel="getDifficultyLabel"
      :getCourseName="getCourseName"
    />
    <QuestionBankImportDialog
      v-model:show="showImportDialog"
      :courseOptions="courseOptions"
      @imported="fetchQuestions"
    />
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="2000">{{ snackbar.text }}</v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import courseService from '../../api/courseService';
import questionBankService from '../../api/questionBankService';
import { extractQuestionKeywords, getExtractedKeywords } from '../../api/index';
import QuestionBankToolbar from './components/QuestionBankToolbar.vue';
import QuestionBankTable from './components/QuestionBankTable.vue';
import QuestionBankFormDialog from './components/QuestionBankFormDialog.vue';
import QuestionBankDetailDialog from './components/QuestionBankDetailDialog.vue';
import QuestionBankImportDialog from './components/QuestionBankImportDialog.vue';

const questions = ref<Array<any & {extractedKeywords?: string[];}>>([]);
const loading = ref(false);
const loadingMore = ref(false); // 加载更多状态
const totalQuestions = ref(0); // 题目总数
const currentPage = ref(1); // 当前页码
const pageSize = ref(20); // 每页大小
const filterType = ref('');
const filterDifficulty = ref('');
const filterTag = ref('');

// 缓存机制
const questionCache = ref(new Map()); // 缓存不同筛选条件下的题目
const getCacheKey = () => filter_course_id.value || 'all';

// 自动加载机制
const autoLoadEnabled = ref(true);
const isNearBottom = ref(false);
const loadStartTime = ref(0);
const lastLoadTime = ref(0);
const courses = ref<Array<{ id: string; name: string }>>([]);
const filter_course_id = ref('');
const courseOptions = computed(() => courses.value.map((c:any) => ({ 
  title: c.name, 
  value: c.id,
  teacher_name: c.teacher_name  // 传递教师名称
})));
const tagOptions = computed(() => {
  const set = new Set();
  questions.value.forEach((q:any) => {
    if (Array.isArray(q.tags)) q.tags.forEach((t:string) => set.add(t));
  });
  return Array.from(set);
});
const headers = [
  { text: 'ID', value: 'id', align: 'center', width: 60 },
  { text: '题目内容', value: 'content', width: 200 },
  { text: '题型', value: 'question_type', width: 80 },
  { text: '课程', value: 'course_id', width: 80 },
  { text: '难度', value: 'difficulty', width: 80 },
  { text: '标签', value: 'tags', width: 120 },
  { text: '选项', value: 'options', width: 120 },
  { text: '答案', value: 'answer', width: 120 },
  { text: '解析', value: 'explanation', width: 120 },
  { text: '备注', value: 'remark', width: 120 },
  { text: '操作', value: 'actions', sortable: false, align: 'center', width: 120 },
];
const questionTypes = [
  { title: '单选题', value: 'single' },
  { title: '多选题', value: 'multiple' },
  { title: '填空题', value: 'blank' },
  { title: '问答题', value: 'essay' },
];
const difficultyOptions = [
  { title: '简单', value: 'easy' },
  { title: '中等', value: 'medium' },
  { title: '困难', value: 'hard' },
];
const showAddDialog = ref(false);
const showImportDialog = ref(false);
const showDetailDialog = ref(false);
const editMode = ref(false);
const form = ref<any>({});
const detailItem = ref<any>({});
const snackbar = ref({ show: false, text: '', color: 'success' });

// 新增：为题目获取知识点
async function fetchAndSetKeywordsForQuestion(questionId: string) {
  try {
    await extractQuestionKeywords(questionId);
    // 等待一段时间再查（可优化为轮询或后端推送）
    await new Promise(res => setTimeout(res, 1200));
    const res = await getExtractedKeywords(questionId);
    const keywords = res.data?.data?.extracted_keywords || [];
    // 控制台打印调试
    console.log(`[关键词提取] 题目ID: ${questionId}, 关联知识点:`, keywords, '完整返回：', res.data);
    // 更新 questions 列表中对应题目的 extractedKeywords 字段
    const q = questions.value.find((q: any) => q.id === questionId);
    if (q) q.extractedKeywords = keywords;
  } catch (e) {
    // 可选：错误处理
    console.error(`[关键词提取] 题目ID: ${questionId} 关联词获取失败`, e);
  }
}

const fetchQuestions = async () => {
  const cacheKey = getCacheKey();
  
  // 检查缓存
  if (questionCache.value.has(cacheKey)) {
    const cached = questionCache.value.get(cacheKey);
    questions.value = cached.questions;
    totalQuestions.value = cached.total;
    currentPage.value = cached.page;
    lastLoadTime.value = 0; // 缓存加载，无需记录时间
    console.log(`⚡ 从缓存快速加载题目：${questions.value.length} 道，缓存键：${cacheKey}`);
    return;
  }
  
  loadStartTime.value = Date.now();
  loading.value = true;
  try {
    // 使用分页API，默认只加载前20条
    const params = {
      page: 1,
      pageSize: 20, // 首次只加载20条，提升加载速度
      ...(filter_course_id.value ? { course_id: filter_course_id.value } : {})
    };
    console.log('正在快速加载题目，参数:', params);
    const res = await questionBankService.getQuestionsPaginated(params);
    questions.value = res.data.list || [];
    
    // 存储总数，用于显示"加载更多"按钮
    totalQuestions.value = res.data.total || 0;
    currentPage.value = 1;
    
    // 记录加载时间
    lastLoadTime.value = Date.now() - loadStartTime.value;
    
    // 缓存结果
    questionCache.value.set(cacheKey, {
      questions: [...questions.value],
      total: totalQuestions.value,
      page: currentPage.value
    });
    
    console.log(`⚡ 快速加载完成：显示 ${questions.value.length} 道题目，总共 ${totalQuestions.value} 道，耗时 ${lastLoadTime.value}ms`);
    
    // 后端已经返回了extractedKeywords，无需重置
  } catch (error) {
    console.error('获取题目列表失败:', error);
    showSnackbar('获取题目列表失败', 'error');
  } finally {
    loading.value = false;
  }
};

// 新增：加载更多题目
const loadMoreQuestions = async () => {
  if (loadingMore.value || questions.value.length >= totalQuestions.value) return;
  
  loadingMore.value = true;
  try {
    const nextPage = currentPage.value + 1;
    const params = {
      page: nextPage,
      pageSize: pageSize.value,
      ...(filter_course_id.value ? { course_id: filter_course_id.value } : {})
    };
    
    console.log(`加载第${nextPage}页题目，参数:`, params);
    const res = await questionBankService.getQuestionsPaginated(params);
    const newQuestions = res.data.list || [];
    
    // 追加到现有题目列表
    questions.value.push(...newQuestions);
    currentPage.value = nextPage;
    
    // 更新缓存
    const cacheKey = getCacheKey();
    questionCache.value.set(cacheKey, {
      questions: [...questions.value],
      total: totalQuestions.value,
      page: currentPage.value
    });
    
    console.log(`加载完成：新增 ${newQuestions.length} 道题目，当前共 ${questions.value.length} 道`);
    
    // 后端已经返回了extractedKeywords，无需重置
  } catch (error) {
    console.error('加载更多题目失败:', error);
    showSnackbar('加载更多失败', 'error');
  } finally {
    loadingMore.value = false;
  }
};

// 新增：计算是否还有更多题目
const hasMoreQuestions = computed(() => {
  // 如果有前端筛选条件（题型、难度、标签），则基于筛选后的数据判断
  if (filterType.value || filterDifficulty.value || filterTag.value) {
    // 前端筛选时，无法准确判断后端是否还有更多数据，所以基于当前已加载的数据判断
    return questions.value.length < totalQuestions.value;
  }
  // 没有前端筛选时，正常判断
  return questions.value.length < totalQuestions.value;
});

// 新增：滚动监听，自动加载更多
const handleScroll = () => {
  if (!autoLoadEnabled.value || loadingMore.value || !hasMoreQuestions.value) return;
  
  const scrollTop = window.scrollY;
  const windowHeight = window.innerHeight;
  const documentHeight = document.documentElement.scrollHeight;
  
  // 当滚动到距离底部200px时自动加载
  if (scrollTop + windowHeight >= documentHeight - 200) {
    isNearBottom.value = true;
    loadMoreQuestions();
  } else {
    isNearBottom.value = false;
  }
};

const openAddDialog = () => {
  editMode.value = false;
  form.value = {
    question_type: '',
    options: [],
    answerIndex: null,
    answerIndices: [],
    answerStr: '',
    content: '',
    explanation: '',
    course_id: '',
    difficulty: '',
    tagsStr: '',
    remark: ''
  };
  showAddDialog.value = true;
};

const submitForm = async () => {
  if (!form.value.question_type) {
    showSnackbar('请先选择题型', 'error');
    return;
  }
  if (!form.value.course_id) {
    showSnackbar('请先选择课程', 'error');
    return;
  }

  // 1. 选项处理：去除空项，转普通数组
  let options = [];
  if (form.value.question_type === 'single' || form.value.question_type === 'multiple') {
    options = Array.isArray(form.value.options)
      ? form.value.options.map((opt: string | { content: string }) => typeof opt === 'object' ? (opt as any).content || '' : opt).filter((opt: string) => !!opt)
      : [];
  }
  // 2. 答案处理
  let answer;
  if (form.value.question_type === 'single') {
    // 单选题：存储选项索引对应的字母（A, B, C, D）
    if (form.value.answerIndex !== null && form.value.answerIndex >= 0 && form.value.answerIndex < options.length) {
      answer = String.fromCharCode(65 + form.value.answerIndex); // 0->A, 1->B, 2->C, 3->D
    } else {
      answer = '';
    }
  } else if (form.value.question_type === 'multiple') {
    // 多选题：存储选项索引对应的字母组合（如 "AB", "AC", "BCD"）
    if (Array.isArray(form.value.answerIndices) && form.value.answerIndices.length > 0) {
      answer = form.value.answerIndices
        .filter((i: number) => i >= 0 && i < options.length)
        .sort((a: number, b: number) => a - b) // 排序确保一致性
        .map((i: number) => String.fromCharCode(65 + i))
        .join(''); // 连接成字符串，如 "AB"
    } else {
      answer = '';
    }
  } else {
    answer = form.value.answerStr ? form.value.answerStr : '';
  }

  // 3. 校验
  if ((form.value.question_type === 'single' || form.value.question_type === 'multiple') && options.length === 0) {
    showSnackbar('请填写选项', 'error');
    return;
  }
  if (form.value.question_type === 'single' && !answer) {
    showSnackbar('请选择正确答案', 'error');
    return;
  }
  if (form.value.question_type === 'multiple' && (!answer || answer.length === 0)) {
    showSnackbar('请选择正确答案', 'error');
    return;
  }
  if ((form.value.question_type === 'blank' || form.value.question_type === 'essay') && !answer) {
    showSnackbar('请填写答案', 'error');
    return;
  }

  // 4. 组装payload
  const payload = {
    content: form.value.content,
    question_type: form.value.question_type,
    options: (form.value.question_type === 'single' || form.value.question_type === 'multiple') ? options : [],
    answer,
    explanation: form.value.explanation,
    course_id: form.value.course_id,
    difficulty: form.value.difficulty,
    tags: form.value.tagsStr.split(',').map((s: string) => s.trim()).filter(Boolean),
    remark: form.value.remark,
  };

  console.log('题库提交payload', payload);

  try {
    if (editMode.value) {
      await questionBankService.updateQuestion(form.value.id, payload);
      showSnackbar('题目已更新', 'success');
    } else {
      const res = await questionBankService.addQuestion(payload);      showSnackbar('题目添加成功', 'success');
      // 新增：自动提取关键词并刷新知识点
      const newId = res.data?.data?.id || res.data?.id;
      if (newId) await fetchAndSetKeywordsForQuestion(newId);
    }
    showAddDialog.value = false;
    
    // 清理缓存并重新加载
    questionCache.value.clear();
    currentPage.value = 1;
    fetchQuestions();
  } catch (error) {
    console.error('提交题目失败:', error);
    showSnackbar('提交题目失败', 'error');
  }
};

const editQuestion = (item: any) => {
  // 检查权限
  if (!item.can_edit) {
    showSnackbar('无权限编辑他人创建的题目', 'error');
    return;
  }
  
  editMode.value = true;
  
  // 清理选项文本，移除重复的选项前缀
  const cleanOptionText = (text: string, optionIndex: number): string => {
    if (!text) return text;
    
    const optionLetter = String.fromCharCode(65 + optionIndex); // A, B, C, D...
    const patterns = [
      new RegExp(`^${optionLetter}\\.\\s*`, 'i'), // 匹配 "A. " 或 "a. "
      new RegExp(`^${optionLetter}\\)\\s*`, 'i'), // 匹配 "A) " 或 "a) "
      new RegExp(`^${optionLetter}\\s+`, 'i'),    // 匹配 "A " 或 "a "
    ];
    
    let cleaned = text;
    for (const pattern of patterns) {
      cleaned = cleaned.replace(pattern, '');
    }
    
    return cleaned.trim();
  };
  
  if (item.question_type === 'single' || item.question_type === 'multiple') {
    // 清理选项文本，移除可能存在的选项前缀
    const cleanedOptions = item.options ? 
      item.options.map((opt: string, index: number) => cleanOptionText(opt, index)) : 
      ['', ''];
    form.value.options = cleanedOptions;
    
    if (item.question_type === 'single') {
      // 单选题：answers字段可能是字符串如"A"、"B"或选项内容
      let answerIndex = null;
      if (item.answers) {
        // 首先检查是否是选项字母（A、B、C、D）
        const answerLetter = item.answers.trim();
        if (/^[A-Z]$/.test(answerLetter)) {
          // 是选项字母，转换为索引
          answerIndex = answerLetter.charCodeAt(0) - 65; // A=0, B=1, C=2, D=3
        } else {
          // 不是选项字母，可能是选项内容，查找匹配的选项
          answerIndex = cleanedOptions ? cleanedOptions.findIndex((opt: string) => opt.trim() === answerLetter) : -1;
        }
        // 确保索引在有效范围内
        if (answerIndex < 0 || answerIndex >= (cleanedOptions?.length || 0)) {
          answerIndex = null;
        }
      }
      form.value.answerIndex = answerIndex;
      form.value.answerIndices = [];    } else {
      // 多选题：answers字段现在统一为字母格式如"AB"、"AC"、"BCD"
      let answerIndices: number[] = [];
      if (item.answers) {
        const answersStr = item.answers.toString().trim();
        
        // 检查是否是连续字母格式（如"AB"、"ACD"）
        if (/^[A-Z]+$/.test(answersStr)) {
          // 是连续字母格式，直接转换
          answerIndices = answersStr.split('').map((letter: string) => {
            return letter.charCodeAt(0) - 65; // A=0, B=1, C=2, D=3
          }).filter((idx: number) => idx >= 0 && idx < (cleanedOptions?.length || 0));
        } else if (answersStr.includes(',')) {
          // 兼容逗号分隔格式（向后兼容旧数据）
          const answerList = answersStr.split(',').map((s: string) => s.trim());
          
          answerIndices = answerList.map((answer: string) => {
            if (/^[A-Z]$/.test(answer)) {
              // 是选项字母，转换为索引
              return answer.charCodeAt(0) - 65;
            } else {
              // 不是选项字母，可能是选项内容
              return cleanedOptions ? cleanedOptions.findIndex((opt: string) => opt.trim() === answer) : -1;
            }
          }).filter((idx: number) => idx >= 0 && idx < (cleanedOptions?.length || 0));
        } else {
          // 其他格式，尝试作为选项内容查找
          answerIndices = [cleanedOptions ? cleanedOptions.findIndex((opt: string) => opt.trim() === answersStr) : -1]
            .filter((idx: number) => idx >= 0 && idx < (cleanedOptions?.length || 0));
        }
      }
      form.value.answerIndices = answerIndices;
      form.value.answerIndex = null;
    }
    form.value.answerStr = '';
  } else {
    form.value.options = [];
    form.value.answerIndex = null;
    form.value.answerIndices = [];
    // 填空题和问答题：直接使用answers或reference字段
    if (item.question_type === 'blank') {
      form.value.answerStr = item.answers || '';
    } else if (item.question_type === 'essay') {
      form.value.answerStr = item.reference || '';
    } else {
      form.value.answerStr = item.answers || '';
    }
  }
  form.value.id = item.id;
  form.value.content = item.content;
  form.value.question_type = item.question_type;
  form.value.explanation = item.explanation;
  form.value.course_id = item.course_id || '';
  form.value.difficulty = item.difficulty || '';
  form.value.tagsStr = item.tags ? item.tags.join(',') : '';
  form.value.remark = item.remark || '';
  showAddDialog.value = true;
};

const showDetail = (item: any) => {
  detailItem.value = { ...item };
  showDetailDialog.value = true;
};

const deleteQuestion = async (id: string) => {
  // 先找到题目检查权限
  const question = questions.value.find(q => q.id === id);
  if (!question || !question.can_edit) {
    showSnackbar('无权限删除他人创建的题目', 'error');
    return;
  }
  
  try {
    await questionBankService.deleteQuestion(id);
    showSnackbar('题目已删除', 'success');
    
    // 清理缓存并重新加载
    questionCache.value.clear();
    currentPage.value = 1;
    fetchQuestions();
  } catch (error: any) {
    console.error('删除题目失败:', error);
    const errorMsg = error.response?.data?.msg || '删除题目失败';
    showSnackbar(errorMsg, 'error');
  }
};

// 批量导入功能已移到 QuestionBankImportDialog 组件中处理

function showSnackbar(text: string, color: string) {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}

function getTypeLabel(type: string) {
  const map: any = { single: '单选题', multiple: '多选题', blank: '填空题', essay: '问答题' };
  return map[type] || type;
}
function getDifficultyLabel(diff: string) {
  const map: any = { easy: '简单', medium: '中等', hard: '困难' };
  return map[diff] || diff || '—';
}

function getCourseName(course_id: string | undefined): string | undefined {
  if (!course_id) return undefined;
  const course = courseOptions.value.find(c => c.value === course_id);
  return course ? course.title : course_id;
}

function onTypeChange() {
  if (form.value.question_type === 'single' || form.value.question_type === 'multiple') {
    if (!form.value.options.length) {
      form.value.options = ['', ''];
    }
    form.value.answerIndex = null;
    form.value.answerIndices = [];
  } else {
    form.value.options = [];
    form.value.answerIndex = null;
    form.value.answerIndices = [];
  }
  form.value.answerStr = '';
}
function addOption() {
  if (!Array.isArray(form.value.options)) form.value.options = [];
  form.value.options.push('');
}
function removeOption(idx: number) {
  form.value.options.splice(idx, 1);
  // 答案同步修正
  if (form.value.question_type === 'single') {
    if (form.value.answerIndex === idx) form.value.answerIndex = null;
    else if (form.value.answerIndex !== null && form.value.answerIndex > idx) form.value.answerIndex--;
  } else if (form.value.question_type === 'multiple') {
    form.value.answerIndices = form.value.answerIndices.filter((i: number) => i !== idx).map((i: number) => (i > idx ? i - 1 : i));
  }
}

// 新增：筛选后题目（课程筛选在后端完成，前端只处理题型、难度和标签筛选）
const questionsTableData = computed(() => {
  return questions.value.filter((q:any) => {
    const typeOk = !filterType.value || q.question_type === filterType.value;
    const diffOk = !filterDifficulty.value || q.difficulty === filterDifficulty.value;
    // 课程筛选已经在后端完成，不需要前端再次筛选
    const tagOk = !filterTag.value || (Array.isArray(q.tags) && q.tags.includes(filterTag.value));
    return typeOk && diffOk && tagOk;
  });
});

// 新增：获取加载更多按钮文本
const getLoadMoreButtonText = () => {
  const hasFilter = filterType.value || filterDifficulty.value || filterTag.value;
  if (hasFilter) {
    // 有前端筛选时，显示筛选后的剩余数量
    const filteredCount = questionsTableData.value.length;
    const remainingFromTotal = totalQuestions.value - questions.value.length;
    return `手动加载更多 (当前筛选显示 ${filteredCount} 道，还可加载 ${remainingFromTotal} 道)`;
  } else {
    // 无前端筛选时，显示总的剩余数量
    const remaining = totalQuestions.value - questions.value.length;
    return `手动加载更多 (还有 ${remaining} 道题目)`;
  }
};

// 新增：获取完成提示文本
const getCompletionText = () => {
  const hasFilter = filterType.value || filterDifficulty.value || filterTag.value;
  if (hasFilter) {
    const filteredCount = questionsTableData.value.length;
    return `已加载全部 ${questions.value.length} 道题目，当前筛选显示 ${filteredCount} 道`;
  } else {
    return `已显示全部 ${totalQuestions.value} 道题目`;
  }
};

// 监听课程筛选条件变化，重新获取题目数据
watch(filter_course_id, (newCourseId, oldCourseId) => {
  console.log('=== 课程筛选条件变化 ===');
  console.log('旧值:', oldCourseId);
  console.log('新值:', newCourseId);
  console.log('当前filter_course_id.value:', filter_course_id.value);
  // 重置分页状态
  currentPage.value = 1;
  fetchQuestions();
}, { 
  // 不在初始化时立即执行，避免重复请求
  immediate: false 
});

// 监听前端筛选条件变化，清理缓存以确保数据一致性
watch([filterType, filterDifficulty, filterTag], () => {
  console.log('=== 前端筛选条件变化 ===');
  console.log('题型筛选:', filterType.value);
  console.log('难度筛选:', filterDifficulty.value);
  console.log('标签筛选:', filterTag.value);
  // 前端筛选变化时不需要重新请求数据，但需要清理缓存以防止状态混乱
  // 注意：这里不调用 fetchQuestions()，因为前端筛选是基于已有数据进行的
}, { 
  immediate: false 
});

onMounted(() => {
  // 获取全平台课程列表用于筛选
  courseService.getAllCourses().then(res => {
    courses.value = res.data.data.list || [];
  }).catch(error => {
    console.error('获取课程列表失败:', error);
    // 如果全平台课程获取失败，回退到只获取自己的课程
    courseService.getCourses().then(res => {
      courses.value = res.data.data.list || [];
    });
  });
  
  // 添加滚动监听
  window.addEventListener('scroll', handleScroll, { passive: true });
  
  fetchQuestions();
});

onUnmounted(() => {
  // 清理滚动监听
  window.removeEventListener('scroll', handleScroll);
});
</script>

<style scoped>
.question-bank-container {
  background: #f5f6fa;
  padding-left: 0 !important;
  padding-right: 0 !important;
}
.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: block;
  width: 100%;
  min-height: unset !important;
  height: auto !important;
  overflow: visible !important;
}
:deep(.content-area) {
  overflow-y: visible !important;
}
</style>