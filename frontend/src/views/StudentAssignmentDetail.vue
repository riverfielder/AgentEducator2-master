<template>
  <v-container>
    <v-btn icon class="back-btn-glass" @click="goBack">
      <v-icon color="#7c3aed" size="24">mdi-arrow-left</v-icon>
    </v-btn>
    <v-card class="assignment-detail-card">      <v-card-title class="d-flex align-center justify-space-between">
        <div>
          {{ assignment.title }}
          <v-chip class="ml-4" color="success" v-if="isFullyGraded">已批改</v-chip>
          <v-chip class="ml-4" color="warning" v-else-if="assignmentStatus === 'submitted'">已提交</v-chip>
          <v-chip class="ml-4" color="error" v-else-if="isOverdue">已截止</v-chip>
        </div>
      </v-card-title>
      <v-card-subtitle>
        课程：{{ assignment.courseName }} | 截止：{{ assignment.dueDate }}
      </v-card-subtitle>
      <v-divider></v-divider>
      <v-card-text>
        <div v-for="(q, idx) in assignment.questions" :key="idx" class="mb-7">
          <div class="mb-2">
            <span class="font-weight-bold">第{{ idx + 1 }}题：</span>
            <v-chip size="small" color="primary">{{ getTypeText(q.type) }}</v-chip>
          </div>
          <div class="mb-2">{{ q.content }}</div>          <!-- 单选题 -->
          <v-radio-group v-if="q.type==='single'" v-model="answers[idx]" class="option-group-unified" density="comfortable" :disabled="!canEdit">
            <v-radio
              v-for="(opt, i) in q.options"
              :key="i"
              :label="String.fromCharCode(65+i) + '. ' + opt.content"
              :value="i"
              class="option-item-unified"
              density="comfortable"
            />
          </v-radio-group>
          <!-- 多选题：用自定义圆形radio模拟多选 -->
          <div v-else-if="q.type==='multiple'" class="option-group-unified">
            <v-radio
              v-for="(opt, i) in q.options"
              :key="i"
              :label="String.fromCharCode(65+i) + '. ' + opt.content"
              :value="i"
              :model-value="answers[idx].includes(i)"
              @click="canEdit && toggleMulti(idx, i)"
              class="option-item-unified custom-multi-radio"
              density="comfortable"
              :disabled="!canEdit"
            />
          </div>
          <!-- 填空题 -->
          <v-textarea 
            v-else-if="q.type==='blank'" 
            v-model="answers[idx]" 
            placeholder="请填写答案" 
            class="answer-textarea" 
            auto-grow 
            rows="2"
            variant="outlined"
            hide-details
            :disabled="!canEdit"
          />
          <!-- 问答题 -->
          <v-textarea 
            v-else-if="q.type==='essay'" 
            v-model="answers[idx]" 
            placeholder="请作答" 
            class="answer-textarea" 
            auto-grow 
            rows="4"
            variant="outlined"
            hide-details
            :disabled="!canEdit"
          />
        </div>
      </v-card-text>
      <v-divider></v-divider>      <v-card-actions>
        <v-btn color="success" @click="submit" :disabled="!canEdit" v-if="canEdit">{{ submitButtonText }}</v-btn>
        <v-btn variant="text" @click="saveLocal" :disabled="!canEdit" v-if="canEdit">保存草稿</v-btn>
        <v-alert v-if="!canEdit" type="info" class="ma-2">
          <template v-if="isFullyGraded">作业已批改完成，无法继续编辑</template>
          <template v-else-if="isOverdue">作业已截止，无法继续编辑</template>
        </v-alert>
      </v-card-actions>
    </v-card>
  </v-container>
</template>
<script setup lang="ts">

console.log('normal detail loaded')

import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import assignmentService from '../api/assignmentService';
import type { StudentSubmission } from '../api/assignmentService';
import { useUserStore } from '../stores/userStore';
import { ElMessage } from 'element-plus';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// assignment数据
const assignment = ref<any>({
  title: '',
  courseName: '',
  dueDate: '',
  questions: []
});
const answers = ref<any[]>([]);
const assignmentStatus = ref<string>('uncompleted'); // 添加状态跟踪
const isFullyGraded = ref<boolean>(false); // 是否已完全批改

// 获取localStorage存储的key
const getStorageKey = () => `assignment_draft_${route.params.id}_${userStore.userId}`;

// 从localStorage加载草稿
const loadFromStorage = () => {
  try {
    const key = getStorageKey();
    const stored = localStorage.getItem(key);
    if (stored) {
      const parsedAnswers = JSON.parse(stored);
      // 确保数组长度匹配
      if (parsedAnswers.length === assignment.value.questions.length) {
        answers.value = parsedAnswers;
        console.log('已从本地存储恢复答案草稿');
      }
    }
  } catch (error) {
    console.error('读取本地草稿失败:', error);
  }
};

// 保存到localStorage
const saveToStorage = () => {
  try {
    if (!assignment.value.id) return;
    const key = getStorageKey();
    localStorage.setItem(key, JSON.stringify(answers.value));
  } catch (error) {
    console.error('保存本地草稿失败:', error);
  }
};

// 清除localStorage中的草稿
const clearStorage = () => {
  try {
    const key = getStorageKey();
    localStorage.removeItem(key);
    console.log('已清除本地草稿');
  } catch (error) {
    console.error('清除本地草稿失败:', error);
  }
};

// 手动保存草稿
const saveLocal = () => {
  saveToStorage();
  ElMessage.success('草稿已保存到本地');
};

// 封装拉取作业详情的逻辑
const fetchAssignmentDetail = async () => {
  // 重置状态
  assignment.value = { title: '', courseName: '', dueDate: '', questions: [] };
  answers.value = [];
  assignmentStatus.value = 'uncompleted';
  isFullyGraded.value = false;

  const id = route.params.id;
  if (!id) return;

  // 获取作业基本信息
  const res = await assignmentService.getAssignmentDetail(id as string);
  if (res.data && res.data.code === 200) {
    assignment.value = res.data.data;
    answers.value = assignment.value.questions.map((q: any) => {
      if (q.type === 'single') return '';
      if (q.type === 'multiple') return [];
      return '';
    });

    // 尝试获取已提交的答案
    try {
      const markingRes = await assignmentService.getAssignmentMarkingInfo(id as string);
      if (markingRes.data && markingRes.data.code === 200) {
        const markingData = markingRes.data.data;
        isFullyGraded.value = markingData.questions_and_answers.every((qa: any) => qa.score !== null);
        markingData.questions_and_answers.forEach((qa: any, index: number) => {
          if (qa.student_answer !== null && qa.student_answer !== undefined) {
            answers.value[index] = qa.student_answer;
          }
        });
        assignmentStatus.value = isFullyGraded.value ? 'expired' : 'submitted';
      }
    } catch (error) {
      assignmentStatus.value = 'uncompleted';
      console.log('学生还未提交或无权限查看批改信息');
    }

    if (assignmentStatus.value === 'uncompleted') {
      loadFromStorage();
    }
  }
};

// 页面加载时获取作业详情
onMounted(fetchAssignmentDetail);

// 监听路由id变化，切换作业时自动刷新
watch(
  () => route.params.id,
  (newId, oldId) => {
    if (newId !== oldId) {
      fetchAssignmentDetail();
    }
  }
);

const isOverdue = computed(() => {
  const dueDate = new Date(assignment.value.dueDate);
  return dueDate < new Date();
});

// 计算是否允许编辑
const canEdit = computed(() => {
  // 如果已完全批改或已过期，不允许编辑
  if (isFullyGraded.value || isOverdue.value) {
    return false;
  }
  // 其他情况允许编辑（未完成或已提交但未完全批改）
  return true;
});

// 计算按钮文字
const submitButtonText = computed(() => {
  if (assignmentStatus.value === 'submitted') {
    return '重新提交';
  }
  return '提交作业';
});

const getTypeText = (type: string) => {
  return { single: '单选', multiple: '多选', blank: '填空', essay: '问答' }[type] || '';
};

const submit = async () => {
  try {
    // 构建提交数据
    const submissionData: StudentSubmission = {
      student_id: userStore.userId,
      assignment_id: assignment.value.id,
      questions_and_answers: assignment.value.questions.map((q: any, index: number) => ({
        question_id: q.id,
        question_type: q.type,
        student_answer: answers.value[index]
      })),
      submit_time: new Date().toISOString()
    };
    console.log('submissionData',submissionData);
    // 调用提交接口
    const res = await assignmentService.submitStudentAssignment(submissionData);
    if (res.data && res.data.code === 200) {
      console.log('提交成功',res);
      // 提交成功后清除本地草稿
      clearStorage();
      ElMessage.success('作业提交成功！');
      router.push('/student-assignments');
    } else {
      ElMessage.error('提交失败：' + (res.data?.message || '未知错误'));
    }
  } catch (error) {
    console.error('提交作业失败:', error);
    ElMessage.error('提交失败，请稍后重试');
  }
};

const goBack = () => {
  router.back();
};

// 多选题自定义toggle
const toggleMulti = (idx: number, i: number) => {
  const arr = answers.value[idx];
  const pos = arr.indexOf(i);
  if (pos === -1) arr.push(i);
  else arr.splice(pos, 1);
};

// 自动保存到localStorage (防抖)
let saveTimeout: any = null;
watch(answers, () => {
  if (!assignment.value.id || isOverdue.value) return;
  
  // 防抖：用户停止输入500ms后保存
  if (saveTimeout) {
    clearTimeout(saveTimeout);
  }
  saveTimeout = setTimeout(() => {
    saveToStorage();
  }, 500);
}, { deep: true });
</script>
<style scoped>
.back-btn-glass {
  position: absolute;
  top: 24px;
  left: 24px;
  z-index: 20;
  background: #fff !important;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, box-shadow 0.2s, transform 0.2s;
  border: none;
  padding: 0;
  box-shadow: none;
}
.back-btn-glass:hover {
  background: #fff !important;
  box-shadow: 0 4px 16px rgba(80,120,200,0.18);
  transform: scale(1.08) rotate(-10deg);
}
.assignment-detail-card {
  border-radius: 20px;
  box-shadow: 0 6px 32px rgba(80,120,200,0.10);
  background: linear-gradient(120deg, #f8fafc 70%, #e3e9f7 100%);
  margin-top: 32px;
  padding-top: 8px;
}
.option-group-unified {
  margin-top: 8px;
  margin-bottom: 8px;
  gap: 0;
}
.option-item-unified, .custom-multi-radio {
  margin-bottom: 8px !important;
  min-height: 40px;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  align-items: center !important;
  font-size: 1rem !important;
  line-height: 1.6 !important;
}
/* 统一单选和多选选项的行间距和label样式 */
:deep(.v-selection-control) {
  min-height: 40px !important;
  margin-bottom: 8px !important;
  align-items: center !important;
}
:deep(.v-selection-control__input) {
  margin-right: 12px !important;
}
:deep(.v-label) {
  font-size: 1rem !important;
  line-height: 1.6 !important;
  color: #222 !important;
  margin-left: 0 !important;
}
.answer-textarea {
  border-radius: 12px;
  margin-top: 8px;
}
:deep(.answer-textarea .v-field) {
  background: #f4f6fb;
  box-shadow: 0 1px 6px rgba(80,120,200,0.06);
}
:deep(.answer-textarea .v-field__input) {
  padding: 12px 16px;
  font-size: 1rem;
  line-height: 1.5;
}
:deep(.answer-textarea .v-field__input::placeholder) {
  color: #999 !important;
  opacity: 0.8;
}
</style>