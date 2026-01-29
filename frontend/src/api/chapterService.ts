import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('wendao_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export interface Chapter {
  id?: string
  courseId: string
  title: string
  description?: string
  chapterNumber: number
  createTime?: string
  updateTime?: string
  isDeleted?: boolean
}

export interface ChapterListResponse {
  code: number
  message: string
  data: {
    list: Chapter[]
    total: number
  }
}

export interface ChapterResponse {
  code: number
  message: string
  data: Chapter
}

export const chapterService = {
  // 获取课程的所有章节
  async getCourseChapters(courseId: string): Promise<ChapterListResponse> {
    const response = await api.get(`/api/chapters/${courseId}`)
    return response.data
  },

  // 创建新章节
  async createChapter(chapterData: Omit<Chapter, 'id' | 'createTime' | 'updateTime' | 'isDeleted'>): Promise<ChapterResponse> {
    const response = await api.post('/api/chapters', chapterData)
    return response.data
  },

  // 更新章节
  async updateChapter(chapterId: string, chapterData: Partial<Omit<Chapter, 'id' | 'courseId' | 'createTime' | 'updateTime' | 'isDeleted'>>): Promise<ChapterResponse> {
    const response = await api.put(`/api/chapters/${chapterId}`, chapterData)
    return response.data
  },

  // 删除章节
  async deleteChapter(chapterId: string): Promise<{ code: number; message: string }> {
    const response = await api.delete(`/api/chapters/${chapterId}`)
    return response.data
  },

  // 将资源分配到章节
  async assignResourceToChapter(assignData: {
    resourceId: string;
    resourceType: 'video' | 'document';
    chapterId?: string | null;
  }): Promise<{ code: number; message: string }> {
    const response = await api.post('/api/chapters/assign-resource', assignData)
    return response.data
  },

  // 获取章节下的所有资源
  async getChapterResources(chapterId: string): Promise<{
    code: number;
    message: string;
    data: {
      chapter: Chapter;
      resources: any[];
      total: number;
    };
  }> {
    const response = await api.get(`/api/chapters/${chapterId}/resources`)
    return response.data
  }
} 