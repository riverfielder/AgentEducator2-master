import { ref, computed } from 'vue'
import type { Ref } from 'vue'
import type { Source } from '@/types/chat'

export interface ToolCallInfo {
  tool_name: string
  tool_icon?: string
  tool_color?: string
  description: string
  context?: Record<string, any>
  startTime: Date
}

export interface ToolResultInfo {
  success: boolean
  message: string
  documents_count?: number
  execution_time?: number
  endTime: Date
}

export interface MessageSegment {
  id: string
  type: 'thinking' | 'tool_call' | 'tool_result' | 'content' | 'status'
  timestamp: Date
  content?: string
  toolInfo?: ToolCallInfo
  toolResult?: ToolResultInfo
  status?: string
  isComplete?: boolean
  showDetailed?: boolean
  hideCompletely?: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Source[]
  error?: boolean
  showSources?: boolean
  showToolsHistory?: boolean
  messageSegments?: MessageSegment[]
  isStreaming?: boolean
}

export interface Chat {
  id: string | null
  title: string
  time: string
  messages: ChatMessage[]
  // 累积的引用ID，用于在对话过程中保持所有出现过的引用
  accumulatedVideoIds?: string[]
  accumulatedCourseIds?: string[]
  accumulatedDocumentIds?: string[]
}

export function useChatMessages() {
  const currentChat = ref<Chat>({
    id: null,
    title: '新对话',
    time: new Date().toLocaleString(),
    messages: []
  })

  const activeSegmentId = ref<string | null>(null)

  // 创建内容片段
  const createContentSegment = (content: string): MessageSegment => {
    return {
      id: `content_${Date.now()}`,
      type: 'content',
      timestamp: new Date(),
      content: content,
      isComplete: true
    }
  }

  // 获取按时间排序的消息片段
  const getSortedSegments = (message: ChatMessage) => {
    if (!message.messageSegments) return []
    return [...message.messageSegments].sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )
  }

  // 智能插入内容片段到消息中
  const insertContentSegment = (messageIndex: number, newContent: string) => {
    const message = currentChat.value.messages[messageIndex]
    if (!message || !message.messageSegments) return

    console.log('insertContentSegment called with:', { 
      newContent: newContent.slice(0, 50) + '...', 
      messageIndex 
    })

    // 检查是否有未完成的工具调用
    const hasRunningTool = message.messageSegments.some(
      seg => seg.type === 'tool_call' && !seg.isComplete
    )

    // 如果有正在运行的工具，将内容暂存，等工具完成后再处理
    if (hasRunningTool) {
      console.log('有正在运行的工具，暂存内容')
      message.content = newContent
      return
    }

    // 查找最新的内容片段
    const contentSegments = message.messageSegments.filter(seg => seg.type === 'content')
    const latestContentSegment = contentSegments[contentSegments.length - 1]

    // 计算已经处理过的内容长度
    const processedContentLength = contentSegments.reduce((total, seg) => {
      return total + (seg.content?.length || 0)
    }, 0)

    // 提取新增的内容部分
    const incrementalContent = newContent.slice(processedContentLength)
    
    console.log('增量内容:', { 
      processedContentLength, 
      incrementalContent: incrementalContent.slice(0, 30) + '...',
      contentSegmentsCount: contentSegments.length 
    })
    
    if (!incrementalContent) return // 没有新内容

    // 检查最后一个片段是否是工具调用（需要创建新内容片段）
    const lastSegment = message.messageSegments[message.messageSegments.length - 1]
    const shouldCreateNewSegment = !latestContentSegment || (lastSegment && lastSegment.type === 'tool_call')

    if (latestContentSegment && !shouldCreateNewSegment) {
      // 增量更新最新的内容片段
      console.log('更新现有内容片段')
      latestContentSegment.content = (latestContentSegment.content || '') + incrementalContent
      latestContentSegment.timestamp = new Date()
    } else {
      // 创建新的内容片段
      console.log('创建新内容片段')
      const contentSegment = createContentSegment(incrementalContent)
      message.messageSegments.push(contentSegment)
    }

    // 清空消息的content，避免重复显示
    message.content = ''
  }

  // 切换引用来源的显示状态
  const toggleSourcesVisibility = (message: ChatMessage) => {
    message.showSources = !message.showSources
  }

  // 切换工具执行历史的显示状态
  const toggleToolsHistoryVisibility = (message: ChatMessage) => {
    message.showToolsHistory = !message.showToolsHistory
  }

  // 添加用户消息
  const addUserMessage = (content: string) => {
    currentChat.value.messages.push({
      role: 'user',
      content,
      timestamp: new Date()
    })
  }

  // 添加AI消息
  const addAIMessage = () => {
    const newAIMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      messageSegments: [],
      isStreaming: true
    }
    currentChat.value.messages.push(newAIMessage)
    return currentChat.value.messages.length - 1
  }

  // 更新累积的引用ID
  const updateAccumulatedIds = (sources: Source[]) => {
    if (!sources || sources.length === 0) return

    // 初始化累积ID数组（如果不存在）
    if (!currentChat.value.accumulatedVideoIds) {
      currentChat.value.accumulatedVideoIds = []
    }
    if (!currentChat.value.accumulatedCourseIds) {
      currentChat.value.accumulatedCourseIds = []
    }
    if (!currentChat.value.accumulatedDocumentIds) {
      currentChat.value.accumulatedDocumentIds = []
    }

    // 使用Set来避免重复
    const videoIds = new Set(currentChat.value.accumulatedVideoIds)
    const courseIds = new Set(currentChat.value.accumulatedCourseIds)
    const documentIds = new Set(currentChat.value.accumulatedDocumentIds)

    // 添加新的引用ID
    sources.forEach((source: Source) => {
      if (source.video_id) {
        videoIds.add(source.video_id)
      }
      if (source.course_id) {
        courseIds.add(source.course_id)
      }
      if (source.document_id) {
        documentIds.add(source.document_id)
      }
    })

    // 更新累积ID数组
    currentChat.value.accumulatedVideoIds = Array.from(videoIds)
    currentChat.value.accumulatedCourseIds = Array.from(courseIds)
    currentChat.value.accumulatedDocumentIds = Array.from(documentIds)
  }

  // 获取累积的引用ID
  const getAccumulatedIds = () => {
    return {
      videoIds: currentChat.value.accumulatedVideoIds || [],
      courseIds: currentChat.value.accumulatedCourseIds || [],
      documentIds: currentChat.value.accumulatedDocumentIds || []
    }
  }

  // 重置聊天
  const resetChat = () => {
    currentChat.value = {
      id: null,
      title: '新对话',
      time: new Date().toLocaleString(),
      messages: [],
      accumulatedVideoIds: [],
      accumulatedCourseIds: [],
      accumulatedDocumentIds: []
    }
  }

  return {
    currentChat,
    activeSegmentId,
    createContentSegment,
    getSortedSegments,
    insertContentSegment,
    toggleSourcesVisibility,
    toggleToolsHistoryVisibility,
    addUserMessage,
    addAIMessage,
    resetChat,
    updateAccumulatedIds,
    getAccumulatedIds
  }
}
