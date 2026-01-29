import { ref } from 'vue'
import chatHistoryService from '../api/chatHistoryService'
import qaService from '../api/qaService'
import type { Chat, Message, MessageSegment, Source, StatusData } from '../types/chat'
import { checkContent, type ContentFilterResult } from '../utils/contentFilter'

export function useMessageSender(
  updateAccumulatedIds?: (sources: Source[]) => void,
  getAccumulatedIds?: () => { videoIds: string[]; courseIds: string[]; documentIds: string[] }
) {
  const isTyping = ref(false)
  const currentStatus = ref<string>('')
  const statusStats = ref<StatusData['stats'] | undefined>(undefined)
  const showStatus = ref(false)
  const currentToolInfo = ref<any>(null)
  // 处理工具事件
  const handleToolEvent = (toolEventData: any, currentChat: Chat, aiMessageIndex: number) => {
    const currentMessage = currentChat.messages[aiMessageIndex]
    if (!currentMessage) return

    // 确保消息片段数组存在
    if (!currentMessage.messageSegments) {
      currentMessage.messageSegments = []
    }

    if (toolEventData.type === 'tool_start') {
      // 设置当前工具信息用于状态显示
      currentToolInfo.value = {
        tool_name: toolEventData.data.tool_name,
        tool_icon: toolEventData.data.tool_icon,
        tool_color: toolEventData.data.tool_color,
        description: toolEventData.data.description,
        context: toolEventData.data.context,
        status: 'running'
      }

      // 创建工具调用片段
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
        showDetailed: true
      }

      currentMessage.messageSegments.push(toolSegment)
    } else if (toolEventData.type === 'tool_result') {
      // 清除当前工具信息
      currentToolInfo.value = null

      // 查找最近的未完成工具调用片段
      const toolCallSegment = [...currentMessage.messageSegments]
        .reverse()
        .find(segment => segment.type === 'tool_call' && !segment.isComplete)

      if (toolCallSegment && toolCallSegment.toolInfo) {        // 标记工具调用完成
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
          // 计算已经处理过的内容长度
          const contentSegments = currentMessage.messageSegments.filter(seg => seg.type === 'content')
          const processedContentLength = contentSegments.reduce((total, seg) => {
            return total + (seg.content?.length || 0)
          }, 0)

          // 提取新增的内容部分
          const incrementalContent = currentMessage.content.slice(processedContentLength)
          
          if (incrementalContent && incrementalContent.trim()) {
            // 创建新的内容片段
            const newContentSegment = createContentSegment(incrementalContent)
            currentMessage.messageSegments.push(newContentSegment)
          }
          
          // 清空暂存内容
          currentMessage.content = ''
        }

        // 工具完成后，等待2秒后自动折叠
        setTimeout(() => {
          if (toolCallSegment.showDetailed !== false) {
            toolCallSegment.showDetailed = false
          }
        }, 2000)
      }
    }
  }

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
  // 插入内容片段（智能处理增量更新）
  const insertContentSegment = (currentChat: Chat, messageIndex: number, newContent: string) => {
    const message = currentChat.messages[messageIndex]
    if (!message) return

    if (!message.messageSegments) {
      message.messageSegments = []
    }

    // 检查是否有未完成的工具调用
    const hasRunningTool = message.messageSegments.some(
      seg => seg.type === 'tool_call' && !seg.isComplete
    )

    // 如果有正在运行的工具，将内容暂存，等工具完成后再处理
    if (hasRunningTool) {
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
    
    if (!incrementalContent) return // 没有新内容

    // 检查最后一个片段是否是工具调用（需要创建新内容片段）
    const lastSegment = message.messageSegments[message.messageSegments.length - 1]
    const shouldCreateNewSegment = !latestContentSegment || (lastSegment && lastSegment.type === 'tool_call')

    if (latestContentSegment && !shouldCreateNewSegment) {
      // 增量更新最新的内容片段
      latestContentSegment.content = (latestContentSegment.content || '') + incrementalContent
    } else {
      // 创建新的内容片段
      const contentSegment = createContentSegment(incrementalContent)
      message.messageSegments.push(contentSegment)
    }
  }// 处理状态事件
  const handleStatusEvent = (statusData: StatusData) => {
    currentStatus.value = statusData.message
    statusStats.value = statusData.stats || undefined
    showStatus.value = true
    
    // 对于某些阶段，设置自动隐藏
    if (statusData.stage === 'generation_start') {
      setTimeout(() => {
        showStatus.value = false
      }, 1000)
    }
  }

  // 发送消息
  const sendMessage = async (
    content: string,
    currentChat: Chat,
    sessionId: string | null,
    qaMode: string,
    selectedReferences: any[]
  ) => {
    if (!content.trim() || isTyping.value || !currentChat) return null

    // 内容审核检测
    const auditResult: ContentFilterResult = checkContent(content)
    if (!auditResult.isValid) {
      return { error: true, message: auditResult.message }
    }

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content,
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    
    currentChat.messages.push(userMessage)
    
    // 开始AI回复
    isTyping.value = true
    currentStatus.value = '准备处理请求...'
    showStatus.value = true
    
    try {
      // 组装历史消息
      const history = currentChat.messages
        .filter(msg => msg.role === 'user' || msg.role === 'assistant')
        .map(msg => ({ role: msg.role, content: msg.content }))

      // 获取累积的引用ID作为基础
      const accumulatedIds = getAccumulatedIds ? getAccumulatedIds() : { videoIds: [], courseIds: [], documentIds: [] }
      
      // 合并累积的ID和当前选择的引用
      const allVideoIds = new Set([...accumulatedIds.videoIds])
      const allCourseIds = new Set([...accumulatedIds.courseIds])
      const allDocumentIds = new Set([...accumulatedIds.documentIds])

      // 根据问答模式设置参数 - 简化为数组格式
      let requestParams: any = {
        query: content,
        sessionId: sessionId,
        isNewSession: !sessionId,
        history,
        videoIds: [],
        courseIds: [],
        documentIds: []
      }

      // 根据选择的引用和模式收集资源ID
      if (qaMode === 'video') {
        const videoRefs = selectedReferences.filter(ref => ref.type === 'video')
        videoRefs.forEach(ref => allVideoIds.add(ref.id))
      } else if (qaMode === 'course') {
        const courseRefs = selectedReferences.filter(ref => ref.type === 'course')
        if (courseRefs.length > 0) {
          courseRefs.forEach(ref => allCourseIds.add(ref.id))
        } else {
          // 如果没有直接选择课程，但选择了视频，使用视频的课程ID
          const videoRefs = selectedReferences.filter(ref => ref.type === 'video')
          const courseIds = [...new Set(videoRefs.map(ref => ref.courseId).filter(id => id))]
          courseIds.forEach(id => allCourseIds.add(id))
        }
      } else if (qaMode === 'document') {
        // 文档模式：收集文档引用
        const documentRefs = selectedReferences.filter(ref => ref.type === 'document')
        documentRefs.forEach(ref => allDocumentIds.add(ref.id))
      } else if (qaMode === 'all') {
        // 全部模式：可以收集所有选择的资源
        const videoRefs = selectedReferences.filter(ref => ref.type === 'video')
        const courseRefs = selectedReferences.filter(ref => ref.type === 'course')
        const documentRefs = selectedReferences.filter(ref => ref.type === 'document')
        
        videoRefs.forEach(ref => allVideoIds.add(ref.id))
        courseRefs.forEach(ref => allCourseIds.add(ref.id))
        documentRefs.forEach(ref => allDocumentIds.add(ref.id))
        
        // 如果没有明确选择任何资源，工具会在所有内容中搜索
      }
      // 其他模式保持数组为空，让工具自由搜索
      
      // 设置最终的ID数组
      requestParams.videoIds = Array.from(allVideoIds)
      requestParams.courseIds = Array.from(allCourseIds)
      requestParams.documentIds = Array.from(allDocumentIds)

      const response = await qaService.askQuestionStream(requestParams)
      if (!response.ok) {
        throw new Error('网络请求失败')
      }      // 处理SSE流
      let aiContent = ''
      let aiSources: any[] = []
      let aiMessageIndex = currentChat.messages.length
      let firstToken = true
      let sessionObj = null
      let contentBuffer = '' // 用于缓冲内容

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
            const data = line.substring(6);
            if (data.startsWith('{')|| data.startsWith('[')) {
            try {
              const jsonData = JSON.parse(data)
              
              if (jsonData.type === 'status') {
                handleStatusEvent(jsonData)
                continue
              }
              
              if (jsonData.sources) {
                aiSources = jsonData.sources
                if (currentChat.messages[aiMessageIndex]) {
                  currentChat.messages[aiMessageIndex].sources = aiSources
                }
                
                // 根据引用源动态扩展ID列表
                if (aiSources && aiSources.length > 0) {
                  // 更新会话级别的累积引用ID
                  if (updateAccumulatedIds) {
                    updateAccumulatedIds(aiSources)
                  }
                  
                  const newVideoIds = new Set(requestParams.videoIds)
                  const newCourseIds = new Set(requestParams.courseIds)
                  const newDocumentIds = new Set(requestParams.documentIds)
                  
                  aiSources.forEach(source => {
                    if (source.video_id && !newVideoIds.has(source.video_id)) {
                      newVideoIds.add(source.video_id)
                    }
                    if (source.course_id && !newCourseIds.has(source.course_id)) {
                      newCourseIds.add(source.course_id)
                    }
                    if (source.document_id && !newDocumentIds.has(source.document_id)) {
                      newDocumentIds.add(source.document_id)
                    }
                  })
                  
                  // 更新请求参数以供后续使用
                  requestParams.videoIds = Array.from(newVideoIds)
                  requestParams.courseIds = Array.from(newCourseIds)
                  requestParams.documentIds = Array.from(newDocumentIds)
                }
              }
              
              if (jsonData.session) {
                sessionObj = jsonData.session
              }
              continue
            } catch (e) {}
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
                  // 移除工具事件部分，继续处理剩余文本
                  textContent = textContent.replace(/\[TOOL_EVENT\].*?\[\/TOOL_EVENT\]/s, '')
                  if (!textContent.trim()) {
                    continue // 如果只是工具事件，跳过文本处理
                  }
                } catch (e) {
                  console.warn('解析工具事件失败:', e)
                }
              }
            }

            // 特殊处理：空的data行表示换行
            if (textContent === '') {
              textContent = '\n'
            }
            // 处理转义的换行符
            else if (textContent === '\\n') {
              textContent = '\n'
            }
            // 处理其他可能的换行表示
            else if (textContent === '\n' || textContent === '\r\n') {
              textContent = '\n'
            }
            // 处理包含换行符的内容
            else if (textContent.includes('\\n')) {
              textContent = textContent.replace(/\\n/g, '\n')
            }

            // 使用内容缓冲区处理内容
            contentBuffer += textContent
            
            const processedContent = processContentBuffer()

            if (processedContent) {
              aiContent += processedContent
              
              if (firstToken) {
                const aiMessage: Message = {
                  id: Date.now(),
                  role: 'assistant',
                  content: '', // 不设置content，只使用messageSegments
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

      // 处理剩余的缓冲区内容
      if (buffer.trim()) {
        if (buffer.startsWith('data: ')) {
          const content = buffer.substring(6)
          try {
            const jsonData = JSON.parse(content)
            if (jsonData.type === 'status') {
              handleStatusEvent(jsonData)
            } else {
              if (jsonData.sources) {
                aiSources = jsonData.sources
              }
              if (jsonData.session) {
                sessionObj = jsonData.session
              }
            }
          } catch (e) {
            contentBuffer += content
            const processedContent = processContentBuffer()
            if (processedContent) {
              aiContent += processedContent
              insertContentSegment(currentChat, aiMessageIndex, aiContent)
            }
          }
        }
      }

      // 流结束时，处理剩余的内容缓冲区
      if (contentBuffer) {
        aiContent += contentBuffer
        insertContentSegment(currentChat, aiMessageIndex, aiContent)
        contentBuffer = ''
      }

      // 标记流式接收结束
      if (currentChat.messages[aiMessageIndex]) {
        currentChat.messages[aiMessageIndex].isStreaming = false
        
        // 重新组装完整的content用于历史记录
        const currentMessage = currentChat.messages[aiMessageIndex]
        if (currentMessage.messageSegments && currentMessage.messageSegments.length > 0) {
          // 提取所有内容片段的文本内容
          const contentParts = currentMessage.messageSegments
            .filter(segment => segment.type === 'content')
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
            .map(segment => segment.content || '')
            .filter(content => content.trim())

          // 组装完整内容
          if (contentParts.length > 0) {
            currentMessage.content = contentParts.join('')
          }
        }
      }

      // 处理会话信息
      if (sessionObj?.sessionId) {
        const newSessionId = sessionObj.sessionId
        
        if (currentChat && !currentChat.id) {
          currentChat.id = newSessionId
          currentChat.title = `通用问答 - ${content.substring(0, 20)}...`
        }
        
        // 自动更新会话的资源ID（从引用源收集）
        if (aiSources && aiSources.length > 0) {
          // 更新累积的引用ID
          if (updateAccumulatedIds) {
            updateAccumulatedIds(aiSources)
          }
          
          try {
            await chatHistoryService.updateSessionResourceIds(newSessionId, aiSources)
          } catch (error) {
            console.warn('更新会话资源ID失败:', error)
          }
        }
        
        return { sessionId: newSessionId }
      }

      return { success: true }
    } catch (error) {
      console.error('AI回复错误:', error)
      
      const errorMessage: Message = {
        id: Date.now(),
        role: 'assistant',
        content: '抱歉，我遇到了一些问题，无法回答您的问题。请稍后再试。',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
        error: true
      }
      currentChat.messages.push(errorMessage)
      
      return { error: true, message: '发送失败' }
    } finally {
      isTyping.value = false
      showStatus.value = false
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
