import request from './index'

export interface KnowledgeNode {
  id: string;
  name: string;
  type: string;
  description?: string;
  prerequisites?: string[];
  children?: KnowledgeNode[];
}

export interface GraphNode {
  id: string;
  name: string;
  symbolSize: number;
  category: number;
  description?: string;
  prerequisites?: string[];
  course_count?: number;
  video_count?: number;
  relatedVideos?: Array<{
    id: string;
    title: string;
    courseName: string;
    courseId: string;
    viewCount: number;
    duration: number;
    type: 'video';
  }>;
  relatedDocuments?: Array<{
    id: string;
    title: string;
    courseName: string;
    courseId: string;
    fileType: string;
    fileSize: number;
    uploadTime: string;
    type: 'document';
  }>;
  allResources?: Array<{
    id: string;
    title: string;
    courseName: string;
    courseId: string;
    type: 'video' | 'document';
    weight: number;
    viewCount?: number;
    duration?: number;
    coverUrl?: string;
    fileType?: string;
    fileSize?: number;
    uploadTime?: string;
  }>;
}

export interface LearningPath {
  id: string;
  name: string;
  description: string;
  steps: {
    id: string;
    name: string;
    courseId?: string;
    status: 'completed' | 'in-progress' | 'not-started';
    order: number;
  }[];
}

export interface SkillNode {
  id: string;
  name: string;
  level: number;
  progress: number;
  children?: SkillNode[];
}

// 知识点详情相关API
const getKnowledgePointDetail = async (keywordId: string) => {
  return await request.get(`/api/knowledge-points/${keywordId}`);
};

const getKnowledgePointChildren = async (keywordId: string) => {
  return await request.get(`/api/knowledge-points/${keywordId}/children`);
};

const getKnowledgePointMastery = async (keywordId: string, recalculate: boolean = false) => {
  return await request.get(`/api/knowledge-points/${keywordId}/mastery`, {
    params: { recalculate }
  });
};

// 获取特定学生的知识点掌握度
const getStudentKnowledgePointMastery = async (keywordId: string, studentId: string, recalculate: boolean = false) => {
  return await request.get(`/api/knowledge-points/${keywordId}/student-mastery/${studentId}`, {
    params: { recalculate }
  });
};

const getKnowledgePointLearningPath = async (keywordId: string) => {
  return await request.get(`/api/knowledge-points/${keywordId}/learning-path`);
};

const getMasteryOverview = async () => {
  return await request.get('/api/knowledge-points/mastery/overview');
};

const batchCalculateMastery = async (data: {
  keyword_ids?: string[];
  force_recalculate?: boolean;
}) => {
  return await request.post('/api/knowledge-points/mastery/batch-calculate', data);
};

const updateDocumentProgress = async (data: {
  document_id: string;
  progress: number;
  last_position?: number;
  reading_time?: number;
  completed?: boolean;
}) => {
  return await request.post('/api/knowledge-points/document-progress', data);
};

const getUserDocumentProgress = async (userId: string) => {
  return await request.get(`/api/knowledge-points/document-progress/${userId}`);
};

// 批量获取课程学生的知识点掌握度
const getCourseStudentsKnowledgePointMastery = async (keywordId: string, courseId?: string, recalculate: boolean = false) => {
  return await request.get(`/api/knowledge-points/${keywordId}/course-students-mastery`, {
    params: { 
      course_id: courseId,
      recalculate 
    }
  });
};

const knowledgeMapService = {
  // 获取课程知识图谱
  getKnowledgeMap: (courseId: string) => {
    return request({
      url: `/api/knowledge-map/${courseId}`,
      method: 'get'
    })
  },

  // 获取推荐学习路径
  getLearningPath: (userId: string) => {
    return request({
      url: `/api/learning-path/${userId}`,
      method: 'get'
    })
  },

  // 获取个人能力图谱
  getSkillMap: (userId: string) => {
    return request({
      url: `/api/skill-map/${userId}`,
      method: 'get'
    })
  },

  // 更新学习进度
  updateLearningProgress: (data: { userId: string; nodeId: string; completed: boolean }) => {
    return request({
      url: '/api/learning-progress',
      method: 'post',
      data
    })
  },  // 生成知识图谱
  generateKnowledgeGraph: (data: { courseId: string; forceRegenerate?: boolean; incremental?: boolean }) => {
    return request({
      url: '/api/knowledge-graph/generate',
      method: 'post',
      data
    })
  },

  // 获取课程知识图谱数据
  getCourseKnowledgeGraph: (courseId: string) => {
    return request({
      url: `/api/knowledge-graph/course/${courseId}`,
      method: 'get'
    })
  },

  // 获取平台知识图谱数据
  getPlatformKnowledgeGraph: () => {
    return request({
      url: '/api/knowledge-graph/platform',
      method: 'get'
    })
  },

  // 获取知识点相关视频
  getKeywordVideos: (keywordId: string) => {
    return request({
      url: `/api/knowledge-graph/keyword/${keywordId}/videos`,
      method: 'get'
    })
  },

  // 获取知识图谱生成任务状态
  getTaskStatus: (taskId: string) => {
    return request({
      url: `/api/knowledge-graph/task/${taskId}`,
      method: 'get'
    })
  },

  // 获取知识点相关视频
  getKeywordRelatedVideos: (keywordId: string) => {
    return request({
      url: `/api/knowledge-graph/keyword/${keywordId}/videos`,
      method: 'get'
    })
  },

  // 获取知识点相关文档
  getKeywordRelatedDocuments: (keywordId: string) => {
    return request({
      url: `/api/knowledge-graph/keyword/${keywordId}/documents`,
      method: 'get'
    })
  },

  // 获取知识点相关资源（视频+文档）
  getKeywordRelatedResources: (keywordId: string) => {
    return request({
      url: `/api/knowledge-graph/keyword/${keywordId}/resources`,
      method: 'get'
    })
  },

  // 创建知识点
  async createKeyword(data: { name: string; category: string; description?: string }) {
    try {
      const response = await request({
        url: '/api/knowledge-graph/keywords',
        method: 'post',
        data
      })
      // 只返回后端 data 字段，便于前端直接追加新节点
      if (response.data && response.data.code === 200) {
        return response.data.data
      } else {
        // 其它业务错误
        throw new Error(response.data?.msg || '创建知识点失败')
      }
    } catch (error: any) {
      // 409 冲突友好提示
      if (error?.response?.data?.code === 409) {
        throw new Error(error.response.data.msg || '知识点名称已存在')
      }
      throw new Error(error?.response?.data?.msg || error.message || '创建知识点失败')
    }
  },

  // 更新知识点
  updateKeyword: (id: string, data: { 
    name: string; 
    category: string; 
    description?: string;
    courseIds?: string[];
    videoIds?: string[];
    documentIds?: string[];
  }) => {
    // 确保所有字段都经过处理
    const payload = {
      name: data.name.trim(),
      category: data.category.trim(),
      description: data.description?.trim() || '',
      courseIds: data.courseIds || [],
      videoIds: data.videoIds || [],
      documentIds: data.documentIds || []
    };
    return request({
      url: `/api/knowledge-graph/keywords/${id}`,
      method: 'put',
      data: payload
    })
  },

  // 删除知识点
  deleteKeyword: (id: string, params?: { courseId?: string; force?: boolean }) => {
  return request({
    url: `/api/knowledge-graph/keywords/${id}`,
    method: 'delete',
    params
  })
},

  // 文档-关键词关联管理
  // 为文档添加知识点
  addDocumentKeyword: (data: { documentId: string; keywordId: string; weight?: number }) => {
    return request({
      url: '/api/knowledge-graph/document-keywords',
      method: 'post',
      data
    })
  },

  // 更新文档知识点权重
  updateDocumentKeyword: (documentKeywordId: string, data: { weight: number }) => {
    return request({
      url: `/api/knowledge-graph/document-keywords/${documentKeywordId}`,
      method: 'put',
      data
    })
  },

  // 删除文档知识点关联
  deleteDocumentKeyword: (documentKeywordId: string) => {
    return request({
      url: `/api/knowledge-graph/document-keywords/${documentKeywordId}`,
      method: 'delete'
    })
  },

  // 获取文档的所有知识点
  getDocumentKeywords: (documentId: string) => {
    return request({
      url: `/api/knowledge-graph/document/${documentId}/keywords`,
      method: 'get'
    })
  },

  // 创建知识点关系
  createRelation: (data: { sourceKeywordId: string; targetKeywordId: string; relationType: string; strength: number; description?: string }) => {
    return request({
      url: '/api/knowledge-graph/relations',
      method: 'post',
      data
    })
  },

  // 删除知识点关系
  deleteRelation: (relationId: string) => {
    return request({
      url: `/api/knowledge-graph/relations/${relationId}`,
      method: 'delete'
    })
  },

  // 获取两个知识点之间的关系
  getRelationsBetweenKeywords: (sourceKeywordId: string, targetKeywordId: string) => {
    return request({
      url: '/api/knowledge-graph/relations/list',
      method: 'get',
      params: {
        sourceKeywordId,
        targetKeywordId
      }
    })
  },

  // 获取课程视频处理状态
  getCourseVideosProcessingStatus: (courseId: string) => {
    return request({
      url: `/api/knowledge-graph/course/${courseId}/videos-status`,
      method: 'get'
    })
  },

  // 搜索关键词
  searchKeywords: (keyword: string) => {
    return request({
      url: `/api/knowledge-graph/search-keywords`,
      method: 'get',
      params: { keyword }
    })
  },

  // 知识点详情相关
  getKnowledgePointDetail,
  getKnowledgePointChildren,
  getKnowledgePointMastery,
  getKnowledgePointLearningPath,
  getMasteryOverview,
  batchCalculateMastery,
  updateDocumentProgress,
  getUserDocumentProgress,
  getStudentKnowledgePointMastery,
  getCourseStudentsKnowledgePointMastery
}

export default knowledgeMapService

// 导出知识点服务（为了向后兼容）
export const knowledgePointService = knowledgeMapService;