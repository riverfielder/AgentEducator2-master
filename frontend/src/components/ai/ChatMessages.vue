<template>
  <div class="chat-messages" ref="messagesContainer">
    <div v-if="currentChat" v-for="(message, index) in currentChat.messages" :key="message.id" 
         :class="['message-wrapper', message.role]">
      <div class="message-content">
        <!-- AI消息的头像 -->
        <div class="message-avatar" v-if="message.role === 'assistant' && !(isTyping && index === currentChat.messages.length - 1 && !message.content.trim())">
          <v-avatar color="primary" size="40">
            <v-icon dark>mdi-robot</v-icon>
          </v-avatar>
        </div>
          <!-- 消息气泡 -->
        <div class="message-bubble" v-if="message.role === 'assistant'">
          <!-- 工具消息片段显示 -->
          <div v-if="message.messageSegments && message.messageSegments.length > 0" class="message-segments">
            <!-- 按时间顺序排列所有片段 -->
            <template v-for="(segment, segIndex) in getSortedSegments(message)" :key="segment.id">
              <!-- 工具调用片段 -->
              <div v-if="segment.type === 'tool_call' && !segment.hideCompletely" class="tool-call-segment mb-2">
                <!-- 成功完成后的简洁显示 -->
                <div v-if="segment.isComplete && !segment.showDetailed" class="tool-call-compact">
                  <v-fade-transition>
                    <div class="d-flex align-center px-3 py-2 tool-success-banner"
                      @click="segment.showDetailed = true">
                      <v-avatar size="20" :color="segment.toolInfo?.tool_color || 'primary'" class="me-2"
                        variant="flat">
                        <v-icon :icon="segment.toolInfo?.tool_icon || 'mdi-tools'" size="12" color="white" />
                      </v-avatar>
                      <span class="text-body-2 me-1">{{ segment.toolInfo?.tool_name }}</span>
                      <v-icon icon="mdi-check-circle" color="success" size="16" class="mr-1" />

                      <!-- 简洁模式下的文档数量显示 -->
                      <v-chip v-if="segment.toolResult?.documents_count" color="info" size="x-small"
                        variant="outlined" class="ml-2">
                        <v-icon start size="x-small">mdi-file-document</v-icon>
                        {{ segment.toolResult.documents_count }}
                      </v-chip>
                    </div>
                  </v-fade-transition>
                </div>
                
                <!-- 执行中或详细显示 -->
                <div v-else class="tool-call-detailed">
                  <div class="d-flex align-center mb-2">
                    <v-avatar :color="segment.toolInfo?.tool_color || 'primary'" size="22" class="me-3"
                      variant="flat">
                      <v-icon :icon="segment.toolInfo?.tool_icon || 'mdi-tools'" size="14" color="white" />
                    </v-avatar>
                    <span class="text-subtitle-2 font-weight-medium">{{ segment.toolInfo?.tool_name }}</span>
                    <v-spacer />

                    <!-- 折叠按钮（仅在完成状态显示） -->
                    <v-btn v-if="segment.isComplete" icon="mdi-chevron-up" size="x-small" variant="text"
                      @click="segment.showDetailed = false" class="me-1" />

                    <v-chip :color="segment.isComplete ? 'success' : 'primary'" variant="flat" size="small"
                      class="ms-1">
                      <v-icon :icon="segment.isComplete ? 'mdi-check' : 'mdi-loading mdi-spin'" start
                        size="x-small" />
                      {{ segment.isComplete ? '已完成' : '执行中' }}
                    </v-chip>
                  </div>

                  <div class="text-caption text-medium-emphasis mb-2">
                    {{ segment.toolInfo?.description }}
                  </div>

                  <!-- 工具上下文信息 -->
                  <div v-if="segment.toolInfo?.context" class="tool-context-chips mb-2">
                    <v-chip v-for="(value, key) in segment.toolInfo.context" :key="String(key)" size="x-small"
                      variant="outlined" color="grey" class="me-1 mb-1">
                      {{ formatContextInfo(String(key), value) }}
                    </v-chip>
                  </div>
                  
                  <!-- 执行进度 -->
                  <v-progress-linear v-if="!segment.isComplete" indeterminate
                    :color="segment.toolInfo?.tool_color || 'primary'" height="2" class="mt-1" />

                  <!-- 执行结果（仅在完成时显示） -->
                  <div v-if="segment.isComplete && segment.toolResult" class="tool-result-info mt-2">
                    <div class="d-flex align-center text-caption text-medium-emphasis">
                      <v-icon :icon="segment.toolResult.success ? 'mdi-check-circle' : 'mdi-alert-circle'"
                        :color="segment.toolResult.success ? 'success' : 'error'" size="12" class="me-1" />
                      <span>{{ segment.toolResult.message }}</span>
                      <v-spacer />
                      <span v-if="segment.toolResult.execution_time">
                        {{ Math.round(segment.toolResult.execution_time) }}ms
                      </span>
                    </div>

                    <div v-if="segment.toolResult.documents_count" class="text-caption text-medium-emphasis mt-1">
                      找到 {{ segment.toolResult.documents_count }} 个相关文档
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 工具结果片段 - 只显示失败情况 -->
              <div v-if="segment.type === 'tool_result' && !segment.toolResult?.success"
                class="tool-result-segment mb-3">
                <div class="tool-result-error">
                  <div class="d-flex align-center mb-2">
                    <v-icon icon="mdi-alert-circle" color="error" size="16" class="me-2" />
                    <span class="text-caption font-weight-medium text-error">
                      执行失败
                    </span>
                    <v-spacer />
                    <span v-if="segment.toolResult?.execution_time" class="text-caption text-medium-emphasis">
                      {{ Math.round(segment.toolResult.execution_time) }}ms
                    </span>
                  </div>

                  <div class="text-caption mb-1 text-error">
                    {{ segment.toolResult?.message }}
                  </div>
                </div>
              </div>

              <!-- 内容片段 -->
              <div v-else-if="segment.type === 'content'" class="content-segment mb-2">
                <div class="text-body-2 markdown-body" v-html="processMessageContent(segment.content || '')"
                  @click="handleCitationClick"
                  @mouseover="handleCitationHover"
                  @mouseleave="handleCitationLeave">
                </div>
              </div>
            </template>
          </div>
          
          <!-- 普通消息内容（当没有片段时显示） -->
          <div v-else-if="message.content.trim()" class="message-text markdown-body" 
               v-html="processMessageContent(message.content)" 
               @click="handleCitationClick"
               @mouseover="handleCitationHover"
               @mouseleave="handleCitationLeave">
          </div>
          
          <div class="message-time">{{ message.time }}</div>
          
          <!-- 引用来源 -->
          <div v-if="message.sources && message.sources.length > 0" class="message-sources">
            <div class="message-sources-toggle" @click="toggleSourcesVisibility(message)">
              引用来源 ({{ message.sources.length }})
              <v-icon small>{{ message.showSources ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
            </div>
            <div v-if="message.showSources" class="message-sources-list">
              <div v-for="source in message.sources" :key="source.index" class="source-item">
                <div class="source-index">[{{ source.index }}]</div>
                <div class="source-content">
                  <div class="source-title">
                    <template v-if="source.document_id">
                      {{ source.document_title || '未知文档' }}
                    </template>
                    <template v-else>
                      {{ source.video_title || '未知视频' }}
                    </template>
                  </div>
                  <div class="source-time" v-if="source.video_id">
                    时间点: {{ source.time_formatted }}
                  </div>
                  <div class="source-info" v-else-if="source.document_id">
                    <template v-if="source.page_number">第{{ source.page_number }}页</template>
                    <template v-else-if="source.segment_number">第{{ source.segment_number }}段</template>
                    <template v-else>文档片段</template>
                  </div>
                  <div class="source-preview">{{ source.content }}</div>
                  <v-btn 
                    x-small 
                    color="primary" 
                    text
                    @click="navigateToSource(source)"
                  >
                    <v-icon x-small left>{{ source.document_id ? 'mdi-file-document' : 'mdi-play' }}</v-icon>
                    {{ source.document_id ? '查看文档' : '跳转到视频' }}
                  </v-btn>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 用户消息气泡 -->
        <div v-else-if="message.role === 'user'" class="message-bubble">
          <div class="message-text markdown-body" v-html="processMessageContent(message.content)" 
               @click="handleCitationClick"
               @mouseover="handleCitationHover"
               @mouseleave="handleCitationLeave"></div>
          <div class="message-time">{{ message.time }}</div>
        </div>
        
        <!-- 用户消息的头像 -->
        <div class="message-avatar" v-if="message.role === 'user'">
          <v-avatar color="grey" size="40">
            <v-icon dark>mdi-account</v-icon>
          </v-avatar>
        </div>
      </div>
    </div>
    
    <!-- 正在输入指示器 -->
    <div v-if="isTyping && (!currentChat?.messages.length || currentChat.messages[currentChat.messages.length - 1].role === 'user')" class="message-wrapper assistant">
      <div class="message-content">
        <div class="message-avatar">
          <v-avatar color="primary" size="40">
            <v-icon dark>mdi-robot</v-icon>
          </v-avatar>
        </div>
        <div class="message-bubble typing">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="!currentChat || currentChat.messages.length === 0" class="empty-chat">
      <div class="empty-icon">
        <v-icon size="64" color="grey">mdi-robot-outline</v-icon>
      </div>
      <div class="empty-text">开始与AI助手对话吧！</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { processContent } from '../../utils/markdownRenderer'
import type { Chat, Message, MessageSegment, Source } from '../../types/chat'
import { useCitationHandler } from '../../composables/useCitationHandler'

interface Props {
  currentChat: Chat | null
  isTyping: boolean
}

const props = defineProps<Props>()

const messagesContainer = ref<HTMLElement | null>(null)

// 获取按时间排序的消息片段
const getSortedSegments = (message: Message) => {
  if (!message.messageSegments) return []
  return [...message.messageSegments].sort((a, b) =>
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )
}

// 格式化上下文信息
const formatContextInfo = (key: string, value: any) => {
  if (key === 'video_id') return `视频: ${value}`
  if (key === 'course_id') return `课程: ${value}`
  if (key === 'query') return `查询: ${value}`
  if (key === 'document_count') return `文档: ${value}`
  return `${key}: ${value}`
}

// 切换源文档显示状态
const toggleSourcesVisibility = (message: Message) => {
  message.showSources = !message.showSources
}

// 导航到引用源（视频或文档）
const navigateToSource = (source: Source) => {
  const courseId = source.course_id
  
  // 根据引用类型决定跳转路径
  if (source.video_id) {
    // 视频引用
    if (courseId) {
      window.open(`/course/${courseId}/video/${source.video_id}?t=${source.time_point}`, '_blank')
    } else {
      // 如果没有courseId，使用旧的单级格式作为后备
      window.open(`/video/${source.video_id}?t=${source.time_point}`, '_blank')
    }
  } else if (source.document_id) {
    // 文档引用
    if (courseId) {
      window.open(`/course/${courseId}/document/${source.document_id}`, '_blank')
    } else {
      // 如果没有courseId，使用旧的单级格式作为后备
      window.open(`/document/${source.document_id}`, '_blank')
    }
  } else {
    console.warn('未知的引用类型:', source)
  }
}

// 视频跳转函数
const jumpToVideoTimepoint = (videoId: string, seconds: number) => {
  window.open(`/video/${videoId}?t=${seconds}`, '_blank')
}

// 文档跳转函数
const jumpToDocumentSegment = (documentId: string, segmentNumber: number) => {
  // 查找对应的引用源并跳转
  if (props.currentChat?.messages) {
    for (const message of props.currentChat.messages) {
      if (message.sources) {
        const source = message.sources.find(s => s.document_id === documentId)
        if (source) {
          navigateToSource(source)
          return
        }
      }
    }
  }
  // 后备方案：直接打开文档链接
  window.open(`/document/${documentId}?segment=${segmentNumber}`, '_blank')
}

// 使用引用处理器
const { 
  handleCitationClick: citationClickHandler,
  handleCitationHover: citationHoverHandler,
  handleCitationLeave: citationLeaveHandler
} = useCitationHandler(
  computed(() => props.currentChat as any || { messages: [] }),
  jumpToVideoTimepoint, // 视频跳转函数
  jumpToDocumentSegment, // 文档跳转函数
  navigateToSource // 直接传入navigateToSource方法
)

// 处理引用标记点击事件
const handleCitationClick = (event: MouseEvent) => {
  citationClickHandler(event)
}

// 处理引用标记悬停事件
const handleCitationHover = (event: MouseEvent) => {
  citationHoverHandler(event)
}

// 处理引用标记鼠标离开事件
const handleCitationLeave = (event: MouseEvent) => {
  citationLeaveHandler(event)
}

// 处理消息渲染
const processMessageContent = (content: string): string => {
  if (!content) return ''
  return processContent(content)
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 暴露给父组件的方法
defineExpose({
  scrollToBottom
})
</script>

<style scoped>
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  height: 100%;
  min-height: 0;
}

.message-wrapper {
  margin-bottom: 20px;
}

.message-wrapper.user {
  display: flex;
  justify-content: flex-end;
}

.message-content {
  display: flex;
  align-items: flex-start;
  max-width: 80%;
}

.message-avatar {
  margin: 0 12px;
}

.message-bubble {
  background-color: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.user .message-bubble {
  background-color: #6f23d1;
  color: white;
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
}

.message-time {
  font-size: 12px;
  color: #95a5a6;
  margin-top: 4px;
}

.user .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.typing {
  display: flex;
  align-items: center;
  padding: 12px 16px;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #95a5a6;
  border-radius: 50%;
  margin: 0 2px;
  animation: typing 1.4s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #95a5a6;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
}

/* 引用来源样式 */
.message-sources {
  margin-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  padding-top: 8px;
}

.message-sources-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #95a5a6;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
}

.message-sources-toggle:hover {
  color: #2980b9;
}

.message-sources-list {
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
  border-left: 2px solid #f0f0f0;
}

.source-item {
  display: flex;
  margin-bottom: 8px;
  padding: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
}

.source-index {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  background-color: #f1f1f1;
  border-radius: 50%;
  font-size: 12px;
  color: #2c3e50;
  font-weight: 500;
  margin-right: 12px;
}

.source-content {
  flex: 1;
}

.source-title {
  font-weight: 500;
  margin-bottom: 4px;
  font-size: 14px;
}

.source-time {
  font-size: 12px;
  color: #2980b9;
  margin-bottom: 4px;
}

.source-preview {
  font-size: 13px;
  color: #7f8c8d;
  background-color: rgba(0, 0, 0, 0.03);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  max-height: 100px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 引用标记样式 */
:deep(.citation-ref) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75em;
  vertical-align: super;
  color: #3498db;
  font-weight: 500;
  margin: 0 1px;
  transition: all 0.2s ease;
  text-decoration: none;
  padding: 1px 3px;
  border-radius: 4px;
  border: 1px solid transparent;
  position: relative;
}

:deep(.citation-ref:hover) {
  background-color: rgba(52, 152, 219, 0.15);
  color: #2980b9;
  border-color: rgba(52, 152, 219, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(52, 152, 219, 0.2);
}

:deep(.citation-ref:active) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(52, 152, 219, 0.2);
}

/* Markdown样式 */
:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
}

:deep(.markdown-body p) {
  margin: 0.5em 0;
  line-height: 1.6;
  white-space: pre-wrap;
}

:deep(.markdown-body br) {
  margin-bottom: 0.5em;
  display: block;
  content: "";
}

:deep(.markdown-body h1) {
  font-size: 1.5em;
  margin: 0.8em 0 0.5em;
  font-weight: 600;
}

:deep(.markdown-body h2) {
  font-size: 1.3em;
  margin: 0.8em 0 0.5em;
  font-weight: 600;
}

:deep(.markdown-body h3) {
  font-size: 1.2em;
  margin: 0.6em 0 0.4em;
  font-weight: 600;
}

:deep(.markdown-body ul, .markdown-body ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

:deep(.markdown-body li) {
  margin: 0.2em 0;
  line-height: 1.5;
}

:deep(.markdown-body code) {
  font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
  padding: 0.1em 0.3em;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
  font-size: 0.9em;
}

:deep(.markdown-body pre) {
  background-color: rgba(0, 0, 0, 0.04);
  border-radius: 4px;
  padding: 0.8em;
  overflow-x: auto;
  margin: 0.5em 0;
}

:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
  display: block;
  font-size: 0.85em;
}

:deep(.markdown-body blockquote) {
  border-left: 3px solid #ddd;
  margin: 0.5em 0;
  padding: 0 0.5em;
  color: #555;
  font-style: italic;
}

:deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
}

:deep(.markdown-body th, .markdown-body td) {
  border: 1px solid #ddd;
  padding: 6px 10px;
  text-align: left;
}

:deep(.markdown-body th) {
  background-color: rgba(0, 0, 0, 0.04);
  font-weight: 600;
}
</style>
