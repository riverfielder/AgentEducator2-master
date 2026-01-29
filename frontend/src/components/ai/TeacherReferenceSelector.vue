<template>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Reference } from '../../types/chat'

// Props
interface Props {
  qaMode: string
  selectedReferences: Reference[]
}

// Emits
interface Emits {
  (e: 'clear-all'): void
  (e: 'remove-reference', ref: Reference): void
}

defineProps<Props>()
defineEmits<Emits>()

// 本地状态
const showCourseSelector = ref(false)
const showVideoSelector = ref(false)
const showStudentSelector = ref(false)

// 获取模式颜色
const getModeColor = (mode: string) => {
  const colors = {
    'teacher_general': 'primary',
    'course_analysis': 'success',
    'content_analysis': 'info',
    'student_insights': 'warning',
    'all': 'purple'
  }
  return colors[mode as keyof typeof colors] || 'primary'
}

// 获取模式标签
const getModeLabel = (mode: string) => {
  const labels = {
    'teacher_general': '通用教师',
    'course_analysis': '课程分析',
    'content_analysis': '内容分析',
    'student_insights': '学生洞察',
    'all': '综合分析'
  }
  return labels[mode as keyof typeof labels] || '未知模式'
}

// 获取模式描述
const getModeDescription = (mode: string) => {
  const descriptions = {
    'teacher_general': '提供通用的教学建议和支持',
    'course_analysis': '深入分析特定课程的教学内容和结构',
    'content_analysis': '分析教学视频和材料的内容质量',
    'student_insights': '基于学生数据提供个性化教学建议',
    'all': '综合多种数据源进行全面分析'
  }
  return descriptions[mode as keyof typeof descriptions] || '智能教学辅助模式'
}

// 获取引用图标
const getRefIcon = (type: string) => {
  const icons = {
    'course': 'mdi-book',
    'video': 'mdi-video',
    'student': 'mdi-account',
    'class': 'mdi-account-group'
  }
  return icons[type as keyof typeof icons] || 'mdi-file'
}
</script>

<style scoped>
.teacher-reference-selector {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  background: #fafafa;
}

.mode-description {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.6);
  line-height: 1.4;
}

.references-list {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  padding: 8px;
}

.references-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.references-items {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.quick-add {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.v-card-title) {
  font-size: 0.875rem;
  font-weight: 500;
}

:deep(.v-card-text) {
  font-size: 0.8rem;
}
</style> 