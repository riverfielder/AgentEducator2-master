<template>
  <div class="teacher-home">
    <v-container fluid class="pa-4 teacher-container">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          教师主页
          <v-spacer></v-spacer>
          <div class="date-display text-body-1 text-medium-emphasis">
            {{ currentDateTime }}
          </div>
        </v-card-title> <v-divider></v-divider>
        <v-card-text class="pa-4">
          <!-- 加载状态 -->
          <div v-if="loading" class="text-center py-8">
            <v-progress-circular indeterminate color="primary" size="60"></v-progress-circular>
            <p class="mt-4 text-h6">正在加载数据...</p>
          </div>

          <!-- 主要内容 -->
          <div v-else>
            <!-- 欢迎部分 -->
            <v-card class="welcome-card mb-4" color="primary" variant="flat">
              <v-card-text class="d-flex flex-column flex-md-row align-md-center text-white pa-6">
                <div>
                  <h2 class="text-h4 font-weight-bold mb-2">欢迎回来，{{ teacherInfo.name || '教师用户' }}！</h2>
                  <p class="text-body-1 mb-0">您有 <span class="font-weight-bold">{{ courseProgress.active_courses
                      }}</span> 个课程正在进行中，<span class="font-weight-bold">{{ courseProgress.pending_messages }}</span>
                    个新消息待处理。</p>
                </div>
                <v-spacer></v-spacer>
                <div class="d-flex mt-4 mt-md-0">
                  <v-btn v-if="unreadComments.length > 0" color="white" variant="outlined" class="ml-2"
                    @click="showMessagesDialog = true">
                    <v-icon start>mdi-message-text</v-icon>
                    查看新消息 ({{ unreadComments.length }})
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>

            <!-- 统计卡片 -->
            <v-row dense class="stats-row mb-6">
              <v-col v-for="(stat, index) in statItems" :key="index" cols="6" sm="3">
                <v-card class="stat-card" hover elevation="1">
                  <v-card-text class="d-flex align-center pa-4">
                    <div class="stat-icon-container mr-4" :class="`stat-${index + 1}`">
                      <v-icon color="white" size="24">{{ stat.icon }}</v-icon>
                    </div>
                    <div class="flex-grow-1">
                      <div class="text-body-2 text-medium-emphasis">{{ stat.label }}</div>
                      <div class="text-h6 font-weight-bold">{{ stat.value }}</div>
                    </div>
                    <div class="stat-trend" :class="stat.trend">
                      <v-icon size="small" :color="stat.trend === 'up' ? 'success' : (stat.trend === 'down' ? 'error' : 'grey')">
                        {{ stat.trend === 'up' ? 'mdi-arrow-up' : (stat.trend === 'down' ? 'mdi-arrow-down' : 'mdi-minus') }}
                      </v-icon>
                      <span class="text-caption ml-1">{{ stat.change }}</span>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- 快捷操作区 -->
            <v-card class="mb-6">
              <v-card-title class="py-3 px-6">
                <v-icon start color="primary">mdi-lightning-bolt</v-icon>
                快捷操作
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-4">
                <v-row>
                  <v-col v-for="(action, index) in quickActions" :key="index" cols="12" sm="4" md="4">
                    <v-card class="action-card" hover @click="navigateTo(action.path)">
                      <v-card-text class="pa-4 d-flex flex-column align-center">
                        <v-icon size="36" color="primary" class="mb-3">{{ action.icon }}</v-icon>
                        <div class="text-subtitle-1 font-weight-medium text-center">{{ action.title }}</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- 最近活动区域 -->
            <v-row>
              <v-col cols="12" md="6">
                <v-card height="100%">
                  <v-card-title class="d-flex py-3 px-6">
                    <div>
                      <v-icon start color="primary">mdi-history</v-icon>
                      最近活动
                    </div>
                    <v-spacer></v-spacer>
                  </v-card-title>
                  <v-divider></v-divider>                  <v-list lines="two">
                    <v-list-item v-for="(activity, index) in recentActivities" :key="index" class="py-3">                      <template v-slot:prepend>
                        <!-- 如果是评论活动且有学生头像，显示头像，否则显示时间 -->
                        <div v-if="activity.type === 'comment' && (activity.student_avatar || activity.student_name)" class="d-flex align-center">
                          <v-avatar size="32" class="me-2" color="grey-lighten-3">
                            <img 
                              v-if="activity.student_avatar && !activity.avatarLoadError" 
                              :src="activity.student_avatar" 
                              @error="handleAvatarError($event, activity)"
                              @load="handleAvatarLoad($event, activity)"
                              style="width: 100%; height: 100%; object-fit: cover;" 
                            />                            <div v-else-if="activity.student_name && activity.student_name.trim()" 
                                 class="letter-avatar" 
                                 :style="getLetterAvatarStyle(activity.student_name)">
                              {{ activity.student_name.charAt(0).toUpperCase() }}
                            </div>
                            <v-icon v-else>mdi-account</v-icon>
                          </v-avatar>
                          <div class="activity-time text-caption text-medium-emphasis">
                            {{ activity.time }}
                          </div>
                        </div>
                        <div v-else class="activity-time text-caption text-medium-emphasis">
                          {{ activity.time }}
                        </div>
                      </template>
                      <template v-slot:default>
                        <v-list-item-title class="d-flex align-center mb-1">
                          <div class="activity-icon me-2" :class="`activity-${activity.type}`">
                            <v-icon size="small" color="white">{{ activity.icon }}</v-icon>
                          </div>
                          {{ activity.title }}
                        </v-list-item-title>
                        <v-list-item-subtitle>
                          {{ activity.description }}
                        </v-list-item-subtitle>
                      </template>
                    </v-list-item>
                    <v-list-item v-if="recentActivities.length === 0" class="py-3">
                      <v-list-item-title class="text-center text-medium-emphasis">
                        暂无最近活动
                      </v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-col>

              <!-- 最近评论区域 -->
              <v-col cols="12" md="6">
                <v-card height="100%">
                  <v-card-title class="d-flex py-3 px-6">
                    <div>
                      <v-icon start color="primary">mdi-comment-multiple</v-icon>
                      最近评论
                    </div>
                    <v-spacer></v-spacer>
                    <v-btn v-if="recentComments.length > 0" density="comfortable" variant="text" color="primary"
                      @click="showMessagesDialog = true">
                      查看全部
                    </v-btn>
                  </v-card-title>
                  <v-divider></v-divider>
                  
                  <div v-if="commentsLoading" class="text-center py-8">
                    <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
                    <p class="mt-2 text-body-2">加载评论中...</p>
                  </div>

                  <div v-else>
                    <v-list lines="two">
                      <v-list-item v-for="comment in recentComments" :key="comment.id" 
                        :class="{'unread-comment': !isCommentRead(comment.id)}"
                        @click="openCommentDetail(comment)">                        <template v-slot:prepend>
                          <v-badge v-if="!isCommentRead(comment.id)" dot color="error" location="start center" class="mr-2 unread-badge">
                            <v-avatar size="40" color="grey-lighten-3">
                              <img 
                                v-if="comment.studentAvatar && !comment.avatarLoadError" 
                                :src="comment.studentAvatar" 
                                @error="handleAvatarError($event, comment)"
                                @load="handleAvatarLoad($event, comment)"
                                style="width: 100%; height: 100%; object-fit: cover;" 
                              />                              <div v-else-if="comment.studentName && comment.studentName.trim()" 
                                   class="letter-avatar" 
                                   :style="getLetterAvatarStyle(comment.studentName)">
                                {{ comment.studentName.charAt(0).toUpperCase() }}
                              </div>
                              <v-icon v-else>mdi-account</v-icon>
                            </v-avatar>
                          </v-badge>
                          <v-avatar v-else size="40" color="grey-lighten-3">
                            <img 
                              v-if="comment.studentAvatar && !comment.avatarLoadError" 
                              :src="comment.studentAvatar" 
                              @error="handleAvatarError($event, comment)"
                              @load="handleAvatarLoad($event, comment)"
                              style="width: 100%; height: 100%; object-fit: cover;" 
                            />                            <div v-else-if="comment.studentName && comment.studentName.trim()" 
                                 class="letter-avatar" 
                                 :style="getLetterAvatarStyle(comment.studentName)">
                              {{ comment.studentName.charAt(0).toUpperCase() }}
                            </div>
                            <v-icon v-else>mdi-account</v-icon>
                          </v-avatar>
                        </template>
                        <template v-slot:default>
                          <v-list-item-title class="d-flex align-center mb-1 text-truncate">
                            {{ comment.studentName }}
                            <span class="text-caption text-medium-emphasis ml-2">
                              {{ formatDateTime(comment.createTime) }}
                            </span>
                          </v-list-item-title>
                          <v-list-item-subtitle class="text-truncate">
                            <span class="course-name mr-1">{{ comment.courseName }}</span> - 
                            <span class="video-title ml-1">{{ comment.videoTitle }}</span>
                          </v-list-item-subtitle>
                          <div class="comment-content text-body-2 text-medium-emphasis text-truncate-2">
                            {{ comment.content }}
                          </div>
                        </template>
                        <template v-slot:append>
                          <v-btn icon="mdi-comment-outline" variant="text" size="small" 
                            @click.stop="replyToComment(comment)" :title="'回复评论'">
                          </v-btn>
                        </template>
                      </v-list-item>
                      <v-list-item v-if="recentComments.length === 0" class="py-6">
                        <v-list-item-title class="text-center text-medium-emphasis">
                          暂无最近评论
                        </v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-card>
              </v-col>
            </v-row>
          </div> <!-- 关闭主要内容的div -->
        </v-card-text>
      </v-card>
    </v-container>    <!-- 消息管理对话框 -->
    <v-dialog v-model="showMessagesDialog" max-width="1200px"  @keydown.esc="closeMessagesDialog">
      <v-card class="messages-dialog">
        <v-card-title class="d-flex align-center py-4 px-6 bg-primary text-white">
          <v-icon start>mdi-message-text</v-icon>
          学生消息管理
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="closeMessagesDialog">
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
              @update:model-value="fetchAllMessages"
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
              @update:model-value="fetchAllMessages"
            ></v-select>
            
            <v-text-field
              v-model="searchKeyword"
              prepend-inner-icon="mdi-magnify"
              label="搜索消息..."
              density="compact"
              style="max-width: 250px;"
              hide-details
              @keyup.enter="fetchAllMessages"
            ></v-text-field>
            
            <v-spacer></v-spacer>
            
            <v-btn @click="fetchAllMessages" color="primary" variant="text">
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
            <div v-if="messagesLoading" class="text-center py-8">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <p class="mt-2">加载消息中...</p>
            </div>
            
            <div v-else-if="messagesError" class="text-center py-8">
              <v-alert type="error" variant="tonal">{{ messagesError }}</v-alert>
              <v-btn @click="fetchAllMessages" color="primary" class="mt-4">重试</v-btn>
            </div>
            
            <div v-else-if="allMessages.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey">mdi-message-outline</v-icon>
              <p class="text-h6 mt-4">暂无消息</p>
            </div>
            
            <v-list v-else lines="three" class="pa-0">              <v-list-item
                v-for="message in allMessages"
                :key="message.id"
                class="message-item"
                :class="{
                  'unread': !isCommentRead(message.id),
                  'high-priority': message.priority === 'high'
                }"
                @click="showMessageDetail(message)"
              >
                <template v-slot:prepend>
                  <v-avatar size="40" color="grey-lighten-3">
                    <img 
                      v-if="message.studentAvatar && !message.avatarLoadError" 
                      :src="message.studentAvatar" 
                      @error="handleAvatarError($event, message)"
                      @load="handleAvatarLoad($event, message)"
                      style="width: 100%; height: 100%; object-fit: cover;" 
                    />                    <div v-else-if="message.studentName && message.studentName.trim()" 
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
                      v-if="!isCommentRead(message.id)"
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
                @update:model-value="fetchAllMessages"
              ></v-pagination>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
    
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
                />                <div v-else-if="selectedMessage.studentName && selectedMessage.studentName.trim()" 
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
            @click="goToVideo(selectedMessage.courseId,selectedMessage.videoId)"
            variant="outlined"
          >
            查看视频
          </v-btn>
          <v-btn
            color="primary"
            @click="sendDetailReply"
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
  </div>
  <div class="test">.</div>
</template>

<script>
import userService from '../../api/userService';
import courseService from '../../api/courseService';
import teacherDashboardService from '../../api/teacherDashboardService';
import commentReadStatus from '../../utils/commentReadStatus';
import message from '../../utils/message';

export default {
  name: 'TeacherHome',
  data() {
    return {
      currentDateTime: '',
      loading: false,
      commentsLoading: false,
      teacherInfo: {
        name: '',
        role: ''
      },
      statItems: [],
      courseProgress: {
        active_courses: 0,
        pending_messages: 0
      },
      quickActions: [
        { title: '新建课程', icon: 'mdi-plus-circle', path: '/courses' },
        { title: '上传视频', icon: 'mdi-upload', path: '/materials' },
        { title: '布置作业', icon: 'mdi-clipboard-text', path: '/assignments' },
      ],
      recentActivities: [],
      recentComments: [],
      unreadComments: [],
      
      // 消息管理相关
      showMessagesDialog: false,
      detailDialog: false,
      quickReplyDialog: false,
      selectedMessage: null,
      replyingMessage: null,
      replyContent: '',
      quickReplyContent: '',
      replying: false,
      
      // 消息列表相关
      allMessages: [],
      messagesLoading: false,
      messagesError: null,
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
      
      // 消息统计
      messageStats: [],
      
      // 回复模板
      replyTemplates: [
        '感谢您的提问！',
        '这是一个很好的问题。',
        '请查看课程资料中的相关内容。',
        '建议您重新观看这部分内容。',
        '如有其他问题，欢迎继续提问。'
      ]
    }
  }, 
  watch: {
    showMessagesDialog(newVal) {
      if (newVal) {
        // 当消息对话框打开时，自动加载消息数据
        this.fetchAllMessages();
        this.fetchCourses();
      }
    }
  },
  methods: {
    async fetchTeacherHomeData() {
      try {
        this.loading = true;

        if (!localStorage.getItem('wendao_token')) {
          this.$router.push('/login');
          return;
        }

        const response = await teacherDashboardService.getTeacherHomeData();

        if (response.data.code === 200) {
          const data = response.data.data;

          // 更新教师信息
          this.teacherInfo = data.teacher_info;

          // 更新统计数据
          this.statItems = data.stat_items;

          // 更新课程进度信息
          this.courseProgress = data.course_progress;          // 更新最近活动
          this.recentActivities = data.recent_activities;
          
          // 调试：打印最近活动数据结构
          console.log('Recent activities data:', this.recentActivities);

        } else {
          throw new Error(response.data.message || '获取教师主页数据失败');
        }
      } catch (error) {
        console.error('获取教师主页数据失败:', error);
        message.error(error.message || '获取数据失败，请稍后重试');

        if (error.response && error.response.status === 401) {
          this.$router.push('/login');
        }
      } finally {
        this.loading = false;
      }
    },    async fetchRecentComments() {
      try {
        this.commentsLoading = true;

        if (!localStorage.getItem('wendao_token')) {
          return;
        }        // 获取最近的学生评论（只获取未回复的）
        const response = await teacherDashboardService.getMessages({
          pageSize: 10,
          page: 1,
          status: 'all'  // 获取所有评论，包括已回复和未回复的
        });if (response.data.code === 200) {
          this.recentComments = response.data.data.list || [];
          
          // 调试：打印评论数据结构
          console.log('Recent comments data:', this.recentComments);
          
          // 标记未读评论
          this.unreadComments = this.recentComments.filter(
            comment => !commentReadStatus.isCommentRead(comment.id)
          );
        } else {
          console.error('获取评论失败:', response.data.message);
        }
      } catch (error) {
        console.error('获取最近评论失败:', error);
      } finally {
        this.commentsLoading = false;
      }
    },
    
    async fetchAllMessages() {
      try {
        this.messagesLoading = true;
        this.messagesError = null;
        
        if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录');
        }
        
        const response = await teacherDashboardService.getMessages({
          page: this.currentPage,
          pageSize: 20,
          status: this.statusFilter,
          course_id: this.courseFilter,
          keyword: this.searchKeyword
        });
        
        if (response.data.code === 200) {
          const data = response.data.data;
          this.allMessages = data.list;
          this.totalPages = Math.ceil(data.total / 20);
          this.updateMessageStats(data.statistics);
        } else {
          throw new Error(response.data.message || '获取消息列表失败');
        }
      } catch (error) {
        console.error('获取消息列表失败:', error);
        this.messagesError = error.message || '获取消息列表失败';
      } finally {
        this.messagesLoading = false;
      }
    },
    
    async fetchCourses() {
      try {
        if (!localStorage.getItem('wendao_token')) return;
        
        const response = await teacherDashboardService.getCourses();
        
        if (response.data.code === 200) {
          this.courseOptions = [
            { id: 'all', name: '所有课程' },
            ...response.data.data
          ];
        }
      } catch (error) {
        console.error('获取课程列表失败:', error);
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
      ];
    },

    async fetchTeacherInfo() {
      try {
        if (!localStorage.getItem('wendao_token')) {
          this.$router.push('/login');
          return;
        }

        const response = await userService.getUserInfo();

        if (response.data.code === 200) {
          this.teacherInfo = response.data.data;
        } else {
          throw new Error(response.data.message || '获取用户信息失败');
        }
      } catch (error) {
        console.error('获取教师信息失败:', error);
        if (error.response && error.response.status === 401) {
          this.$router.push('/login');
        }
      }
    },
      isCommentRead(commentId) {
      return commentReadStatus.isCommentRead(commentId);
    },
    
    openCommentDetail(comment) {
      // 标记为已读
      commentReadStatus.markCommentAsRead(comment.id);
      
      // 在未读列表中移除
      this.unreadComments = this.unreadComments.filter(c => c.id !== comment.id);
      
      // 打开回复对话框
      this.selectedMessage = comment;
      this.replyContent = '';
      this.detailDialog = true;
    },
    
    showMessageDetail(message) {
      // 标记为已读
      commentReadStatus.markCommentAsRead(message.id);
      
      this.selectedMessage = message;
      this.replyContent = '';
      this.detailDialog = true;
    },
    
    replyToComment(comment) {
      // 标记为已读
      commentReadStatus.markCommentAsRead(comment.id);
      
      // 在未读列表中移除
      this.unreadComments = this.unreadComments.filter(c => c.id !== comment.id);
      
      // 打开回复对话框
      this.replyingMessage = comment;
      this.quickReplyContent = '';
      this.quickReplyDialog = true;
    },
    
    quickReply(message) {
      // 标记为已读
      commentReadStatus.markCommentAsRead(message.id);
      
      this.replyingMessage = message;
      this.quickReplyContent = '';
      this.quickReplyDialog = true;
    },
    
    async sendDetailReply() {
      if (!this.replyContent.trim() || !this.selectedMessage) return;
      
      try {
        this.replying = true;
        
        if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录');
        }
        
        const response = await teacherDashboardService.replyToMessage(
          this.selectedMessage.id,
          this.replyContent.trim()
        );
        
        if (response.data.code === 200) {
          message.success('回复发送成功');
          this.detailDialog = false;
          
          // 刷新评论列表
          this.fetchRecentComments();
          
          // 如果消息列表对话框也开着，刷新全部消息
          if (this.showMessagesDialog) {
            this.fetchAllMessages();
          }
        } else {
          throw new Error(response.data.message || '发送回复失败');
        }
      } catch (error) {
        console.error('发送回复失败:', error);
        message.error(error.message || '发送回复失败，请稍后重试');
      } finally {
        this.replying = false;
      }
    },
    
    async sendQuickReply() {
      if (!this.quickReplyContent.trim() || !this.replyingMessage) return;
      
      try {
        this.replying = true;
        
        if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录');
        }
        
        const response = await teacherDashboardService.replyToMessage(
          this.replyingMessage.id,
          this.quickReplyContent.trim()
        );
        
        if (response.data.code === 200) {
          message.success('回复发送成功');
          this.quickReplyDialog = false;
          
          // 刷新消息列表
          this.fetchRecentComments();
          
          // 如果消息列表对话框也开着，刷新全部消息
          if (this.showMessagesDialog) {
            this.fetchAllMessages();
          }
        } else {
          throw new Error(response.data.message || '发送回复失败');
        }
      } catch (error) {
        console.error('发送回复失败:', error);
        message.error(error.message || '发送回复失败，请稍后重试');
      } finally {
        this.replying = false;
      }
    },
    
    goToVideo(courseId,videoId) {
      this.detailDialog = false;
      this.closeMessagesDialog();
      this.$router.push(`/course/${courseId}/video/${videoId}`);
    },
    
    closeMessagesDialog() {
      this.showMessagesDialog = false;
    },
    
    formatTime(seconds) {
      if (!seconds) return '0:00';
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.floor(seconds % 60);
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    },
    
    logout() {
      // 清除token
      localStorage.removeItem('wendao_token');
      localStorage.removeItem('wendao_user_id');
      localStorage.removeItem('wendao_user_name');
      localStorage.removeItem('wendao_user_role');

      // 调用登出API（无需等待响应）
      userService.logout().catch(err => console.error('登出API调用失败:', err));

      // 跳转到登录页
      this.$router.push('/login');
    },
    navigateTo(path) {
      this.$router.push(path);
    },
    updateDateTime() {
      const now = new Date();
      const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long',
        hour: '2-digit',
        minute: '2-digit'
      };
      this.currentDateTime = now.toLocaleDateString('zh-CN', options);
    },
    formatDateTime(dateTimeStr) {
      const date = new Date(dateTimeStr);
      const now = new Date();
      const diff = now - date;
      
      // 如果是今天
      if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
        return date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // 如果是昨天
      const yesterday = new Date(now);
      yesterday.setDate(yesterday.getDate() - 1);
      if (date.getDate() === yesterday.getDate()) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }
      
      // 其他日期
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    // 获取随机颜色 - 与Header组件保持一致
    getRandomColor(seed) {
      const colors = [
        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
        '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
      ];
      const index = seed.charCodeAt(0) % colors.length;
      return colors[index];
    },    // 生成字母头像样式
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
    },// 处理头像加载错误
    handleAvatarError(event, item) {
      console.error('TeacherHome avatar error for:', item.studentName || item.student_name || item.name || 'unknown');
      // Vue 3 中直接设置属性即可实现响应式
      item.avatarLoadError = true;
      // 隐藏错误的图片元素
      event.target.style.display = 'none';
    },

    // 处理头像加载成功
    handleAvatarLoad(event, item) {
      console.log('TeacherHome avatar loaded for:', item.studentName || item.student_name || item.name || 'unknown');
      // Vue 3 中直接设置属性即可实现响应式
      item.avatarLoadError = false;
      event.target.style.display = 'block';
    }
  },  mounted() {
    this.updateDateTime();
    setInterval(this.updateDateTime, 60000); // 每分钟更新一次时间
    this.fetchTeacherHomeData(); // 使用新的方法获取完整的教师主页数据
    this.fetchRecentComments(); // 获取最近的评论
    this.fetchCourses(); // 获取课程列表用于筛选
  }
}
</script>

<style scoped>
.teacher-home {
  width: 100%;
}

.teacher-container {
  width: 100%;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
}

.content-card>.v-card-text {
  padding: 16px;
}

.test {
  width: 100%;
  height: 1000px;
  background-color: #f8f9fa;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
  color: #f8f9fa;
  margin-bottom: 16px;
}

/* 欢迎卡片样式 */
.welcome-card {
  border-radius: 12px;
  background: linear-gradient(to right, #6f23d1, #8d40e8);
  box-shadow: 0 4px 20px rgba(111, 35, 209, 0.2);
}

/* 统计卡片样式 */
.stats-row {
  margin-left: -8px;
  margin-right: -8px;
}

.stat-card {
  border-radius: 12px;
  height: 100%;
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1) !important;
}

.stat-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-1 {
  background-color: #6f23d1;
}

.stat-2 {
  background-color: #4caf50;
}

.stat-3 {
  background-color: #2196f3;
}

.stat-4 {
  background-color: #f44336;
}

.stat-trend {
  display: flex;
  align-items: center;
}

.stat-trend.up {
  color: #4caf50;
}

.stat-trend.down {
  color: #f44336;
}

/* 快捷操作区域 */
.action-card {
  border-radius: 12px;
  height: 100%;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #f8f9fa;
}

.action-card:hover {
  transform: translateY(-3px);
  background-color: #f0f4ff;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05) !important;
}

/* 活动列表样式 */
.activity-time {
  min-width: 70px;
  text-align: right;
  padding-right: 16px;
}

.activity-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.activity-icon.upload {
  background-color: #4caf50;
}

.activity-icon.course {
  background-color: #2196f3;
}

.activity-icon.comment {
  background-color: #ff9800;
}

.activity-icon.grade {
  background-color: #9c27b0;
}

/* 列表项样式 */
:deep(.v-list-item) {
  padding: 12px 16px;
}

:deep(.v-list-item:not(:last-child)) {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

:deep(.v-list-item:hover) {
  background-color: #f5f5f5;
}

/* 评论列表样式 */
.unread-comment {
  background-color: #fef9e7;
}

.unread-badge {
  position: relative;
}

.comment-content {
  margin-top: 4px;
  display: -webkit-box;
  display: box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  overflow: hidden;
}

.course-name {
  color: #1976d2;
  font-weight: 500;
}

.video-title {
  color: #666;
}

.text-truncate-2 {
  display: -webkit-box;
  display: box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  overflow: hidden;
}

.border-bottom {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

/* Letter avatar styles */
.letter-avatar {
  border-radius: 50%;
  text-transform: uppercase;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: white;
  font-size: 14px;
}

.letter-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255,255,255,0.1) 0%, 
    rgba(255,255,255,0) 50%, 
    rgba(0,0,0,0.1) 100%);
  pointer-events: none;
}
</style>
