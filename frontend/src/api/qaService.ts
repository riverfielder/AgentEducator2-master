import apiClient from './index';

/*interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
  sources?: any[];
}

interface ChatSession {
  id: string;
  title?: string;
  created_at: string;
  messages: ChatMessage[];
}
  */

// 接口定义
interface AskQuestionData {
  query: string;
  videoIds?: string[];     // 新：视频ID数组
  courseIds?: string[];    // 新：课程ID数组
  documentIds?: string[];  // 新：文档ID数组
  sessionId?: string;
  isNewSession?: boolean;
  history?: any[];
}

interface AgentConfig {
  agent_mode_enabled: boolean;
  max_iterations: number;
  handle_parsing_errors: boolean;
  verbose: boolean;
  tool_configs: any;
  cache_configs: any;
}

interface AgentStats {
  agent_mode_enabled: boolean;
  max_iterations: number;
  verbose: boolean;
}

export default {
  // 常规问答请求
  askQuestion(data: any) {
    return apiClient.post('/api/qa/ask', data);
  },
    // 流式问答请求 - POST，支持多资源ID数组
  askQuestionStream({ query, videoIds, courseIds, documentIds, sessionId, isNewSession, history }: AskQuestionData) {
    const body = {
      query,
      videoIds,
      courseIds, 
      documentIds,
      sessionId,
      isNewSession,
      history
    };
    return fetch(`${apiClient.defaults.baseURL}/api/qa/ask-stream`, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('wendao_token')}`
      },
      body: JSON.stringify(body)
    });
  },
  

  
  // 获取视频摘要
  getVideoSummary(videoId: string) {
    return apiClient.get(`/api/summaries/video/${videoId}`);
  },
  
  // 生成视频摘要
  generateSummary(data: any) {
    return apiClient.post('/api/summaries/generate', data);
  },
  // Agent配置管理
  getAgentConfig() {
    return apiClient.get('/api/qa/agent-config');
  },

  updateAgentConfig(config: Partial<AgentConfig>) {
    return apiClient.post('/api/qa/agent-config', config);
  },

  // Agent统计信息
  getAgentStats() {
    return apiClient.get('/api/qa/agent-stats');
  },
/*
  // 获取历史对话列表
  getChatHistoryList(): Promise<{ history: ChatSession[] }> {
    return apiClient.get('/api/qa/sessions');
  },

  // 获取历史对话内容
  getChatHistory(sessionId: string): Promise<ChatSession> {
    return apiClient.get(`/api/qa/sessions/${sessionId}/messages`);
  }
    */
};
