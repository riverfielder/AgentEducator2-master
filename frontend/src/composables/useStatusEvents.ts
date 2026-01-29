import { ref } from 'vue'
import type { Ref } from 'vue'
import type { ChatMessage, MessageSegment } from './useChatMessages'

export function useStatusEvents(currentChat: Ref<{ messages: ChatMessage[] }>) {
  const currentStatus = ref<string>('')
  const statusStats = ref<any>(null)
  const showStatus = ref(false)

  // 处理状态事件 - 增强以支持推理步骤显示
  const handleStatusEvent = (statusData: any) => {
    // 更新当前状态显示
    currentStatus.value = statusData.message || ''

    // 如果有统计信息则更新
    if (statusData.stats) {
      statusStats.value = statusData.stats
    }

    // 确保状态显示在AI思考中
    showStatus.value = true

    // 处理Agent推理步骤状态（支持developer和debug模式的状态显示）
    if (statusData.type === 'status_update' && statusData.data) {
      const statusInfo = statusData.data

      // 获取当前正在流式接收的AI消息
      const currentAIMessageIndex = currentChat.value.messages.findIndex(
        msg => msg.role === 'assistant' && msg.isStreaming
      )

      if (currentAIMessageIndex !== -1) {
        const currentMessage = currentChat.value.messages[currentAIMessageIndex]

        // 确保消息片段数组存在
        if (!currentMessage.messageSegments) {
          currentMessage.messageSegments = []
        }
        
        // 如果是推理步骤状态，创建状态片段
        if (statusInfo.step && statusInfo.step > 0) {
          const statusSegment: MessageSegment = {
            id: `status_${Date.now()}`,
            type: 'status',
            timestamp: new Date(),
            status: statusInfo.message,
            isComplete: true
          }

          currentMessage.messageSegments.push(statusSegment)
        }
      }
    }

    // 根据不同阶段执行不同操作
    switch (statusData.stage) {
      case 'retrieval_start':
        // 开始检索时，显示状态
        break

      case 'retrieval_complete':
        // 检索完成，显示文档数量
        break

      case 'question_analysis':
        // 问题分析阶段
        break

      case 'generation_start':
        // 生成开始阶段，立即隐藏状态栏外层显示
        // 但在AI思考中的状态仍然保留
        setTimeout(() => {
          showStatus.value = false
          currentStatus.value = ''
          statusStats.value = null
        }, 1000)
        break

      case 'analysis_start':
        // 通用模式分析开始
        break
    }
  }

  // 重置状态
  const resetStatus = () => {
    showStatus.value = false
    currentStatus.value = ''
    statusStats.value = null
  }

  return {
    currentStatus,
    statusStats,
    showStatus,
    handleStatusEvent,
    resetStatus
  }
}
