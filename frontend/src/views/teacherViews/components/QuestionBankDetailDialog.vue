<template>
  <v-dialog :model-value="show" @update:modelValue="(val: boolean) => emit('update:show', val)" max-width="600px">
    <v-card>
      <v-card-title>题目详情</v-card-title>
      <v-card-text>
        <v-list dense>
          <v-list-item><b>题目内容：</b>{{ detailItem?.content || '—' }}</v-list-item>
          <v-list-item><b>题型：</b>{{ getTypeLabel(detailItem?.question_type) }}</v-list-item>
          <v-list-item><b>课程：</b>{{ getCourseName(detailItem?.category) || '—' }}</v-list-item>
          <v-list-item><b>难度：</b>{{ getDifficultyLabel(detailItem?.difficulty) }}</v-list-item>
          <v-list-item><b>标签：</b>
            <span v-if="detailItem?.tags && detailItem.tags.length">
              <v-chip v-for="tag in detailItem.tags" :key="tag" color="indigo lighten-3" class="mr-1 mb-1" small>{{ tag }}</v-chip>
            </span>
            <span v-else>—</span>
          </v-list-item>          <v-list-item v-if="detailItem?.options && detailItem.options.length"><b>选项：</b>{{ formatOptions(detailItem.options) }}</v-list-item>
          <v-list-item><b>答案：</b>{{ getCorrectAnswerByType(detailItem) }}</v-list-item>
          <v-list-item><b>解析：</b>{{ detailItem?.explanation || '—' }}</v-list-item>
          <v-list-item><b>备注：</b>{{ detailItem?.remark || '—' }}</v-list-item>
        </v-list>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn text @click="emit('update:show', false)">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
const props = defineProps({
  show: { type: Boolean, default: false },
  detailItem: { type: Object, default: () => ({}) },
  getTypeLabel: { type: Function, required: true },
  getDifficultyLabel: { type: Function, required: true },
  getCourseName: { type: Function, required: true }
});
const emit = defineEmits(['update:show']);

// 添加清理选项前缀的函数
function cleanOptionText(text: string, optionIndex: number): string {
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
}

// 处理选项显示
function formatOptions(options: string[]): string {
  if (!options || !options.length) return '—';
  return options.map((opt, index) => {
    const letter = String.fromCharCode(65 + index);
    const cleanedText = cleanOptionText(opt, index);
    return `${letter}. ${cleanedText}`;
  }).join(' / ');
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
</script> 