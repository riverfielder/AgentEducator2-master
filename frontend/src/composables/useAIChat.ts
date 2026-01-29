import { ref, onMounted, watch, onBeforeUnmount, nextTick } from 'vue'
import { useChatMessages } from './useChatMessages'
import { useToolEvents } from './useToolEvents'
import { useStatusEvents } from './useStatusEvents'
import { useChatHistory } from './useChatHistory'
import { useVoiceInput } from './useVoiceInput'
import { useAgentConfig } from './useAgentConfig'
import { useMessageSending } from './useMessageSending'
import { useCitationHandler } from './useCitationHandler'
import chatHistoryService from '../api/chatHistoryService'

export function useAIChat(props: any, emit: any) {
  // 基础状态
  const userInput = ref('')
  const chatHistory = ref<HTMLElement | null>(null)
  const inputField = ref<HTMLTextAreaElement | null>(null)
  const sessionId = ref<string | null>(null)

  // 使用各个功能模块
  const {
    currentChat,
    activeSegmentId,
    getSortedSegments,
    insertContentSegment,
    toggleSourcesVisibility,
    toggleToolsHistoryVisibility,
    addUserMessage,
    addAIMessage,
    resetChat,
    updateAccumulatedIds,
    getAccumulatedIds
  } = useChatMessages()

  // 滚动到底部功能
  const scrollToBottom = () => {
    nextTick(() => {
      if (chatHistory.value) {
        chatHistory.value.scrollTop = chatHistory.value.scrollHeight
      }
    })
  }

  const {
    currentToolInfo,
    toolExecutionHistory,
    handleToolEvent,
    getToolStatusColor,
    getToolStatusIcon,
    getToolStatusText,
    formatContextInfo
  } = useToolEvents(currentChat, insertContentSegment, scrollToBottom)

  const {
    currentStatus,
    statusStats,
    showStatus,
    handleStatusEvent,
    resetStatus
  } = useStatusEvents(currentChat)

  const {
    chatHistoryList,
    historyLoading,
    showHistoryDrawer,
    showEditDialog,
    editTitle,
    editingChatId,
    loadChatHistory,
    loadHistoryChat: _loadHistoryChat,
    deleteHistoryChat,
    editSessionTitle,
    updateSessionTitle,
    formatDate
  } = useChatHistory(currentChat, sessionId)

  // 包装 loadHistoryChat 以添加滚动功能
  const loadHistoryChat = async (chat: any) => {
    await _loadHistoryChat(chat)
    scrollToBottom()
  }

  const {
    isRecording,
    toggleVoiceInput,
    initVoiceRecognition
  } = useVoiceInput(userInput)

  const {
    agentConfig,
    editableAgentConfig,
    showAgentSettings,
    loadAgentConfig,
    saveAgentConfig,
    resetAgentConfigEdit,
    getToolDisplayName
  } = useAgentConfig()

  // 创建新的聊天会话
  const createNewChatSession = async (userMessage: string, videoId?: string, courseId?: string, documentId?: string): Promise<string | null> => {
    try {
      const response = await chatHistoryService.createChatSession({
        title: userMessage.slice(0, 50) + (userMessage.length > 50 ? '...' : ''),
        videoId,
        courseId,
        documentId
      })
      return response.data.session_id
    } catch (error) {
      console.error('创建聊天会话失败:', error)
      return null
    }
  }

  const {
    isTyping,
    sendMessage: _sendMessage,
    processMessageContent
  } = useMessageSending(
    currentChat,
    sessionId,
    insertContentSegment,
    handleToolEvent,
    handleStatusEvent,
    scrollToBottom,
    addAIMessage,
    createNewChatSession,
    updateAccumulatedIds,
    getAccumulatedIds
  )

  const {
    handleCitationClick,
    jumpToTimepoint
  } = useCitationHandler(
    currentChat,
    (videoId: string, seconds: number) => {
      emit('jump-to-video-timepoint', videoId, seconds)
    },
    (documentId: string, segmentNumber: number) => {
      emit('jump-to-document-segment', documentId, segmentNumber)
    }
  )

  const createNewChat = async () => {
    resetChat()
    sessionId.value = null
    userInput.value = ''

    if (inputField.value) {
      inputField.value.focus()
    }
  }

  // 发送消息的包装函数
  const sendMessage = async () => {
    const userMessage = userInput.value.trim()
    if (!userMessage) return

    // 添加用户消息
    addUserMessage(userMessage)
    userInput.value = ''

    // 发送消息
    await _sendMessage(
      userMessage,
      () => loadChatHistory(props.videoId, props.courseId, props.documentId),
      props.videoId,
      props.courseId,
      props.documentId,

    )
  }

  // 格式化时间显示
  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // 生命周期钩子
  onMounted(() => {
    loadChatHistory(props.videoId, props.courseId, props.documentId)
    loadAgentConfig()
    initVoiceRecognition()

    // 监听auto-chat事件
    document.querySelector('.ai-chat-container')?.addEventListener('auto-chat', ((event: CustomEvent) => {
      const { prompt } = event.detail
      if (prompt) {
        userInput.value = prompt
        nextTick(() => {
          sendMessage()
        })
      }
    }) as EventListener)
  })

  // 观察消息变化，自动滚动到底部
  watch(() => currentChat.value.messages, () => {
    nextTick(() => {
      scrollToBottom()
    })
  })

  // 监听自动提示词变化
  watch(() => props.autoPrompt, (newPrompt) => {
    if (newPrompt) {
      userInput.value = newPrompt
      nextTick(() => {
        sendMessage()
      })
      emit('update:autoPrompt', '')
    }
  }, { immediate: true })

  // 组件卸载前清理
  onBeforeUnmount(() => {
    document.querySelector('.ai-chat-container')?.removeEventListener('auto-chat', (() => { }) as EventListener)
  })

  return {
    // 基础状态
    userInput,
    chatHistory,
    inputField,
    sessionId,
    isTyping,
    isRecording,

    // 聊天相关
    currentChat,
    createNewChat,
    sendMessage,

    // 消息处理
    getSortedSegments,
    processMessageContent,
    handleCitationClick,
    toggleSourcesVisibility,
    toggleToolsHistoryVisibility,
    formatTime,

    // 工具相关
    currentToolInfo,
    toolExecutionHistory,
    getToolStatusColor,
    getToolStatusIcon,
    getToolStatusText,
    formatContextInfo,

    // 状态相关
    currentStatus,
    statusStats,
    showStatus,

    // 历史记录
    chatHistoryList,
    historyLoading,
    showHistoryDrawer,
    showEditDialog,
    editTitle,
    editingChatId,
    loadHistoryChat,
    deleteHistoryChat,
    editSessionTitle,
    updateSessionTitle,
    formatDate,

    // 语音输入
    toggleVoiceInput,

    // Agent配置
    agentConfig,
    editableAgentConfig,
    showAgentSettings,
    saveAgentConfig,
    resetAgentConfigEdit,
    getToolDisplayName,

    // 跳转功能
    jumpToTimepoint: (seconds: number) => jumpToTimepoint(seconds, emit),
    jumpToVideoTimepoint: (videoId: string, seconds: number) => emit('jump-to-video-timepoint', videoId, seconds),
    jumpToDocument: (source: any) => {
      if (source.course_id) {
        window.open(`/course/${source.course_id}/document/${source.document_id}`, '_blank')
      } else {
        window.open(`/document/${source.document_id}`, '_blank')
      }
    }
  }
}
