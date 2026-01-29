<template>
  <v-dialog :model-value="show" @update:modelValue="(val: boolean) => emit('update:show', val)" max-width="800px" persistent>
    <v-card class="form-card">
      <v-card-title class="form-title d-flex align-center justify-space-between">
        <div class="d-flex align-center">
          <v-icon color="primary" class="mr-3" size="28">mdi-pencil-box-outline</v-icon>
          <span>{{ editMode ? '编辑题目' : '新建试题' }}</span>
        </div>
        <v-btn icon variant="text" @click="$emit('cancel')" class="close-btn">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider class="mb-6"></v-divider>
      
      <v-card-text class="form-content">
        <!-- 基础信息区域 -->
        <div class="form-section">
          <div class="section-title">
            <v-icon color="primary" class="mr-2" size="20">mdi-information-outline</v-icon>
            基础信息
          </div>
          
          <v-row class="mb-4">
            <v-col cols="12" md="6">
              <div class="form-label">题型 <span class="required">*</span></div>
              <v-btn-toggle v-model="form.question_type" class="type-toggle w-100" rounded>
                <v-btn v-for="(item, i) in questionTypes" :key="item.value" :value="item.value" 
                       :color="form.question_type === item.value ? 'primary' : ''" 
                       class="type-btn flex-grow-1">
                  {{ item.title }}
                </v-btn>
              </v-btn-toggle>
              <div v-if="!form.question_type" class="type-hint">
                <v-icon color="warning" size="16" class="mr-1">mdi-information-outline</v-icon>
                <span class="text-caption text-warning">请选择题型</span>
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="form-label">课程 <span class="required">*</span></div>
              <v-select
                v-model="form.course_id"
                :items="courseOptions"
                item-title="title"
                item-value="value"
                label="请选择课程"
                clearable
                variant="outlined"
                density="comfortable"
                class="course-select"
                hide-details
                required
              />
            </v-col>
          </v-row>
          
          <v-row class="mb-4">
            <v-col cols="12" md="6">
              <div class="form-label">试题难度 <span class="required">*</span></div>
              <v-btn-toggle v-model="form.difficulty" class="difficulty-toggle w-100" rounded mandatory>
                <v-btn v-for="(item, i) in difficultyOptions" :key="item.value" :value="item.value" 
                       :color="form.difficulty === item.value ? 'primary' : ''" 
                       class="difficulty-btn flex-grow-1">
                  {{ item.title }}
                </v-btn>
              </v-btn-toggle>
            </v-col>
          </v-row>
        </div>

        <!-- 题目内容区域 -->
        <div class="form-section">
          <div class="section-title">
            <v-icon color="primary" class="mr-2" size="20">mdi-text-box-outline</v-icon>
            题目内容
          </div>
          
          <div class="mb-4">
            <div class="form-label">题干 <span class="required">*</span></div>
            <v-textarea 
              v-model="form.content" 
              label="请输入题目内容" 
              variant="outlined"
              auto-grow 
              required 
              rows="3" 
              class="content-textarea"
              hide-details
            />
          </div>
        </div>

        <!-- 选项和答案区域 -->
        <div v-if="form.question_type === 'single'" class="form-section">
          <div class="section-title">
            <v-icon color="primary" class="mr-2" size="20">mdi-radiobox-marked</v-icon>
            选项和答案 <span class="required">*</span>
          </div>
          
          <v-radio-group v-model="form.answerIndex" class="options-container">
            <div v-for="(opt, idx) in form.options" :key="idx" class="option-item">
              <div class="option-header">
                <div class="option-label-badge">{{ String.fromCharCode(65 + idx) }}</div>
                <div class="option-input-container">
                  <v-text-field 
                    v-model="form.options[idx]" 
                    :placeholder="getPlaceholder(idx)"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="option-input"
                    @input="handleOptionInput(form.options[idx], idx)"
                  />
                </div>
                <div class="option-actions">
                  <v-radio :value="idx" hide-details class="answer-radio" />
                  <v-btn 
                    icon 
                    variant="text" 
                    color="error" 
                    size="small"
                    @click="$emit('remove-option', idx)" 
                    :disabled="form.options.length <= 2"
                    class="delete-btn"
                  >
                    <v-icon size="20">mdi-delete-outline</v-icon>
                  </v-btn>
                </div>
              </div>
            </div>
          </v-radio-group>
          
          <v-btn 
            variant="outlined" 
            color="primary" 
            class="add-option-btn" 
            @click="$emit('add-option')"
          >
            <v-icon left>mdi-plus</v-icon>
            添加选项
          </v-btn>
        </div>

        <div v-else-if="form.question_type === 'multiple'" class="form-section">
          <div class="section-title">
            <v-icon color="primary" class="mr-2" size="20">mdi-checkbox-multiple-marked</v-icon>
            选项和答案 <span class="required">*</span>
          </div>
          
          <div class="options-container">
            <div v-for="(opt, idx) in form.options" :key="idx" class="option-item">
              <div class="option-header">
                <div class="option-label-badge">{{ String.fromCharCode(65 + idx) }}</div>
                <div class="option-input-container">
                  <v-text-field 
                    v-model="form.options[idx]" 
                    :placeholder="getPlaceholder(idx)"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="option-input"
                    @input="handleOptionInput(form.options[idx], idx)"
                  />
                </div>
                <div class="option-actions">
                  <v-checkbox v-model="form.answerIndices" :value="idx" hide-details class="answer-checkbox" />
                  <v-btn 
                    icon 
                    variant="text" 
                    color="error" 
                    size="small"
                    @click="$emit('remove-option', idx)" 
                    :disabled="form.options.length <= 2"
                    class="delete-btn"
                  >
                    <v-icon size="20">mdi-delete-outline</v-icon>
                  </v-btn>
                </div>
              </div>
            </div>
          </div>
          
          <v-btn 
            variant="outlined" 
            color="primary" 
            class="add-option-btn" 
            @click="$emit('add-option')"
          >
            <v-icon left>mdi-plus</v-icon>
            添加选项
          </v-btn>
        </div>

        <div v-if="form.question_type === 'blank' || form.question_type === 'essay'" class="form-section">
          <div class="section-title">
            <v-icon color="primary" class="mr-2" size="20">mdi-text-box-check-outline</v-icon>
            答案 <span class="required">*</span>
          </div>
          
          <v-text-field 
            v-model="form.answerStr" 
            label="请填写答案" 
            variant="outlined"
            density="comfortable"
            required
            hide-details
          />
        </div>

        <!-- 附加信息区域 -->
        <div class="form-section">
          <div class="section-title">
            <v-icon color="primary" class="mr-2" size="20">mdi-information-variant</v-icon>
            附加信息
          </div>
          
          <div class="mb-4">
            <div class="form-label">解析</div>
            <v-textarea 
              v-model="form.explanation" 
              label="请输入解析" 
              variant="outlined"
              auto-grow 
              rows="2"
              hide-details
            />
          </div>
          
          <v-row>
            <v-col cols="12" md="6">
              <div class="form-label">标签</div>
              <v-text-field 
                v-model="form.tagsStr" 
                label="标签（用逗号分隔）"
                variant="outlined"
                density="comfortable"
                hide-details
              />
            </v-col>
            <v-col cols="12" md="6">
              <div class="form-label">备注</div>
              <v-text-field 
                v-model="form.remark" 
                label="请输入备注"
                variant="outlined"
                density="comfortable"
                hide-details
              />
            </v-col>
          </v-row>
        </div>
      </v-card-text>
      
      <v-divider class="mt-4"></v-divider>
      
      <v-card-actions class="form-actions">
        <v-spacer></v-spacer>
        <v-btn variant="text" size="large" @click="$emit('cancel')" class="cancel-btn">
          取消
        </v-btn>
        <v-btn color="primary" variant="flat" size="large" @click="$emit('submit')" class="submit-btn">
          <v-icon left>mdi-check</v-icon>
          确定
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { computed, watch } from 'vue';

interface OptionItem {
  title: string;
  value: string;
}

const props = defineProps({
  show: { type: Boolean, default: false },
  editMode: { type: Boolean, default: false },
  form: { type: Object, required: true },
  questionTypes: { type: Array as () => OptionItem[], default: () => [] },
  difficultyOptions: { type: Array as () => OptionItem[], default: () => [] },
  courseOptions: { type: Array, default: () => [] }
});

const emit = defineEmits(['update:show', 'submit', 'cancel', 'type-change', 'add-option', 'remove-option']);

// 监听题型变化，重置表单状态
watch(() => props.form.question_type, (newType, oldType) => {
  if (newType !== oldType && oldType !== undefined) {
    emit('type-change');
  }
});

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

// 处理选项输入的变化
const handleOptionInput = (value: string, index: number) => {
  const cleaned = cleanOptionText(value, index);
  if (cleaned !== value) {
    // 如果文本被清理了，更新表单数据
    props.form.options[index] = cleaned;
  }
};

// 计算属性：获取清理后的选项文本用于显示
const getCleanOption = (optionText: string, index: number): string => {
  return cleanOptionText(optionText || '', index);
};

// 生成占位符文本
const getPlaceholder = (index: number): string => {
  return `请输入选项内容（无需添加${String.fromCharCode(65 + index)}.前缀）`;
};
</script>
<style scoped>
.form-card {
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  background: #fff;
  overflow: hidden;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 0.5px;
  padding: 24px 32px 16px 32px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  color: #2c3e50;
}

.close-btn {
  opacity: 0.7;
}

.close-btn:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.1);
}

.form-content {
  padding: 0 32px 24px 32px;
  max-height: 70vh;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 32px;
  padding: 20px;
  border-radius: 12px;
  background: #fafbfc;
  border: 1px solid #e9ecef;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 2px solid #e3f2fd;
}

.form-label {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
  color: #495057;
  letter-spacing: 0.3px;
}

.required {
  color: #e74c3c;
  font-size: 14px;
  margin-left: 4px;
}

.type-toggle, .difficulty-toggle {
  margin-top: 4px;
  margin-bottom: 4px;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  overflow: hidden;
}

.type-btn, .difficulty-btn {
  border-radius: 0 !important;
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0.3px;
}

.course-select {
  margin-top: 4px;
}

.content-textarea {
  margin-top: 4px;
}

.options-container {
  margin-top: 16px;
}

.option-item {
  margin-bottom: 16px;
  padding: 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
}

.option-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
}

.option-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.option-label-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.option-input-container {
  flex: 1;
}

.option-input {
  margin: 0;
}

.option-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.answer-radio, .answer-checkbox {
  margin: 0;
}

.delete-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background-color: rgba(220, 53, 69, 0.1);
  transform: scale(1.05);
}

.delete-btn:disabled {
  opacity: 0.3;
}

.add-option-btn {
  margin-top: 16px;
  border-radius: 8px;
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.form-actions {
  padding: 24px 32px;
  background: #f8f9fa;
}

.cancel-btn, .submit-btn {
  min-width: 100px;
  border-radius: 8px;
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.cancel-btn {
  margin-right: 12px;
}

.submit-btn {
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.2);
}

.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

/* 滚动条美化 */
.form-content::-webkit-scrollbar {
  width: 6px;
}

.form-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.form-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.form-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.type-hint {
  margin-top: 8px;
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background-color: rgba(255, 193, 7, 0.1);
  border-radius: 4px;
  border-left: 3px solid #ffc107;
}
</style>