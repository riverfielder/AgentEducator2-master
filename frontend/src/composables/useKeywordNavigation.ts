import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import knowledgeMapService from '@/api/knowledgeMapService'
import type { KeywordData, VideoKeywordData, RelatedVideo } from '@/types/keyword'
import { jwtDecode } from 'jwt-decode'
import { parseJwt } from '@/utils/jwt'

/**
 * 关键词导航相关的composable
 */
export function useKeywordNavigation() {
  const router = useRouter()
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 判断用户是否为教师
  const isTeacher = computed(() => {
    const token = localStorage.getItem('wendao_token')
    let role = ''
    if (token) {
      try {
        const payload: any = jwtDecode(token)
        role = payload.role || ''
      } catch (e) {
        const payload = parseJwt(token)
        role = payload?.role || ''
      }
    } else {
      role = localStorage.getItem('wendao_user_role') || ''
    }
    return role === 'teacher' || role === 'admin'
  })

  /**
   * 导航到知识点详情页面
   */
  const navigateToKeywordDetail = (keyword: KeywordData | VideoKeywordData) => {
    if (!keyword?.id) {
      console.error('关键词ID不存在')
      return
    }
    
    // 根据用户角色跳转到不同的详情页面
    if (isTeacher.value) {
      router.push({
        name: 'TeacherKnowledgeDetail',
        params: { id: keyword.id }
      })
    } else {
      router.push({
        name: 'KnowledgePointDetail',
        params: { id: keyword.id }
      })
    }
  }

  /**
   * 处理关键词点击事件（用于DocumentSummary）
   */
  const handleKeywordClick = (keyword: KeywordData) => {
    navigateToKeywordDetail(keyword)
  }

  /**
   * 处理视频关键词点击事件（用于VideoSummary）
   * 获取相关视频并返回关键词数据
   */
  const handleVideoKeywordClick = async (keyword: KeywordData): Promise<VideoKeywordData | null> => {
    if (!keyword?.id) {
      console.error('关键词ID不存在')
      return null
    }

    loading.value = true
    error.value = null

    try {
      const response = await knowledgeMapService.getKeywordRelatedVideos(keyword.id)
      
      if (response.data?.code === 200) {
        const { keyword: keywordInfo, videos } = response.data.data
        
        // 转换视频数据格式
        const relatedVideos: RelatedVideo[] = videos.map((video: any) => ({
          id: video.id,
          title: video.title,
          courseName: video.course?.name || '未知课程',
          viewCount: video.view_count || 0,
          duration: video.duration || 0
        }))

        return {
          ...keywordInfo,
          relatedVideos
        }
      } else {
        error.value = response.data?.msg || '获取相关视频失败'
        return null
      }
    } catch (err: any) {
      error.value = err.message || '网络错误'
      console.error('获取关键词相关视频失败:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 右键点击跳转到知识点详情页面
   */
  const goToKnowledgePointDetail = (keyword: KeywordData | VideoKeywordData) => {
    navigateToKeywordDetail(keyword)
  }

  return {
    loading,
    error,
    navigateToKeywordDetail,
    handleKeywordClick,
    handleVideoKeywordClick,
    goToKnowledgePointDetail
  }
}

/**
 * 关键词显示相关的composable
 */
export function useKeywordDisplay() {
  /**
   * 格式化关键词文本
   */
  const formatKeywordText = (keyword: KeywordData | VideoKeywordData): string => {
    return keyword.name || '未知关键词'
  }

  /**
   * 获取关键词提示文本
   */
  const getKeywordTooltip = (context: 'document' | 'video' = 'document'): string => {
    if (context === 'video') {
      return '左键：查看相关视频\n右键：查看掌握情况'
    }
    return '点击查看掌握情况'
  }

  /**
   * 获取关键词芯片的key值
   */
  const getKeywordChipKey = (keyword: KeywordData | VideoKeywordData, index: number): string => {
    return keyword.id || `keyword-${index}`
  }

  return {
    formatKeywordText,
    getKeywordTooltip,
    getKeywordChipKey
  }
}