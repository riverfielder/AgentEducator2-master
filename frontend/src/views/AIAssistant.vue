<template>
  <div class="ai-assistant">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          AI助手
          <v-spacer></v-spacer>
        </v-card-title>
        <v-divider></v-divider>
        
        <v-card-text class="pa-0">
          <v-row class="ma-0 fill-height">
            <!-- 左侧对话历史 -->
            <v-col cols="3" class="pa-0">
              <div style="display: flex; flex-direction: column; height: 100%;">
                <ReferenceSelector
                  :qa-mode="qaMode"
                  :selected-references="selectedReferences"
                  @clear-all="clearAllReferences"
                  @remove-reference="removeReference"
                />
                
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
                class="flex-grow-1"
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
                :show-preset-questions="shouldShowPresetQuestions"
                @toggle-voice="handleToggleVoice"
                @remove-image="removeImage"
                @send="handleSendMessage"
                @input="handleInputChange"
                @keydown="handleKeyDown"
                @suggestion-select="handleSuggestionSelect"
                @preset-question-select="handlePresetQuestionSelect"
                @update:selected-suggestion-index="selectedSuggestionIndex = $event"
                class="flex-shrink-0"
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
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import ChatHistory from '../components/ai/ChatHistory.vue'
import ChatMessages from '../components/ai/ChatMessages.vue'
import MessageInput from '../components/ai/MessageInput.vue'
import StatusBar from '../components/ai/StatusBar.vue'
import ReferenceSelector from '../components/ai/ReferenceSelector.vue'
import ChatDialogs from '../components/ai/ChatDialogs.vue'
import { useChatManager } from '../composables/useChatManager'
import { useReferenceManager } from '../composables/useReferenceManager'
import { useSuggestions } from '../composables/useSuggestions'
import { useChatMessages } from '../composables/useChatMessages'
import { useMessageSender } from '../composables/useMessageSender'
import { useVoiceInput, useImageUpload } from '../composables/useInputHandlers'
import type { Chat } from '../types/chat'
import type { Reference } from '../types/chat'

// 聊天管理
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

// 引用管理
const {
  qaMode,
  selectedReferences,
  clearAllReferences,
  removeReference,
  addReference
} = useReferenceManager()

// 建议搜索
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

// 聊天消息管理（提供累积ID功能）
const {
  updateAccumulatedIds,
  getAccumulatedIds
} = useChatMessages()

// 消息发送
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
} = useMessageSender(updateAccumulatedIds, getAccumulatedIds)

// 语音输入
const { isRecording, toggleVoiceInput } = useVoiceInput()

// 图片上传
const { uploadedImage, handleImageUpload: processImageUpload, removeImage } = useImageUpload()

// 本地状态
const userInput = ref('')
const chatMessagesRef = ref<InstanceType<typeof ChatMessages> | null>(null)
const messageInputRef = ref<InstanceType<typeof MessageInput> | null>(null)

// 对话框状态
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showContentWarning = ref(false)
const editingChat = ref<Chat | null>(null)
const deletingChat = ref<Chat | null>(null)
const contentWarningMessage = ref('')

// 处理编辑对话
const handleEditChat = (chat: Chat) => {
  editingChat.value = chat
  showEditDialog.value = true
}

// 处理删除对话
const handleDeleteChat = (chat: Chat) => {
  deletingChat.value = chat
  showDeleteDialog.value = true
}

// 保存编辑标题
const handleSaveEditTitle = async (title: string) => {
  if (editingChat.value?.id) {
    const success = await updateChatTitle(editingChat.value.id, title)
    if (success) {
      showEditDialog.value = false
      editingChat.value = null
    }
  }
}

// 确认删除
const handleConfirmDelete = async () => {
  if (deletingChat.value?.id) {
    const success = await deleteChat(deletingChat.value.id)
    if (success) {
      showDeleteDialog.value = false
      deletingChat.value = null
    }
  }
}

// 处理语音输入
const handleToggleVoice = () => {
  toggleVoiceInput((transcript: string) => {
    userInput.value = transcript
  })
}

// 处理图片上传
const handleImageUpload = async (file: File) => {
  const imageData = await processImageUpload(file)
  // 可以在这里添加OCR处理等逻辑
}

// 处理输入变化
const handleInputChange = (event: Event) => {
  const textareaComponent = messageInputRef.value?.textareaRef
  if (textareaComponent) {
    // 检查是否为Vue组件实例
    let textarea: HTMLTextAreaElement | null = null
    
    if ((textareaComponent as any).$el) {
      // 如果是Vue组件，从$el中获取textarea
      textarea = (textareaComponent as any).$el.querySelector('textarea')
    } else if (textareaComponent instanceof HTMLTextAreaElement) {
      // 如果已经是DOM元素
      textarea = textareaComponent
    }
    
    if (textarea && typeof textarea.value === 'string') {
      handleTextareaInput(event, userInput.value, textarea)
    }
  }
}

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  // 处理建议选择
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
      // 只添加支持的引用类型
      if (result.suggestion.type === 'course' || result.suggestion.type === 'video') {
        addReference(result.suggestion as Reference)
      }
    }
    return
  }

  // 处理 Enter 和 Shift+Enter
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSendMessage()
  }
}

// 处理建议选择
const handleSuggestionSelect = (suggestion: any) => {
  const result = onSuggestionClick(
    suggestion,
    userInput.value,
    messageInputRef.value?.textareaRef
  )
  if (result) {
    userInput.value = result.newValue
    // 只添加支持的引用类型
    if (result.suggestion.type === 'course' || result.suggestion.type === 'video') {
      addReference(result.suggestion as Reference)
    }
  }
}

// 预设问题相关
const shouldShowPresetQuestions = computed(() => {
  return !currentChat.value?.messages || currentChat.value.messages.length === 0
})

// 处理预设问题选择
const handlePresetQuestionSelect = (question: string) => {
  userInput.value = question
  // 自动发送消息
  nextTick(() => {
    handleSendMessage()
  })
}

// 发送消息
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
      // 如果是新会话，添加到历史列表
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
.ai-assistant {
  width: 100%;
  height: 100%;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  height: calc(100vh - 130px);
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
