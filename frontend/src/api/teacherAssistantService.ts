import apiClient from './index'
import type { Reference } from '../types/chat'

export interface TeacherMessageRequest {
  content: string
  sessionId: string
  qaMode: string
  references: Reference[]
  chatId: string | null
  history?: any[]  // 添加历史记录字段
}

export interface TeacherMessageResponse {
  success: boolean
  sessionId?: string
  error?: boolean
  message?: string
  data?: any
}

class TeacherAssistantService {
  
  /**
   * 发送教师端消息（流式）
   */
  async sendMessage(request: TeacherMessageRequest): Promise<Response> {
    try {
      console.log('🎓 发送教师端流式消息:', request)
      
      // 发送流式请求，复用学生端的流式接口逻辑
      const response = await fetch(`${apiClient.defaults.baseURL}/api/teacher-assistant/chat/stream`, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('wendao_token')}`
        },
        body: JSON.stringify({
          content: request.content,
          sessionId: request.sessionId,
          qaMode: request.qaMode,
          references: request.references,
          chatId: request.chatId,
          history: request.history || [],  // 包含历史记录
          isNewSession: !request.sessionId
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      return response
      
    } catch (error) {
      console.error('教师端流式消息发送失败:', error)
      throw error
    }
  }

  /**
   * 获取教师端聊天历史
   */
  async getChatHistory(teacherId: string): Promise<any[]> {
    try {
      console.log('📚 获取教师端聊天历史:', teacherId)
      const response = await apiClient.get(`/api/teacher-assistant/history/${teacherId}`)
      return response.data.data || []
    } catch (error) {
      console.error('获取教师端聊天历史失败:', error)
      return []
    }
  }

  /**
   * 创建新的教师端聊天会话
   */
  async createChatSession(teacherId: string): Promise<string | null> {
    try {
      console.log('🆕 创建教师端聊天会话:', teacherId)
      const response = await apiClient.post('/api/teacher-assistant/session', { teacherId })
      return response.data.sessionId
    } catch (error) {
      console.error('创建教师端聊天会话失败:', error)
      return null
    }
  }

  /**
   * 删除教师端聊天会话
   */
  async deleteChatSession(sessionId: string): Promise<boolean> {
    try {
      console.log('🗑️ 删除教师端聊天会话:', sessionId)
      const response = await apiClient.delete(`/api/teacher-assistant/session/${sessionId}`)
      return response.data.success
    } catch (error) {
      console.error('删除教师端聊天会话失败:', error)
      return false
    }
  }

  /**
   * 更新教师端聊天会话标题
   */
  async updateChatTitle(sessionId: string, title: string): Promise<boolean> {
    try {
      console.log('📝 更新教师端聊天标题:', { sessionId, title })
      const response = await apiClient.put(`/api/teacher-assistant/session/${sessionId}`, { title })
      return response.data.success
    } catch (error) {
      console.error('更新教师端聊天标题失败:', error)
      return false
    }
  }
}

export const teacherAssistantService = new TeacherAssistantService()
export default teacherAssistantService 