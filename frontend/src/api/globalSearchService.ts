import apiClient from './index'
import { parseCourseDescription } from '../utils/courseUtils'

// 全局搜索结果类型定义
export interface GlobalSearchResult {
  id: string
  title?: string
  name?: string
  description?: string
  type: 'video' | 'document' | 'course' | 'keyword'
  course_id?: string
  course_name?: string
  keywords?: string[]
  cover_url?: string
  duration?: number
  upload_time?: string
  file_type?: string
  file_size?: number
  code?: string
  image_url?: string
  start_date?: string
  end_date?: string
  teacher_name?: string
  student_count?: number
  video_count?: number
  document_count?: number
  category?: string
}

export interface GlobalSearchResponse {
  results: {
    videos?: GlobalSearchResult[]
    documents?: GlobalSearchResult[]
    courses?: GlobalSearchResult[]
    keywords?: GlobalSearchResult[]
  }
  total_count: number
  query: string
  search_type: string
  scope: string[]
  course_id?: string
}

export interface SearchSuggestion {
  text: string
  type: 'keyword' | 'course' | 'video' | 'document'
  category?: string
  id?: string
  description?: string
}

export interface GlobalSearchParams {
  q: string // 搜索关键词
  scope?: string // 搜索范围，逗号分隔
  search_type?: 'keyword_search' | 'fulltext_search' // 搜索类型
  course_id?: string // 限制在特定课程内搜索
  page?: number // 页码
  page_size?: number // 每页大小
  limit?: number // 每个类型的最大结果数
}

export interface SuggestionsParams {
  q: string // 搜索关键词前缀
  limit?: number // 建议数量限制
}

class GlobalSearchService {
  async search(params: GlobalSearchParams): Promise<GlobalSearchResponse> {
    try {
      const response = await apiClient.get('/api/global-search', { params })
      
      // 检查响应格式 - 后端返回格式: {code: 200, data: {...}, message: "..."}
      if (!response || !response.data || response.data.code !== 200 || !response.data.data) {
        console.error('搜索响应格式错误:', response)
        return {
          results: {},
          total_count: 0,
          query: params.q,
          search_type: params.search_type || 'keyword_search',
          scope: params.scope ? params.scope.split(',') : ['videos', 'documents', 'courses', 'keywords']
        }
      }
      
      return response.data.data
    } catch (error) {
      console.error('全局搜索失败:', error)
      return {
        results: {},
        total_count: 0,
        query: params.q,
        search_type: params.search_type || 'keyword_search',
        scope: params.scope ? params.scope.split(',') : ['videos', 'documents', 'courses', 'keywords']
      }
    }
  }

  // 获取所有课程作为建议
  async getAllCoursesForSuggestions(): Promise<SearchSuggestion[]> {
    try {
      // 使用学生课程接口获取课程列表
      const response = await apiClient.get('/api/students/courses', { 
        params: { 
          page: 1, 
          pageSize: 20 // 限制数量，避免过多 
        } 
      })
      
      if (response.data && response.data.code === 200 && response.data.data && response.data.data.list) {
        const courses = response.data.data.list
        const suggestions: SearchSuggestion[] = []
        
        courses.forEach((course: any) => {
          const text = course.name || `课程-${course.id}`
          if (text && text.trim()) {
            // 解析课程描述以处理可能的JSON格式
            const descObj = parseCourseDescription(course.description)
            
            suggestions.push({
              text: text.trim(),
              type: 'course',
              id: course.id,
              // 添加解析后的描述信息（如果需要的话）
              description: descObj.description,
              category: descObj.category.length > 0 ? descObj.category[0] : undefined
            })
          }
        })
        
        return suggestions
      }
      
      return []
    } catch (error) {
      console.error('获取课程列表失败:', error)
      return []
    }
  }

  async getSuggestions(params: SuggestionsParams): Promise<SearchSuggestion[]> {
    try {
      // 使用统一的全局搜索接口获取建议
      const searchParams: GlobalSearchParams = {
        q: params.q,
        limit: params.limit || 10,
        scope: 'videos,documents,courses,keywords'
      }
      const response = await this.search(searchParams)
      
      // 检查响应是否有效
      if (!response || !response.results) {
        return []
      }
      
      // 将搜索结果转换为建议格式
      const suggestions: SearchSuggestion[] = []
      
      // 添加课程建议（优先级1）
      if (response.results.courses && Array.isArray(response.results.courses)) {
        response.results.courses.forEach(course => {
          const text = course.name || `课程-${course.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'course',
              id: course.id
            })
          }
        })
      }

      // 添加视频建议（优先级2）
      if (response.results.videos && Array.isArray(response.results.videos)) {
        response.results.videos.forEach(video => {
          const text = video.title || `视频-${video.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'video' as any,
              id: video.id
            })
          }
        })
      }

      // 添加文档建议（优先级3）
      if (response.results.documents && Array.isArray(response.results.documents)) {
        response.results.documents.forEach(document => {
          const text = document.title || `文档-${document.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'document' as any,
              id: document.id
            })
          }
        })
      }

      // 添加知识点建议（优先级4）
      if (response.results.keywords && Array.isArray(response.results.keywords)) {
        response.results.keywords.forEach(keyword => {
          const text = keyword.name || `知识点-${keyword.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'keyword',
              category: keyword.category,
              id: keyword.id
            })
          }
        })
      }
      
      return suggestions.slice(0, params.limit || 10)
    } catch (error) {
      console.error('获取搜索建议失败:', error)
      return []
    }
  }

  async searchVideos(params: { query: string; page?: number; pageSize?: number }): Promise<GlobalSearchResponse> {
    try {
      const searchParams = { q: params.query, scope: 'videos', page: params.page, page_size: params.pageSize }
      const response = await apiClient.get('/api/global-search', { params: searchParams })
      if (response.data && response.data.code === 200 && response.data.data) {
        return response.data.data
      }
      return { results: { videos: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['videos'] }
    } catch (error) {
      console.error('搜索视频失败:', error)
      return { results: { videos: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['videos'] }
    }
  }

  async searchDocuments(params: { query: string; page?: number; pageSize?: number }): Promise<GlobalSearchResponse> {
    try {
      const searchParams = { q: params.query, scope: 'documents', page: params.page, page_size: params.pageSize }
      const response = await apiClient.get('/api/global-search', { params: searchParams })
      if (response.data && response.data.code === 200 && response.data.data) {
        return response.data.data
      }
      return { results: { documents: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['documents'] }
    } catch (error) {
      console.error('搜索文档失败:', error)
      return { results: { documents: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['documents'] }
    }
  }

  async searchCourses(params: { query: string; page?: number; pageSize?: number }): Promise<GlobalSearchResponse> {
    try {
      const searchParams = { q: params.query, scope: 'courses', page: params.page, page_size: params.pageSize }
      const response = await apiClient.get('/api/global-search', { params: searchParams })
      if (response.data && response.data.code === 200 && response.data.data) {
        return response.data.data
      }
      return { results: { courses: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['courses'] }
    } catch (error) {
      console.error('搜索课程失败:', error)
      return { results: { courses: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['courses'] }
    }
  }

  async searchKeywords(params: { query: string; page?: number; pageSize?: number }): Promise<GlobalSearchResponse> {
    try {
      const searchParams = { q: params.query, scope: 'keywords', page: params.page, page_size: params.pageSize }
      const response = await apiClient.get('/api/global-search', { params: searchParams })
      if (response.data && response.data.code === 200 && response.data.data) {
        return response.data.data
      }
      return { results: { keywords: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['keywords'] }
    } catch (error) {
      console.error('搜索知识点失败:', error)
      return { results: { keywords: [] }, total_count: 0, query: params.query, search_type: 'keyword_search', scope: ['keywords'] }
    }
  }

  async searchForSuggestions(query: string, courseId?: string): Promise<SearchSuggestion[]> {
    try {
      // 如果查询为空，返回所有课程列表
      if (!query || query.trim() === '') {
        return await this.getAllCoursesForSuggestions()
      }

      const searchParams: GlobalSearchParams = {
        q: query,
        limit: 10,
        scope: 'videos,documents,courses,keywords'
      }
      if (courseId) {
        searchParams.course_id = courseId
      }
      
      // 直接调用 API
      const apiResponse = await apiClient.get('/api/global-search', { params: searchParams })
      
      // 检查响应格式 - 后端返回格式: {code: 200, data: {...}, message: "..."}
      if (!apiResponse || !apiResponse.data || apiResponse.data.code !== 200 || !apiResponse.data.data) {
        console.warn('搜索建议响应格式异常:', apiResponse)
        return []
      }
      
      const response = apiResponse.data.data
      
      // 检查响应是否有效
      if (!response || !response.results) {
        return []
      }
      
      // 将搜索结果转换为建议格式
      const suggestions: SearchSuggestion[] = []
      
      // 添加课程建议（优先级1）
      if (response.results.courses && Array.isArray(response.results.courses)) {
        response.results.courses.forEach((course: GlobalSearchResult) => {
          const text = course.name || `课程-${course.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'course',
              id: course.id
            })
          }
        })
      }
      
      // 添加视频建议（优先级2）
      if (response.results.videos && Array.isArray(response.results.videos)) {
        response.results.videos.forEach((video: GlobalSearchResult) => {
          const text = video.title || `视频-${video.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'video' as any,
              id: video.id
            })
          }
        })
      }
      
      // 添加文档建议（优先级3）
      if (response.results.documents && Array.isArray(response.results.documents)) {
        response.results.documents.forEach((document: GlobalSearchResult) => {
          const text = document.title || `文档-${document.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'document' as any,
              id: document.id
            })
          }
        })
      }
      
      // 添加知识点建议（优先级4）
      if (response.results.keywords && Array.isArray(response.results.keywords)) {
        response.results.keywords.forEach((keyword: GlobalSearchResult) => {
          const text = keyword.name || `知识点-${keyword.id}`
          if (text && text.trim()) {
            suggestions.push({
              text: text.trim(),
              type: 'keyword',
              category: keyword.category,
              id: keyword.id
            })
          }
        })
      }
      
      return suggestions.slice(0, 10)
    } catch (error) {
      console.error('搜索建议失败:', error)
      return []
    }
  }
}

export const globalSearchService = new GlobalSearchService()
export default globalSearchService