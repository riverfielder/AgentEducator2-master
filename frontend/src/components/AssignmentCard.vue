<template>
  <v-card
    class="assignment-card"
    elevation="0"
    hover
    @click="$emit('view', assignment)"
  >
    <!-- 状态条 -->
    <div class="status-indicator" :class="getStatusClass()"></div>
    
    <v-card-text class="card-content">
      <!-- 标题 -->
      <h3 class="assignment-title">{{ assignment.title }}</h3>
      
      <!-- 副标题信息 -->
      <div class="assignment-meta">
        <div class="meta-item">
          <v-icon size="16" class="meta-icon">mdi-book-outline</v-icon>
          <span class="meta-text">{{ displayCourseName }}</span>
        </div>
        <div class="meta-item">
          <v-icon size="16" class="meta-icon">mdi-account-outline</v-icon>
          <span class="meta-text">{{ displayTeacherName }}</span>
        </div>
        <div class="meta-item">
          <v-icon size="16" class="meta-icon">mdi-clock-outline</v-icon>
          <span class="meta-text">{{ formatTimeInfo }}</span>
        </div>
      </div>
      
      <!-- 状态和操作按钮 -->
      <div class="card-footer">
        <div class="status-chip" :class="getStatusClass()">
          <span class="status-text">{{ statusText }}</span>
        </div>
        
        <div class="action-buttons">
          <v-btn
            v-if="assignment.status === '未完成'"
            class="action-btn primary-btn"
            variant="flat"
            size="small"
            @click.stop="$emit('action', assignment)"
          >
            去作答
          </v-btn>
          <v-btn
            v-else-if="assignment.status === '已提交'"
            class="action-btn warning-btn"
            variant="flat"
            size="small"
            @click.stop="$emit('action', assignment)"
          >
            继续完成
          </v-btn>
          <v-btn
            v-else
            class="action-btn success-btn"
            variant="flat"
            size="small"
            @click.stop="$emit('view', assignment)"
          >
            查看结果
          </v-btn>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import userService from '@/api/userService';

interface Assignment {
  id: string | number;
  title: string;
  teacherName?: string;
  teacherId?: string;
  teacher?: string;
  courseName?: string;
  courseId?: string;
  dueDate: string;
  createTime?: string;
  status: string;
  timeInfo?: string;
}

const props = defineProps<{
  assignment: Assignment,
  statusText: string,
  statusColor: string
}>();

const teacherName = ref<string>('');

// 获取教师名称
const fetchTeacherName = async () => {
  if (props.assignment.teacherId && !props.assignment.teacherName) {
    try {
      const response = await userService.getUserById(props.assignment.teacherId);
      if (response.data.code === 200) {
        teacherName.value = response.data.data.name;
      }
    } catch (error) {
      console.error('获取教师信息失败:', error);
    }
  }
};

onMounted(() => {
  fetchTeacherName();
});

// 显示的教师名称
const displayTeacherName = computed(() => {
  return props.assignment.teacherName || teacherName.value || props.assignment.teacher || '未知教师';
});

// 显示的课程名称
const displayCourseName = computed(() => {
  return props.assignment.courseName || '未知课程';
});

// 格式化时间信息
const formatTimeInfo = computed(() => {
  if (props.assignment.timeInfo) {
    return props.assignment.timeInfo;
  }
  
  const dueDate = new Date(props.assignment.dueDate);
  const createTime = props.assignment.createTime ? new Date(props.assignment.createTime) : null;

  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  if (createTime) {
    return `创建于 ${formatDate(createTime)} | 截止 ${formatDate(dueDate)}`;
  }
  return `截止时间：${formatDate(dueDate)}`;
});

// 判断是否已过期
const isOverdue = computed(() => {
  const dueDate = new Date(props.assignment.dueDate);
  return new Date() > dueDate;
});

// 获取状态样式类
const getStatusClass = () => {
  switch (props.assignment.status) {
    case '未完成':
      return 'status-pending';
    case '已提交':
      return 'status-submitted';
    case '已完成':
      return 'status-completed';
    default:
      return 'status-default';
  }
};
</script>

<style scoped>
.assignment-card {
  border-radius: 20px;
  background: linear-gradient(145deg, #ffffff 0%, #fafbfc 100%);
  border: 1px solid rgba(229, 231, 235, 0.8);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
}

.assignment-card:hover {
  border-color: rgba(59, 130, 246, 0.3);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.12), 0 4px 10px rgba(0, 0, 0, 0.08);
  transform: translateY(-4px) scale(1.02);
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
}

.assignment-card:active {
  transform: translateY(-2px) scale(1.01);
  transition: all 0.15s ease;
}

.status-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 5px;
  height: 100%;
  border-radius: 0 3px 3px 0;
}

.status-pending {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 50%, #ea580c 100%);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
}

.status-submitted {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #1e40af 100%);
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.status-completed {
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}

.status-default {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 50%, #374151 100%);
  box-shadow: 0 0 10px rgba(107, 114, 128, 0.3);
}

.card-content {
  padding: 24px 24px 24px 32px;
}

.assignment-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 16px;
  line-height: 1.3;
  letter-spacing: -0.025em;
  background: linear-gradient(135deg, #111827 0%, #374151 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: all 0.3s ease;
}

.assignment-card:hover .assignment-title {
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.assignment-meta {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  padding: 6px 0;
  border-radius: 8px;
}

.meta-icon {
  color: #6b7280;
  margin-right: 12px;
  background: rgba(107, 114, 128, 0.1);
  padding: 4px;
  border-radius: 6px;
}

.meta-text {
  font-size: 0.9rem;
  color: #4b5563;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.status-chip {
  padding: 8px 16px;
  border-radius: 25px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.status-chip::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.status-chip:hover::before {
  left: 100%;
}

.status-chip.status-pending {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(249, 115, 22, 0.15) 100%);
  color: #ea580c;
  border: 1px solid rgba(245, 158, 11, 0.2);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1);
}

.status-chip.status-submitted {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(29, 78, 216, 0.15) 100%);
  color: #1e40af;
  border: 1px solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.status-chip.status-completed {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%);
  color: #047857;
  border: 1px solid rgba(16, 185, 129, 0.2);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.1);
}

.status-chip.status-default {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.15) 0%, rgba(75, 85, 99, 0.15) 100%);
  color: #374151;
  border: 1px solid rgba(107, 114, 128, 0.2);
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.1);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  border-radius: 12px;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.025em;
  min-width: 90px;
  height: 36px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.action-btn:hover::before {
  left: 100%;
}

.primary-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 50%, #1e40af 100%);
  color: white;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.warning-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 50%, #ea580c 100%);
  color: white;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.success-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%);
  color: white;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.action-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.primary-btn:hover {
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.warning-btn:hover {
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
}

.success-btn:hover {
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.action-btn:active {
  transform: translateY(-1px) scale(1.02);
  transition: all 0.15s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-content {
    padding: 20px 20px 20px 28px;
  }
  
  .assignment-title {
    font-size: 1.125rem;
  }
  
  .meta-text {
    font-size: 0.875rem;
  }
  
  .action-btn {
    min-width: 80px;
    height: 32px;
    font-size: 0.875rem;
  }
  
  .status-chip {
    padding: 6px 12px;
    font-size: 0.75rem;
  }
}

@media (max-width: 480px) {
  .card-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .status-chip {
    text-align: center;
  }
}
</style>