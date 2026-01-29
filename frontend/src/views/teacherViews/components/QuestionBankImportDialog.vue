<template>
  <v-dialog :model-value="show" @update:modelValue="(val: boolean) => emit('update:show', val)" max-width="800px">
    <v-card>
      <v-card-title>批量导入题目</v-card-title>
      <v-card-text>
        <v-stepper v-model="step">
          <v-stepper-header>
            <v-stepper-item :value="1" title="上传文件与选择题号格式" />
            <v-divider />
            <v-stepper-item :value="2" title="预览解析结果" />
            <v-divider />
            <v-stepper-item :value="3" title="确认导入" />
          </v-stepper-header>
          <v-stepper-window>
            <v-stepper-window-item :value="1">
              <v-row>
                <v-col cols="7">
                  <v-file-input
                    v-model="localFile"
                    label="选择Word或PDF文件"
                    accept=".doc,.docx,.pdf"
                    prepend-icon="mdi-upload"
                  />
                </v-col>
                <v-col cols="5">
                  <div class="mb-2">选择试题题号格式：</div>
                  <v-radio-group v-model="numberFormat">
                    <v-radio label="3." value="3." />
                    <v-radio label="3)" value="3)" />
                    <v-radio label="(3)" value="(3)" />
                    <v-radio label="3、" value="3、" />
                    <v-radio label="3 ." value="3 ." />
                  </v-radio-group>
                </v-col>
              </v-row>
              <div class="d-flex justify-end mt-4">
                <v-btn 
                  color="primary" 
                  :disabled="!localFile" 
                  :loading="loadingPreview"
                  @click="handlePreview"
                >
                  <v-icon left v-if="!loadingPreview">mdi-arrow-right</v-icon>
                  <span v-if="!loadingPreview">第一步：识别和分离试题</span>
                  <span v-else>正在识别试题...</span>
                </v-btn>
              </div>
            </v-stepper-window-item>
            <v-stepper-window-item :value="2">
              <v-row>
                <v-col cols="7">
                  <div class="preview-box">
                    <div v-if="loadingPreview" class="text-center my-4"><v-progress-circular indeterminate color="primary" /></div>
                    <div v-else-if="previewQuestions.length">
                      <div class="d-flex justify-space-between align-center mb-3">
                        <div class="text-h6">预览题目 ({{ previewQuestions.length }}道)</div>
                        <div class="d-flex gap-2">
                          <v-btn 
                            :color="editMode ? 'primary' : 'secondary'" 
                            size="small" 
                            @click="toggleEditMode"
                          >
                            <v-icon left>{{ editMode ? 'mdi-close' : 'mdi-pencil' }}</v-icon>
                            {{ editMode ? '退出编辑' : '编辑所有题目' }}
                          </v-btn>
                          <v-btn 
                            v-if="editMode && selectedQuestions !== -1"
                            color="primary" 
                            size="small" 
                            @click="editSelectedQuestions"
                          >
                            <v-icon left>mdi-pencil</v-icon>
                            编辑选中题目
                          </v-btn>
                        </div>
                      </div>
                      <div v-for="(q, idx) in previewQuestions" :key="idx" class="mb-4 question-item">
                        <div class="d-flex align-center justify-space-between">
                          <div class="d-flex align-center">
                            <v-radio 
                              v-if="editMode"
                              v-model="selectedQuestions" 
                              :value="idx" 
                              hide-details 
                              class="mr-2"
                            />
                            <div><b>{{ idx+1 }}.</b> <span class="type-chip">{{ typeLabel(q.question_type) }}</span> {{ q.content }}</div>
                          </div>
                        </div>
                        <div v-if="q.options && q.options.length">
                          <div v-for="(opt, oidx) in q.options" :key="oidx">{{ opt }}</div>
                        </div>
                        <div v-if="getCorrectAnswerByType(q)"><span class="grey--text">答案：</span>{{ getCorrectAnswerByType(q) }}</div>
                      </div>
                    </div>
                    <div v-else class="grey--text">暂无解析结果</div>
                  </div>
                </v-col>
                <v-col cols="5">
                  <div class="mb-2">如题号格式不正确可切换后重新识别：</div>
                  <v-radio-group v-model="numberFormat">
                    <v-radio label="3." value="3." />
                    <v-radio label="3)" value="3)" />
                    <v-radio label="(3)" value="(3)" />
                    <v-radio label="3、" value="3、" />
                    <v-radio label="3 ." value="3 ." />
                  </v-radio-group>
                  <v-btn color="primary" class="mt-2" :disabled="!localFile" @click="handlePreview">
                    <v-icon left>mdi-refresh</v-icon>
                    重新识别
                  </v-btn>
                  <div class="mt-6">
                    <v-select
                      v-model="importCourseId"
                      :items="props.courseOptions"
                      item-title="title"
                      item-value="value"
                      label="请选择课程"
                      clearable
                      dense
                      hide-details
                      solo
                      required
                    />
                  </div>
                </v-col>
              </v-row>
              <div class="d-flex justify-space-between mt-4">
                <v-btn text @click="step = 1">
                  <v-icon left>mdi-arrow-left</v-icon>
                  上一步
                </v-btn>
                <v-btn color="primary" :disabled="!previewQuestions.length" @click="step=3">
                  下一步：确认导入
                  <v-icon right>mdi-arrow-right</v-icon>
                </v-btn>
              </div>
            </v-stepper-window-item>
            <v-stepper-window-item :value="3">
              <div class="mb-2">请确认下列题目无误后点击"导入"：</div>
              <div class="mb-4" style="max-width: 300px;">
                <v-select
                  v-model="importCourseId"
                  :items="props.courseOptions"
                  item-title="title"
                  item-value="value"
                  label="请选择课程"
                  clearable
                  dense
                  hide-details
                  solo
                  required
                />
              </div>
              <div class="preview-box mb-4">
                <div v-for="(q, idx) in previewQuestions" :key="idx" class="mb-4">
                  <div><b>{{ idx+1 }}.</b> <span class="type-chip">{{ typeLabel(q.question_type) }}</span> {{ q.content }}</div>
                  <div v-if="q.options && q.options.length">
                    <div v-for="(opt, oidx) in q.options" :key="oidx">{{ opt }}</div>
                  </div>
                  <div v-if="getCorrectAnswerByType(q)"><span class="grey--text">答案：</span>{{ getCorrectAnswerByType(q) }}</div>
                </div>
              </div>
              <div class="d-flex justify-space-between align-center">
                <v-btn text @click="step = 2">
                  <v-icon left>mdi-arrow-left</v-icon>
                  上一步
                </v-btn>
                <div class="d-flex align-center">
                  <v-btn color="primary" :disabled="!previewQuestions.length || importing || !importCourseId" @click="handleImport">
                    <v-icon left v-if="!importing">mdi-upload</v-icon>
                    <span v-if="!importing">导入</span>
                    <span v-else>正在导入...({{ importProgress }}/{{ previewQuestions.length }})</span>
                  </v-btn>
                  <v-progress-linear v-if="importing" :value="importProgressPercent" height="6" color="primary" class="ml-4" style="width: 200px"/>
                </div>
              </div>
            </v-stepper-window-item>
          </v-stepper-window>
        </v-stepper>
        <QuestionBankFormDialog
          v-model:show="editDialog"
          :editMode="true"
          :form="editForm"
          :questionTypes="questionTypes"
          :difficultyOptions="difficultyOptions"
          :courseOptions="props.courseOptions"
          @submit="saveEdit"
          @cancel="editDialog = false"
          @type-change="() => {}"
          @add-option="() => { editForm.options = editForm.options || []; editForm.options.push(''); }"
          @remove-option="(idx:number) => { editForm.options.splice(idx,1); }"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="handleCancel">取消</v-btn>
        <v-btn text @click="emit('update:show', false)">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import questionBankService from '../../../api/questionBankService';
import QuestionBankFormDialog from './QuestionBankFormDialog.vue';
const props = defineProps({
  show: { type: Boolean, default: false },
  courseOptions: { type: Array as () => Array<{title: string, value: string}>, default: () => [] }
});
const emit = defineEmits(['update:show', 'imported']);
const step = ref(1);
const localFile = ref<File|null>(null);
const numberFormat = ref('3.');
const previewQuestions = ref<any[]>([]);
const loadingPreview = ref(false);
const importing = ref(false);
const importProgress = ref(0);
const importProgressPercent = computed(() => previewQuestions.value.length ? Math.round(importProgress.value / previewQuestions.value.length * 100) : 0);
const importCourseId = ref('');
const editDialog = ref(false);
const editIndex = ref(-1);
const editForm = ref<any>({});
const questionTypes = [
  { title: '单选题', value: 'single' },
  { title: '多选题', value: 'multiple' },
  { title: '填空题', value: 'blank' },
    { title: '问答题', value: 'essay' }
];
const difficultyOptions = [
  { title: '简单', value: 'easy' },
  { title: '中等', value: 'medium' },
  { title: '困难', value: 'hard' }
];
const editMode = ref(false);
const selectedQuestions = ref<number>(-1);

watch(() => props.courseOptions, (opts) => {
  if (opts && opts.length && !importCourseId.value) importCourseId.value = opts[0].value;
}, { immediate: true });

watch(() => props.show, (val) => {
  if (!val) {
    step.value = 1;
  }
});

const handlePreview = async () => {
  if (!localFile.value) return;
  loadingPreview.value = true;
  previewQuestions.value = [];
  try {
    const res = await questionBankService.importPreview({
      file: localFile.value,
      number_format: numberFormat.value
    });
    previewQuestions.value = res.data.questions || [];
    step.value = 2;
  } catch (e) {
    console.error('预览导入失败:', e);
    previewQuestions.value = [];
  } finally {
    loadingPreview.value = false;
  }
};

function typeLabel(type: string) {
  switch(type) {
    case 'single': return '单选题';
    case 'multiple': return '多选题';
    case 'blank': return '填空题';
    case 'essay': return '简答题';
    default: return '未知';
  }
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

const handleImport = async () => {
  importing.value = true;
  importProgress.value = 0;
  try {
    const batchSize = 10;
    for (let i = 0; i < previewQuestions.value.length; i += batchSize) {
      const batch = previewQuestions.value.slice(i, i + batchSize);
      await questionBankService.importCommit({
        questions: batch,
        course_id: importCourseId.value
      });
      importProgress.value = Math.min(i + batch.length, previewQuestions.value.length);
    }
    emit('update:show', false);
    emit('imported');
  } catch (error) {
    console.error('导入题目失败:', error);
  } finally {
    importing.value = false;
    importCourseId.value = '';
  }
};

const handleCancel = () => {
  step.value = 1;
  localFile.value = null;
  numberFormat.value = '3.';
  previewQuestions.value = [];
  loadingPreview.value = false;
  importing.value = false;
  importProgress.value = 0;
  importCourseId.value = '';
  editDialog.value = false;
  editIndex.value = -1;
  editForm.value = {};
  editMode.value = false;
  selectedQuestions.value = -1;
  emit('update:show', false);
};

function openEdit(idx: number) {
  editIndex.value = idx;
  editForm.value = { ...previewQuestions.value[idx] };
  editDialog.value = true;
}

function saveEdit() {
  if (editIndex.value >= 0) {
    previewQuestions.value[editIndex.value] = { ...editForm.value };
  }
  editDialog.value = false;
}

function toggleEditMode() {
  editMode.value = !editMode.value;
  if (!editMode.value) {
    selectedQuestions.value = -1;
  }
}

function toggleQuestionSelection(idx: number) {
  selectedQuestions.value = selectedQuestions.value === idx ? -1 : idx;
}

function editSelectedQuestions() {
  if (selectedQuestions.value === -1) return;
  openEdit(selectedQuestions.value);
}
</script>
<style scoped>
.preview-box {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  min-height: 300px;
  max-height: 400px;
  overflow-y: auto;
  font-size: 15px;
}
.type-chip {
  display: inline-block;
  background: #e3eafc;
  color: #1976d2;
  border-radius: 8px;
  font-size: 13px;
  padding: 2px 8px;
  margin-right: 8px;
}
.question-item {
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}
.question-item:hover {
  background-color: #f0f0f0;
}
.gap-2 {
  gap: 8px;
}
</style>