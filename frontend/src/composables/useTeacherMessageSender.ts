import { ref } from 'vue';
import type { Chat, Reference, ToolCallInfo } from '../types/chat';
// 临时注释，避免编译错误
// import teacherAssistantService from '../api/teacherAssistantService'

export function useTeacherMessageSender(
  updateAccumulatedIds: (sources: any[]) => void,
  getAccumulatedIds: () => { videoIds: string[]; courseIds: string[]; documentIds: string[] }
) {
  // 状态管理
  const isTyping = ref(false)
  const currentStatus = ref('')
  const statusStats = ref({})
  const showStatus = ref(false)
  const currentToolInfo = ref<ToolCallInfo | null>(null)

  // 处理工具事件（复用学生端逻辑）
  const handleToolEvent = (toolEventData: any, currentChat: Chat, aiMessageIndex: number) => {
    const currentMessage = currentChat.messages[aiMessageIndex]
    if (!currentMessage) return

    if (!currentMessage.messageSegments) {
      currentMessage.messageSegments = []
    }

    if (toolEventData.type === 'tool_start') {
      currentToolInfo.value = {
        tool_name: toolEventData.data.tool_name,
        tool_icon: toolEventData.data.tool_icon,
        tool_color: toolEventData.data.tool_color,
        description: toolEventData.data.description,
        context: toolEventData.data.context,
        startTime: new Date()
      }

      const toolSegment = {
        id: `tool_${Date.now()}`,
        type: 'tool_call' as const,
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
        showDetailed: true
      }

      currentMessage.messageSegments.push(toolSegment)
    } else if (toolEventData.type === 'tool_result') {
      currentToolInfo.value = null

      const toolCallSegment = [...currentMessage.messageSegments]
        .reverse()
        .find(segment => segment.type === 'tool_call' && !segment.isComplete)

      if (toolCallSegment && toolCallSegment.toolInfo) {
        toolCallSegment.isComplete = true
        toolCallSegment.toolResult = {
          success: toolEventData.data.success,
          message: toolEventData.data.message,
          documents_count: toolEventData.data.documents_count,
          execution_time: new Date().getTime() - toolCallSegment.toolInfo.startTime.getTime(),
          endTime: new Date()
        }

        setTimeout(() => {
          if (toolCallSegment.showDetailed !== false) {
            toolCallSegment.showDetailed = false
          }
        }, 2000)
      }
    }
  }

  // 插入内容片段（复用学生端逻辑）
  const insertContentSegment = (currentChat: Chat, messageIndex: number, newContent: string) => {
    const message = currentChat.messages[messageIndex]
    if (!message) return

    if (!message.messageSegments) {
      message.messageSegments = []
    }

    const hasRunningTool = message.messageSegments.some(
      seg => seg.type === 'tool_call' && !seg.isComplete
    )

    if (hasRunningTool) {
      message.content = newContent
      return
    }

    const contentSegments = message.messageSegments.filter(seg => seg.type === 'content')
    const latestContentSegment = contentSegments[contentSegments.length - 1]

    const processedContentLength = contentSegments.reduce((total, seg) => {
      return total + (seg.content?.length || 0)
    }, 0)

    const incrementalContent = newContent.slice(processedContentLength)
    
    if (!incrementalContent) return

    const lastSegment = message.messageSegments[message.messageSegments.length - 1]
    const shouldCreateNewSegment = !latestContentSegment || (lastSegment && lastSegment.type === 'tool_call')

    if (latestContentSegment && !shouldCreateNewSegment) {
      latestContentSegment.content = (latestContentSegment.content || '') + incrementalContent
    } else {
      const contentSegment = {
        id: `content_${Date.now()}`,
        type: 'content' as const,
        timestamp: new Date(),
        content: incrementalContent,
        isComplete: true
      }
      message.messageSegments.push(contentSegment)
    }
  }

  // 处理状态事件
  const handleStatusEvent = (statusData: any) => {
    console.log('📊 教师端状态事件:', statusData)
    currentStatus.value = statusData.message || '处理中...'
    statusStats.value = statusData.stats || {}
    showStatus.value = true
  }

  // 发送消息（教师端专用逻辑，支持流式响应）
  const sendMessage = async (
    content: string,
    currentChat: Chat,
    sessionId: string,
    qaMode: string,
    selectedReferences: Reference[]
  ) => {
    console.log('🎓 教师端消息发送:', {
      content: content.substring(0, 50) + '...',
      qaMode,
      referencesCount: selectedReferences.length,
      sessionId
    })

    if (!content.trim() || isTyping.value || !currentChat) return null

    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      role: 'user' as const,
      content,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    
    currentChat.messages.push(userMessage)

    try {
      isTyping.value = true
      showStatus.value = true
      currentStatus.value = '正在处理您的请求...'

      // 组装历史消息（与学生端保持一致）
      const history = currentChat.messages
        .filter(msg => msg.role === 'user' || msg.role === 'assistant')
        .map(msg => ({ role: msg.role, content: msg.content }))

      // 动态导入教师端API服务
      const { teacherAssistantService } = await import('../api/teacherAssistantService')
      
      // 调用教师端流式API
      const response = await teacherAssistantService.sendMessage({
        content,
        sessionId,
        qaMode,
        references: selectedReferences,
        chatId: currentChat.id,
        history  // 传递历史记录
      })

      // 处理流式响应
      let aiContent = ''
      let aiSources: any[] = []
      let aiMessageIndex = currentChat.messages.length
      let firstToken = true
      let sessionObj = null
      let contentBuffer = ''

      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法读取响应')
      
      const decoder = new TextDecoder()
      let buffer = ''

      // 简化的内容处理函数：不使用任何缓冲，直接返回内容
      function processContentBuffer(): string {
        if (!contentBuffer) return ''
        
        // 直接返回所有内容，不做任何缓冲处理
        const result = contentBuffer
        contentBuffer = ''
        return result
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6)
            
            try {
              const jsonData = JSON.parse(data)
              
              // 只有当解析结果是对象且包含我们期望的字段时，才作为JSON处理
              if (typeof jsonData === 'object' && jsonData !== null && 
                  (jsonData.type || jsonData.sources || jsonData.session)) {
                
                // 调试：记录有效JSON解析
                console.log(`📄 有效JSON解析: data="${data}", jsonData=`, jsonData)
                
                if (jsonData.type === 'status') {
                  handleStatusEvent(jsonData)
                  continue
                }
                
                if (jsonData.sources) {
                  aiSources = jsonData.sources
                  if (currentChat.messages[aiMessageIndex]) {
                    currentChat.messages[aiMessageIndex].sources = aiSources
                  }
                  
                  // 更新累积的引用ID
                  if (updateAccumulatedIds) {
                    updateAccumulatedIds(aiSources)
                  }
                }
                
                if (jsonData.session) {
                  sessionObj = jsonData.session
                }
                continue
              } else {
                // 调试：JSON解析成功但不是预期的对象格式
                console.log(`📝 JSON解析成功但作为文本处理: data="${data}", jsonData=`, jsonData)
              }
            } catch (e) {
              // 调试：记录JSON解析失败的情况
              console.log(`📝 JSON解析失败，作为文本处理: data="${data}"`)
            }
            
            // 处理文本内容
            let textContent = data

            // 检查是否是工具事件
            if (textContent.includes('[TOOL_EVENT]') && textContent.includes('[/TOOL_EVENT]')) {
              const toolEventMatch = textContent.match(/\[TOOL_EVENT\](.*?)\[\/TOOL_EVENT\]/s)
              if (toolEventMatch) {
                try {
                  const toolEvent = JSON.parse(toolEventMatch[1])
                  handleToolEvent(toolEvent, currentChat, aiMessageIndex)
                  textContent = textContent.replace(/\[TOOL_EVENT\].*?\[\/TOOL_EVENT\]/s, '')
                  if (!textContent.trim()) {
                    continue
                  }
                } catch (e) {
                  console.warn('解析教师端工具事件失败:', e)
                }
              }
            }

            // 处理换行符
            if (textContent === '') {
              textContent = '\n'
            } else if (textContent === '\\n') {
              textContent = '\n'
            } else if (textContent.includes('\\n')) {
              textContent = textContent.replace(/\\n/g, '\n')
            }

            // 使用内容缓冲区
            contentBuffer += textContent
            const processedContent = processContentBuffer()

            // 调试：记录每个token的处理情况
            console.log(`🔍 Token处理: textContent="${textContent}", processedContent="${processedContent}", 长度=${processedContent.length}`)

            if (processedContent !== '') {  // 修复：使用严格比较，避免数字'0'被错误过滤
              aiContent += processedContent
              
              if (firstToken) {
                const aiMessage = {
                  id: Date.now(),
                  role: 'assistant' as const,
                  content: '',
                  time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
                  sources: aiSources,
                  showSources: false,
                  messageSegments: [],
                  isStreaming: true
                }
                currentChat.messages.push(aiMessage)
                aiMessageIndex = currentChat.messages.length - 1
                firstToken = false
              }

              // 插入内容片段
              insertContentSegment(currentChat, aiMessageIndex, aiContent)
            }
          }
        }
      }

      // 处理剩余内容
      if (contentBuffer) {
        aiContent += contentBuffer
        insertContentSegment(currentChat, aiMessageIndex, aiContent)
      }

      // 标记流式接收结束
      if (currentChat.messages[aiMessageIndex]) {
        currentChat.messages[aiMessageIndex].isStreaming = false
        
        // 确保最终内容正确显示 - 使用累积的aiContent而不是重新组装
        const currentMessage = currentChat.messages[aiMessageIndex]
        if (aiContent) {
          currentMessage.content = aiContent
        }
      }

      // 处理会话信息
      if (sessionObj?.sessionId) {
        const newSessionId = sessionObj.sessionId
        
        if (currentChat && !currentChat.id) {
          currentChat.id = newSessionId
          currentChat.title = `教师助手 - ${content.substring(0, 20)}...`
        }
        
        return { sessionId: newSessionId }
      }

      return { success: true }
    } catch (error) {
      console.error('教师端消息发送失败:', error)
      
      const errorMessage = {
        id: Date.now(),
        role: 'assistant' as const,
        content: '抱歉，我遇到了一些问题，无法回答您的问题。请稍后再试。',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        error: true
      }
      currentChat.messages.push(errorMessage)
      
      return { error: true, message: '发送失败' }
    } finally {
      isTyping.value = false
      showStatus.value = false
      currentStatus.value = ''
    }
  }

  return {
    isTyping,
    currentStatus,
    statusStats,
    showStatus,
    currentToolInfo,
    sendMessage,
    handleStatusEvent,
    handleToolEvent,
    insertContentSegment
  }
} 