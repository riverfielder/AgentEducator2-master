<template>
  <div>
    <!-- 当前问答模式显示 -->
    <div v-if="qaMode !== 'general'" class="qa-mode-display px-4 pb-3">
      <v-card variant="outlined" class="pa-3">
        <div class="text-subtitle-2 mb-2 d-flex align-center">
          <v-icon 
            :color="getModeColor(qaMode)" 
            size="small" 
            class="mr-2"
          >
            {{ getModeIcon(qaMode) }}
          </v-icon>
          {{ getModeLabel(qaMode) }}
        </div>
        <div class="text-caption text-grey">
          {{ getModeDescription(qaMode) }}
        </div>
      </v-card>
    </div>
    
    <!-- 当前选择的课程/视频信息 -->
    <div v-if="selectedReferences.length > 0" class="current-selection px-4 pb-3">
      <v-card variant="outlined" class="pa-3">
        <div class="text-subtitle-2 mb-2 d-flex align-items-center justify-space-between">
          已选择内容 ({{ selectedReferences.length }})
          <v-btn 
            size="x-small" 
            variant="text" 
            @click="$emit('clear-all')"
            class="text-caption"
          >
            清除全部
          </v-btn>
        </div>
        <div class="selected-references">
          <div 
            v-for="ref in selectedReferences" 
            :key="`${ref.type}-${ref.id}`"
            class="selected-ref-item"
          >
            <v-icon 
              size="small" 
              :color="ref.type === 'course' ? 'primary' : 'secondary'" 
              class="mr-2"
            >
              {{ ref.type === 'course' ? 'mdi-book-open-variant' : 'mdi-play-circle' }}
            </v-icon>
            <div class="flex-grow-1">
              <div class="text-caption font-weight-bold">{{ ref.name }}</div>
              <div v-if="ref.courseName" class="text-caption text-grey">{{ ref.courseName }}</div>
            </div>
            <v-btn 
              size="x-small" 
              variant="text" 
              icon
              @click="$emit('remove-reference', ref)"
            >
              <v-icon size="16">mdi-close</v-icon>
            </v-btn>
          </div>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Reference } from '../../types/chat'

interface Props {
  qaMode: string
  selectedReferences: Reference[]
}

defineProps<Props>()

defineEmits<{
  'clear-all': []
  'remove-reference': [ref: Reference]
}>()

// 模式显示相关的辅助方法
const getModeColor = (mode: string) => {
  switch (mode) {
    case 'video': return 'secondary'
    case 'course': return 'primary'
    case 'all': return 'warning'
    default: return 'grey'
  }
}

const getModeIcon = (mode: string) => {
  switch (mode) {
    case 'video': return 'mdi-play-circle'
    case 'course': return 'mdi-book-open-variant'
    case 'all': return 'mdi-earth'
    default: return 'mdi-chat'
  }
}

const getModeLabel = (mode: string) => {
  switch (mode) {
    case 'video': return '视频问答'
    case 'course': return '课程问答'
    case 'all': return '全平台问答'
    default: return '通用问答'
  }
}

const getModeDescription = (mode: string) => {
  switch (mode) {
    case 'video': return '基于所选视频内容进行问答'
    case 'course': return '基于所选课程内容进行问答'
    case 'all': return '基于全平台所有内容进行问答'
    default: return '通用AI问答，不限制特定内容范围'
  }
}
</script>

<style scoped>
.current-selection .v-card {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef !important;
}

.selected-ref-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
  gap: 8px;
}

.selected-ref-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 4px;
  padding-bottom: 8px;
}
</style>
