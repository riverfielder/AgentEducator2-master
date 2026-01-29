export interface Source {
    index: number
    course_id: string
    course_title: string
    video_id?: string
    video_title?: string
    document_id?: string
    document_title?: string
    segment_number?: number
    segment_type?: string
    segment_title?: string
    time_point: number
    time_formatted: string
    content: string
    type?: 'video' | 'document' // 引用源类型
    page_number?: number // 文档页码
}

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

export interface Message {
  id: number | string
  role: 'user' | 'assistant'
  content: string
  time: string
  sources?: Source[]
  error?: boolean
  showSources?: boolean
  messageSegments?: MessageSegment[]
  isStreaming?: boolean
}

export interface Chat {
  id: string | null
  title: string
  time: string
  messages: Message[]
  type: string
  videoInfo: any
  courseInfo: any
  documentInfo?: any
}

export interface StatusData {
  message: string
  stage?: string
  stats?: {
    document_count?: number
    tokens?: number
    sources?: number
  }
}

export interface Reference {
  id: string
  type: 'course' | 'video'
  name: string
  description?: string
  courseName?: string
  courseId?: string
}

export interface Suggestion {
  id: string
  type: 'course' | 'video' | 'document' | 'keyword'
  name: string
  text?: string // 建议显示文本，作为name的备选
  description?: string
  courseName?: string
  courseId?: string
  category?: string // 用于知识点分类
}

export interface ContentFilterResult {
  isValid: boolean
  message: string
}
