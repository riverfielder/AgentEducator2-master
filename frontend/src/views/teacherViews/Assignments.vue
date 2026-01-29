<template>
  <div class="assignments-container">
    <v-container fluid>
      <!-- 顶部操作栏 -->
      <v-row class="mb-4">
        <v-col cols="12" class="d-flex flex-wrap justify-space-between align-center gap-4">
          <div class="d-flex flex-wrap align-center gap-4">
            <!-- 搜索框 -->
            <v-text-field
              v-model="searchQuery"
              placeholder="搜索作业"
              prepend-inner-icon="mdi-magnify"
              density="comfortable"
              hide-details
              style="min-width: 200px; max-width: 300px;"
              @update:model-value="handleSearch"
            ></v-text-field>

            <div class="d-flex flex-wrap align-center gap-4">
              <!-- 课程筛选 -->
              <v-select
                v-model="selectedCourse"
                :items="courses"
                item-title="name"
                item-value="id"
                label="按课程筛选"
                density="comfortable"
                hide-details
                style="min-width: 180px; max-width: 250px;"
                @update:model-value="handleFilter"
              ></v-select>

              <!-- 状态筛选 -->
              <v-select
                v-model="selectedStatus"
                :items="statusOptions"
                label="状态"
                density="comfortable"
                hide-details
                style="min-width: 120px; max-width: 150px;"
                @update:model-value="handleFilter"
              ></v-select>
            </div>
          </div>          <!-- 新建按钮 -->
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="handleCreate"
          >
            新建作业
          </v-btn>
        </v-col>
      </v-row>

      <!-- 作业列表 -->
      <v-row>
        <v-col cols="12">
          <v-card>
            <!-- 自定义加载动画 -->
            <div v-if="loading" class="loading-container">
              <div class="loading-content">
                <v-progress-circular
                  indeterminate
                  size="64"
                  width="4"
                  color="primary"
                  class="mb-4"
                ></v-progress-circular>
                <div class="loading-text">
                  <h3 class="text-h6 mb-2">正在加载作业列表</h3>
                  <p class="text-body-2 text-medium-emphasis">请稍候，正在获取最新数据...</p>
                </div>
                <!-- 骨架屏效果 -->
                <div class="skeleton-table mt-6">
                  <div class="skeleton-header">
                    <v-skeleton-loader
                      type="table-heading"
                      class="mb-2"
                    ></v-skeleton-loader>
                  </div>
                  <div class="skeleton-rows">
                    <v-skeleton-loader
                      v-for="i in 5"
                      :key="i"
                      type="table-row-divider"
                      class="mb-1"
                    ></v-skeleton-loader>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 数据表格 -->
            <v-data-table
              v-else
              :headers="headers"
              :items="assignments"
              :items-per-page="itemsPerPage"
              :page="currentPage"
              :length="totalItems"
              :items-per-page-options="[5, 10, 20, 50]"
              @update:options="handleTableUpdate"
              item-value="id"
              disable-sort
              hide-default-footer
              class="elevation-1"
            >
              <template v-slot:item="{ item }">
                <tr>
                  <td>
                    <div class="d-flex align-center">
                      <v-icon
                        :icon="getStatusIcon(item.status)"
                        :color="getStatusColor(item.status)"
                        class="me-2"
                        size="small"
                      ></v-icon>
                      {{ item.title }}
                    </div>
                  </td>
                  <td>{{ getCourseTitle(item.courseId) }}</td>
                  <td>{{ formatTime(item.publishTime) }}</td>
                  <td>{{ formatTime(item.dueDate) }}</td>
                  <td class="text-center">
                    <v-chip
                      :color="getStatusColor(item.teacherStatus || item.status)"
                      size="small"
                      class="text-uppercase"
                    >
                      <v-icon
                        :icon="getStatusIcon(item.teacherStatus || item.status)"
                        size="small"
                        class="me-1"
                      ></v-icon>
                      {{ getStatusText(item.teacherStatus || item.status) }}
                    </v-chip>
                  </td>                  <td class="text-center">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      class="me-2"
                      @click="handleView(item)"
                    >
                      <v-icon size="small">mdi-eye</v-icon>
                      <v-tooltip activator="parent" location="top">查看</v-tooltip>
                    </v-btn>
                    <!-- 草稿状态显示发布按钮 -->
                    <v-btn
                      v-if="(item.teacherStatus || item.status) === 'draft'"
                      icon
                      variant="text"
                      size="small"
                      class="me-2"
                      color="success"
                      @click="handlePublish(item)"
                    >
                      <v-icon size="small">mdi-send</v-icon>
                      <v-tooltip activator="parent" location="top">发布</v-tooltip>
                    </v-btn>
                    <!-- 待发布状态显示编辑按钮和取消按钮 -->
                    <v-btn
                      v-if="(item.teacherStatus || item.status) === 'scheduled'"
                      icon
                      variant="text"
                      size="small"
                      class="me-2"
                      color="warning"
                      @click="handleView(item)"
                    >
                      <v-icon size="small">mdi-clock-edit</v-icon>
                      <v-tooltip activator="parent" location="top">查看定时发布</v-tooltip>
                    </v-btn>
                    <!-- 已发布状态显示批改按钮 -->
                    <v-btn
                      v-if="(item.teacherStatus || item.status) === 'published'"
                      icon
                      variant="text"
                      size="small"
                      class="me-2"
                      @click="handleMark(item)"
                    >
                      <v-icon size="small">mdi-pencil</v-icon>
                      <v-tooltip activator="parent" location="top">批改</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click="handleDelete(item)"
                    >
                      <v-icon size="small">mdi-delete</v-icon>
                      <v-tooltip activator="parent" location="top">删除</v-tooltip>
                    </v-btn>
                  </td>
                </tr>
              </template>            </v-data-table>
              <!-- 自定义分页控件 - 模仿v-data-table footer样式 -->
            <div class="v-data-table-footer">              <div class="v-data-table-footer__items-per-page">
                <span class="v-data-table-footer__items-per-page-text">Items per page:</span>
                <v-select
                  v-model="itemsPerPage"
                  :items="[5, 10, 20, 50]"
                  density="compact"
                  variant="outlined"
                  hide-details
                  class="v-data-table-footer__items-per-page-select"
                  @update:model-value="() => { currentPage = 1; updateDisplayedData(); }"
                ></v-select>
              </div>
              <div class="v-data-table-footer__info">
                {{ ((currentPage - 1) * itemsPerPage + 1) }}-{{ Math.min(currentPage * itemsPerPage, totalItems) }} of {{ totalItems }}
              </div>
              <div class="v-data-table-footer__pagination">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  :disabled="currentPage === 1"
                  @click="() => { currentPage = 1; updateDisplayedData(); }"
                  class="v-data-table-footer__pagination-btn"
                >
                  <v-icon size="small">mdi-page-first</v-icon>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  :disabled="currentPage === 1"
                  @click="() => { currentPage--; updateDisplayedData(); }"
                  class="v-data-table-footer__pagination-btn"
                >
                  <v-icon size="small">mdi-chevron-left</v-icon>
                </v-btn>                <span class="v-data-table-footer__page-info">
                  {{ currentPage }}
                </span>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  :disabled="currentPage >= Math.ceil(totalItems / itemsPerPage)"
                  @click="() => { currentPage++; updateDisplayedData(); }"
                  class="v-data-table-footer__pagination-btn"
                >
                  <v-icon size="small">mdi-chevron-right</v-icon>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  :disabled="currentPage >= Math.ceil(totalItems / itemsPerPage)"
                  @click="() => { currentPage = Math.ceil(totalItems / itemsPerPage); updateDisplayedData(); }"
                  class="v-data-table-footer__pagination-btn"
                >
                  <v-icon size="small">mdi-page-last</v-icon>
                </v-btn>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>
      <!-- 删除确认对话框 -->
      <v-dialog v-model="deleteDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h6">
            确认删除
          </v-card-title>
          <v-card-text>
            确定要删除这个作业吗？此操作不可撤销。
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="grey-darken-1"
              variant="text"
              @click="deleteDialog = false"
            >
              取消
            </v-btn>
            <v-btn
              color="error"
              variant="text"
              :loading="deleting"
              @click="confirmDelete"
            >
              删除
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- 发布确认对话框 -->
      <v-dialog v-model="publishDialog" max-width="400">
        <v-card>
          <v-card-title class="text-h6">
            确认发布
          </v-card-title>
          <v-card-text>
            确定要发布这个作业草稿吗？发布后学生将能够看到并完成这个作业。
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="grey-darken-1"
              variant="text"
              @click="publishDialog = false"
            >
              取消
            </v-btn>
            <v-btn
              color="success"
              variant="text"
              :loading="publishing"
              @click="confirmPublish"
            >
              发布
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- 作业详情对话框 -->
      <AssignmentDetailDialog
        v-model="showDetailDialog"
        :assignment-id="selectedAssignmentId"
      />
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import { useSnackbar } from '../../stores/snackbarStore';
import assignmentService from '../../api/assignmentService';
import courseService from '../../api/courseService';
import type { Assignment } from '../../api/assignmentService';
import AssignmentDetailDialog from './components/AssignmentDetailDialog.vue';

const router = useRouter();
const snackbar = useSnackbar();

// 分页相关变量
const currentPage = ref(1);
const itemsPerPage = ref(10);
const totalItems = ref(0);

// 数据缓存相关
const allAssignments = ref<Assignment[]>([]); // 缓存所有数据
const displayedAssignments = ref<Assignment[]>([]); // 当前显示的数据
const isDataLoaded = ref(false); // 数据是否已加载
const lastLoadParams = ref<any>(null); // 上次加载的参数

// 基础数据
const loading = ref(false);
const searchQuery = ref('');
const selectedCourse = ref<string | null>(null);
const selectedStatus = ref('all');
const assignments = ref<Assignment[]>([]);
const courses = ref<Array<{ id: string; name: string }>>([]);

// 删除对话框
const deleteDialog = ref(false);
const deleting = ref(false);
const assignmentToDelete = ref<Assignment | null>(null);

// 发布对话框
const publishDialog = ref(false);
const publishing = ref(false);
const assignmentToPublish = ref<Assignment | null>(null);

// 作业详情对话框
const showDetailDialog = ref(false);
const selectedAssignmentId = ref('');

// 表格配置
const headers = [
  { title: '作业标题', key: 'title', align: 'start', sortable: true },
  { title: '所属课程', key: 'courseTitle', align: 'start', sortable: true },
  { title: '发布时间', key: 'publishTime', align: 'start', sortable: true },
  { title: '截止时间', key: 'dueDate', align: 'start', sortable: true },
  { title: '状态', key: 'status', align: 'center', sortable: true },
  { title: '操作', key: 'actions', align: 'center', sortable: false }
];

// 状态选项
const statusOptions = [
  { title: '全部', value: 'all' },
  { title: '草稿', value: 'draft' },
  { title: '待发布', value: 'scheduled' },
  { title: '已发布', value: 'published' }
];


async function fetchCourses() {
  try {
    const response = await courseService.getCourses()
    if (response.data && response.data.code === 200) {
      courses.value = response.data.data.list || []
    } else {
      console.error('获取课程列表响应格式错误:', response);
      snackbar.show({
        text: '获取课程列表失败',
        color: 'error'
      });
    }
  } catch (error) {
    console.error('获取课程列表失败:', error)
    snackbar.show({
      text: '获取课程列表失败',
      color: 'error'
    });
  }
}

// 获取课程标题
const getCourseTitle = (courseId: string | undefined) => {
  if (!courseId) return '-';
  const course = courses.value.find(c => c.id === courseId);
  return course ? course.name : '-';
};

// 获取状态图标
const getStatusIcon = (status: string | undefined) => {
  if (!status) return 'mdi-file-question-outline';
  const iconMap: Record<'draft' | 'published' | 'scheduled', string> = {
    draft: 'mdi-file-document-outline',
    published: 'mdi-file-check-outline',
    scheduled: 'mdi-clock-outline'
  };
  return iconMap[status as 'draft' | 'published' | 'scheduled'] || 'mdi-file-question-outline';
};

// 获取状态颜色
const getStatusColor = (status: string | undefined) => {
  if (!status) return 'grey';
  const colorMap: Record<'draft' | 'published' | 'scheduled', string> = {
    draft: 'grey',
    published: 'success',
    scheduled: 'warning'
  };
  return colorMap[status as 'draft' | 'published' | 'scheduled'] || 'grey';
};

// 获取状态文本
const getStatusText = (status: string | undefined) => {
  if (!status) return '-';
  const textMap: Record<'draft' | 'published' | 'scheduled', string> = {
    draft: '草稿',
    published: '已发布',
    scheduled: '待发布'
  };
  return textMap[status as 'draft' | 'published' | 'scheduled'] || status;
};

// 格式化时间
const formatTime = (timeString: string | undefined) => {
  if (!timeString) return '-';
  try {
    const date = new Date(timeString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch (error) {
    console.error('时间格式化错误:', error);
    return timeString;
  }
};

// 修改 loadData 支持缓存和前端分页
const loadData = async (forceReload = false) => {
  const currentParams = {
    courseId: selectedCourse.value || undefined,
    status: selectedStatus.value === 'all' ? undefined : selectedStatus.value,
    search: searchQuery.value || undefined
  };

  // 检查是否需要重新加载数据
  const paramsChanged = !lastLoadParams.value || 
    JSON.stringify(currentParams) !== JSON.stringify(lastLoadParams.value);

  if (!forceReload && isDataLoaded.value && !paramsChanged) {
    // 如果数据已加载且参数没变，只需要重新计算显示的数据
    updateDisplayedData();
    return;
  }

  loading.value = true;
  try {
    // 一次性加载所有数据（不分页）
    const params = {
      ...currentParams,
      page: 1,
      pageSize: 1000 // 加载大量数据
    };

    const response = await assignmentService.getAssignmentList(params);
    if (response.data && response.data.code === 200) {
      const list = response.data.data.list || [];
      allAssignments.value = list.map((item: any) => ({
        ...item,
        raw: item
      }));
      totalItems.value = response.data.data.total || 0;
      isDataLoaded.value = true;
      lastLoadParams.value = { ...currentParams };
      
      // 更新显示的数据
      updateDisplayedData();
    } else {
      allAssignments.value = [];
      totalItems.value = 0;
      displayedAssignments.value = [];
      snackbar.show({
        text: response.data?.message || '获取作业列表失败',
        color: 'error'
      });
    }
  } catch (error: any) {
    allAssignments.value = [];
    totalItems.value = 0;
    displayedAssignments.value = [];
    snackbar.show({
      text: error.response?.data?.message || '加载作业列表失败',
      color: 'error'
    });
  } finally {
    loading.value = false;
  }
};

// 更新当前页显示的数据
const updateDisplayedData = () => {
  const startIndex = (currentPage.value - 1) * itemsPerPage.value;
  const endIndex = startIndex + itemsPerPage.value;
  displayedAssignments.value = allAssignments.value.slice(startIndex, endIndex);
  assignments.value = displayedAssignments.value;
};

// 搜索防抖定时器
let searchTimeout: NodeJS.Timeout | null = null;

// 搜索处理
const handleSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  searchTimeout = setTimeout(() => {
    currentPage.value = 1; // 搜索时重置到第一页
    isDataLoaded.value = false; // 标记需要重新加载
    loadData();
  }, 500);
};

// 筛选处理
const handleFilter = () => {
  currentPage.value = 1; // 筛选时重置到第一页
  isDataLoaded.value = false; // 标记需要重新加载
  loadData();
};

// 新建作业
const handleCreate = () => {
  router.push('/create-assignment');
};

// 查看作业
const handleView = (assignment: Assignment) => {
  selectedAssignmentId.value = assignment.id as string;
  showDetailDialog.value = true;
};

// 批改作业
const handleMark = (assignment: Assignment) => {
  router.push(`/assignments/${assignment.id}/mark`);
};

// 删除作业
const handleDelete = (assignment: Assignment) => {
  assignmentToDelete.value = assignment;
  deleteDialog.value = true;
};

// 发布作业草稿
const handlePublish = (assignment: Assignment) => {
  assignmentToPublish.value = assignment;
  publishDialog.value = true;
};

// 确认删除
const confirmDelete = async () => {
  if (!assignmentToDelete.value?.id) return;

  deleting.value = true;
  try {
    await assignmentService.deleteAssignment(assignmentToDelete.value.id as any);
    snackbar.show({
      text: '删除成功',
      color: 'success'
    });
    deleteDialog.value = false;
    loadData();
  } catch (error) {
    console.error('删除作业失败:', error);
    snackbar.show({
      text: '删除失败',
      color: 'error'
    });
  } finally {
    deleting.value = false;
  }
};

// 确认发布草稿
const confirmPublish = async () => {
  if (!assignmentToPublish.value?.id) return;

  publishing.value = true;
  try {
    await assignmentService.updateAssignment(assignmentToPublish.value.id as string, {
      status: 'published'
    });
    snackbar.show({
      text: '发布成功',
      color: 'success'
    });
    publishDialog.value = false;
    loadData(); // 重新加载列表
  } catch (error: any) {
    console.error('发布作业失败:', error);
    snackbar.show({
      text: error.response?.data?.message || '发布失败',
      color: 'error'
    });
  } finally {
    publishing.value = false;
  }
};

// 定时刷新相关
const refreshInterval = ref<NodeJS.Timeout | null>(null);

// 生命周期
onMounted(async () => {
  await fetchCourses();
  loadData();
  
  // 设置定时刷新（每30秒检查一次状态变化）
  refreshInterval.value = setInterval(() => {
    loadData();
  }, 30000);
});

// 组件销毁时清理定时器
onBeforeUnmount(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
  }
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
});

// 分页、排序等表格事件处理
const handleTableUpdate = (options: any) => {
  let needUpdate = false;
  
  if (options.page !== undefined && options.page !== currentPage.value) {
    currentPage.value = options.page;
    needUpdate = true;
  }
  
  if (options.itemsPerPage !== undefined && options.itemsPerPage !== itemsPerPage.value) {
    itemsPerPage.value = options.itemsPerPage;
    currentPage.value = 1; // 改变每页条数时重置到第一页
    needUpdate = true;
  }
  
  if (needUpdate) {
    // 如果数据已加载，只需要更新显示的数据，不需要重新请求API
    if (isDataLoaded.value) {
      updateDisplayedData();
    } else {
      loadData();
    }
  }
};
</script>

<style scoped>
.assignments-container {
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

/* 加载动画样式 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 40px 20px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.02) 0%, rgba(var(--v-theme-secondary), 0.02) 100%);
}

.loading-content {
  text-align: center;
  max-width: 500px;
  width: 100%;
}

.loading-text {
  margin-bottom: 24px;
}

.loading-text h3 {
  color: rgba(var(--v-theme-on-surface), 0.87);
  font-weight: 500;
}

.loading-text p {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.skeleton-table {
  width: 100%;
  opacity: 0.6;
}

.skeleton-header {
  margin-bottom: 16px;
}

.skeleton-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 加载动画的呼吸效果 */
@keyframes breathe {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

.loading-content {
  animation: breathe 3s ease-in-out infinite;
}

/* 自定义分页控件样式 - 模仿v-data-table footer */
.v-data-table-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  min-height: 60px;
  padding: 0 16px;
  border-top: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  background-color: rgb(var(--v-theme-surface));
}

.v-data-table-footer__items-per-page {
  display: flex;
  align-items: center;
  margin-right: 32px;
}

.v-data-table-footer__items-per-page-text {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-right: 8px;
}

.v-data-table-footer__items-per-page-select {
  width: 120px;
  margin-left: 8px;
}

.v-data-table-footer__info {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-right: 32px;
}

.v-data-table-footer__pagination {
  display: flex;
  align-items: center;
}

.v-data-table-footer__pagination-btn {
  margin: 0 2px;
}

.v-data-table-footer__page-info {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0 12px;
  min-width: 60px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 600px) {
  .v-data-table-footer {
    flex-direction: column;
    align-items: stretch;
    padding: 8px 16px;
  }
  
  .v-data-table-footer__items-per-page,
  .v-data-table-footer__info {
    margin-right: 0;
    margin-bottom: 8px;
    justify-content: center;
  }
  
  .v-data-table-footer__pagination {
    justify-content: center;
  }
}
</style>