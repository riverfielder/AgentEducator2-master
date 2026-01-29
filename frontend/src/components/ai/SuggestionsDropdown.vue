<template>
  <div
    v-if="showSuggestions"
    class="suggestions-dropdown"
    :style="{
      position: 'fixed',
      top: position.top + 'px',
      left: position.left + 'px',
      zIndex: 1000
    }"
  >
    <v-card class="suggestions-card" elevation="8">
      <v-card-text class="pa-0">
        <div v-if="isSearching" class="suggestion-loading">
          <v-progress-circular indeterminate size="16" class="mr-2"></v-progress-circular>
          <span class="text-caption">搜索视频中...</span>
        </div>
        <div
          v-for="(suggestion, index) in suggestions"
          :key="`${suggestion.type}-${suggestion.id}`"
          class="suggestion-item"
          :class="{ 'suggestion-selected': index === selectedIndex }"
          @click="$emit('select', suggestion)"
          @mouseenter="$emit('update:selectedIndex', index)"
        >
          <div class="suggestion-content">
            <div class="suggestion-header">
              <v-icon 
                :color="suggestion.type === 'course' ? 'primary' : 'secondary'"
                size="small"
                class="mr-2"
              >
                {{ suggestion.type === 'course' ? 'mdi-book-open-variant' : 'mdi-play-circle' }}
              </v-icon>
              <span class="suggestion-title">{{ suggestion.text || suggestion.name }}</span>
            </div>
            <div v-if="suggestion.description" class="suggestion-description">
              {{ truncate(suggestion.description, 50) }}
            </div>
            <div v-if="suggestion.courseName" class="suggestion-course">
              来自课程: {{ suggestion.courseName }}
            </div>
          </div>
        </div>
        <div v-if="suggestions.length === 0 && !isSearching" class="suggestion-empty">
          <span class="text-caption text-grey">没有找到匹配的课程或视频</span>
        </div>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="pa-2">
        <span class="text-caption text-grey">
          使用 ↑↓ 选择，Enter 确认，Esc 取消
        </span>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import type { Suggestion } from '../../types/chat'

interface Props {
  showSuggestions: boolean
  suggestions: Suggestion[]
  selectedIndex: number
  position: { top: number; left: number }
  isSearching: boolean
}

defineProps<Props>()

defineEmits<{
  select: [suggestion: Suggestion]
  'update:selectedIndex': [index: number]
}>()

// 截断文本
const truncate = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}
</script>

<style scoped>
.suggestions-dropdown {
  max-width: 400px;
  min-width: 300px;
}

.suggestions-card {
  border-radius: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.suggestion-item:hover,
.suggestion-item.suggestion-selected {
  background-color: #f8f9fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-content {
  width: 100%;
}

.suggestion-header {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.suggestion-title {
  font-weight: 500;
  font-size: 14px;
}

.suggestion-description {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 2px;
  line-height: 1.3;
}

.suggestion-course {
  font-size: 11px;
  color: #28a745;
  font-style: italic;
}

.suggestion-loading {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
}

.suggestion-empty {
  padding: 12px 16px;
  text-align: center;
  color: #6c757d;
}
</style>
