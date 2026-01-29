<template>
  <div>
    <!-- 预设问题胶囊 -->
    <div v-if="showPresetQuestions" class="preset-questions-container">
      <h4 class="preset-questions-title">💬 试试这些问题开始对话</h4>
      <div class="preset-questions-chips">
        <v-chip
          v-for="question in displayedQuestions"
          :key="question"
          class="preset-question-chip"
          color="primary"
          variant="outlined"
          size="small"
          @click="selectPresetQuestion(question)"
        >
          {{ question }}
        </v-chip>
      </div>
    </div>
    
    <div class="ai-input-row">
      <div class="ai-input-actions">
      <v-btn 
        icon 
        :color="isRecording ? 'primary' : 'grey'" 
        @click="$emit('toggle-voice')" 
        class="ai-input-btn-small"
      >
        <v-icon>{{ isRecording ? 'mdi-microphone' : 'mdi-microphone-outline' }}</v-icon>
      </v-btn>
      <input 
        type="file" 
        ref="imageInput" 
        accept="image/*" 
        style="display:none" 
        @change="handleImageUpload" 
      />
      <div v-if="uploadedImage" class="ai-uploaded-thumb">
        <img :src="uploadedImage" alt="预览" class="ai-thumb-img" />
        <v-btn icon size="x-small" class="ai-thumb-remove" @click="$emit('remove-image')">
          <v-icon size="16">mdi-close</v-icon>
        </v-btn>
      </div>
    </div>
    
    <!-- 输入框容器 -->
    <div class="input-container">
      <v-textarea
        ref="textareaRef"
        v-model="inputValue"
        placeholder="输入问题，支持 @ 引用课程或视频..."
        rows="2"
        auto-grow
        density="compact"
        hide-details
        variant="outlined"
        class="ai-input-textarea-large"
        @input="$emit('input', $event)"
        @keydown="$emit('keydown', $event)"
        :disabled="disabled"
      ></v-textarea>
      
      <SuggestionsDropdown
        :show-suggestions="showSuggestions"
        :suggestions="suggestions"
        :selected-index="selectedSuggestionIndex"
        :position="suggestionsPosition"
        :is-searching="isSearching"
        @select="$emit('suggestion-select', $event)"
        @update:selected-index="$emit('update:selected-suggestion-index', $event)"
      />
    </div>
    
    <v-btn
      color="primary"
      icon
      @click="$emit('send')"
      class="ai-input-send-btn"
      :disabled="!inputValue.trim() && !uploadedImage || disabled"
    >
      <v-icon>mdi-send</v-icon>
    </v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SuggestionsDropdown from './SuggestionsDropdown.vue'
import type { Suggestion } from '../../types/chat'

interface Props {
  modelValue: string
  disabled: boolean
  isRecording: boolean
  uploadedImage: string | null
  showSuggestions: boolean
  suggestions: Suggestion[]
  selectedSuggestionIndex: number
  suggestionsPosition: { top: number; left: number }
  isSearching: boolean
  showPresetQuestions?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'toggle-voice': []
  'image-upload': [file: File]
  'remove-image': []
  'send': []
  'input': [event: Event]
  'keydown': [event: KeyboardEvent]
  'suggestion-select': [suggestion: Suggestion]
  'preset-question-select': [question: string]
  'update:selected-suggestion-index': [index: number]
}>()

const imageInput = ref<HTMLInputElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const inputValue = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value)
})

// 预设问题数据
const presetQuestions = [
  '总结一下我学的怎样',
  '我准备写作业，为我复习相关知识点',
  '什么是人月神话？',
]

const displayedQuestions = ref<string[]>([])

// 获取随机问题
const getRandomQuestions = () => {
  const shuffled = [...presetQuestions].sort(() => 0.5 - Math.random())
  return shuffled.slice(0, 3)
}

// 选择预设问题
const selectPresetQuestion = (question: string) => {
  emit('preset-question-select', question)
}

// 初始化显示的问题
onMounted(() => {
  displayedQuestions.value = getRandomQuestions()
})

const triggerImageUpload = () => {
  imageInput.value?.click()
}

const handleImageUpload = async (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files || files.length === 0) return
  
  const file = files[0]
  emit('image-upload', file)
  
  // 重置input的value，允许重复上传同一图片
  if (imageInput.value) imageInput.value.value = ''
}

// 暴露textarea引用给父组件
defineExpose({
  textareaRef
})
</script>

<style scoped>
.ai-input-row {
  display: flex;
  align-items: flex-end;
  padding: 16px;
  gap: 12px;
  background: #fff;
  position: sticky;
  bottom: 0;
  z-index: 10;
  border-top: 1px solid #e0e0e0;
}

.ai-input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}

.ai-input-btn-small {
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: 6px;
  margin: 0;
  padding: 0;
}

.ai-input-textarea-large {
  flex: 1;
  min-height: 48px;
  font-size: 16px;
  margin: 0 8px;
}

.ai-input-send-btn {
  width: 40px;
  height: 40px;
  min-width: 40px;
  min-height: 40px;
  border-radius: 10px;
  margin-left: 0;
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-container {
  position: relative;
  flex: 1;
}

/* 上传图片预览样式 */
.ai-uploaded-thumb {
  position: relative;
  display: inline-block;
  margin-left: 8px;
}

.ai-thumb-img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.ai-thumb-remove {
  position: absolute;
  top: -4px;
  right: -4px;
  background-color: #f44336 !important;
  color: white !important;
  width: 18px !important;
  height: 18px !important;
  min-width: 18px !important;
  min-height: 18px !important;
}

/* 预设问题胶囊样式 */
.preset-questions-container {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(25, 118, 210, 0.1);
  text-align: left;
}

.preset-questions-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #1976d2, #42a5f5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
  text-align: left;
  letter-spacing: 0.5px;
}

.preset-questions-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-start;
}

.preset-question-chip {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  font-weight: 500;
  border-radius: 20px !important;
  padding: 8px 16px !important;
  height: auto !important;
  min-height: 36px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.preset-question-chip:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 16px rgba(25, 118, 210, 0.25);
  background: linear-gradient(135deg, #1976d2, #42a5f5) !important;
  color: white !important;
  border-color: transparent !important;
}
</style>
