<template>
  <div>
    <div class="question-card-list">      <div class="card-list-inner">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-content">
            <div class="loading-spinner-container">
              <v-progress-circular
                indeterminate
                color="primary"
                size="48"
                width="4"
              ></v-progress-circular>
              <v-icon class="loading-icon" color="primary" size="24">mdi-database</v-icon>
            </div>
            <div class="loading-text">正在加载题库...</div>
            <div class="loading-subtext">请稍候，正在为您获取最新的题目数据</div>
            
            <!-- 骨架屏预览 -->
            <div class="skeleton-preview">
              <div class="skeleton-card" v-for="i in 3" :key="i">
                <div class="skeleton-header">
                  <div class="skeleton-type"></div>
                  <div class="skeleton-title"></div>
                </div>
                <div class="skeleton-content">
                  <div class="skeleton-line"></div>
                  <div class="skeleton-line short"></div>
                </div>
                <div class="skeleton-footer">
                  <div class="skeleton-chip"></div>
                  <div class="skeleton-chip"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-else-if="!questions.length" class="empty-state">
          <v-icon size="60" color="grey lighten-1">mdi-database-search</v-icon>
          <div class="mt-2 grey--text">暂无题目，点击上方"新增题目"按钮添加</div>
        </div>
        
        <!-- 题目列表 -->
        <v-card
          v-else
          v-for="(item, idx) in questions"
          :key="item.id"
          class="question-card beautiful-card"
          outlined
          elevation="4"
        >
          <div class="card-content-row">
            <div class="card-main-content">
              <div class="question-title-row">
                <span class="type-label">({{ getTypeLabel(item.question_type) }})</span>
                <span class="question-title-text">{{ item.content }}</span>
              </div>
              <div class="course-row" v-if="item.course_name || getCourseName(item.course_id)">
                <v-chip :color="item.can_edit ? 'primary' : 'grey'" size="small" class="course-chip">
                  <v-icon start small>mdi-book-open-variant</v-icon>
                  {{ item.course_name || getCourseName(item.course_id) }}
                  <span v-if="getCourseTeacher(item.course_id)" class="ml-1 teacher-name">({{ getCourseTeacher(item.course_id) }})</span>
                </v-chip>
              </div>
              <div v-if="(item.question_type === 'single' || item.question_type === 'multiple') && item.options && item.options.length" class="option-list-row">
                <div v-for="(opt, oidx) in item.options" :key="oidx" class="option-item-row">
                  <span class="option-label-row">{{ String.fromCharCode(65 + oidx) }}.</span>
                  <span>{{ cleanOptionText(opt, oidx) }}</span>
                </div>
              </div>              <div v-if="getCorrectAnswerByType(item)" class="ref-answer-row">
                <span class="ref-answer-label">参考答案：</span>
                <span class="ref-answer-value">{{ getCorrectAnswerByType(item) }}</span>
              </div>
              <div v-if="item.explanation" class="explanation-row">
                <span class="explanation-label">解析：</span>
                <span class="explanation-value">{{ item.explanation }}</span>
              </div>
            </div>
            <div class="card-actions-row">
              <!-- 只有可编辑的题目才显示编辑和删除按钮 -->
              <template v-if="item.can_edit">
                <v-btn icon color="primary" size="small" class="action-btn-row" @click="$emit('edit', item)"><v-icon>mdi-pencil</v-icon></v-btn>
                <v-btn icon color="red" size="small" class="action-btn-row" @click="$emit('delete', item.id)"><v-icon>mdi-delete</v-icon></v-btn>
              </template>
              <!-- 不可编辑的题目显示查看按钮 -->
              <template v-else>
                <v-btn icon color="info" size="small" class="action-btn-row" @click="$emit('show-detail', item)">
                  <v-icon>mdi-eye</v-icon>
                </v-btn>
                <v-chip color="orange" size="small" class="ml-2">他人题目</v-chip>
              </template>
            </div>
          </div>
          <v-divider class="my-2" />
          <div class="card-bottom-row">
            <span class="difficulty-label">难度：<span class="difficulty-value">{{ getDifficultyLabel(item.difficulty || '') }}</span></span>
            <span class="course-label">课程：{{ item.course_name || getCourseName(item.course_id) || '—' }}</span>
            <!-- 当有知识点时只显示知识点，否则显示标签 -->
            <span v-if="item.extractedKeywords && item.extractedKeywords.length" class="extracted-keywords-label">
              知识点：
              <v-chip
                v-for="(k, index) in item.extractedKeywords"
                :key="index"
                :color="getKeywordTagColor(k.category)"
                size="small"
                class="mr-1 mb-1"
                @click="navigateToKeywordDetail(k.id)"
              >
                {{ k.name || k }}
              </v-chip>
            </span>
            <span v-else class="tags-label">知识点：
              <template v-if="item.tags && item.tags.length">
                <v-chip v-for="tag in item.tags.slice(0, 5)" :key="tag" color="indigo lighten-3" class="mr-1 mb-1" small>{{ tag }}</v-chip>
                <span v-if="item.tags.length > 5" class="text-caption text-grey ml-1">+{{ item.tags.length - 5 }}个</span>
              </template>
              <template v-else>—</template>
            </span>
            <span class="remark-label">备注：{{ item.remark || '—' }}</span>
          </div>
        </v-card>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { defineProps, ref } from 'vue';
import { useRouter } from 'vue-router';

interface KeywordItem {
  id: number;
  name: string;
  category: string;
}

interface QuestionItem {
  id: number | string;
  content: string;
  question_type: string;
  options?: string[];
  answer: string | string[];
  explanation?: string;
  course_id?: string;
  difficulty?: string;
  tags?: string[];
  remark?: string;
  extractedKeywords?: KeywordItem[];
  course_name?: string;
  can_edit?: boolean;  // 添加权限字段
}

const props = defineProps({
  headers: { type: Array, default: () => [] },
  questions: { type: Array as () => QuestionItem[], default: () => [] },
  loading: { type: Boolean, default: false },
  courseOptions: { type: Array as () => Array<{title: string, value: string}>, default: () => [] }
});

const router = useRouter();

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

function getTypeLabel(type: string) {
  const map: any = {
    single: '单选题',
    multiple: '多选题',
    blank: '填空题',
    essay: '问答题'
  };
  return map[type] || type;
}
function getDifficultyLabel(diff: string) {
  const map: any = { easy: '简单', medium: '普通', hard: '困难' };
  return map[diff] || diff || '—';
}
function getCourseName(course_id: string | undefined): string | undefined {
  if (!course_id) return undefined;
  const course = props.courseOptions.find(c => c.value === course_id);
  return course ? course.title : course_id;
}

function getCourseTeacher(course_id: string | undefined): string | undefined {
  if (!course_id) return undefined;
  const course = props.courseOptions.find(c => c.value === course_id);
  return course && (course as any).teacher_name ? (course as any).teacher_name : undefined;
}

// 根据题型获取正确的答案字段显示
function getCorrectAnswerByType(item: QuestionItem): string {
  if (!item) return '';
  
  if (item.question_type === 'blank') {
    // 填空题：从 reference 字段获取答案
    return (item as any).reference || '';
  } else if (item.question_type === 'essay') {
    // 问答题：从 reference 字段获取答案
    return (item as any).reference || '';
  } else if (item.question_type === 'single') {
    // 单选题：从 answer 字段获取答案
    return (item as any).answer || (item as any).correct_answer || '';
  } else if (item.question_type === 'multiple') {
    // 多选题：从 answers 字段获取答案
    const answers = (item as any).answers || (item as any).correct_answer || '';
    return Array.isArray(answers) ? answers.join(', ') : answers;
  }
  
  // 兜底逻辑：使用原来的 answer 字段
  return Array.isArray(item.answer) ? item.answer.join(', ') : (item.answer || '');
}

// 根据知识点级别获取标签颜色
function getKeywordTagColor(category: string): string {
  switch (category) {
    case 'core_concept':
      return '#ff6b6b';  // 一级知识点 - 红色
    case 'main_module':
      return '#4ecdc4';  // 二级知识点 - 青色
    case 'specific_point':
      return '#45b7d1';  // 三级知识点 - 蓝色
    default:
      return '#cccccc';  // 默认颜色
  }
}

// 跳转到知识点详情页
function navigateToKeywordDetail(keywordId: number) {
  if (keywordId) {
    router.push({
      name: 'TeacherKnowledgeDetail',
      params: { id: keywordId }
    });
  }
}
</script>
<style scoped>
.question-card-list {
  display: flex;
  justify-content: center;
  width: 100%;
}
.card-list-inner {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  justify-content: center;
  align-items: stretch;
}
.question-card.beautiful-card {
  width: 100%;
  min-height: 180px;
  border-radius: 18px;
  box-shadow: 0 4px 24px rgba(60,60,60,0.10);
  background: #fff;
  transition: box-shadow 0.2s, transform 0.2s;
  padding: 24px 32px 16px 32px;
  margin: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.question-card.beautiful-card:hover {
  box-shadow: 0 12px 48px rgba(60,60,60,0.18);
  transform: translateY(-2px) scale(1.01);
}
.card-content-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: flex-start;
}
.card-main-content {
  flex: 1;
}
.question-title-row {
  font-size: 17px;
  font-weight: 500;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.type-label {
  color: #1976d2;
  font-weight: bold;
  font-size: 15px;
}
.question-title-text {
  color: #222;
}
.ref-answer-row {
  margin-bottom: 8px;
  font-size: 15px;
}
.ref-answer-label {
  color: #888;
  margin-right: 4px;
}
.ref-answer-value {
  font-weight: bold;
  color: #222;
}
.option-list-row {
  display: flex;
  flex-direction: row;
  gap: 32px;
  margin-bottom: 4px;
}
.option-item-row {
  display: flex;
  align-items: center;
  font-size: 15px;
  color: #333;
  min-width: 180px;
}
.option-label-row {
  font-weight: bold;
  margin-right: 4px;
  color: #888;
}
.card-actions-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
  margin-left: 24px;
}
.action-btn-row {
  border-radius: 8px;
  background: #f5f5f5;
  box-shadow: none;
}
.card-bottom-row {
  display: flex;
  flex-direction: row;
  gap: 32px;
  align-items: center;
  font-size: 14px;
  color: #888;
  margin-top: 2px;
  flex-wrap: wrap;
}
.difficulty-label {
  color: #888;
}
.difficulty-value {
  color: #1976d2;
  font-weight: bold;
}
.course-label {
  color: #888;
}
.tags-label {
  display: flex;
  align-items: center;
}
.remark-label {
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.empty-state {
  text-align: center;
  color: #aaa;
  padding: 48px 0 32px 0;
}

/* 加载状态样式 */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  padding: 60px 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border-radius: 12px;
  margin: 0;
  width: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  animation: fadeIn 0.3s ease-in-out;
}

.loading-content {
  text-align: center;
  width: 100%;
}

.loading-spinner-container {
  position: relative;
  display: inline-block;
  animation: pulse 2s ease-in-out infinite;
}

.loading-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: rotate 3s linear infinite;
}

.loading-text {
  font-size: 18px;
  font-weight: 500;
  color: #1976d2;
  margin: 24px 0 8px 0;
  animation: slideUp 0.5s ease-out;
}

.loading-subtext {
  font-size: 14px;
  color: #666;
  margin-bottom: 40px;
  opacity: 0.8;
  animation: slideUp 0.5s ease-out 0.2s both;
}

/* 骨架屏样式 */
.skeleton-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  margin-top: 20px;
}

.skeleton-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  animation: skeletonShimmer 1.5s ease-in-out infinite;
}

.skeleton-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.skeleton-type {
  width: 60px;
  height: 20px;
  background: #e0e0e0;
  border-radius: 4px;
  animation: skeletonPulse 1.2s ease-in-out infinite;
}

.skeleton-title {
  width: 200px;
  height: 20px;
  background: #e0e0e0;
  border-radius: 4px;
  animation: skeletonPulse 1.2s ease-in-out infinite 0.1s;
}

.skeleton-content {
  margin-bottom: 16px;
}

.skeleton-line {
  height: 14px;
  background: #f0f0f0;
  border-radius: 4px;
  margin-bottom: 8px;
  animation: skeletonPulse 1.2s ease-in-out infinite 0.2s;
}

.skeleton-line.short {
  width: 60%;
}

.skeleton-footer {
  display: flex;
  gap: 8px;
}

.skeleton-chip {
  width: 80px;
  height: 24px;
  background: #e8e8e8;
  border-radius: 12px;
  animation: skeletonPulse 1.2s ease-in-out infinite 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes rotate {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

@keyframes skeletonPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes skeletonShimmer {
  0% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(100%);
  }
  100% {
    transform: translateX(-100%);
  }
}
.explanation-row {
  margin-bottom: 8px;
  font-size: 15px;
}
.explanation-label {
  color: #888;
  margin-right: 4px;
}
.explanation-value {
  color: #1976d2;
}
.course-row {
  margin: 4px 0 0 0;
}
.course-chip {
  font-size: 13px;
  margin-top: 2px;
}
.extracted-keywords-label {
  display: flex;
  align-items: center;
}

.cursor-pointer {
  cursor: pointer;
}
</style>