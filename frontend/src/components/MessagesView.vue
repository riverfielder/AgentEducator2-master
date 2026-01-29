<template>
  <v-dialog v-model="dialog" max-width="1200px" persistent>
    <v-card class="messages-dialog">
      <v-card-title class="d-flex align-center py-4 px-6 bg-primary text-white">
        <v-icon start>mdi-message-text</v-icon>
        学生消息管理
        <v-spacer></v-spacer>
        <v-btn icon variant="text" @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text class="pa-0">
        <!-- 工具栏 -->
        <v-toolbar flat color="grey-lighten-4">
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            label="状态筛选"
            density="compact"
            style="max-width: 150px;"
            class="mr-4"
            @update:model-value="fetchMessages"
          ></v-select>
          
          <v-select
            v-model="courseFilter"
            :items="courseOptions"
            item-title="name"
            item-value="id"
            label="课程筛选"
            density="compact"
            style="max-width: 200px;"
            class="mr-4"
            @update:model-value="fetchMessages"
          ></v-select>
          
          <v-text-field
            v-model="searchKeyword"
            prepend-inner-icon="mdi-magnify"
            label="搜索消息..."
            density="compact"
            style="max-width: 250px;"
            hide-details
            @keyup.enter="fetchMessages"
          ></v-text-field>
          
          <v-spacer></v-spacer>
          
          <v-btn @click="fetchMessages" color="primary" variant="text">
            <v-icon start>mdi-refresh</v-icon>
            刷新
          </v-btn>
        </v-toolbar>
        
        <!-- 统计概览 -->
        <v-row class="pa-4" dense>
          <v-col v-for="(stat, index) in messageStats" :key="index" cols="3">
            <v-card variant="flat" :color="stat.color" class="text-white">
              <v-card-text class="pa-3 text-center">
                <v-icon size="24" class="mb-2">{{ stat.icon }}</v-icon>
                <div class="text-h6 font-weight-bold">{{ stat.value }}</div>
                <div class="text-caption">{{ stat.label }}</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <v-divider></v-divider>
        
        <!-- 消息列表 -->
        <div class="messages-container">
          <div v-if="loading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <p class="mt-2">加载消息中...</p>
          </div>
          
          <div v-else-if="error" class="text-center py-8">
            <v-alert type="error" variant="tonal">{{ error }}</v-alert>
            <v-btn @click="fetchMessages" color="primary" class="mt-4">重试</v-btn>
          </div>
          
          <div v-else-if="messages.length === 0" class="text-center py-8">
            <v-icon size="64" color="grey">mdi-message-outline</v-icon>
            <p class="text-h6 mt-4">暂无消息</p>
          </div>
          
          <v-list v-else lines="three" class="pa-0">
            <v-list-item
              v-for="(message, index) in messages"
              :key="message.id"
              class="message-item"
              :class="{
                'unread': message.isUnread,
                'high-priority': message.priority === 'high'
              }"
              @click="showMessageDetail(message)"
            >              <template v-slot:prepend>
                <v-avatar size="40" color="grey-lighten-3">
                  <img 
                    v-if="message.studentAvatar && !message.avatarLoadError" 
                    :src="message.studentAvatar" 
                    @error="handleAvatarError($event, message)"
                    @load="handleAvatarLoad($event, message)"
                    style="width: 100%; height: 100%; object-fit: cover;" 
                  />
                  <div v-else-if="message.studentName && message.studentName.trim()" 
                       class="letter-avatar" 
                       :style="getLetterAvatarStyle(message.studentName)">
                    {{ message.studentName.charAt(0).toUpperCase() }}
                  </div>
                  <v-icon v-else>mdi-account</v-icon>
                </v-avatar>
              </template>
              
              <template v-slot:title>
                <div class="d-flex align-center">
                  <span class="font-weight-medium">{{ message.studentName }}</span>
                  <v-chip
                    v-if="message.isUnread"
                    color="red"
                    variant="flat"
                    size="x-small"
                    class="ml-2"
                  >
                    未读
                  </v-chip>
                  <v-chip
                    v-if="message.priority === 'high'"
                    color="orange"
                    variant="flat"
                    size="x-small"
                    class="ml-2"
                  >
                    高优先级
                  </v-chip>
                </div>
              </template>
              
              <template v-slot:subtitle>
                <div class="message-meta mb-2">
                  <span class="course-name">{{ message.courseName }}</span>
                  <span class="mx-2">•</span>
                  <span class="video-title">{{ message.videoTitle }}</span>
                  <span v-if="message.timePoint" class="mx-2">•</span>
                  <span v-if="message.timePoint" class="time-point">
                    {{ formatTime(message.timePoint) }}
                  </span>
                </div>
                <div class="message-content">{{ message.content }}</div>
              </template>
              
              <template v-slot:append>
                <div class="message-actions">
                  <div class="message-time text-caption text-medium-emphasis mb-2">
                    {{ formatDateTime(message.createTime) }}
                  </div>
                  <div class="d-flex align-center">
                    <v-chip
                      :color="message.hasTeacherReply ? 'success' : 'grey'"
                      variant="flat"
                      size="small"
                      class="mr-2"
                    >
                      <v-icon start size="14">
                        {{ message.hasTeacherReply ? 'mdi-check-circle' : 'mdi-clock-outline' }}
                      </v-icon>
                      {{ message.hasTeacherReply ? '已回复' : '待回复' }}
                    </v-chip>
                    <v-btn
                      v-if="!message.hasTeacherReply"
                      color="primary"
                      variant="text"
                      size="small"
                      @click.stop="quickReply(message)"
                    >
                      回复
                    </v-btn>
                  </div>
                  <div class="d-flex align-center mt-2">
                    <v-icon size="14" color="red" class="mr-1">mdi-heart</v-icon>
                    <span class="text-caption">{{ message.likes }}</span>
                    <span v-if="message.replyCount > 0" class="ml-3 text-caption">
                      <v-icon size="14" class="mr-1">mdi-comment</v-icon>
                      {{ message.replyCount }}
                    </span>
                  </div>
                </div>
              </template>
            </v-list-item>
          </v-list>
          
          <!-- 分页 -->
          <div v-if="totalPages > 1" class="d-flex justify-center pa-4">
            <v-pagination
              v-model="currentPage"
              :length="totalPages"
              @update:model-value="fetchMessages"
            ></v-pagination>
          </div>
        </div>
      </v-card-text>
    </v-card>
    
    <!-- 消息详情对话框 -->
    <v-dialog v-model="detailDialog" max-width="800px">
      <v-card v-if="selectedMessage">
        <v-card-title class="bg-primary text-white">
          <v-icon start>mdi-message-text</v-icon>
          消息详情
        </v-card-title>
        <v-card-text class="pa-6">
          <div class="message-header mb-4">            <div class="d-flex align-center mb-3">
              <v-avatar size="48" class="mr-3" color="grey-lighten-3">
                <img 
                  v-if="selectedMessage.studentAvatar && !selectedMessage.avatarLoadError" 
                  :src="selectedMessage.studentAvatar" 
                  @error="handleAvatarError($event, selectedMessage)"
                  @load="handleAvatarLoad($event, selectedMessage)"
                  style="width: 100%; height: 100%; object-fit: cover;" 
                />
                <div v-else-if="selectedMessage.studentName && selectedMessage.studentName.trim()" 
                     class="letter-avatar" 
                     :style="getLetterAvatarStyle(selectedMessage.studentName)">
                  {{ selectedMessage.studentName.charAt(0).toUpperCase() }}
                </div>
                <v-icon v-else>mdi-account</v-icon>
              </v-avatar>
              <div>
                <div class="text-h6">{{ selectedMessage.studentName }}</div>
                <div class="text-caption text-medium-emphasis">
                  {{ formatDateTime(selectedMessage.createTime) }}
                </div>
              </div>
            </div>
            
            <div class="course-info mb-3">
              <v-chip color="primary" variant="outlined" class="mr-2">
                {{ selectedMessage.courseName }}
              </v-chip>
              <v-chip color="info" variant="outlined">
                {{ selectedMessage.videoTitle }}
              </v-chip>
              <span v-if="selectedMessage.timePoint" class="ml-2 text-caption">
                时间点: {{ formatTime(selectedMessage.timePoint) }}
              </span>
            </div>
          </div>
          
          <div class="message-content mb-4">
            <div class="text-subtitle-1 mb-2">消息内容</div>
            <v-card variant="outlined" class="pa-3">
              {{ selectedMessage.content }}
            </v-card>
          </div>
          
          <div class="reply-section">
            <div class="text-subtitle-1 mb-2">快速回复</div>
            <v-textarea
              v-model="replyContent"
              label="输入回复内容..."
              rows="3"
              variant="outlined"
              :disabled="replying"
            ></v-textarea>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="detailDialog = false">关闭</v-btn>
          <v-btn
            color="primary"
            @click="goToVideo(selectedMessage.videoId)"
            variant="outlined"
          >
            查看视频
          </v-btn>
          <v-btn
            color="primary"
            @click="sendReply"
            :loading="replying"
            :disabled="!replyContent.trim()"
          >
            发送回复
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 快速回复对话框 -->
    <v-dialog v-model="quickReplyDialog" max-width="500px">
      <v-card>
        <v-card-title>快速回复</v-card-title>
        <v-card-text>
          <div v-if="replyingMessage" class="mb-4">
            <div class="text-subtitle-2">回复给：{{ replyingMessage.studentName }}</div>
            <div class="text-caption text-medium-emphasis">
              {{ replyingMessage.courseName }} • {{ replyingMessage.videoTitle }}
            </div>
          </div>
          
          <v-textarea
            v-model="quickReplyContent"
            label="输入回复内容..."
            rows="4"
            variant="outlined"
            :disabled="replying"
          ></v-textarea>
          
          <div class="mt-3">
            <div class="text-subtitle-2 mb-2">快速回复模板</div>
            <v-chip-group>
              <v-chip
                v-for="template in replyTemplates"
                :key="template"
                @click="quickReplyContent = template"
                size="small"
                variant="outlined"
              >
                {{ template }}
              </v-chip>
            </v-chip-group>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="quickReplyDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            @click="sendQuickReply"
            :loading="replying"
            :disabled="!quickReplyContent.trim()"
          >
            发送
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script>
import teacherDashboardService from '../api/teacherDashboardService'
import { showSuccessMessage, showErrorMessage } from '../utils/notification'

export default {
  name: 'MessagesView',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      loading: false,
      error: null,
      messages: [],
      messageStats: [],
      totalPages: 0,
      currentPage: 1,
      
      // 筛选和搜索
      statusFilter: 'all',
      courseFilter: 'all',
      searchKeyword: '',
      statusOptions: [
        { label: '全部消息', value: 'all' },
        { label: '未读消息', value: 'unread' },
        { label: '已回复', value: 'replied' }
      ],
      courseOptions: [
        { id: 'all', name: '所有课程' }
      ],
      
      // 对话框
      detailDialog: false,
      quickReplyDialog: false,
      selectedMessage: null,
      replyingMessage: null,
      
      // 回复
      replyContent: '',
      quickReplyContent: '',
      replying: false,
      replyTemplates: [
        '感谢您的提问！',
        '这是一个很好的问题。',
        '请查看课程资料中的相关内容。',
        '建议您重新观看这部分内容。',
        '如有其他问题，欢迎继续提问。'
      ]
    }
  },
  computed: {
    dialog: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  watch: {
    dialog(newVal) {
      if (newVal) {
        this.fetchCourses()
        this.fetchMessages()
      }
    }
  },
  methods: {
    async fetchMessages() {
      try {
        this.loading = true
        this.error = null
          if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录')
        }
        
        const response = await teacherDashboardService.getMessages({
          page: this.currentPage,
          pageSize: 20,
          status: this.statusFilter,
          course_id: this.courseFilter,
          keyword: this.searchKeyword
        })
        
        if (response.data.code === 200) {
          const data = response.data.data
          this.messages = data.list
          this.totalPages = Math.ceil(data.total / 20)
          this.updateMessageStats(data.statistics)
        } else {
          throw new Error(response.data.message || '获取消息列表失败')
        }
      } catch (error) {
        console.error('获取消息列表失败:', error)
        this.error = error.message || '获取消息列表失败'
      } finally {
        this.loading = false
      }
    },
    
    async fetchCourses() {
      try {        if (!localStorage.getItem('wendao_token')) return
        
        const response = await teacherDashboardService.getCourses()
        
        if (response.data.code === 200) {
          this.courseOptions = [
            { id: 'all', name: '所有课程' },
            ...response.data.data
          ]
        }
      } catch (error) {
        console.error('获取课程列表失败:', error)
      }
    },
    
    updateMessageStats(statistics) {
      this.messageStats = [
        {
          label: '总消息数',
          value: statistics.totalMessages,
          icon: 'mdi-message-text',
          color: 'primary'
        },
        {
          label: '未读消息',
          value: statistics.unreadCount,
          icon: 'mdi-message-alert',
          color: 'warning'
        },
        {
          label: '已回复',
          value: statistics.repliedCount,
          icon: 'mdi-message-check',
          color: 'success'
        },
        {
          label: '今日消息',
          value: statistics.todayMessages,
          icon: 'mdi-message-processing',
          color: 'info'
        }
      ]
    },
    
    showMessageDetail(message) {
      this.selectedMessage = message
      this.replyContent = ''
      this.detailDialog = true
    },
    
    quickReply(message) {
      this.replyingMessage = message
      this.quickReplyContent = ''
      this.quickReplyDialog = true
    },
    
    async sendReply() {
      if (!this.replyContent.trim()) return
      
      try {
        this.replying = true
          if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录')
        }
        
        const response = await teacherDashboardService.replyToMessage(
          this.selectedMessage.id,
          this.replyContent
        )        
        if (response.data.code === 200) {
          showSuccessMessage('回复发送成功')
          this.detailDialog = false
          this.fetchMessages() // 刷新消息列表
        } else {
          throw new Error(response.data.message || '发送回复失败')
        }
      } catch (error) {
        console.error('发送回复失败:', error)
        showErrorMessage(error.message || '发送回复失败')
      } finally {
        this.replying = false
      }
    },
    
    async sendQuickReply() {
      if (!this.quickReplyContent.trim()) return
      
      try {
        this.replying = true
          if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录')
        }
        
        const response = await teacherDashboardService.replyToMessage(
          this.replyingMessage.id,
          this.quickReplyContent
        )        
        if (response.data.code === 200) {
          showSuccessMessage('回复发送成功')
          this.quickReplyDialog = false
          this.fetchMessages() // 刷新消息列表
        } else {
          throw new Error(response.data.message || '发送回复失败')
        }
      } catch (error) {
        console.error('发送回复失败:', error)
        showErrorMessage(error.message || '发送回复失败')
      } finally {
        this.replying = false
      }
    },
    
    goToVideo(videoId) {
      this.detailDialog = false
      this.closeDialog()
      this.$router.push(`/videos/${videoId}`)
    },
    
    closeDialog() {
      this.dialog = false
    },
    
    // 工具方法
    formatTime(seconds) {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = Math.floor(seconds % 60)
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
    },
    
    formatDateTime(dateTimeStr) {
      const date = new Date(dateTimeStr)
      const now = new Date()
      const diff = now - date
      
      // 如果是今天
      if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })
      }
      
      // 如果是昨天
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      if (date.getDate() === yesterday.getDate()) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })
      }
        // 其他日期
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    // 头像相关方法
    getRandomColor(seed) {
      const colors = [
        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
        '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
      ];
      const index = seed.charCodeAt(0) % colors.length;
      return colors[index];
    },

    getLetterAvatarStyle(username) {
      if (!username || typeof username !== 'string' || username.length === 0) {
        return {
          backgroundColor: '#9e9e9e',
          color: 'white',
          fontWeight: 'bold',
          fontSize: '16px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          width: '100%',
          height: '100%'
        };
      }
      const color = this.getRandomColor(username);
      return {
        backgroundColor: color,
        color: 'white',
        fontWeight: 'bold',
        fontSize: '16px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        height: '100%'
      };
    },

    // 处理头像加载错误
    handleAvatarError(event, item) {
      console.error('MessagesView avatar error for:', item.studentName || 'unknown');
      // Vue 3 中直接设置属性即可实现响应式
      item.avatarLoadError = true;
      // 隐藏错误的图片元素
      event.target.style.display = 'none';
    },

    // 处理头像加载成功
    handleAvatarLoad(event, item) {
      console.log('MessagesView avatar loaded for:', item.studentName || 'unknown');
      // Vue 3 中直接设置属性即可实现响应式
      item.avatarLoadError = false;
      event.target.style.display = 'block';
    }
  }
}
</script>

<style scoped>
.messages-dialog {
  border-radius: 12px;
}

.messages-container {
  max-height: 600px;
  overflow-y: auto;
}

.message-item {
  border-bottom: 1px solid #e0e0e0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.message-item:hover {
  background-color: #f5f5f5;
}

.message-item.unread {
  background-color: #fff3e0;
  border-left: 4px solid #ff9800;
}

.message-item.high-priority {
  border-left: 4px solid #f44336;
}

.message-meta {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.course-name {
  color: #1976d2;
  font-weight: 500;
}

.video-title {
  color: #666;
}

.time-point {
  color: #ff9800;
  font-weight: 500;
}

.message-content {
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 120px;
}

.message-time {
  white-space: nowrap;
}

.message-header {
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 16px;
}

.course-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.reply-section {
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}

/* 字母头像样式 */
.letter-avatar {
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  transition: all 0.3s ease;
}

.letter-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
</style>
