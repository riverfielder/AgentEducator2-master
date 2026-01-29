import apiClient, { uploadClient } from "./index";

export interface PersonalizedRecommendation {
  user_mastery_overview?: any
  highest_mastery_keywords?: any[]
  learning_path_recommendations?: Array<{
    source_keyword: {
      id: string
      name: string
      mastery_level: number
    }
    recommended_keyword: {
      id: number
      name: string
      category?: string
      current_mastery?: number
    }
    resources: {
      videos: Array<any>
      documents: Array<any>
      questions: Array<any>
    }
    recommendation_reason: string
    priority_score: number
  }>
  total_recommendations?: number
  // 支持 next_steps 格式
  next_steps?: Array<{
    from_keyword: string
    to_keyword: string
    reason: string
    learning_benefits: string[]
    priority_score: number
    resources_summary: {
      videos: number
      documents: number
      questions: number
    }
    recommended_keyword: {
      id: number
      name: string
      category?: string
      current_mastery?: number
    }
    resources: {
      videos: Array<any>
      documents: Array<any>
      questions: Array<any>
    }
  }>
  user_mastery_summary?: {
    total_keywords: number
    mastered_keywords: number
    average_mastery: number
  }
  // 添加缓存信息
  cache_info?: {
    is_from_cache: boolean
    created_at: string
    expires_in_seconds: number
    cache_key?: string
  }
}

export interface LearningPath {
  path: Array<{
    keyword_id: number
    keyword: string
    mastery_level: number
    recommended_resources: {
      videos: number
      documents: number
      questions: number
    }
  }>
  total_estimated_hours: number
  difficulty_level: string
  description: string
}

export interface StudyPlan {
  plan: Array<{
    week: number
    topics: string[]
    estimated_hours: number
    resources: {
      videos: Array<{ id: number; title: string }>
      documents: Array<{ id: number; title: string }>
      questions: Array<{ id: number; title: string }>
    }
  }>
  total_weeks: number
  total_hours: number
  difficulty_assessment: string
  learning_objectives: string[]
}

class PersonalizedRecommendationService {
  /**
   * 获取个性化学习路径推荐
   */
  async getLearningPath(): Promise<LearningPath> {
    const response = await apiClient.get('/api/personalized-recommendation/learning-path')
    return response.data.data
  }

  /**
   * 获取下一步学习建议
   */
  async getNextSteps(forceRefresh: boolean = false): Promise<PersonalizedRecommendation> {
    const params = forceRefresh ? { force_refresh: 'true' } : {}
    const response = await uploadClient.get('/api/personalized-recommendation/next-steps', { params })
    return response.data.data
  }

  /**
   * 获取特定知识点的个性化推荐
   */
  async getKnowledgePointRecommendation(keywordId: number): Promise<any> {
    const response = await apiClient.get(`/api/personalized-recommendation/knowledge-point/${keywordId}`)
    return response.data.data
  }

  /**
   * 获取特定知识点的学习资源推荐
   */
  async getLearningResources(keywordId: number): Promise<any> {
    const response = await apiClient.get(`/api/personalized-recommendation/learning-resources/${keywordId}`)
    return response.data.data
  }

  /**
   * 生成个性化学习计划
   */
  async getStudyPlan(): Promise<StudyPlan> {
    const response = await apiClient.get('/api/personalized-recommendation/study-plan')
    return response.data.data
  }
}

export const personalizedRecommendationService = new PersonalizedRecommendationService()
export default personalizedRecommendationService