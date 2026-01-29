<template>
  <v-dialog v-model="dialog" max-width="800">
    <v-card>
      <v-card-title class="d-flex align-center pa-4">
        <span class="text-h5">作业详情</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="closeDialog"></v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <v-container v-if="assignment">
          <!-- 基本信息 -->
          <v-row>
            <v-col cols="12" class="pb-0">
              <div class="d-flex align-center mb-4">
                <v-icon icon="mdi-file-document-outline" color="primary" class="me-2"></v-icon>
                <span class="text-h6">{{ assignment.title }}</span>
              </div>
              <v-chip
                :color="displayStatus.color"
                class="me-2"
              >
                {{ displayStatus.text }}
              </v-chip>
              <v-chip color="info" class="me-2">
                截止日期：{{ formatDateTime(assignment.dueDate) }}
              </v-chip>
            </v-col>
          </v-row>

          <!-- 题目列表 -->
          <v-row>
            <v-col cols="12">
              <div class="text-h6 mb-4 mt-4">题目列表</div>
              <v-expansion-panels>
                <v-expansion-panel
                  v-for="(question, index) in assignment.questions"
                  :key="index"
                >
                  <v-expansion-panel-title>
                    <div class="d-flex align-center">
                      <span class="me-2">第 {{ index + 1 }} 题</span>
                      <v-chip
                        size="small"
                        :color="getQuestionTypeColor(question.type)"
                        class="me-2"
                      >
                        {{ getQuestionTypeText(question.type) }}
                      </v-chip>
                      <span class="text-truncate">{{ question.content }}</span>
                    </div>
                  </v-expansion-panel-title>
                  
                  <v-expansion-panel-text>
                    <!-- 题目内容 -->
                    <div class="mb-4">
                      <div class="font-weight-bold mb-2">题目内容：</div>
                      <div>{{ question.content }}</div>
                    </div>

                    <!-- 选项（单选/多选题） -->
                    <template v-if="['single', 'multiple'].includes(question.type)">
                      <div class="font-weight-bold mb-2">选项：</div>
                      <v-list>
                        <v-list-item
                          v-for="(option, optIndex) in question.options"
                          :key="optIndex"
                          :class="{ 'bg-light-green-lighten-4': option.isCorrect }"
                        >
                          <template v-slot:prepend>
                            <span class="me-2">{{ String.fromCharCode(65 + optIndex) }}.</span>
                          </template>
                          <v-list-item-title>
                            {{ option.content }}
                            <v-icon
                              v-if="option.isCorrect"
                              icon="mdi-check"
                              color="success"
                              class="ms-2"
                            ></v-icon>
                          </v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </template>

                    <!-- 填空题答案 -->
                    <template v-if="question.type === 'blank'">
                      <div class="font-weight-bold mb-2">参考答案：</div>
                      <div>{{ question.answers }}</div>
                    </template>

                    <!-- 问答题答案 -->
                    <template v-if="question.type === 'essay'">
                      <div class="font-weight-bold mb-2">参考答案：</div>
                      <div>{{ question.reference }}</div>
                    </template>

                    <!-- 解析 -->
                    <template v-if="question.explanation">
                      <div class="font-weight-bold mb-2 mt-4">解析：</div>
                      <div>{{ question.explanation }}</div>
                    </template>

                    <!-- 分值 -->
                    <div class="mt-4">
                      <v-chip color="primary" size="small">
                        分值：{{ question.maxScore }} 分
                      </v-chip>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-col>
          </v-row>
        </v-container>

        <!-- 加载中状态 -->
        <v-container v-else-if="loading">
          <v-row justify="center" align="center" style="height: 200px">
            <v-col cols="12" class="text-center">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import assignmentService from '@/api/assignmentService';
import type { Assignment } from '@/api/assignmentService';

const props = defineProps<{
  modelValue: boolean;
  assignmentId: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const dialog = ref(false);
const loading = ref(false);
const assignment = ref<Assignment | null>(null);

// 计算教师端显示状态
const displayStatus = computed(() => {
  if (!assignment.value) return { text: '', color: '' };
  
  // 优先使用teacherStatus，如果不存在则使用status
  const status = assignment.value.teacherStatus || assignment.value.status;
  
  switch (status) {
    case 'draft':
      return { text: '草稿', color: 'grey' };
    case 'scheduled':
      return { text: '待发布', color: 'orange' };
    case 'published':
      return { text: '已发布', color: 'success' };
    default:
      return { text: assignment.value.status === 'published' ? '已发布' : '草稿', color: assignment.value.status === 'published' ? 'success' : 'grey' };
  }
});

// 监听对话框显示状态
watch(() => props.modelValue, (newVal) => {
  dialog.value = newVal;
  if (newVal && props.assignmentId) {
    loadAssignmentDetail();
  }
});

// 监听对话框关闭
watch(() => dialog.value, (newVal) => {
  if (!newVal) {
    emit('update:modelValue', false);
  }
});

// 加载作业详情
const loadAssignmentDetail = async () => {
  loading.value = true;
  try {
    const response = await assignmentService.getAssignmentDetail(props.assignmentId);
    console.log('作业详情接口返回数据:', response);
    
    if (response.data && response.data.code === 200) {
      assignment.value = response.data.data;
    } else {
      console.error('接口返回错误:', response.data);
    }
  } catch (error) {
    console.error('加载作业详情失败:', error);
  } finally {
    loading.value = false;
  }
};


// 格式化日期时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch (error) {
    return dateString;
  }
};

// 获取题型文本
const getQuestionTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '问答题'
  };
  return typeMap[type] || type;
};

// 获取题型颜色
const getQuestionTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    single: 'primary',
    multiple: 'secondary',
    blank: 'info',
    essay: 'warning'
  };
  return colorMap[type] || 'grey';
};

// 关闭对话框
const closeDialog = () => {
  dialog.value = false;
};
</script>

<style scoped>
.bg-light-green-lighten-4 {
  background-color: rgb(var(--v-theme-success-lighten-4)) !important;
}
</style> 