import { ref, nextTick } from 'vue'
import type { Ref } from 'vue'
import qaService from '../api/qaService'
import chatHistoryService from '../api/chatHistoryService'
import { processContent } from '../utils/markdownRenderer'
import type { ChatMessage } from './useChatMessages'
import type { Source } from '@/types/chat'
export function useMessageSending(
  currentChat: Ref<{ id: string | null; messages: ChatMessage[]; accumulatedVideoIds?: string[]; accumulatedCourseIds?: string[]; accumulatedDocumentIds?: string[] }>,
  sessionId: Ref<string | null>,
  insertContentSegment: (messageIndex: number, newContent: string) => void,
  handleToolEvent: (toolEventData: any) => void,
  handleStatusEvent: (statusData: any) => void,
  scrollToBottom: () => void,
  addAIMessage: () => number,
  createNewChatSession: (userMessage: string, videoId?: string, courseId?: string, documentId?: string) => Promise<string | null>,
  updateAccumulatedIds: (sources: Source[]) => void,
  getAccumulatedIds: () => { videoIds: string[]; courseIds: string[]; documentIds: string[] }
) {
  const isTyping = ref(false)

  // 处理消息渲染，支持Markdown并将引用标记转换为可点击的元素
  const processMessageContent = (content: string): string => {
    if (!content) return ''
    return processContent(content)
  }
    
  // 发送消息处理
  const sendMessage = async (
    userMessage: string,
    loadChatHistory: () => Promise<void>,
    videoId?: string,
    courseId?: string,
    documentId?: string,

  ) => {
    if (!userMessage.trim()) {
      return
    }

    // 如果是新会话，创建会话记录
    if (!currentChat.value.id) {
      const newSessionId = await createNewChatSession(userMessage, videoId, courseId, documentId)
      if (newSessionId) {
        loadChatHistory()
      }
    }

    isTyping.value = true

    // 重置并准备状态显示
    const aiMessageIndex = addAIMessage()
    scrollToBottom()

    try {
      // 组装历史消息（不含最后一条AI消息）
      const history = currentChat.value.messages
        .filter((msg, idx) => idx < aiMessageIndex)
        .map(msg => ({ role: msg.role, content: msg.content }))

      // 获取累积的引用ID作为基础
      const accumulatedIds = getAccumulatedIds()
      
      // 合并当前页面的ID和累积的ID
      const allVideoIds = new Set([...accumulatedIds.videoIds])
      const allCourseIds = new Set([...accumulatedIds.courseIds])
      const allDocumentIds = new Set([...accumulatedIds.documentIds])
      
      // 添加当前页面的ID（如果存在）
      if (videoId) allVideoIds.add(videoId)
      if (courseId) allCourseIds.add(courseId)
      if (documentId) allDocumentIds.add(documentId)

      // 使用简化的多资源模式进行对话
      const requestParams: any = {
        query: userMessage.replace(/<[^>]+>/g, ''),
        sessionId: sessionId.value,
        isNewSession: !sessionId.value,
        history,
        videoIds: Array.from(allVideoIds),
        courseIds: Array.from(allCourseIds),
        documentIds: Array.from(allDocumentIds)
      }

      // 请求流式API（POST）
      const response = await qaService.askQuestionStream(requestParams)
      const reader = response.body?.getReader()

      let aiContent = ''
      let decoder = new TextDecoder('utf-8')
      let firstToken = true
      let sources = []
      let sessionObj: { sessionId?: string } | null = null
      let buffer = '' // 用于处理不完整的数据！！
      let contentBuffer = '' // 用于缓冲内容以处理Markdown序号

      // 内容缓冲处理函数（修复数字截断问题）
      function processContentBuffer(): string {
        if (!contentBuffer) return ''

        // 更精确的序号标记检测：必须是行首的数字加标点
        const potentialMarkerRegex = /^\d+[.）)]\s*\*{0,2}$/
        const completeMarkerRegex = /^\d+[.）)]\s*\*{0,2}\S/

        // 如果包含完整的序号标记，可以释放
        if (completeMarkerRegex.test(contentBuffer)) {
          const result = contentBuffer
          contentBuffer = ''
          return result
        }

        // 如果以句号、感叹号、问号、换行符结尾，可以释放
        if (/[.!?。！？\n]\s*$/.test(contentBuffer)) {
          const result = contentBuffer
          contentBuffer = ''
          return result
        }

        // 如果缓冲区太大，释放内容（但不要在数字处截断）
        if (contentBuffer.length > 50) {
          // 检查是否是行首的序号格式
          if (potentialMarkerRegex.test(contentBuffer.trim())) {
            // 如果是潜在的序号，保留不释放
            return ''
          } else {
            // 否则释放全部内容
            const result = contentBuffer
            contentBuffer = ''
            return result
          }
        }

        return ''
      }

      while (true) {
        const { done, value } = await reader!.read()
        if (done) break

        // 将新数据添加到缓冲区
        buffer += decoder.decode(value, { stream: true })

        // 按行分割数据
        const lines = buffer.split('\n')

        // 保留最后一行（可能不完整）
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue // 跳过空行
          
          // 处理 data: 行
          if (line.startsWith('data: ')) {
            const content = line.substring(6) // 'data: '.length = 6
            if (content.startsWith('{')|| content.startsWith('[')) {
            // 尝试解析JSON（可能是源文档、会话信息或状态事件）
            try {
              const jsonData = JSON.parse(content)

              // 处理状态事件
              if (jsonData.type === 'status') {
                handleStatusEvent(jsonData)
                continue
              }

              // 处理其他JSON数据
              if (jsonData.sources) {
                sources = jsonData.sources
                
                // 根据引用源动态扩展ID列表
                if (sources && sources.length > 0) {
                  // 更新会话级别的累积引用ID
                  updateAccumulatedIds(sources)
                  
                  const newVideoIds = new Set(requestParams.videoIds)
                  const newCourseIds = new Set(requestParams.courseIds)
                  const newDocumentIds = new Set(requestParams.documentIds)
                  
                  sources.forEach((source:Source) => {
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
            } catch (e) {
              // 不是JSON，当作普通文本处理
            }
          }
            // 处理文本内容
            let textContent = content

            // 检查是否是工具事件
            if (textContent.includes('[TOOL_EVENT]') && textContent.includes('[/TOOL_EVENT]')) {
              const toolEventMatch = textContent.match(/\[TOOL_EVENT\](.*?)\[\/TOOL_EVENT\]/s)
              if (toolEventMatch) {
                try {
                  const toolEvent = JSON.parse(toolEventMatch[1])
                  handleToolEvent(toolEvent)
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

            // 使用内容缓冲区处理Markdown序号分割问题
            contentBuffer += textContent
            const processedContent = processContentBuffer()

            if (processedContent) {
              // 智能流式处理
              aiContent += processedContent

              // 获取当前消息
              const currentMessage = currentChat.value.messages[aiMessageIndex]

              // 只更新内容片段，不更新 message.content（避免重复显示）
              if (currentMessage && currentMessage.messageSegments) {
                insertContentSegment(aiMessageIndex, aiContent)
              }

              if (firstToken) {
                const aiMessage: ChatMessage = {
                  role: 'assistant' as const,
                  content: '', // 不设置content，只使用messageSegments
                  timestamp: new Date(),
                  sources: [],
                  messageSegments: currentChat.value.messages[aiMessageIndex].messageSegments || [],
                  isStreaming: true
                }
                currentChat.value.messages[aiMessageIndex] = aiMessage
                firstToken = false
              }

              // 滚动到底部
              scrollToBottom()
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

            // 处理状态事件
            if (jsonData.type === 'status') {
              handleStatusEvent(jsonData)
            } else {
              // 处理其他JSON数据
              if (jsonData.sources) {
                sources = jsonData.sources
              }
              if (jsonData.session) {
                sessionObj = jsonData.session
              }
            }
          } catch (e) {
            // 不是JSON，当作普通文本处理
            contentBuffer += content
            const processedContent = processContentBuffer()
            if (processedContent) {
              aiContent += processedContent
              const currentMessage = currentChat.value.messages[aiMessageIndex]
              if (currentMessage && currentMessage.messageSegments) {
                insertContentSegment(aiMessageIndex, aiContent)
              }
            }
          }
        }
      }

      // 流结束时，处理剩余的内容缓冲区
      if (contentBuffer) {
        aiContent += contentBuffer
        // 只更新内容片段，不更新 message.content
        const currentMessage = currentChat.value.messages[aiMessageIndex]
        if (currentMessage && currentMessage.messageSegments) {
          insertContentSegment(aiMessageIndex, aiContent)
        }
        contentBuffer = ''
      }

      // 标记流式接收结束
      currentChat.value.messages[aiMessageIndex].isStreaming = false

      // 重新组装完整的content用于历史记录
      const currentMessage = currentChat.value.messages[aiMessageIndex]
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

      // 设置源文档
      if (sources.length > 0) {
        currentChat.value.messages[aiMessageIndex].sources = sources
        currentChat.value.messages[aiMessageIndex].showSources = false
        
        // 更新累积的引用ID
        updateAccumulatedIds(sources)
        
        // 更新会话资源IDs
        if (sessionId.value || currentChat.value.id) {
          const currentSessionId = sessionId.value || currentChat.value.id
          if (currentSessionId) {
            try {
              await chatHistoryService.updateSessionResourceIds(currentSessionId, sources)
              console.log('会话资源IDs已更新')
            } catch (error) {
              console.warn('更新会话资源IDs失败:', error)
            }
          }
        }
      }

      // 解析sessionId
      if (sessionObj && sessionObj.sessionId) {
        sessionId.value = sessionObj.sessionId
        currentChat.value.id = sessionObj.sessionId
      }
    } catch (error) {
      console.error('AI回复错误:', error)
      // 清空消息片段，只显示错误消息
      const errorMessage: ChatMessage = {
        role: 'assistant' as const,
        content: '抱歉，我遇到了一些问题，无法回答您的问题。请稍后再试。',
        timestamp: new Date(),
        error: true,
        isStreaming: false,
        messageSegments: [] // 确保没有消息片段
      }
      currentChat.value.messages[aiMessageIndex] = errorMessage
    } finally {
      isTyping.value = false
    }
  }

  return {
    isTyping,
    sendMessage,
    processMessageContent
  }
}
