import apiClient from './index';

export default {
  /**
   * 获取视频总结
   * @param videoId 视频ID
   */
  getVideoSummary(videoId: String) {
    return apiClient.get(`/api/summaries/video/${videoId}`);
  },

  /**
   * 触发生成视频总结
   * @param params 包含videoId和是否强制重新生成的参数
   */
  generateSummary(params: { videoId: String; forceRegenerate?: boolean }) {
    return apiClient.post('/api/summaries/generate', params);
  },

  /**
   * 提问视频总结相关问题
   * @param params 提问参数
   */
  askQuestion(params: { videoId: String; sectionIndex?: number; question: string }) {
    return apiClient.post('/api/summaries/question', params);
  }
};
