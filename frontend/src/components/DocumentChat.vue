<template>
  <div class="document-chat d-flex flex-column h-100">
    <!-- 聊天历史 -->
    <div class="chat-messages flex-grow-1 pa-4" ref="messagesContainer">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="d-flex flex-column justify-center align-center h-100">
        <v-icon size="64" color="primary" class="mb-4">mdi-chat-question-outline</v-icon>
        <h3 class="text-h6 text-primary mb-2">AI助手已就绪</h3>
        <p class="text-body-2 text-grey text-center">
          您可以就此文档的内容向AI助手提问<br>
          例如：这篇文档的主要内容是什么？
        </p>
      </div>

      <!-- 消息列表 -->
      <div v-for="(message, index) in messages" :key="index" class="message-group mb-4">
        <!-- 用户消息 -->
        <div v-if="message.role === 'user'" class="d-flex justify-end mb-2">
          <v-card
            class="user-message"
            color="primary"
            variant="flat"
            max-width="80%">
            <v-card-text class="pa-3 text-white">
              <p class="mb-0 text-body-1">{{ message.content }}</p>
            </v-card-text>
          </v-card>
        </div>

        <!-- AI回复 -->
        <div v-if="message.role === 'assistant'" class="d-flex justify-start mb-2">
          <div class="d-flex align-start" style="max-width: 85%;">
            <v-avatar size="32" color="blue-grey-lighten-2" class="me-3 mt-1">
              <v-icon color="white">mdi-robot</v-icon>
            </v-avatar>
            <v-card
              class="assistant-message flex-grow-1"
              color="grey-lighten-5"
              variant="flat">
              <v-card-text class="pa-3">
                <div 
                  v-if="message.isStreaming"
                  class="streaming-content text-body-1">
                  {{ message.content }}
                  <span class="typing-cursor">|</span>
                </div>
                <div v-else class="text-body-1">
                  {{ message.content }}
                </div>
              </v-card-text>
            </v-card>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="d-flex justify-start mb-2">
        <div class="d-flex align-start">
          <v-avatar size="32" color="blue-grey-lighten-2" class="me-3">
            <v-icon color="white">mdi-robot</v-icon>
          </v-avatar>
          <v-card
            color="grey-lighten-5"
            variant="flat"
            class="loading-message">
            <v-card-text class="pa-3 d-flex align-center">
              <v-progress-circular 
                indeterminate 
                size="16" 
                width="2" 
                color="primary"
                class="me-2">
              </v-progress-circular>
              <span class="text-body-2 text-grey">AI正在思考...</span>
            </v-card-text>
          </v-card>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <v-divider></v-divider>
    <div class="chat-input pa-4">
      <v-card variant="outlined" class="input-card">
        <v-card-text class="pa-3">
          <v-textarea
            v-model="currentMessage"
            placeholder="请输入您的问题..."
            variant="plain"
            auto-grow
            rows="1"
            max-rows="4"
            hide-details
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="addNewLine"
            :disabled="loading">
          </v-textarea>
          
          <div class="d-flex justify-between align-center mt-2">
            <div class="text-caption text-grey">
              按Enter发送，Shift+Enter换行
            </div>
            <div class="d-flex ga-2">
              <v-btn
                size="small"
                variant="outlined"
                color="grey"
                @click="clearMessages"
                :disabled="loading || messages.length === 0">
                <v-icon start>mdi-delete-outline</v-icon>
                清空
              </v-btn>
              <v-btn
                size="small"
                color="primary"
                variant="flat"
                @click="sendMessage"
                :disabled="loading || !currentMessage.trim()">
                <v-icon start>mdi-send</v-icon>
                发送
              </v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- 错误提示 -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="5000">
      {{ errorMessage }}
      <template #actions>
        <v-btn variant="text" @click="errorSnackbar = false">关闭</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { documentService } from '@/api/documentService'

// Props
interface Props {
  documentId: string
}

const props = defineProps<Props>()

// 消息接口
interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  isStreaming?: boolean
}

// 响应式数据
const messages = ref<Message[]>([])
const currentMessage = ref('')
const loading = ref(false)
const errorSnackbar = ref(false)
const errorMessage = ref('')
const messagesContainer = ref<HTMLElement>()

// 方法
const sendMessage = async () => {
  const question = currentMessage.value.trim()
  if (!question || loading.value) return

  // 添加用户消息
  const userMessage: Message = {
    role: 'user',
    content: question,
    timestamp: Date.now()
  }
  messages.value.push(userMessage)
  currentMessage.value = ''

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 发送请求
  try {
    loading.value = true
    console.log('发送问答请求，documentId:', props.documentId, 'question:', question)

    // 添加临时的AI消息用于流式显示
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true
    }
    messages.value.push(assistantMessage)

    const response = await documentService.askQuestion(props.documentId, question)
    console.log('问答API响应:', response)

    // 更新AI回复
    const lastMessage = messages.value[messages.value.length - 1]
    if (response.data && response.data.code === 200 && response.data.data) {
      lastMessage.content = response.data.data.answer || '抱歉，我无法回答这个问题。'
    } else {
      lastMessage.content = '抱歉，处理您的问题时出现了错误。'
    }
    lastMessage.isStreaming = false

  } catch (error) {
    console.error('问答请求失败:', error)
    
    // 移除最后一条消息（如果是加载中的消息）
    if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'assistant') {
      messages.value.pop()
    }
    
    // 添加错误消息
    messages.value.push({
      role: 'assistant',
      content: '抱歉，网络连接出现问题，请稍后再试。',
      timestamp: Date.now()
    })
    
    showError('发送消息失败')
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

const addNewLine = () => {
  currentMessage.value += '\n'
}

const clearMessages = () => {
  messages.value = []
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const showError = (message: string) => {
  errorMessage.value = message
  errorSnackbar.value = true
}

// 生命周期
onMounted(() => {
  console.log('DocumentChat组件已挂载，documentId:', props.documentId)
})
</script>

<style scoped>
.document-chat {
  height: 100%;
  background: #fafafa;
}

.chat-messages {
  overflow-y: auto;
  background: linear-gradient(to bottom, #f5f5f5, #fafafa);
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
}

.message-group {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  border-radius: 18px 18px 4px 18px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

.assistant-message {
  border-radius: 18px 18px 18px 4px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.loading-message {
  border-radius: 18px 18px 18px 4px !important;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.streaming-content {
  position: relative;
}

.typing-cursor {
  animation: blink 1s infinite;
  color: #1976d2;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.chat-input {
  background: white;
}

.input-card {
  transition: all 0.2s ease;
}

.input-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1) !important;
}

.input-card:focus-within {
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2) !important;
}
</style> 