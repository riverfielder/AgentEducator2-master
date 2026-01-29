import { ref, computed } from 'vue'
import type { Chat, Message, Reference } from '../types/chat'
import chatHistoryService from '../api/chatHistoryService'

export function useChatManager() {
  const chatHistory = ref<Chat[]>([])
  const currentChat = ref<Chat | null>(null)
  const sessionId = ref<string | null>(null)

  // 计算属性：按类型分组聊天历史
  const generalChats = computed(() => chatHistory.value.filter(chat => chat.type === 'general'))
  const videoChats = computed(() => chatHistory.value.filter(chat => chat.type === 'video'))
  const courseChats = computed(() => chatHistory.value.filter(chat => chat.type === 'course'))

  // 格式化时间显示
  const formatTime = (dateTime: string) => {
    const date = new Date(dateTime)
    const now = new Date()
    const diffTime = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60))
    const diffMinutes = Math.floor(diffTime / (1000 * 60))
    
    if (diffDays > 0) {
      if (diffDays === 1) return '昨天'
      if (diffDays < 7) return `${diffDays}天前`
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    } else if (diffHours > 0) {
      return `${diffHours}小时前`
    } else if (diffMinutes > 0) {
      return `${diffMinutes}分钟前`
    } else {
      return '刚刚'
    }
  }

  // 格式化消息时间
  const formatMessageTime = (dateTime: string) => {
    const date = new Date(dateTime)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  // 加载聊天历史
  const loadChatHistory = async () => {
    try {
      const response = await chatHistoryService.getChatSessionsList({
        page: 1,
        size: 50,
        includeAll: true
      })
      
      if (response.data.code === 200) {
        const sessions = response.data.data.list
        
        chatHistory.value = sessions.map((session: any) => ({
          id: session.id,
          title: session.title,
          time: formatTime(session.updated_at),
          messages: [],
          type: session.type,
          videoInfo: session.video_info,
          courseInfo: session.course_info
        }))
        
        if (chatHistory.value.length > 0 && !currentChat.value) {
          await selectChat(chatHistory.value[0])
        }
      }
    } catch (error) {
      console.error('加载聊天历史失败:', error)
    }
  }

  // 开始新对话
  const startNewChat = () => {
    const newChat = {
      id: null,
      title: '新对话',
      time: '刚刚',
      messages: [],
      type: 'general',
      videoInfo: null,
      courseInfo: null
    }
    currentChat.value = newChat
    sessionId.value = null
  }

  // 选择对话
  const selectChat = async (chat: Chat) => {
    try {
      currentChat.value = chat
      
      if (!chat.id || chat.messages.length > 0) {
        return
      }
      
      const response = await chatHistoryService.getChatSessionDetail(chat.id)
      if (response.data.code === 200) {
        const sessionData = response.data.data
        const messages = sessionData.messages || []
        
        chat.messages = messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          time: formatMessageTime(msg.created_at),
          sources: msg.time_references || [],
          showSources: false
        }))
        
        sessionId.value = chat.id
      }
    } catch (error) {
      console.error('加载会话详情失败:', error)
    }
  }

  // 编辑对话标题
  const updateChatTitle = async (chatId: string, title: string) => {
    try {
      const response = await chatHistoryService.updateChatSession(chatId, { title })
      
      if (response.data.code === 200) {
        const chat = chatHistory.value.find(c => c.id === chatId)
        if (chat) {
          chat.title = title
        }
        return true
      }
    } catch (error) {
      console.error('更新标题错误:', error)
    }
    return false
  }

  // 删除对话
  const deleteChat = async (chatId: string) => {
    try {
      const response = await chatHistoryService.deleteChatSession(chatId)
      
      if (response.data.code === 200) {
        const index = chatHistory.value.findIndex(chat => chat.id === chatId)
        if (index > -1) {
          chatHistory.value.splice(index, 1)
        }
        
        if (currentChat.value && currentChat.value.id === chatId) {
          currentChat.value = null
          sessionId.value = null
        }
        return true
      }
    } catch (error) {
      console.error('删除对话错误:', error)
    }
    return false
  }

  return {
    chatHistory,
    currentChat,
    sessionId,
    generalChats,
    videoChats,
    courseChats,
    loadChatHistory,
    startNewChat,
    selectChat,
    updateChatTitle,
    deleteChat,
    formatTime,
    formatMessageTime
  }
}
