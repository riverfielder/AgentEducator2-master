import { ref, nextTick } from 'vue'
import type { Ref } from 'vue'
import type { MessageSegment, ChatMessage } from './useChatMessages'

export function useToolEvents(
  currentChat: Ref<{ messages: ChatMessage[] }>,
  insertContentSegment: (messageIndex: number, newContent: string) => void,
  scrollToBottom: () => void
) {
  const currentToolInfo = ref<any>(null)
  const toolExecutionHistory = ref<any[]>([])

  // 处理工具事件 - 优化为支持线性穿插显示
  const handleToolEvent = (toolEventData: any) => {
    console.log('收到工具事件:', toolEventData)

    // 获取当前正在流式接收的AI消息
    const currentAIMessageIndex = currentChat.value.messages.findIndex(
      msg => msg.role === 'assistant' && msg.isStreaming
    )

    if (currentAIMessageIndex === -1) return

    const currentMessage = currentChat.value.messages[currentAIMessageIndex]

    // 确保消息片段数组存在
    if (!currentMessage.messageSegments) {
      currentMessage.messageSegments = []
    }

    if (toolEventData.type === 'tool_start') {
      // 在工具开始时，如果有内容则先创建内容片段
      if (currentMessage.content && currentMessage.content.trim()) {
        // 计算已经处理过的内容长度
        const contentSegments = currentMessage.messageSegments.filter(seg => seg.type === 'content')
        const processedContentLength = contentSegments.reduce((total, seg) => {
          return total + (seg.content?.length || 0)
        }, 0)

        // 提取新增的内容部分
        const incrementalContent = currentMessage.content.slice(processedContentLength)
        
        if (incrementalContent && incrementalContent.trim()) {
          const currentContentSegment = createContentSegment(incrementalContent)
          currentMessage.messageSegments.push(currentContentSegment)
        }
        
        // 清空消息内容，后续内容将作为新片段处理
        currentMessage.content = ''
      }

      // 创建工具调用片段，插入到正确的时间线位置
      const toolSegment: MessageSegment = {
        id: `tool_${Date.now()}`,
        type: 'tool_call',
        timestamp: new Date(),
        toolInfo: {
          tool_name: toolEventData.data.tool_name,
          tool_icon: toolEventData.data.tool_icon,
          tool_color: toolEventData.data.tool_color,
          description: toolEventData.data.description,
          context: toolEventData.data.context,
          startTime: new Date()
        },
        isComplete: false,
        showDetailed: true // 执行时显示详细信息
      }

      // 将工具片段插入到当前时间线的正确位置
      currentMessage.messageSegments.push(toolSegment)

      // 滚动到底部以显示新的工具调用
      nextTick(() => {
        scrollToBottom()
      })
    } else if (toolEventData.type === 'tool_result') {
      console.log('工具调用完成，处理结果')
      // 查找最近的未完成工具调用片段
      const toolCallSegment = [...currentMessage.messageSegments]
        .reverse()
        .find(segment => segment.type === 'tool_call' && !segment.isComplete)

      if (toolCallSegment && toolCallSegment.toolInfo) {
        // 标记工具调用完成
        toolCallSegment.isComplete = true
        toolCallSegment.toolResult = {
          success: toolEventData.data.success,
          message: toolEventData.data.message,
          documents_count: toolEventData.data.documents_count,
          execution_time: new Date().getTime() - toolCallSegment.toolInfo.startTime.getTime(),
          endTime: new Date()
        }

        // 工具完成后，处理暂存的内容（如果有）
        if (currentMessage.content && currentMessage.content.trim()) {
          console.log('工具完成后处理暂存内容:', currentMessage.content.slice(0, 50) + '...')
          
          // 计算已经处理过的内容长度
          const contentSegments = currentMessage.messageSegments.filter(seg => seg.type === 'content')
          const processedContentLength = contentSegments.reduce((total, seg) => {
            return total + (seg.content?.length || 0)
          }, 0)

          // 提取新增的内容部分
          const incrementalContent = currentMessage.content.slice(processedContentLength)
          
          if (incrementalContent && incrementalContent.trim()) {
            console.log('创建工具完成后的新内容片段:', incrementalContent.slice(0, 30) + '...')
            // 创建新的内容片段
            const newContentSegment = createContentSegment(incrementalContent)
            currentMessage.messageSegments.push(newContentSegment)
          }
          
          // 清空暂存内容
          currentMessage.content = ''
        }

        // 工具完成后，等待2秒后自动折叠
        setTimeout(() => {
          if (toolCallSegment && toolCallSegment.showDetailed !== false) {
            toolCallSegment.showDetailed = false
          }
        }, 2000)
      }
    }
  }

  // 创建内容片段辅助函数
  const createContentSegment = (content: string): MessageSegment => {
    return {
      id: `content_${Date.now()}`,
      type: 'content',
      timestamp: new Date(),
      content: content,
      isComplete: true
    }
  }

  // 工具状态相关辅助函数
  const getToolStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'primary'
      case 'success': return 'success'
      case 'error': return 'error'
      default: return 'grey'
    }
  }

  const getToolStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return 'mdi-loading'
      case 'success': return 'mdi-check-circle'
      case 'error': return 'mdi-alert-circle'
      default: return 'mdi-circle'
    }
  }

  const getToolStatusText = (status: string) => {
    switch (status) {
      case 'running': return '执行中'
      case 'success': return '完成'
      case 'error': return '失败'
      default: return '准备'
    }
  }

  const formatContextInfo = (key: string, value: any) => {
    if (typeof value === 'boolean') {
      return value ? `✓ ${key}` : `✗ ${key}`
    }
    if (typeof value === 'number') {
      return `${key}: ${value}`
    }
    return `${key}: ${value}`
  }

  return {
    currentToolInfo,
    toolExecutionHistory,
    handleToolEvent,
    getToolStatusColor,
    getToolStatusIcon,
    getToolStatusText,
    formatContextInfo
  }
}
