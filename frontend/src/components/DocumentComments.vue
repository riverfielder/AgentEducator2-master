<template>
  <div class="document-comments">
    <!-- 评论输入框 -->
    <div class="comment-input-section">
      <h4 class="section-title">
        <v-icon color="primary" size="20">mdi-comment-text-outline</v-icon>
        文档笔记
      </h4>
      
      <div class="comment-input-container">
        <v-textarea
          v-model="newComment"
          placeholder="记录你的想法和笔记..."
          rows="3"
          variant="outlined"
          density="compact"
          class="comment-textarea">
        </v-textarea>
        
        <div class="comment-actions">
          <v-btn
            color="primary"
            size="small"
            :disabled="!newComment.trim()"
            @click="submitComment">
            发布笔记
          </v-btn>
        </div>
      </div>
    </div>

    <!-- 评论列表 -->
    <div class="comments-list">
      <div v-if="isLoading" class="loading-container">
        <v-progress-circular indeterminate size="24" color="primary"></v-progress-circular>
        <span class="ml-2 text-body-2">正在加载笔记...</span>
      </div>

      <div v-else-if="comments.length === 0" class="empty-container">
        <v-icon color="grey" size="48">mdi-comment-outline</v-icon>
        <p class="empty-message mt-2">还没有笔记，来写下第一条吧！</p>
      </div>

      <div v-else class="comments-content">
        <div 
          v-for="comment in comments" 
          :key="comment.id" 
          class="comment-item">
          
          <div class="comment-header">
            <div class="user-info">
              <v-avatar size="24" color="primary">
                <span class="text-caption">{{ comment.user?.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
              </v-avatar>
              <span class="username">{{ comment.user?.username || '匿名用户' }}</span>
            </div>
            <span class="comment-time">{{ formatTime(comment.create_time) }}</span>
          </div>
          
          <div class="comment-content">
            {{ comment.content }}
          </div>
          
          <div class="comment-actions" v-if="canDeleteComment(comment)">
            <v-btn
              icon="mdi-delete"
              variant="text"
              size="small"
              color="error"
              @click="deleteComment(comment.id)">
            </v-btn>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <v-snackbar v-model="errorSnackbar" color="error" timeout="3000">
      {{ errorMessage }}
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/stores/userStore'

// Props
interface Props {
  documentId: string
  document?: any
}

const props = defineProps<Props>()

// Store
const userStore = useUserStore()

// 状态
const isLoading = ref(false)
const comments = ref<any[]>([])
const newComment = ref('')
const errorSnackbar = ref(false)
const errorMessage = ref('')

// 计算属性
const currentUser = computed(() => ({
  id: userStore.userId,
  username: userStore.username,
  role: userStore.userRole
}))

// 生命周期
onMounted(() => {
  loadComments()
})

// 加载评论
const loadComments = async () => {
  try {
    isLoading.value = true
    
    // 这里应该调用API获取文档评论
    // const response = await commentService.getDocumentComments(props.documentId)
    // 临时使用模拟数据
    comments.value = [
      {
        id: '1',
        content: '这个文档很有用，特别是关于PDF处理的部分。',
        user: { username: 'student1' },
        create_time: new Date().toISOString()
      }
    ]
  } catch (error) {
    console.error('加载评论失败:', error)
    showError('加载评论失败')
  } finally {
    isLoading.value = false
  }
}

// 提交评论
const submitComment = async () => {
  if (!newComment.value.trim()) return
  
  try {
    // 这里应该调用API提交评论
    // const response = await commentService.createDocumentComment(props.documentId, newComment.value)
    
    // 临时处理：直接添加到本地列表
    const tempComment = {
      id: Date.now().toString(),
      content: newComment.value,
      user: currentUser.value,
      create_time: new Date().toISOString()
    }
    
    comments.value.unshift(tempComment)
    newComment.value = ''
  } catch (error) {
    console.error('发布评论失败:', error)
    showError('发布评论失败')
  }
}

// 删除评论
const deleteComment = async (commentId: string) => {
  try {
    // 这里应该调用API删除评论
    // await commentService.deleteComment(commentId)
    
    // 临时处理：从本地列表删除
    comments.value = comments.value.filter(c => c.id !== commentId)
  } catch (error) {
    console.error('删除评论失败:', error)
    showError('删除评论失败')
  }
}

// 检查是否可以删除评论
const canDeleteComment = (comment: any) => {
  return currentUser.value && 
         (currentUser.value.id === comment.user?.id || 
          currentUser.value.role === 'teacher' || 
          currentUser.value.role === 'admin')
}

// 格式化时间
const formatTime = (timeString: string) => {
  const time = new Date(timeString)
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时后`
  if (days < 7) return `${days}天前`
  
  return time.toLocaleDateString()
}

// 显示错误信息
const showError = (message: string) => {
  errorMessage.value = message
  errorSnackbar.value = true
}
</script>

<style scoped>
.document-comments {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.comment-input-section {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 12px;
  color: #1a1a1a;
}

.section-title .v-icon {
  margin-right: 8px;
}

.comment-input-container {
  margin-top: 12px;
}

.comment-textarea {
  margin-bottom: 8px;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
}

.comments-list {
  flex: 1;
  overflow-y: auto;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: #666;
}

.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
  color: #666;
  flex: 1;
}

.empty-message {
  font-size: 0.875rem;
  margin: 0;
}

.comments-content {
  padding: 0;
}

.comment-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.user-info {
  display: flex;
  align-items: center;
}

.username {
  margin-left: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #333;
}

.comment-time {
  font-size: 0.75rem;
  color: #999;
}

.comment-content {
  font-size: 0.875rem;
  line-height: 1.5;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 8px;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
  opacity: 0;
  transition: opacity 0.2s;
}

.comment-item:hover .comment-actions {
  opacity: 1;
}
</style> 