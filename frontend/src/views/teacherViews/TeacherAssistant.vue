<template>
  <div class="teacher-ai-assistant">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          <v-icon class="me-3" color="primary">fas fa-robot</v-icon>
          智能助教
          <v-chip class="ms-3" color="success" size="small" variant="outlined">
            教师专用
          </v-chip>
          <v-spacer></v-spacer>
          <v-tooltip text="教师专用AI助手，提供课程分析、学生洞察、教学建议等功能">
            <template v-slot:activator="{ props }">
              <v-icon v-bind="props" color="grey">mdi-help-circle-outline</v-icon>
            </template>
          </v-tooltip>
        </v-card-title>
        <v-divider></v-divider>
        
        <v-card-text class="pa-0">
          <v-row class="ma-0 fill-height">
            <!-- 左侧对话历史 -->
            <v-col cols="3" class="pa-0">
              <div style="display: flex; flex-direction: column; height: 100%;">

                
                <ChatHistory
                  :chat-history="chatHistory"
                  :current-chat="currentChat"
                  @new-chat="startNewChat"
                  @select-chat="selectChat"
                  @edit-chat="handleEditChat"
                  @delete-chat="handleDeleteChat"
                />
              </div>
            </v-col>
            
            <!-- 右侧聊天区域 -->
            <v-col cols="9" class="pa-0 chat-main">
              <StatusBar
                :show-status="showStatus"
                :current-status="currentStatus"
                :status-stats="statusStats"
                :current-tool-info="currentToolInfo"
              />
              
              <ChatMessages
                ref="chatMessagesRef"
                :current-chat="currentChat"
                :is-typing="isTyping"
              />
              
              <!-- MessageInput已注释图片上传功能 -->
              <MessageInput
                ref="messageInputRef"
                v-model="userInput"
                :disabled="isTyping"
                :is-recording="isRecording"
                :uploaded-image="uploadedImage"
                :show-suggestions="showSuggestions"
                :suggestions="suggestionsList"
                :selected-suggestion-index="selectedSuggestionIndex"
                :suggestions-position="suggestionsPosition"
                :is-searching="isSearchingVideos"
                :placeholder="'向智能助教提问，获取教学分析和建议...'"
                @toggle-voice="handleToggleVoice"
                @remove-image="removeImage"
                @send="handleSendMessage"
                @input="handleInputChange"
                @keydown="handleKeyDown"
                @suggestion-select="handleSuggestionSelect"
                @update:selected-suggestion-index="selectedSuggestionIndex = $event"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-container>
    
    <ChatDialogs
      v-model:show-edit-dialog="showEditDialog"
      v-model:show-delete-dialog="showDeleteDialog"
      v-model:show-content-warning="showContentWarning"
      :editing-chat="editingChat"
      :deleting-chat="deletingChat"
      :content-warning-message="contentWarningMessage"
      @save-edit-title="handleSaveEditTitle"
      @confirm-delete="handleConfirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import ChatHistory from '../../components/ai/ChatHistory.vue'
import ChatMessages from '../../components/ai/ChatMessages.vue'
import MessageInput from '../../components/ai/MessageInput.vue'
import StatusBar from '../../components/ai/StatusBar.vue'
//import TeacherReferenceSelector from '../../components/ai/TeacherReferenceSelector.vue'
import ChatDialogs from '../../components/ai/ChatDialogs.vue'
import { useChatManager } from '../../composables/useChatManager'
import { useTeacherReferenceManager } from '../../composables/useTeacherReferenceManager'
import { useSuggestions } from '../../composables/useSuggestions'
import { useChatMessages } from '../../composables/useChatMessages'
import { useTeacherMessageSender } from '../../composables/useTeacherMessageSender'
import { useVoiceInput, useImageUpload } from '../../composables/useInputHandlers'
import type { Chat } from '../../types/chat'

// 聊天管理 - 复用现有逻辑
const {
  chatHistory,
  currentChat,
  sessionId,
  loadChatHistory,
  startNewChat,
  selectChat,
  updateChatTitle,
  deleteChat
} = useChatManager()

// 教师端引用管理 - 新的教师专用逻辑
const {
  qaMode,
  selectedReferences,
  clearAllReferences,
  removeReference,
  addReference
} = useTeacherReferenceManager()

// 建议搜索 - 复用现有逻辑
const {
  showSuggestions,
  suggestionsList,
  selectedSuggestionIndex,
  suggestionsPosition,
  isSearchingVideos,
  handleTextareaInput,
  onSuggestionClick,
  handleSuggestionKeyDown,
  hideSuggestions
} = useSuggestions()

// 聊天消息管理 - 复用现有逻辑
const {
  updateAccumulatedIds,
  getAccumulatedIds
} = useChatMessages()

// 教师端消息发送 - 新的教师专用逻辑
const {
  isTyping,
  currentStatus,
  statusStats,
  showStatus,
  currentToolInfo,
  sendMessage,
  handleStatusEvent,
  handleToolEvent,
  insertContentSegment
} = useTeacherMessageSender(updateAccumulatedIds, getAccumulatedIds)

// 语音输入 - 复用现有逻辑
const { isRecording, toggleVoiceInput } = useVoiceInput()

// 图片上传 - 复用现有逻辑
const { uploadedImage, handleImageUpload: processImageUpload, removeImage } = useImageUpload()

// 本地状态
const userInput = ref('')
const chatMessagesRef = ref<InstanceType<typeof ChatMessages> | null>(null)
const messageInputRef = ref<InstanceType<typeof MessageInput> | null>(null)

// 对话框状态 - 复用现有逻辑
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showContentWarning = ref(false)
const editingChat = ref<Chat | null>(null)
const deletingChat = ref<Chat | null>(null)
const contentWarningMessage = ref('')

// 处理编辑对话 - 复用现有逻辑
const handleEditChat = (chat: Chat) => {
  editingChat.value = chat
  showEditDialog.value = true
}

// 处理删除对话 - 复用现有逻辑
const handleDeleteChat = (chat: Chat) => {
  deletingChat.value = chat
  showDeleteDialog.value = true
}

// 保存编辑标题 - 复用现有逻辑
const handleSaveEditTitle = async (title: string) => {
  if (editingChat.value?.id) {
    const success = await updateChatTitle(editingChat.value.id, title)
    if (success) {
      showEditDialog.value = false
      editingChat.value = null
    }
  }
}

// 确认删除 - 复用现有逻辑
const handleConfirmDelete = async () => {
  if (deletingChat.value?.id) {
    const success = await deleteChat(deletingChat.value.id)
    if (success) {
      showDeleteDialog.value = false
      deletingChat.value = null
    }
  }
}

// 处理语音输入 - 复用现有逻辑
const handleToggleVoice = () => {
  toggleVoiceInput((transcript: string) => {
    userInput.value = transcript
  })
}

// 处理图片上传 - 复用现有逻辑
const handleImageUpload = async (file: File) => {
  const imageData = await processImageUpload(file)
  // 可以在这里添加OCR处理等逻辑
}

// 处理输入变化 - 复用现有逻辑
const handleInputChange = (event: Event) => {
  const textareaComponent = messageInputRef.value?.textareaRef
  if (textareaComponent) {
    let textarea: HTMLTextAreaElement | null = null
    
    if ((textareaComponent as any).$el) {
      textarea = (textareaComponent as any).$el.querySelector('textarea')
    } else if (textareaComponent instanceof HTMLTextAreaElement) {
      textarea = textareaComponent
    }
    
    if (textarea && typeof textarea.value === 'string') {
      handleTextareaInput(event, userInput.value, textarea)
    }
  }
}

// 处理键盘事件 - 复用现有逻辑
const handleKeyDown = (event: KeyboardEvent) => {
  const suggestionResult = handleSuggestionKeyDown(event)
  if (suggestionResult === true) return
  
  if (typeof suggestionResult === 'object') {
    const result = onSuggestionClick(
      suggestionResult,
      userInput.value,
      messageInputRef.value?.textareaRef
    )
    if (result) {
      userInput.value = result.newValue
      addReference(result.suggestion)
    }
    return
  }

  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

// 处理建议选择 - 复用现有逻辑
const handleSuggestionSelect = (suggestion: any) => {
  const result = onSuggestionClick(
    suggestion,
    userInput.value,
    messageInputRef.value?.textareaRef
  )
  if (result) {
    userInput.value = result.newValue
    addReference(result.suggestion)
  }
}

// 发送消息 - 使用教师端专用逻辑
const handleSendMessage = async () => {
  if (!currentChat.value) return

  let content = userInput.value.trim()
  
  // 如果有上传的图片，添加到内容中
  if (uploadedImage.value) {
    content = `<img src='${uploadedImage.value}' style='max-width:220px;max-height:140px;border-radius:12px;margin:8px 0;display:block;' /><div>${content}</div>`
  }

  if (!content && !uploadedImage.value) return

  const result = await sendMessage(
    content,
    currentChat.value,
    sessionId.value,
    qaMode.value,
    selectedReferences.value
  )

  if (result?.error) {
    if (result.message) {
      contentWarningMessage.value = result.message
      showContentWarning.value = true
    }
    return
  }

  // 清空输入
  userInput.value = ''
  removeImage()

  // 更新sessionId
  if (result?.sessionId) {
    sessionId.value = result.sessionId
    if (currentChat.value && !chatHistory.value.find((c: Chat) => c.id === result.sessionId)) {
      chatHistory.value.unshift({ ...currentChat.value })
    }
  }

  // 滚动到底部
  await nextTick()
  chatMessagesRef.value?.scrollToBottom()
}

// 组件挂载
onMounted(() => {
  loadChatHistory()
  // 如果没有当前对话，创建新对话
  if (!currentChat.value) {
    startNewChat()
  }
})

// 组件卸载前清理
onBeforeUnmount(() => {
  hideSuggestions()
})
</script>

<style scoped>
.teacher-ai-assistant {
  width: 100%;
  height: 100%;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: calc(100vh - 150px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-main {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 确保卡片内容占满高度 */
:deep(.v-card-text) {
  height: 100%;
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:deep(.v-card-title) {
  flex-shrink: 0;
}

:deep(.v-divider) {
  flex-shrink: 0;
}

/* 确保行布局占满高度 */
:deep(.ma-0.fill-height) {
  height: 100%;
  min-height: 0;
}
</style> 