import { ref } from 'vue'
import type { Ref } from 'vue'
import chatHistoryService from '../api/chatHistoryService'
import type { ChatSession, ChatMessage as HistoryMessage } from '../api/chatHistoryService'
import type { Chat, ChatMessage } from './useChatMessages'
import { format } from 'date-fns'

export function useChatHistory(
  currentChat: Ref<Chat>,
  sessionId: Ref<string | null>
) {
  const chatHistoryList = ref<ChatSession[]>([])
  const historyLoading = ref(false)
  const showHistoryDrawer = ref(false)
  const showEditDialog = ref(false)
  const editTitle = ref('')
  const editingChatId = ref<string | null>(null)

  // 加载聊天历史列表
  const loadChatHistory = async (videoId?: string, courseId?: string, documentId?: string) => {
    historyLoading.value = true
    try {
      const response = await chatHistoryService.getChatSessionsList({
        videoId,
        courseId,
        documentId
      })

      if (response.data.code === 200) {
        chatHistoryList.value = response.data.data.list
      } else {
        console.error('加载聊天历史失败:', response.data.message)
      }
    } catch (error) {
      console.error('加载聊天历史出错:', error)
    } finally {
      historyLoading.value = false
    }
  }

  // 加载聊天历史详情
  const loadHistoryChat = async (chat: ChatSession) => {
    historyLoading.value = true
    try {
      const response = await chatHistoryService.getChatSessionDetail(chat.id)

      if (response.data.code === 200) {
        const data = response.data.data

        // 构造符合当前组件格式的消息
        const formattedMessages = data.messages.map((msg: HistoryMessage) => ({
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          sources: msg.time_references || []
        }))

        // 从历史消息中提取所有引用ID
        const allVideoIds = new Set<string>()
        const allCourseIds = new Set<string>()
        const allDocumentIds = new Set<string>()
        
        formattedMessages.forEach((msg: any) => {
          if (msg.sources && Array.isArray(msg.sources)) {
            msg.sources.forEach((source: any) => {
              if (source.video_id) allVideoIds.add(source.video_id)
              if (source.course_id) allCourseIds.add(source.course_id)
              if (source.document_id) allDocumentIds.add(source.document_id)
            })
          }
        })

        // 更新当前会话
        currentChat.value = {
          id: data.session.id,
          title: data.session.title,
          time: data.session.updated_at,
          messages: formattedMessages,
          accumulatedVideoIds: Array.from(allVideoIds),
          accumulatedCourseIds: Array.from(allCourseIds),
          accumulatedDocumentIds: Array.from(allDocumentIds)
        }

        // 获取会话ID
        sessionId.value = data.session.id

        // 关闭抽屉
        showHistoryDrawer.value = false
      } else {
        console.error('加载聊天详情失败:', response.data.message)
      }
    } catch (error) {
      console.error('加载聊天详情出错:', error)
    } finally {
      historyLoading.value = false
    }
  }

  // 删除聊天历史
  const deleteHistoryChat = async (id: string) => {
    if (!id) return

    try {
      const response = await chatHistoryService.deleteChatSession(id)

      if (response.data.code === 200) {
        // 从列表中移除
        chatHistoryList.value = chatHistoryList.value.filter(chat => chat.id !== id)

        // 如果删除的是当前会话，创建新会话
        if (currentChat.value.id === id) {
          currentChat.value = {
            id: null,
            title: '新对话',
            time: new Date().toLocaleString(),
            messages: []
          }
          sessionId.value = null
        }
      } else {
        console.error('删除聊天历史失败:', response.data.message)
      }
    } catch (error) {
      console.error('删除聊天历史出错:', error)
    }
  }

  // 编辑会话标题
  const editSessionTitle = (chat: ChatSession) => {
    editingChatId.value = chat.id
    editTitle.value = chat.title
    showEditDialog.value = true
  }

  // 更新会话标题
  const updateSessionTitle = async () => {
    if (!editingChatId.value || !editTitle.value.trim()) {
      showEditDialog.value = false
      return
    }

    try {
      const response = await chatHistoryService.updateChatSession(
        editingChatId.value,
        { title: editTitle.value.trim() }
      )

      if (response.data.code === 200) {
        // 更新列表中的标题
        const chatIndex = chatHistoryList.value.findIndex(c => c.id === editingChatId.value)
        if (chatIndex >= 0) {
          chatHistoryList.value[chatIndex].title = editTitle.value.trim()
        }

        // 如果是当前会话，也更新当前会话标题
        if (currentChat.value.id === editingChatId.value) {
          currentChat.value.title = editTitle.value.trim()
        }
      } else {
        console.error('更新标题失败:', response.data.message)
      }
    } catch (error) {
      console.error('更新标题出错:', error)
    } finally {
      showEditDialog.value = false
      editingChatId.value = null
    }
  }

  // 格式化日期
  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'yyyy-MM-dd HH:mm')
    } catch (e) {
      return dateStr
    }
  }

  return {
    chatHistoryList,
    historyLoading,
    showHistoryDrawer,
    showEditDialog,
    editTitle,
    editingChatId,
    loadChatHistory,
    loadHistoryChat,
    deleteHistoryChat,
    editSessionTitle,
    updateSessionTitle,
    formatDate
  }
}
