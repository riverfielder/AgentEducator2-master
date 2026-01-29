import apiClient, { uploadClient } from './index'

// 确保API_BASE_URL有正确的默认值
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

export interface Document {
  id: string
  title: string
  description?: string
  file_url: string
  file_type: string
  file_size: number
  course_id: string
  chapter_id?: string
  order_index: number
  download_count: number
  upload_time: string
  processing_status: string
  course?: {
    id: string
    name: string
  }
  chapter?: {
    id: string
    title: string
  }
}

export interface DocumentListResponse {
  code: number
  message: string
  data: {
    list: Document[]
    total: number
  }
}

export interface DocumentUploadData {
  courseId: string
  title: string
  description?: string
  chapterId?: string
  file: File
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface DocumentSummary {
  id: string
  document_id: string
  main_points: string
  keywords: string
  sections: Array<{
    title: string
    content: string
    segment_count?: number
  }>
  whole_summary: string
  generate_time: string
}

export interface DocumentSegment {
  id: string
  document_id: string
  segment_number: number
  title: string
  content: string
  page_number?: number
  segment_type: string
}

export const documentService = {
  // 获取所有文档
  async getAllDocuments() {
    return apiClient.get('/api/documents/all')
  },

  // 获取课程文档
  async getCourseDocuments(courseId: string) {
    return apiClient.get(`/api/documents/${courseId}`)
  },

  // 上传文档
  async uploadDocument(data: DocumentUploadData) {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('courseId', data.courseId)
    formData.append('title', data.title)
    if (data.description) {
      formData.append('description', data.description)
    }
    if (data.chapterId) {
      formData.append('chapterId', data.chapterId)
    }

    return apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 处理文档 - 使用长超时的uploadClient，因为文档处理可能需要几分钟
  async processDocument(documentId: string, data: any) {
    return uploadClient.post(`/api/documents/${documentId}/process`, data)
  },



  // 更新文档
  async updateDocument(documentId: string, data: Partial<Document>) {
    return apiClient.put(`/api/documents/${documentId}`, data)
  },

  // 删除文档
  async deleteDocument(documentId: string) {
    return apiClient.delete(`/api/documents/${documentId}`)
  },

  // 下载文档
  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await apiClient.get(`/api/documents/${documentId}/download`, {
      responseType: 'blob'
    })
    return response.data
  },

  // 获取预览URL - 用于PDF等文档的直接预览
  getPreviewUrl(documentId: string): string {
    const token = localStorage.getItem('wendao_token')
    return `${API_BASE_URL}/api/documents/${documentId}/preview?token=${encodeURIComponent(token || '')}`
  },

  // 预览文档 - 返回blob URL用于在当前页面预览
  async previewDocument(documentId: string): Promise<string> {
    const response = await apiClient.get(`/api/documents/${documentId}/preview`, {
      responseType: 'blob'
    })
    return URL.createObjectURL(response.data)
  },

  // 流式预览 - 用于大文件的流式加载
  async streamPreview(documentId: string): Promise<ReadableStream> {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/preview`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('wendao_token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('预览失败')
    }
    
    return response.body!
  },

  // 获取文档详情
  async getDocumentDetail(documentId: string) {
    return apiClient.get(`/api/documents/detail/${documentId}`)
  },

  // 获取文档摘要
  async getDocumentSummary(documentId: string) {
    return apiClient.get(`/api/documents/${documentId}/summary`)
  },

  // 问答功能
  async askQuestion(documentId: string, question: string) {
    return apiClient.post(`/api/documents/${documentId}/ask`, {
      question,
      document_id: documentId
    })
  },

  // 获取文档分段列表
  async getDocumentSegments(documentId: string) {
    return apiClient.get(`/api/documents/${documentId}/segments`)
  },

  // 获取特定分段内容
  async getDocumentSegment(documentId: string, segmentNumber: number) {
    return apiClient.get(`/api/documents/${documentId}/segments/${segmentNumber}`)
  },

  // 批量获取文档处理状态
  getBatchProcessingStatus(documentIds: string[]): Promise<ApiResponse<any>> {
    return apiClient.post('/api/documents/batch/processing-status', {
      document_ids: documentIds
    })
  },

  // 更新文档阅读进度
  async updateDocumentProgress(documentId: string, data: { reading_time: number }) {
    return apiClient.post(`/api/documents/${documentId}/progress`, data)
  },

  // 获取文档阅读进度
  async getDocumentProgress(documentId: string) {
    return apiClient.get(`/api/documents/${documentId}/progress`)
  },
}