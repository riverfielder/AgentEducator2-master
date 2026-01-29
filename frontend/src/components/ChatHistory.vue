<template>
  <v-dialog v-model="dialog" width="800">
    <template v-slot:activator="{ props }">
      <v-btn v-bind="props" variant="outlined" class="ml-2" prepend-icon="mdi-history">
        历史对话
      </v-btn>
    </template>

    <v-card>
      <v-card-title class="text-h5">
        历史对话记录
        <v-spacer></v-spacer>
        <v-btn icon @click="dialog = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-row class="ma-0">
        <!-- 左侧会话列表 -->
        <v-col cols="4" class="pa-0">
          <v-list lines="two" density="compact" class="history-list">
            <v-list-subheader>所有对话</v-list-subheader>
            
            <div v-if="loading" class="d-flex justify-center align-center py-4">
              <v-progress-circular indeterminate></v-progress-circular>
            </div>
            
            <div v-else-if="sessions.length === 0" class="text-center pa-4 text-grey">
              暂无历史对话
            </div>
            
            <v-list-item
              v-for="session in sessions"
              :key="session.id"
              :active="session.id === selectedSessionId"
              @click="selectSession(session.id)"
              class="session-item"
            >
              <v-list-item-title>{{ session.title }}</v-list-item-title>
              <v-list-item-subtitle>
                {{ formatDate(session.create_time) }}
                <v-chip size="x-small" class="ml-2">{{ session.message_count }}条</v-chip>
              </v-list-item-subtitle>
              
              <template v-slot:append>
                <v-btn
                  icon="mdi-delete"
                  variant="text"
                  density="compact"
                  color="error"
                  @click.stop="confirmDelete(session.id)"
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>
        </v-col>

        <!-- 右侧会话内容 -->
        <v-col cols="8" class="pa-0 border-left">
          <div v-if="!selectedSessionId" class="d-flex justify-center align-center fill-height text-grey">
            请选择一个会话查看详情
          </div>
          
          <div v-else>
            <v-card-title class="py-2 px-4 d-flex align-center">
              <span>{{ selectedSession?.title }}</span>
              <v-spacer></v-spacer>
              <v-btn
                v-if="selectedSession"
                variant="text"
                prepend-icon="mdi-play"
                size="small"
                color="primary"
                @click="continueChat"
              >
                继续对话
              </v-btn>
            </v-card-title>
            
            <v-divider></v-divider>
            
            <div v-if="messagesLoading" class="d-flex justify-center align-center py-4">
              <v-progress-circular indeterminate></v-progress-circular>
            </div>
            
            <v-card-text v-else class="chat-messages pb-4">
              <div 
                v-for="(message, index) in selectedSessionMessages"
                :key="index"
                class="message-container mb-4"
                :class="message.role === 'user' ? 'user-message' : 'ai-message'"
              >
                <div class="message-content">
                  <div class="message-header">
                    <strong>{{ message.role === 'user' ? '我' : 'AI' }}</strong>
                    <span class="text-caption ml-2">{{ formatDateTime(message.create_time) }}</span>
                    <span v-if="message.time_point" class="time-point ml-2">
                      <v-chip size="x-small" @click="jumpToVideoTime(message.time_point)">
                        {{ formatVideoTime(message.time_point) }}
                      </v-chip>
                    </span>
                  </div>
                  <div class="message-text" v-html="formatContent(message.content)"></div>
                </div>
              </div>
            </v-card-text>
          </div>
        </v-col>
      </v-row>
    </v-card>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" width="400">
      <v-card>
        <v-card-title class="text-h6">
          确认删除
        </v-card-title>
        <v-card-text>
          确定要删除这个对话吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">取消</v-btn>
          <v-btn variant="flat" color="error" @click="deleteSession">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import chatHistoryService from '../api/chatHistoryService';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import type { PropType } from 'vue';

const props = defineProps({
  videoId: {
    type: String as PropType<string>,
    required: true
  }
});

const emit = defineEmits(['continue-chat']);

// 状态变量
const dialog = ref(false);
const loading = ref(false);
const messagesLoading = ref(false);
const sessions = ref<any[]>([]);
const selectedSessionId = ref<string | null>(null);
const selectedSession = ref<any>(null);
const selectedSessionMessages = ref<any[]>([]);
const deleteDialog = ref(false);
const sessionToDelete = ref<string | null>(null);

// 加载历史会话
const loadSessions = async () => {
  loading.value = true;
  try {
    const response = await chatHistoryService.getChatSessionsList({ videoId: props.videoId });
    if (response.data.code === 200) {
      sessions.value = response.data.data;
    } else {
      console.error('加载历史会话失败:', response.data.message);
    }
  } catch (error) {
    console.error('加载历史会话出错:', error);
  } finally {
    loading.value = false;
  }
};

// 选择会话
const selectSession = async (sessionId: string) => {
  if (selectedSessionId.value === sessionId) return;
  
  selectedSessionId.value = sessionId;
  messagesLoading.value = true;
  
  try {
    const response = await chatHistoryService.getChatSessionDetail(sessionId);
    if (response.data.code === 200) {
      selectedSession.value = response.data.data;
      selectedSessionMessages.value = response.data.data.messages || [];
    } else {
      console.error('加载会话详情失败:', response.data.message);
    }
  } catch (error) {
    console.error('加载会话详情出错:', error);
  } finally {
    messagesLoading.value = false;
  }
};

// 确认删除对话
const confirmDelete = (sessionId: string) => {
  sessionToDelete.value = sessionId;
  deleteDialog.value = true;
};

// 删除会话
const deleteSession = async () => {
  if (!sessionToDelete.value) return;
  
  try {
    const response = await chatHistoryService.deleteChatSession(sessionToDelete.value);
    if (response.data.code === 200) {
      // 如果删除的是当前选中的会话，清空选择
      if (selectedSessionId.value === sessionToDelete.value) {
        selectedSessionId.value = null;
        selectedSession.value = null;
        selectedSessionMessages.value = [];
      }
      
      // 从会话列表中移除
      sessions.value = sessions.value.filter(s => s.id !== sessionToDelete.value);
      deleteDialog.value = false;
    } else {
      console.error('删除会话失败:', response.data.message);
    }
  } catch (error) {
    console.error('删除会话出错:', error);
  }
};

// 继续聊天
const continueChat = () => {
  if (selectedSessionId.value) {
    emit('continue-chat', selectedSessionId.value);
    dialog.value = false;
  }
};

// 跳转到视频时间点
const jumpToVideoTime = (timePoint: number) => {
  // 使用自定义事件通知视频播放器跳转到特定时间点
  const videoElement = document.querySelector('video');
  if (videoElement) {
    videoElement.currentTime = timePoint;
    videoElement.play();
  }
  dialog.value = false;
};

// 格式化日期时间
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
};

const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return `${formatDate(dateString)} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
};

// 格式化视频时间点
const formatVideoTime = (seconds: number) => {
  if (!seconds && seconds !== 0) return '';
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

// 格式化消息内容，支持Markdown
const formatContent = (content: string) => {
  if (!content) return '';
  // 使用marked转换Markdown，并使用DOMPurify净化HTML
  return DOMPurify.sanitize(marked.parse(content,{async:false}));
};

// 监听对话框打开
watch(dialog, (newValue) => {
  if (newValue) {
    loadSessions();
  }
});

// 初始化
onMounted(() => {
  if (dialog.value) {
    loadSessions();
  }
});
</script>

<style scoped>
.border-left {
  border-left: 1px solid #e0e0e0;
}

.history-list {
  height: 550px;
  overflow-y: auto;
}

.chat-messages {
  height: 480px;
  overflow-y: auto;
  padding: 16px;
}

.session-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.session-item:hover {
  background-color: #f5f5f5;
}

.message-container {
  display: flex;
  flex-direction: column;
}

.user-message {
  align-items: flex-end;
}

.ai-message {
  align-items: flex-start;
}

.message-content {
  max-width: 85%;
  border-radius: 8px;
  padding: 8px 12px;
  background-color: #f5f5f5;
}

.user-message .message-content {
  background-color: #e3f2fd;
}

.message-header {
  margin-bottom: 4px;
  font-size: 0.85rem;
  color: #666;
}

.message-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.time-point {
  cursor: pointer;
}
</style> 