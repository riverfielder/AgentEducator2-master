import apiClient, { uploadClient } from './index';
import type { AxiosRequestConfig } from 'axios';

interface UploadConfig extends AxiosRequestConfig {
  timeout?: number;
  headers?: Record<string, string>;
}

export default {
  // 获取视频列表
  getVideos(params: any) {
    return apiClient.get('/api/videos', { params });
  },

  // 获取视频详情
  getVideoDetail(videoId: string | number) {
    return apiClient.get(`/api/videos/${videoId}`);
  },// 上传视频
  uploadVideo(formData: FormData, config: UploadConfig = {}) {
    return uploadClient.post('/api/uploads/course_video', formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(config.headers || {})
      },
      timeout: config.timeout
    });
  },
  // 更新视频信息
  updateVideo(videoId: string | number, data: any) {
    return apiClient.put(`/api/videos/update/${videoId}`, data);
  },

  // 删除视频 - 已使用DELETE方法
  deleteVideo(videoId: string | number) {
    return apiClient.delete(`/api/videos/${videoId}`);
  },

  // 搜索视频
  searchVideos(params: any) {
    return apiClient.get('/api/videos/search', { params });
  },

  // 更新视频观看进度
  updateProgress(videoId: string | number, data: any) {
    return apiClient.post(`/api/videos/${videoId}/progress`, data);
  },

  // 获取视频评论列表
  getVideoComments(videoId: string | number, params: any = {}) {
    return apiClient.get(`/api/videos/${videoId}/comments`, { params });
  },

  // 添加视频评论
  addVideoComment(videoId: string | number, data: any) {
    return apiClient.post(`/api/videos/${videoId}/comments`, data);
  },

  // 点赞/取消点赞评论
  likeComment(commentId: string | number, data: any) {
    return apiClient.post(`/api/videos/comments/${commentId}/like`, data);
  },
  
  // 处理视频 - 触发视频分析处理任务
  processVideo(videoId: string | number) {
    return apiClient.post(`/api/videos/${videoId}/process`);
  },

  // 处理视频（带设置参数）
  processVideoWithSettings(videoId: string | number, data: any) {
    return apiClient.post(`/api/videos/${videoId}/process`, data);
  },

  // 批量获取视频处理状态
  getBatchProcessingStatus(videoIds: string[]) {
    return apiClient.post('/api/videos/batch/processing-status', {
      video_ids: videoIds
    });
  },

  // 删除评论
  deleteComment(commentId: string | number) {
    return apiClient.delete(`/api/videos/comments/${commentId}`);
  }
};
