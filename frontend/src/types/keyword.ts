/**
 * 关键词相关的TypeScript类型定义
 */

// 文档摘要数据接口
export interface DocumentSummaryData {
  id?: string;
  document_id?: string;
  whole_summary?: string;
  main_points?: string;
  keywords?: string;
  sections?: Array<{
    title?: string;
    content: string;
    segment_count?: number;
  }>;
  created_at?: string;
  updated_at?: string;
}

// 基础关键词接口
export interface KeywordData {
  id: string
  name: string
  description?: string
  category?: string
  weight?: number
  document_keyword_id?: string
}

// 视频摘要中的关键词（包含相关视频信息）
export interface VideoKeywordData extends KeywordData {
  relatedVideos?: RelatedVideo[]
}

// 相关视频信息
export interface RelatedVideo {
  id: string
  title: string
  courseName: string
  viewCount: number
  duration: number
}

// 关键词搜索结果
export interface KeywordSearchResult {
  id: string
  name: string
  description: string
  category: string
}

// 文档关键词响应
export interface DocumentKeywordsResponse {
  code: number
  msg: string
  data: {
    keywords: KeywordData[]
  }
}

// 关键词搜索响应
export interface KeywordSearchResponse {
  code: number
  msg: string
  data: KeywordSearchResult[]
}

// 关键词相关视频响应
export interface KeywordRelatedVideosResponse {
  code: number
  msg: string
  data: {
    keyword: KeywordData
    videos: {
      id: string
      title: string
      view_count: number
      duration: number
      course: {
        name: string
      }
    }[]
  }
}

// 关键词点击事件参数
export interface KeywordClickEvent {
  keyword: KeywordData
  action: 'navigate' | 'context-menu'
}

// 路由跳转参数
export interface NavigationParams {
  name: string
  params: {
    id: string
  }
}