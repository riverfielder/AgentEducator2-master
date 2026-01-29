<template>
  <div class="task-monitor">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          资源处理任务监控
          <v-spacer></v-spacer>
          <div class="refresh-control">
            <label>
              <input type="checkbox" v-model="autoRefresh"> 自动刷新
            </label>
            <select v-model="refreshInterval" @change="handleRefreshIntervalChange">
              <option :value="5000">5秒</option>
              <option :value="10000">10秒</option>
              <option :value="30000">30秒</option>
              <option :value="60000">1分钟</option>
            </select>
            <button class="refresh-btn" @click="refreshData">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': isRefreshing }"></i> 刷新
            </button>
          </div>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <!-- 筛选和搜索 -->
          <div class="filter-section mb-4">
            <v-row align="center">
              <v-col cols="12" md="2">
                <v-select
                  v-model="taskTypeFilter"
                  :items="taskTypeOptions"
                  label="任务类型"
                  variant="outlined"
                  density="compact"
                  @update:model-value="fetchTasks"
                  clearable
                ></v-select>
              </v-col>
              <v-col cols="12" md="2">
                <v-select
                  v-model="statusFilter"
                  :items="statusOptions"
                  label="状态筛选"
                  variant="outlined"
                  density="compact"
                  @update:model-value="fetchTasks"
                  clearable
                ></v-select>
              </v-col>
              <v-col cols="12" md="5">
                <v-text-field
                  v-model="searchQuery"
                  label="搜索任务（资源标题）"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-magnify"
                  @update:model-value="handleSearch"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="3" class="text-right">
                <v-chip variant="outlined" class="mr-2">
                  总共 {{ totalTasks }} 个任务
                </v-chip>
              </v-col>
            </v-row>
          </div>

          <!-- 任务列表 -->
          <div class="tasks-list-container">
            <v-data-table
              :headers="headers"
              :items="tasks"
              :loading="loading"
              :items-per-page="-1"
              hide-default-footer
              class="task-table"
              no-data-text="没有找到处理任务"
            >
              <!-- 资源信息列 -->
              <template v-slot:item.resource_info="{ item }">
                <div class="resource-info-cell">
                  <v-avatar size="60" class="mr-3">
                    <v-img
                      :src="getResourceIcon(item)"
                      :alt="item.resource_title"
                      cover
                    ></v-img>
                  </v-avatar>
                  <div>
                    <div class="resource-title font-weight-medium">{{ item.resource_title }}</div>
                    <div class="resource-meta text-caption text-medium-emphasis">
                      <v-chip
                        :color="getResourceTypeColor(item.resource_type)"
                        variant="tonal"
                        size="x-small"
                        class="mr-1"
                      >
                        {{ getResourceTypeText(item.resource_type) }}
                      </v-chip>
                      {{ item.resource_type === 'document' && item.file_type ? `(${item.file_type.toUpperCase()})` : '' }}
                      <br>
                      ID: {{ item.resource_id }}
                    </div>
                  </div>
                </div>
              </template>

              <!-- 状态列 -->
              <template v-slot:item.status="{ item }">
                <v-chip
                  :color="getStatusColor(item.status)"
                  variant="flat"
                  size="small"
                >
                  {{ getStatusText(item.status) }}
                </v-chip>
              </template>

              <!-- 进度列 -->
              <template v-slot:item.progress="{ item }">
                <div class="progress-cell">
                  <v-progress-linear
                    :model-value="Math.round(item.progress * 100)"
                    :color="getProgressColor(item.status)"
                    height="8"
                    rounded
                  ></v-progress-linear>
                  <div class="progress-text text-caption mt-1">
                    {{ Math.round(item.progress * 100) }}%
                  </div>
                </div>
              </template>

              <!-- 处理类型列 -->
              <template v-slot:item.processing_type="{ item }">
                <v-chip
                  variant="outlined"
                  size="small"
                  color="primary"
                >
                  {{ getProcessingTypeText(item.processing_type) }}
                </v-chip>
              </template>

              <!-- 时间信息列 -->
              <template v-slot:item.time_info="{ item }">
                <div class="time-info-cell">
                  <div class="time-row">
                    <span class="time-label">开始：</span>
                    <span class="time-value">{{ formatShortTime(item.start_time) }}</span>
                  </div>
                  <div v-if="item.end_time" class="time-row">
                    <span class="time-label">结束：</span>
                    <span class="time-value">{{ formatShortTime(item.end_time) }}</span>
                  </div>
                  <div v-if="item.start_time && item.end_time" class="time-row">
                    <span class="time-label">耗时：</span>
                    <span class="time-value duration">{{ calculateDuration(item.start_time, item.end_time) }}</span>
                  </div>
                  <div v-else-if="item.status === 'processing' || item.status === 'running'" class="time-row">
                    <span class="time-label">已运行：</span>
                    <span class="time-value duration">{{ calculateRunningDuration(item.start_time) }}</span>
                  </div>
                </div>
              </template>

              <!-- 操作列 -->
              <template v-slot:item.actions="{ item }">
                <div class="action-buttons">
                  <v-btn
                    variant="text"
                    size="small"
                    color="primary"
                    @click="openLogDialog(item)"
                  >
                    查看日志
                  </v-btn>
                  <v-btn
                    variant="text"
                    size="small"
                    color="error"
                    @click="confirmDeleteTask(item)"
                    :loading="isDeleting && selectedTask?.task_id === item.task_id"
                  >
                    删除
                  </v-btn>
                </div>
              </template>
            </v-data-table>

            <!-- 自定义分页组件 -->
            <div v-if="totalTasks > 0" class="custom-pagination mt-4">
              <v-row align="center" justify="space-between">
                <v-col cols="auto">
                  <div class="pagination-info">
                    显示第 {{ startIndex }} - {{ endIndex }} 条，共 {{ totalTasks }} 条记录
                  </div>
                </v-col>
                <v-col cols="auto">
                  <div class="pagination-controls d-flex align-center">
                    <!-- 每页条数选择 -->
                    <div class="items-per-page-control mr-4">
                      <span class="text-body-2 mr-2">每页条数:</span>
                      <v-select
                        v-model="itemsPerPage"
                        :items="itemsPerPageOptions"
                        variant="outlined"
                        density="compact"
                        style="min-width: 100px;"
                        @update:model-value="onItemsPerPageChange"
                      ></v-select>
                    </div>

                    <!-- 分页按钮 -->
                    <div class="pagination-buttons">
                      <v-btn
                        variant="text"
                        icon="mdi-page-first"
                        :disabled="currentPage <= 1"
                        @click="goToPage(1)"
                        size="small"
                      ></v-btn>
                      
                      <v-btn
                        variant="text"
                        icon="mdi-chevron-left"
                        :disabled="currentPage <= 1"
                        @click="goToPage(currentPage - 1)"
                        size="small"
                      ></v-btn>

                      <!-- 页码按钮 -->
                      <template v-for="page in visiblePages" :key="page">
                        <v-btn
                          v-if="page !== '...'"
                          variant="text"
                          :color="page === currentPage ? 'primary' : 'default'"
                          :disabled="page === currentPage"
                          @click="goToPage(page)"
                          size="small"
                          class="mx-1"
                        >
                          {{ page }}
                        </v-btn>
                        <span v-else class="mx-1">...</span>
                      </template>

                      <v-btn
                        variant="text"
                        icon="mdi-chevron-right"
                        :disabled="currentPage >= totalPagesComputed"
                        @click="goToPage(currentPage + 1)"
                        size="small"
                      ></v-btn>

                      <v-btn
                        variant="text"
                        icon="mdi-page-last"
                        :disabled="currentPage >= totalPagesComputed"
                        @click="goToPage(totalPagesComputed)"
                        size="small"
                      ></v-btn>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-container>

    <!-- 日志查看对话框 -->
    <v-dialog v-model="showLogDialog" max-width="1000" scrollable>
      <v-card v-if="selectedTask">
        <v-card-title class="d-flex align-center">
          <v-icon start icon="mdi-file-document-outline"></v-icon>
          任务日志 - {{ selectedTask.resource_title }}
          <v-spacer></v-spacer>
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="showLogDialog = false"
          ></v-btn>
        </v-card-title>
        <v-divider></v-divider>
        
        <!-- 任务详情摘要 -->
        <v-card-text class="pb-0">
          <v-row>
            <v-col cols="12" md="6">
              <div class="task-summary">
                <h4 class="mb-2">任务信息</h4>
                <div class="summary-item">
                  <span class="label">任务ID：</span>
                  <span class="value">{{ selectedTask.task_id }}</span>
                </div>
                <div class="summary-item">
                  <span class="label">资源类型：</span>
                  <v-chip
                    :color="getResourceTypeColor(selectedTask.resource_type)"
                    variant="tonal"
                    size="small"
                  >
                    {{ getResourceTypeText(selectedTask.resource_type) }}
                  </v-chip>
                </div>
                <div class="summary-item">
                  <span class="label">资源ID：</span>
                  <span class="value">{{ selectedTask.resource_id }}</span>
                </div>
                <div class="summary-item">
                  <span class="label">处理类型：</span>
                  <span class="value">{{ getProcessingTypeText(selectedTask.processing_type) }}</span>
                </div>
                <div class="summary-item">
                  <span class="label">状态：</span>
                  <v-chip
                    :color="getStatusColor(selectedTask.status)"
                    variant="flat"
                    size="small"
                  >
                    {{ getStatusText(selectedTask.status) }}
                  </v-chip>
                </div>
                <div class="summary-item">
                  <span class="label">进度：</span>
                  <span class="value">{{ Math.round(selectedTask.progress * 100) }}%</span>
                </div>
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="task-summary">
                <h4 class="mb-2">时间信息</h4>
                <div class="summary-item">
                  <span class="label">开始时间：</span>
                  <span class="value">{{ formatTime(selectedTask.start_time) }}</span>
                </div>
                <div v-if="selectedTask.end_time" class="summary-item">
                  <span class="label">结束时间：</span>
                  <span class="value">{{ formatTime(selectedTask.end_time) }}</span>
                </div>
                <div class="summary-item">
                  <span class="label">{{ selectedTask.end_time ? '总耗时：' : '已运行：' }}</span>
                  <span class="value">
                    {{ selectedTask.end_time 
                      ? calculateDuration(selectedTask.start_time, selectedTask.end_time)
                      : calculateRunningDuration(selectedTask.start_time) 
                    }}
                  </span>
                </div>
              </div>
            </v-col>
          </v-row>
          
          <!-- 进度条 -->
          <v-progress-linear
            :model-value="Math.round(selectedTask.progress * 100)"
            :color="getProgressColor(selectedTask.status)"
            height="12"
            rounded
            class="mt-3"
          ></v-progress-linear>
          
          <!-- 错误信息 -->
          <v-alert
            v-if="selectedTask.status === 'failed' && selectedTask.error_message"
            type="error"
            variant="tonal"
            class="mt-3"
          >
            <strong>错误信息：</strong>{{ selectedTask.error_message }}
          </v-alert>
        </v-card-text>
        
        <v-divider></v-divider>
        
        <!-- 日志内容 -->
        <v-card-text style="height: 400px;">
          <div v-if="logsLoading" class="text-center pa-4">
            <v-progress-circular indeterminate></v-progress-circular>
            <div class="mt-2">加载日志中...</div>
          </div>
          
          <div v-else-if="logs.length === 0" class="text-center pa-4 text-medium-emphasis">
            该任务暂无处理日志
          </div>
          
          <div v-else class="logs-container">
            <div 
              v-for="log in logs" 
              :key="log.id" 
              :class="['log-item', `log-${log.log_level}`]"
            >
              <div class="log-header">
                <span class="log-timestamp">{{ formatTime(log.timestamp) }}</span>
                <v-chip
                  :color="getLogLevelColor(log.log_level)"
                  variant="flat"
                  size="x-small"
                  class="ml-2"
                >
                  {{ log.log_level.toUpperCase() }}
                </v-chip>
              </div>
              <div class="log-content">{{ log.message }}</div>
            </div>
          </div>
        </v-card-text>
        
        <v-divider></v-divider>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="refreshLogs" variant="outlined" prepend-icon="mdi-refresh">
            刷新日志
          </v-btn>
          <v-btn @click="showLogDialog = false" color="primary">
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteConfirm" max-width="500">
      <v-card>
        <v-card-title class="text-error">
          <v-icon start icon="mdi-alert" color="error"></v-icon>
          确认删除任务
        </v-card-title>
        
        <v-card-text>
          <p>您确定要删除此任务及其所有日志吗？</p>
          <v-alert
            v-if="selectedTask && (selectedTask.status === 'processing' || selectedTask.status === 'running')"
            type="warning"
            variant="tonal"
            class="mt-3"
          >
            <strong>警告</strong>: 该任务正在处理中，删除将会<strong>终止处理进程</strong>！
          </v-alert>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="default"
            variant="text"
            @click="showDeleteConfirm = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="isDeleting"
            :disabled="isDeleting"
            @click="deleteTask"
          >
            {{ isDeleting ? '删除中...' : '确认删除' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../stores/userStore';
import { ElMessage } from 'element-plus';
import taskService from '../../api/taskService';
import { teacherNavItems } from '../../config/navigation'; 

export default {
  name: 'TaskMonitor',
  setup() {
    // 状态变量
    const userStore = useUserStore();
    const router = useRouter();
    const tasks = ref([]);
    const loading = ref(false);
    const currentPage = ref(1);
    const totalPages = ref(1);
    const totalTasks = ref(0);
    const itemsPerPage = ref(10); // 默认每页10个任务
    const statusFilter = ref('');
    const taskTypeFilter = ref('');
    const searchQuery = ref('');
    const selectedTask = ref(null);
    const logs = ref([]);
    const logsLoading = ref(false);
    const autoRefresh = ref(true);
    const refreshInterval = ref(10000);
    const refreshTimer = ref(null);
    const isRefreshing = ref(false);
    const showDeleteConfirm = ref(false);
    const showLogDialog = ref(false);
    const isDeleting = ref(false);
    
    // 表格列定义
    const headers = ref([
      {
        title: '资源信息',
        key: 'resource_info',
        sortable: false,
        width: '300px'
      },
      {
        title: '状态',
        key: 'status',
        sortable: true,
        width: '100px'
      },
      {
        title: '进度',
        key: 'progress',
        sortable: true,
        width: '150px'
      },
      {
        title: '处理类型',
        key: 'processing_type',
        sortable: true,
        width: '120px'
      },
      {
        title: '时间信息',
        key: 'time_info',
        sortable: false,
        width: '200px'
      },
      {
        title: '操作',
        key: 'actions',
        sortable: false,
        width: '150px'
      }
    ]);

    // 状态选项
    const statusOptions = ref([
      { title: '所有状态', value: '' },
      { title: '等待处理', value: 'pending' },
      { title: '处理中', value: 'processing' },
      { title: '运行中', value: 'running' },
      { title: '已完成', value: 'completed' },
      { title: '失败', value: 'failed' },
      { title: '已取消', value: 'cancelled' }
    ]);

    // 任务类型选项
    const taskTypeOptions = ref([
      { title: '所有类型', value: 'all' },
      { title: '视频处理', value: 'video' },
      { title: '文档处理', value: 'document' }
    ]);

    // 分页选项
    const itemsPerPageOptions = ref([
      { value: 10, title: '10条/页' },
      { value: 15, title: '15条/页' },
      { value: 20, title: '20条/页' },
      { value: 25, title: '25条/页' },
      { value: 50, title: '50条/页' }
    ]);

    // 计算属性
    const totalPagesComputed = computed(() => Math.ceil(totalTasks.value / itemsPerPage.value));
    const startIndex = computed(() => (currentPage.value - 1) * itemsPerPage.value + 1);
    const endIndex = computed(() => Math.min(currentPage.value * itemsPerPage.value, totalTasks.value));
    
    // 可见页码计算
    const visiblePages = computed(() => {
      const pages = [];
      const total = totalPagesComputed.value;
      const current = currentPage.value;
      
      if (total <= 7) {
        // 如果总页数少于等于7，显示所有页码
        for (let i = 1; i <= total; i++) {
          pages.push(i);
        }
      } else {
        // 复杂的分页逻辑
        if (current <= 4) {
          // 当前页在前部
          pages.push(1, 2, 3, 4, 5, '...', total);
        } else if (current >= total - 3) {
          // 当前页在后部
          pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total);
        } else {
          // 当前页在中部
          pages.push(1, '...', current - 1, current, current + 1, '...', total);
        }
      }
      
      return pages;
    });
    
    // 获取任务列表
    const fetchTasks = async () => {
      loading.value = true;
      try {
        const response = await taskService.getTasksList({
          page: currentPage.value,
          size: itemsPerPage.value,
          status: statusFilter.value || undefined,
          task_type: taskTypeFilter.value || undefined,
          search: searchQuery.value || undefined
        });
        
        if (response.data.code === 200) {
          const newTasks = response.data.data.list || [];
          const newTotal = response.data.data.total || 0;
          
          // 更新数据
          tasks.value = newTasks;
          totalTasks.value = newTotal;
          totalPages.value = Math.ceil(newTotal / itemsPerPage.value);
          
          // 调试信息
          console.log('🔍 [分页调试] 数据加载完成:', {
            total: totalTasks.value,
            currentPage: currentPage.value,
            itemsPerPage: itemsPerPage.value,
            totalPages: totalPages.value,
            tasksCount: tasks.value.length,
            paginationEnabled: totalTasks.value > itemsPerPage.value
          });
          
          // 验证分页数据完整性
          if (totalTasks.value > 0 && tasks.value.length === 0) {
            console.warn('⚠️ [分页警告] 总数大于0但任务列表为空，可能需要调整页码');
            if (currentPage.value > 1) {
              currentPage.value = 1;
              return fetchTasks(); // 重新获取第一页数据
            }
          }
        } else {
          console.error('获取任务列表失败:', response.msg);
          tasks.value = [];
          totalTasks.value = 0;
        }
      } catch (error) {
        console.error('获取任务列表出错:', error);
        tasks.value = [];
        totalTasks.value = 0;
      } finally {
        loading.value = false;
        isRefreshing.value = false;
      }
    };
    
    // 获取任务日志
    const fetchTaskLogs = async (taskId) => {
      if (!taskId) return;
      
      logsLoading.value = true;
      try {
        const response = await taskService.getTaskLogs(taskId);
        
        if (response.data.code === 200) {
          logs.value = response.data.data.logs;
          // 更新选中的任务信息
          const taskInfo = response.data.data.task;
          if (taskInfo) {
            selectedTask.value = taskInfo;
          }
        } else {
          console.error('获取任务日志失败:', response.msg);
        }
      } catch (error) {
        console.error('获取任务日志出错:', error);
      } finally {
        logsLoading.value = false;
      }
    };
    
    // 打开日志对话框
    const openLogDialog = (task) => {
      selectedTask.value = task;
      showLogDialog.value = true;
      fetchTaskLogs(task.task_id);
    };

    // 刷新日志
    const refreshLogs = () => {
      if (selectedTask.value) {
        fetchTaskLogs(selectedTask.value.task_id);
      }
    };
    
    // 搜索处理
    let searchTimeout = null;
    const handleSearch = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      searchTimeout = setTimeout(() => {
        currentPage.value = 1; // 重置到第一页
        fetchTasks();
      }, 500); // 500ms 防抖
    };

    // 跳转到指定页面
    const goToPage = (page) => {
      if (page >= 1 && page <= totalPagesComputed.value && page !== currentPage.value) {
        console.log('🔍 [分页调试] 跳转到页面:', { 
          oldPage: currentPage.value, 
          newPage: page,
          totalTasks: totalTasks.value,
          itemsPerPage: itemsPerPage.value
        });
        currentPage.value = page;
        fetchTasks();
      }
    };

    // 每页条数变化处理
    const onItemsPerPageChange = (newItemsPerPage) => {
      console.log('🔍 [分页调试] 每页条数变化:', { 
        oldItemsPerPage: itemsPerPage.value, 
        newItemsPerPage 
      });
      itemsPerPage.value = newItemsPerPage;
      currentPage.value = 1; // 重置到第一页
      fetchTasks();
    };
    
    // 刷新数据
    const refreshData = () => {
      isRefreshing.value = true;
      fetchTasks();
    };
      // 设置自动刷新
    const setupAutoRefresh = () => {
      clearAutoRefresh();
      
      if (autoRefresh.value) {
        refreshTimer.value = setInterval(refreshData, refreshInterval.value);
      }
    };
    
    // 清除自动刷新
    const clearAutoRefresh = () => {
      if (refreshTimer.value) {
        clearInterval(refreshTimer.value);
        refreshTimer.value = null;
      }
    };
    
    // 当刷新间隔改变时
    const handleRefreshIntervalChange = () => {
      setupAutoRefresh();
    };
    
    // 确认删除任务
    const confirmDeleteTask = (task) => {
      selectedTask.value = task;
      showDeleteConfirm.value = true;
    };
    
    // 删除任务
    const deleteTask = async () => {
      if (!selectedTask.value) return;
      
      isDeleting.value = true;
      try {
        const response = await taskService.deleteTask(selectedTask.value.task_id);
        
        if (response.data.code === 200) {
          // 从响应中获取删除信息
          const deleteData = response.data.data;
          const message = response.data.message || '任务删除成功';
          
          // 隐藏确认对话框
          showDeleteConfirm.value = false;
          showLogDialog.value = false;
          
          // 立即从任务列表中移除删除的任务，避免等待刷新
          if (deleteData && deleteData.taskTitle) {
            const taskId = selectedTask.value.task_id;
            tasks.value = tasks.value.filter(task => task.task_id !== taskId);
            totalTasks.value = Math.max(0, totalTasks.value - 1);
          }
          
          // 重新加载任务列表以确保数据同步
          fetchTasks();
          
          // 清空当前选择
          selectedTask.value = null;
          logs.value = [];
          
          // 显示成功消息，包含删除的详细信息
          if (deleteData && deleteData.taskTitle) {
            ElMessage.success(`${message} - ${deleteData.taskTitle}`);
          } else {
            ElMessage.success(message);
          }
          
          // 在控制台输出删除详情（调试用）
          if (deleteData && deleteData.deletionLog) {
            console.log('任务删除详情:', deleteData.deletionLog);
          }
        } else {
          console.error('删除任务失败:', response.data.message || response.data.msg);
          ElMessage.error('删除任务失败: ' + (response.data.message || response.data.msg || '未知错误'));
        }
      } catch (error) {
        console.error('删除任务出错:', error);
        ElMessage.error('删除任务出错: ' + (error.message || '未知错误'));
      } finally {
        isDeleting.value = false;
      }
    };
    
    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'pending': '等待处理',
        'processing': '处理中',
        'running': '运行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
      };
      return statusMap[status] || status;
    };

    // 获取资源类型文本
    const getResourceTypeText = (resourceType) => {
      const typeMap = {
        'video': '视频',
        'document': '文档'
      };
      return typeMap[resourceType] || resourceType;
    };

    // 获取资源类型颜色
    const getResourceTypeColor = (resourceType) => {
      const colorMap = {
        'video': 'blue',
        'document': 'green'
      };
      return colorMap[resourceType] || 'grey';
    };

    // 获取处理类型文本
    const getProcessingTypeText = (processingType) => {
      const typeMap = {
        // 视频处理类型
        'transcoding': '视频转码',
        'thumbnail': '生成缩略图',
        'subtitle': '字幕处理',
        'all': '完整处理',
        
        // 文档处理类型
        'markitdown': 'Markdown转换',
        'segmentation': '智能分段',
        'vectorization': '向量化',
        'summary': '智能摘要'
      };
      return typeMap[processingType] || processingType;
    };

    // 获取资源图标
    const getResourceIcon = (item) => {
      if (item.resource_type === 'video') {
        return item.resource_cover || '/temp_img/default_video_thumbnail.jpg';
      } else if (item.resource_type === 'document') {
        // 文档使用文件类型图标
        return item.resource_cover || '/static/icons/document-icon.png';
      }
      return '/static/icons/default-icon.png';
    };
    
    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    };
    
    // 格式化时间
    const formatTime = (dateString) => {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      });    };
    
    // 计算运行时长（对于正在运行的任务）
    const calculateRunningDuration = (startTime) => {
      if (!startTime) return '';
      
      const start = new Date(startTime);
      const now = new Date();
      const diffMs = now - start;
      
      const diffSec = Math.floor(diffMs / 1000);
      const hours = Math.floor(diffSec / 3600);
      const minutes = Math.floor((diffSec % 3600) / 60);
      const seconds = diffSec % 60;
      
      if (hours > 0) {
        return `${hours}时${minutes}分${seconds}秒`;
      } else if (minutes > 0) {
        return `${minutes}分${seconds}秒`;
      } else {
        return `${seconds}秒`;
      }
    };

    // 获取状态颜色
    const getStatusColor = (status) => {
      const colorMap = {
        'pending': 'orange',
        'processing': 'blue',
        'completed': 'green',
        'failed': 'red',
        'cancelled': 'grey'
      };
      return colorMap[status] || 'grey';
    };

    // 获取进度条颜色
    const getProgressColor = (status) => {
      const colorMap = {
        'pending': 'orange',
        'processing': 'blue',
        'running': 'blue',
        'completed': 'green',
        'failed': 'red',
        'cancelled': 'grey'
      };
      return colorMap[status] || 'blue';
    };

    // 获取日志级别颜色
    const getLogLevelColor = (level) => {
      const colorMap = {
        'debug': 'grey',
        'info': 'blue',
        'warning': 'orange',
        'error': 'red'
      };
      return colorMap[level] || 'blue';
    };

    // 格式化短时间
    const formatShortTime = (timeStr) => {
      if (!timeStr) return '';
      const time = new Date(timeStr);
      return time.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    // 计算任务持续时间
    const calculateDuration = (startTime, endTime) => {
      if (!startTime || !endTime) return '';
      
      const start = new Date(startTime);
      const end = new Date(endTime);
      const diffMs = end - start;
      
      const diffSec = Math.floor(diffMs / 1000);
      const hours = Math.floor(diffSec / 3600);
      const minutes = Math.floor((diffSec % 3600) / 60);
      const seconds = diffSec % 60;
      
      if (hours > 0) {
        return `${hours}时${minutes}分${seconds}秒`;
      } else if (minutes > 0) {
        return `${minutes}分${seconds}秒`;
      } else {
        return `${seconds}秒`;
      }
    };
    
    // 登出
    const logout = () => {
      userStore.clearUserInfo();
      router.push('/login');
    };
    
    // 监听自动刷新的改变
    watch(autoRefresh, (newValue) => {
      if (newValue) {
        setupAutoRefresh();
      } else {
        clearAutoRefresh();
      }
    });
    
    // 组件挂载时
    onMounted(() => {
      fetchTasks();
      setupAutoRefresh();
    });
    
    // 组件卸载前
    onBeforeUnmount(() => {
      clearAutoRefresh();
    });
      return {
      // 数据
      userStore,
      tasks,
      loading,
      currentPage,
      totalPages,
      totalTasks,
      itemsPerPage,
      statusFilter,
      taskTypeFilter,
      searchQuery,
      selectedTask,
      logs,
      logsLoading,
      autoRefresh,
      refreshInterval,
      isRefreshing,
      showDeleteConfirm,
      showLogDialog,
      isDeleting,
      headers,
      statusOptions,
      taskTypeOptions,
      itemsPerPageOptions,
      
      // 计算属性
      totalPagesComputed,
      startIndex,
      endIndex,
      visiblePages,
      
      // 方法
      fetchTasks,
      openLogDialog,
      refreshLogs,
      handleSearch,
      goToPage,
      onItemsPerPageChange,
      refreshData,
      handleRefreshIntervalChange,
      confirmDeleteTask,
      deleteTask,
      getStatusText,
      getResourceTypeText,
      getResourceTypeColor,
      getProcessingTypeText,
      getResourceIcon,
      getStatusColor,
      getProgressColor,
      getLogLevelColor,
      formatDate,
      formatTime,
      formatShortTime,
      calculateDuration,
      calculateRunningDuration,
      logout
    };
  }
};
</script>

<style scoped>
.task-monitor {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.content-card > .v-card-text {
  overflow-y: auto;
  flex: 1;
}

/* 刷新控制 */
.refresh-control {
  display: flex;
  align-items: center;
  gap: 10px;
}

.refresh-control label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.refresh-control select {
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.refresh-btn {
  padding: 5px 10px;
  background: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}

.refresh-btn:hover {
  background: #1565c0;
}

/* 筛选部分 */
.filter-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

/* 任务表格相关样式 */
.tasks-list-container {
  margin-top: 16px;
}

/* 自定义分页样式 */
.custom-pagination {
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
  margin-top: 16px;
}

.pagination-info {
  color: #666;
  font-size: 14px;
}

.pagination-controls {
  gap: 8px;
}

.items-per-page-control {
  display: flex;
  align-items: center;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.task-table :deep(.v-data-table__wrapper) {
  border-radius: 8px;
  overflow: hidden;
}

.task-table :deep(.v-data-table-header) {
  background-color: #f5f5f5;
}

.task-table :deep(.v-data-table__td) {
  padding: 16px 12px;
  border-bottom: 1px solid #e0e0e0;
}

/* 视频信息单元格 */
.resource-info-cell {
  display: flex;
  align-items: center;
}

.resource-title {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-meta {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}

/* 进度单元格 */
.progress-cell {
  min-width: 120px;
}

.progress-text {
  text-align: center;
  font-size: 12px;
  color: #666;
}

/* 时间信息单元格 */
.time-info-cell {
  min-width: 160px;
}

.time-row {
  display: flex;
  align-items: center;
  margin-bottom: 2px;
  font-size: 12px;
}

.time-label {
  color: #666;
  min-width: 40px;
}

.time-value {
  color: #333;
  margin-left: 4px;
}

.time-value.duration {
  color: #1976d2;
  font-weight: 500;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
}

/* 日志对话框样式 */
.task-summary {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.summary-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.summary-item .label {
  color: #666;
  min-width: 80px;
}

.summary-item .value {
  color: #333;
  font-weight: 500;
}

/* 日志容器 */
.logs-container {
  max-height: 350px;
  overflow-y: auto;
}

.log-item {
  border-left: 4px solid #e0e0e0;
  padding: 12px 16px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.log-item:hover {
  background: #f0f0f0;
}

.log-item.log-debug {
  border-left-color: #9e9e9e;
}

.log-item.log-info {
  border-left-color: #2196f3;
}

.log-item.log-warning {
  border-left-color: #ff9800;
}

.log-item.log-error {
  border-left-color: #f44336;
  background: #ffebee;
}

.log-header {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.log-timestamp {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.log-content {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
  word-break: break-word;
  font-family: 'Monaco', 'Consolas', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .task-table :deep(.v-data-table__td) {
    padding: 8px;
  }
  
  .resource-info-cell {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .resource-info-cell .mr-3 {
    margin-right: 0 !important;
    margin-bottom: 8px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  
  .time-info-cell {
    min-width: 120px;
  }
}

/* 状态颜色样式 */
.status-pending {
  color: #ff9800;
}

.status-processing {
  color: #2196f3;
}

.status-completed {
  color: #4caf50;
}

.status-failed {
  color: #f44336;
}

.status-cancelled {
  color: #9e9e9e;
}
</style>

