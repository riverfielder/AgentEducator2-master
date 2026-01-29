import apiClient, { uploadClient } from './index';
import request from './index';

export default {
  uploadImage(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    return uploadClient.post('/api/uploads/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
  uploadVideo(
    file: File, 
    courseId: string, 
    title?: string, 
    description?: string, 
    jsonSub?: File, 
    processingSteps?: string[] | null,
    previewMode?: boolean,
    onProgress?: (progressEvent: any) => void, 
    signal?: AbortSignal
  ) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('courseId', courseId); // 添加课程ID
    formData.append('title', title || file.name); // 如果没有提供标题，使用文件名
    
    if (description) {
      formData.append('description', description); // 可选的描述
    }
    
    if (jsonSub) {
      formData.append('json_sub', jsonSub); // 可选的字幕JSON文件
    }
    
    // 添加处理步骤参数
    if (processingSteps && processingSteps.length > 0) {
      formData.append('processingSteps', JSON.stringify(processingSteps));
    }
    
    // 添加预览模式参数
    if (previewMode !== undefined) {
      formData.append('previewMode', previewMode.toString());
    }
    
    return uploadClient.post('/api/uploads/course_video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress,
      signal
    });
  },

  uploadDocument(file: File, courseId: number, onProgress?: (progressEvent: any) => void) {
    if (!courseId) {
        throw new Error('课程ID不能为空');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('courseId', courseId.toString());
    
    return uploadClient.post('/api/uploads/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    });
  },

  uploadAvatar(formData: FormData) {
    return uploadClient.post('/api/uploads/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * 获取课程的文档列表
   * @param courseId 课程ID
   */
  getDocuments(courseId: string | number) {
    return uploadClient.get('/api/uploads/document', {
      params: { courseId }
    });
  },

  deleteDocument(documentId: string | number) {
    return request({
      url: `/api/upload/document/${documentId}`,
      method: 'delete'
    });
  },

 

  /**
   * 上传文档到指定章节
   * @param file 文件对象
   * @param courseId 课程ID
   * @param chapterId 章节ID
   */
  uploadDocumentToChapter(file: File, courseId: string, chapterId: number) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('courseId', courseId);
    formData.append('chapterId', String(chapterId));
    
    return uploadClient.post('/api/uploads/document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};
