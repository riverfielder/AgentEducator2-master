<template>
  <v-container class="graded-detail-root px-0">
    <!-- AI Agent 悬浮按钮（右上角） -->
    <v-btn class="ai-fab-top" color="deep-purple" dark fab @click="onAIAgent">
      <v-icon>mdi-robot</v-icon>
      向AI提问
    </v-btn>
    <v-drawer v-model="showAIAssistant" location="right" width="700" :scrim="true" temporary>
      <AIAssistant v-if="showAIAssistant" />
    </v-drawer>
    <!-- 顶部信息区 -->
    <v-card class="assignment-header-card elevation-12 pa-8 mb-10 mx-auto">
      <v-card-title class="d-flex align-center justify-space-between mb-4">
        <div class="d-flex align-center">
          <span class="text-h4 font-weight-bold text-deep-purple">{{ assignment.title }}</span>
          <v-chip class="ml-4" color="success" v-if="assignment.status === 'marked'">已评分</v-chip>
          <v-chip class="ml-4" color="warning" v-else>未评分</v-chip>
        </div>
        <div class="text-h4 text-primary font-weight-bold">总分：{{ assignment.totalScore }}/{{ assignment.maxTotalScore }}</div>
      </v-card-title>
      <v-card-subtitle class="mb-2 text-grey-darken-1 text-body-1">
        课程：<span class="font-weight-bold text-indigo-darken-2">{{ assignment.courseName || '未知课程' }}</span>
        &nbsp;|&nbsp; 截止：<span class="font-weight-bold">{{ assignment.dueDate || '未知' }}</span>
      </v-card-subtitle>
    </v-card>
    <!-- 题目分组卡片 -->
    <div class="question-group-list mx-auto">
      <v-card v-for="(q, idx) in assignment.questions" :key="idx" class="question-card elevation-4 pa-6 mb-8">
        <div class="d-flex align-center mb-3">
          <div class="question-index-circle mr-3">{{ idx + 1 }}</div>
          <span class="font-weight-bold text-body-1 text-indigo-darken-2">{{ getTypeText(q.question_type) }}</span>
          <v-chip size="small" color="success" class="ml-4 font-weight-bold">
            得分：{{ (q.score === null || q.score === undefined || String(q.score) === '') ? '--' : Number(q.score) }}/{{ q.max_score }}
          </v-chip>
          <v-chip size="small" :color="q.is_correct ? 'success' : 'error'" class="ml-2">
            {{ q.is_correct ? '正确' : '错误' }}
          </v-chip>
        </div>
        <div class="mb-4 text-body-1 font-weight-medium question-content">{{ q.question_content }}</div>
        
        <!-- 选择题选项显示 -->
        <template v-if="q.question_type === 'single' || q.question_type === 'multiple'">
          <div class="option-list mb-4">
            <div v-for="(option, i) in q.options" :key="i" class="option-item"
              :class="{
                'selected': isSelected(q, i),
                'correct': isCorrect(q, i),
                'unselected': !isSelected(q, i) && !isCorrect(q, i)
              }">
              <span class="option-label">{{ String.fromCharCode(65 + i) }}.</span>
              <span class="option-content">{{ option.content }}</span>
              <v-icon v-if="isCorrect(q, i)" color="success" size="20" class="ml-1">mdi-check-circle</v-icon>
              <v-icon v-if="isSelected(q, i) && !isCorrect(q, i)" color="error" size="20" class="ml-1">mdi-close-circle</v-icon>
            </div>
          </div>
        </template>
        
        <!-- 学生答案显示 -->
        <v-row>
          <v-col cols="12" md="6">
            <v-alert type="info" class="mb-2" border="start" color="primary" variant="tonal">
              <template #prepend>
                <v-icon color="primary">mdi-account</v-icon>
              </template>
              <span class="font-weight-bold">我的答案：</span>
              {{ formatStudentAnswer(q) }}
            </v-alert>
          </v-col>
          <v-col cols="12" md="6">
            <v-alert type="success" class="mb-2" border="start" color="success" variant="tonal">
              <template #prepend>
                <v-icon color="success">mdi-check-circle</v-icon>
              </template>
              <span class="font-weight-bold">参考答案：</span>
              {{ formatReferenceAnswer(q) }}
            </v-alert>
          </v-col>
        </v-row>
          <!-- 解析 -->
        <v-alert v-if="q.explanation" type="info" class="mb-2" border="start" color="deep-purple" variant="tonal">
          <template #prepend>
            <v-icon color="deep-purple">mdi-lightbulb</v-icon>
          </template>
          <span class="font-weight-bold">解析：</span>{{ q.explanation }}
        </v-alert>
        
        <!-- 批改评语 -->
        <v-alert v-if="q.comment" type="warning" class="mb-2" border="start" color="orange" variant="tonal">
          <template #prepend>
            <v-icon color="orange">mdi-comment-text</v-icon>
          </template>
          <span class="font-weight-bold">批改评语：</span>{{ q.comment }}
        </v-alert>

        <!-- 知识点标签 -->
        <div v-if="q.knowledge_points && q.knowledge_points.length > 0" class="mt-4">
          <div class="d-flex align-center">
            <v-icon color="deep-purple" size="small" class="mr-2">mdi-tag-multiple</v-icon>
            <span class="text-subtitle-2 font-weight-medium text-deep-purple">相关知识点：</span>
          </div>
          <div class="d-flex flex-wrap gap-2 mt-2">
            <v-chip
              v-for="point in q.knowledge_points"
              :key="point.id"
              size="small"
              :color="getKeywordTagColor(point.category || '')"
              variant="outlined"
              class="mr-2"
              @click="navigateToKnowledgePoint(point.id)"
            >
              {{ point.name }}
              <v-icon v-if="point.category" size="small" class="ml-1">mdi-bookmark</v-icon>
            </v-chip>
          </div>
        </div>
      </v-card>
    </div>
    
    <!-- 总评语卡片 -->
    <v-card class="elevation-4 pa-6 mx-auto mb-12 summary-card">
      <div class="d-flex align-center justify-space-between mb-2">
        <div class="text-h5 font-weight-bold text-indigo-darken-2">评分状态：</div>
        <div class="text-body-1 text-grey-darken-2">
          <v-chip :color="assignment.status === 'marked' ? 'success' : 'warning'">
            {{ assignment.status === 'marked' ? '已评分' : '未评分' }}
          </v-chip>
        </div>
      </div>
    </v-card>
  </v-container>
</template>
<script setup lang="ts">

console.log('graded detail loaded')

import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import AIAssistant from './AIAssistant.vue';
import assignmentService from '../api/assignmentService';

const router = useRouter();
const route = useRoute();

// 添加知识点相关的接口
interface KnowledgePoint {
  id: string;
  name: string;
  category?: string;
}

interface QuestionAnswer {
  question_id: string;
  question_type: 'single' | 'multiple' | 'blank' | 'essay';
  question_content: string;
  student_answer: string | number | number[] | null;  // 支持多种答案类型
  score: number;
  max_score: number;
  is_correct: boolean;
  reference_answer?: string;
  explanation?: string;
  comment?: string;  // 批改评语
  options?: Array<{ content: string; isCorrect: boolean }>;  // 选择题选项
  knowledge_points?: KnowledgePoint[];
}

interface AssignmentData {
  assignment_title: string;
  course_name?: string;
  due_date?: string;
  total_score: number;
  max_total_score: number;
  questions_and_answers: QuestionAnswer[];
  status: 'marked' | 'unmarked';
}

const assignment = ref<{
  title: string;
  courseName: string;
  dueDate: string;
  status: 'marked' | 'unmarked';
  totalScore: number;
  maxTotalScore: number;
  questions: QuestionAnswer[];
}>({
  title: '',
  courseName: '',
  dueDate: '',
  status: 'unmarked',
  totalScore: 0,
  maxTotalScore: 0,
  questions: []
});

const showAIAssistant = ref(false);

// 修改获取知识点的函数
const fetchQuestionKnowledgePoints = async (questionId: string) => {
  try {
    const response = await assignmentService.getExtractedKeywords(questionId);
    if (response.data && response.data.code === 200) {
      console.log('获取到的知识点:', response.data.data);
      // 使用 question_keywords 数组中的数据
      const keywords = response.data.data.question_keywords || [];
      return keywords.map((keyword: any) => ({
        id: keyword.keyword_id,  // 使用 keyword_id 作为导航参数
        name: keyword.keyword_name,  // 显示知识点名称
        category: keyword.keyword_category || 'specific_point'  // 使用后端返回的实际分类
      }));
    }
    return [];
  } catch (error) {
    console.error('获取题目知识点失败:', error);
    return [];
  }
};

// 添加导航函数
const navigateToKnowledgePoint = (knowledgePointId: string) => {
  router.push(`/knowledge-point/${knowledgePointId}`);
};

// 重构数据获取逻辑为独立函数
const fetchAssignmentData = async (id: string) => {
  if (!id) {
    ElMessage.error('作业ID不存在');
    router.push('/assignments');
    return;
  }
  
  try {
    const res = await assignmentService.getAssignmentMarkingInfo(id);
    if (res.data && res.data.code === 200) {
      const data: AssignmentData = res.data.data;
      
      // 获取每道题的知识点
      const questionsWithKnowledgePoints = await Promise.all(
        data.questions_and_answers.map(async (q) => {
          const knowledgePoints = await fetchQuestionKnowledgePoints(q.question_id);
          return {
            ...q,
            knowledge_points: knowledgePoints
          };
        })
      );
      
      // 映射后端数据到前端格式
      assignment.value = {
        title: data.assignment_title,
        courseName: data.course_name || '未知课程',
        dueDate: data.due_date ? formatDateTime(data.due_date) : '未知',
        status: data.status,
        totalScore: data.total_score,
        maxTotalScore: data.max_total_score,
        questions: questionsWithKnowledgePoints
      };
      
      console.log('获取到的作业数据:', assignment.value);
    } else {
      ElMessage.error(res.data?.message || '获取作业详情失败');
      router.push('/student-assignments');
    }
  } catch (e) {
    console.error('获取作业详情失败:', e);
    ElMessage.warning('教师还未批改，待会再来吧');
    router.push('/student-assignments');
  }
};

onMounted(async () => {
  const id = route.params.id;
  await fetchAssignmentData(id as string);
});

// 监听路由参数变化
watch(
  () => route.fullPath,
  async (newPath, oldPath) => {
    // 只在 student-assignments/:id/graded 路由下才拉取作业数据
    if (/^\/student-assignments\/.+\/graded$/.test(newPath)) {
      const id = route.params.id
      if (id) {
        await fetchAssignmentData(id as string)
      }
    }
  }
)

const getTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    single: '单选题',
    multiple: '多选题', 
    blank: '填空题',
    essay: '问答题'
  };
  return typeMap[type] || '未知题型';
};

// 获取知识点标签颜色
const getKeywordTagColor = (category: string) => {
  const colors = {
    core_concept: '#ff6b6b',     // 一级知识点 - 红色
    main_module: '#4ecdc4',      // 二级知识点 - 青色
    specific_point: '#45b7d1'   // 三级知识点 - 蓝色
  };
  return colors[category as keyof typeof colors] || '#cccccc';
};

// 格式化日期时间
const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return '未知';
  try {
    const date = new Date(dateTimeStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch (error) {
    console.error('时间格式化错误:', error);
    return dateTimeStr;
  }
};

const goBack = () => {
  router.back();
};

const onAIAgent = () => {
  showAIAssistant.value = true;
};

const isSelected = (question: QuestionAnswer, index: number) => {
  if (question.student_answer === null || question.student_answer === undefined) return false;
  
  if (question.question_type === 'single') {
    // 单选题：学生答案可能是数字或字符串
    const studentAnswer = question.student_answer;
    if (typeof studentAnswer === 'number') {
      return studentAnswer === index;
    } else if (typeof studentAnswer === 'string') {
      return parseInt(studentAnswer) === index;
    }
    return false;
  } else if (question.question_type === 'multiple') {
    // 多选题：学生答案应该是数组
    const studentAnswer = question.student_answer;
    if (Array.isArray(studentAnswer)) {
      return studentAnswer.includes(index);
    } else if (typeof studentAnswer === 'string') {
      try {
        const answers = JSON.parse(studentAnswer);
        return Array.isArray(answers) && answers.includes(index);
      } catch {
        return false;
      }
    }
    return false;
  }
  return false;
};

const isCorrect = (question: QuestionAnswer, index: number) => {
  if (!question.options || !question.options[index]) return false;
  return question.options[index].isCorrect;
};

const formatStudentAnswer = (question: QuestionAnswer) => {
  if (question.student_answer === null || question.student_answer === undefined) return '未作答';
  
  if (question.question_type === 'single') {
    // 单选题：显示选中的选项字母
    let index: number;
    if (typeof question.student_answer === 'number') {
      index = question.student_answer;
    } else if (typeof question.student_answer === 'string') {
      index = parseInt(question.student_answer);
    } else {
      return '未作答';
    }
    
    if (!isNaN(index) && question.options && question.options[index]) {
      return String.fromCharCode(65 + index) + '. ' + question.options[index].content;
    }
    return '未作答';
  } else if (question.question_type === 'multiple') {
    // 多选题：显示所有选中的选项
    let answers: number[];
    if (Array.isArray(question.student_answer)) {
      answers = question.student_answer;
    } else if (typeof question.student_answer === 'string') {
      try {
        answers = JSON.parse(question.student_answer);
      } catch {
        return question.student_answer;
      }
    } else {
      return '未作答';
    }
    
    if (question.options && Array.isArray(answers)) {
      return answers.map((index: number) => {
        if (question.options && question.options[index]) {
          return String.fromCharCode(65 + index) + '. ' + question.options[index].content;
        }
        return '';
      }).filter(Boolean).join('; ');
    }
    return answers.join(', ');
  }
  
  return question.student_answer;
};

const formatReferenceAnswer = (question: QuestionAnswer) => {
  if (question.question_type === 'single' || question.question_type === 'multiple') {
    if (question.options) {
      const correctOptions = question.options
        .map((option, index) => ({ ...option, index }))
        .filter(option => option.isCorrect);
      
      return correctOptions.map(option => 
        String.fromCharCode(65 + option.index) + '. ' + option.content
      ).join('; ');
    }
    return question.reference_answer || '无';
  }
  
  return question.reference_answer || '无';
};
</script>
<style scoped>
.graded-detail-root {
  min-height: 100vh;
  background: linear-gradient(120deg, #f8fafc 70%, #e3e9f7 100%);
  padding-bottom: 80px;
  padding-top: 32px;
}
.assignment-header-card {
  max-width: 900px;
  border-radius: 32px;
  box-shadow: 0 12px 48px rgba(80,120,200,0.18);
  background: #fff;
}
.question-group-list {
  max-width: 900px;
}
.question-card {
  border-radius: 24px;
  background: #f9f7fd;
  box-shadow: 0 4px 24px rgba(80,120,200,0.10);
}
.question-index-circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ede9fe 60%, #c7d2fe 100%);
  color: #6d28d9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.2rem;
  margin-right: 12px;
  box-shadow: 0 2px 8px rgba(80,120,200,0.10);
}
.option-list {
  margin-bottom: 12px;
}
.option-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-radius: 12px;
  margin-bottom: 10px;
  font-size: 1.12rem;
  background: #f4f6fb;
  border: 2px solid transparent;
  transition: background 0.2s, border 0.2s;
  box-shadow: 0 2px 8px rgba(80,120,200,0.06);
}
.option-item.selected {
  background: #ede9fe;
  border-color: #a78bfa;
  color: #6d28d9;
  font-weight: bold;
  box-shadow: 0 4px 16px rgba(109,40,217,0.08);
}
.option-item.correct {
  border-color: #22c55e;
  background: #e7fbe9;
  color: #16a34a;
  font-weight: bold;
  box-shadow: 0 4px 16px rgba(34,197,94,0.08);
}
.option-item.unselected {
  color: #b0b3bb;
}
.option-label {
  font-weight: bold;
  margin-right: 12px;
  min-width: 28px;
  display: inline-block;
}
.option-content {
  flex: 1;
}
.summary-card {
  max-width: 900px;
  border-radius: 24px;
  background: #f3f4f6;
}
.ai-fab-top {
  position: fixed;
  right: 48px;
  top: 32px;
  z-index: 200;
  box-shadow: 0 6px 24px rgba(109,40,217,0.18);
  font-weight: 700;
  letter-spacing: 0.5px;
  border-radius: 28px;
  padding: 0 32px;
  font-size: 1.18rem;
  height: 56px;
}
</style>