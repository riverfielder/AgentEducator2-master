<template>
  <div class="student-management">
    <v-container fluid class="pa-4">
      <v-card class="content-card">
        <v-card-title class="d-flex align-center py-4 px-6">
          学生管理
          <v-spacer></v-spacer>
          <v-text-field
            v-model="searchQuery"
            prepend-inner-icon="mdi-magnify"
            label="搜索学生..."
            single-line
            hide-details
            density="compact"
            variant="outlined"
            class="search-field"
            style="max-width: 300px"
            @input="searchStudents"
          ></v-text-field>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <!-- 导入学生区域 -->
          <v-card class="mb-6">
            <v-card-title class="py-3 px-6">
              <v-icon start color="primary">mdi-account-plus</v-icon>
              导入学生
              <v-spacer></v-spacer>
              <div class="d-flex align-center">
                <v-btn
                  color="primary"
                  variant="text"
                  class="mr-2"
                  @click="showSingleImport = true"
                >
                  <v-icon start>mdi-account-plus</v-icon>
                  单独导入
                </v-btn>
                <v-btn
                  color="primary"
                  variant="text"
                  @click="downloadTemplate"
                >
                  <v-icon start>mdi-download</v-icon>
                  下载模板
                </v-btn>
              </div>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-6">
              <v-sheet
                class="import-area"
                :class="{ 'drag-over': isDragging }"
                rounded
                border
                @dragover.prevent 
                @dragenter.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="onFileDrop"
              >
                <div class="import-inner" v-if="!importingFile">
                  <v-icon size="48" color="primary" class="mb-4">mdi-cloud-upload-outline</v-icon>
                  <h3 class="text-h6 mb-2">将文件拖放到此处</h3>
                  <p class="text-body-2 mb-4">或</p>
                  <v-btn
                    color="primary"
                    @click="$refs.fileInput.click()"
                  >
                    选择文件
                  </v-btn>
                  <input
                    ref="fileInput"
                    type="file"
                    @change="onFileSelected"
                    accept=".xlsx,.xls,.csv"
                    style="display: none"
                  />
                  <p class="text-caption text-medium-emphasis mt-4">支持格式：Excel (.xlsx, .xls), CSV</p>
                </div>
                <div class="import-progress" v-else>
                  <div class="d-flex justify-space-between align-center mb-2">
                    <span class="text-body-2">{{ importingFile.name }}</span>
                    <span class="text-body-2">{{ importProgress }}%</span>
                  </div>
                  <v-progress-linear
                    v-model="importProgress"
                    height="8"
                    rounded
                    color="primary"
                  ></v-progress-linear>
                  <div class="d-flex justify-end mt-4">
                    <v-btn
                      color="error"
                      variant="text"
                      @click="cancelImport"
                    >
                      取消导入
                    </v-btn>
                  </div>
                </div>
              </v-sheet>
            </v-card-text>
          </v-card>

          <!-- 学生列表 -->
          <v-card>
            <v-card-title class="py-3 px-6">
              <div class="d-flex align-center">
                <v-icon start color="primary">mdi-account-group</v-icon>
                学生列表
                <v-chip class="ml-2" color="primary" size="small">{{ totalStudents }}</v-chip>
              </div>
              <v-spacer></v-spacer>
              <div class="d-flex">
                <v-select
                  v-model="currentClass"
                  :items="courseFilterOptions"
                  label="学生筛选"
                  hide-details
                  density="compact"
                  variant="outlined"
                  class="mr-2"
                  style="min-width: 150px"
                  @update:model-value="fetchStudents"
                ></v-select>
                <v-select
                  v-model="currentSort"
                  :items="sortOptions"
                  label="排序方式"
                  hide-details
                  density="compact"
                  variant="outlined"
                  style="min-width: 150px"
                ></v-select>
              </div>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="pa-0">
              <v-data-table
                :headers="headers"
                :items="students"
                :loading="loading"
                :items-per-page="10"
                :items-per-page-options="[5, 10, 20, 50]"
                class="student-table"
              >                <template v-slot:item.avatar="{ item }">
                  <v-avatar size="40" color="grey-lighten-3">
                    <img 
                      v-if="item.avatar && !item.avatarLoadError" 
                      :src="item.avatar" 
                      @error="handleAvatarError($event, item)"
                      @load="handleAvatarLoad($event, item)"
                      style="width: 100%; height: 100%; object-fit: cover;" 
                    />
                    <div v-else-if="item.name && item.name.trim()" 
                         class="letter-avatar" 
                         :style="getLetterAvatarStyle(item.name)">
                      {{ item.name.charAt(0).toUpperCase() }}
                    </div>
                    <v-icon v-else>mdi-account</v-icon>
                  </v-avatar>
                </template>
                <template v-slot:item.name="{ item }">
                  <div class="font-weight-medium">{{ item.name }}</div>
                </template>
                <template v-slot:item.courses="{ item }">
                  <div v-if="item.teacherCourses && item.teacherCourses.length > 0">
                    <v-chip
                      v-for="course in item.teacherCourses"
                      :key="course.id"
                      size="small"
                      color="primary"
                      variant="outlined"
                      class="ma-1"
                    >
                      {{ course.name }}
                    </v-chip>
                  </div>
                  <div v-else class="text-caption text-grey">暂未加入具体课程</div>
                </template>
                <template v-slot:item.status="{ item }">
                  <v-chip
                    :color="getStatusColor(item.status)"
                    size="small"
                    class="text-caption"
                  >
                    {{ getStatusText(item.status) }}
                  </v-chip>
                </template>
                <template v-slot:item.actions="{ item }">
                  <div class="d-flex">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click="viewStudent(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click="editStudent(item)"
                    >
                      <v-icon>mdi-pencil</v-icon>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click="confirmDeleteStudent(item)"
                    >
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </div>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>
    </v-container>

    <!-- 单独导入弹出框 -->
    <v-dialog v-model="showSingleImport" max-width="500">
      <v-card>
        <v-card-title class="text-h5 py-4 px-6">
          单独导入学生
          <v-spacer></v-spacer>
          <v-btn icon @click="showSingleImport = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="py-4 px-6">
          <v-form ref="singleStudentForm" @submit.prevent="importSingleStudent">
            <v-text-field
              v-model="singleStudent.name"
              label="姓名"
              required
              variant="outlined"
              class="mb-3"
            ></v-text-field>
            <v-text-field
              v-model="singleStudent.user_number"
              label="学号"
              required
              variant="outlined"
              class="mb-3"
              hint="学号必须以大写S开头"
              persistent-hint
              @focus="handleUserNumberFocus"
              @input="handleUserNumberInput"
            ></v-text-field>
            <v-text-field
              v-model="singleStudent.email"
              label="邮箱"
              required
              variant="outlined"
              class="mb-3"
              type="email"
            ></v-text-field>
            <v-select
              v-model="singleStudent.courseId"
              :items="availableCourses"
              item-title="displayName"
              item-value="id"
              label="选择课程"
              required
              variant="outlined"
              class="mb-3"
              :loading="loadingCourses"
            ></v-select>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey-darken-1" 
            variant="text" 
            @click="showSingleImport = false"
          >
            取消
          </v-btn>
          <v-btn 
            color="primary" 
            @click="importSingleStudent"
            :loading="addingStudent"
          >
            确认导入
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认弹窗 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5 py-4 px-6">
          确认删除
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="py-4 px-6">
          <p>您确定要删除学生 <strong>{{ studentToDelete?.name }}</strong> 吗？此操作无法撤销。</p>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey-darken-1" 
            variant="text" 
            @click="showDeleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn 
            color="error" 
            @click="deleteStudent"
            :loading="deletingStudent"
          >
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 学生详情弹窗 -->
    <v-dialog v-model="showStudentDetail" max-width="800">
      <v-card>
        <v-card-title class="text-h5 py-4 px-6">
          学生详情
          <v-spacer></v-spacer>
          <v-btn icon @click="showStudentDetail = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="py-4 px-6" v-if="selectedStudent">
          <div class="d-flex flex-column flex-md-row">
            <!-- 左侧：学生基本信息 -->
            <div class="text-center mb-4 mb-md-0 mr-md-6" style="min-width: 200px;">
              <!-- 姓名 -->
              <div class="text-h5 font-weight-bold mb-3">{{ selectedStudent.username }}</div>
              <!-- 学生学号 -->
              <div class="text-subtitle-1 text-medium-emphasis mb-3">学号: {{ selectedStudent.user_number || '未设置' }}</div>
              <!-- 头像 -->
              <v-avatar size="120" class="mb-3" color="grey-lighten-3">
                <img 
                  v-if="selectedStudent.avatar && !selectedStudent.avatarLoadError" 
                  :src="selectedStudent.avatar" 
                  @error="handleAvatarError($event, selectedStudent)"
                  @load="handleAvatarLoad($event, selectedStudent)"
                  style="width: 100%; height: 100%; object-fit: cover;" 
                />
                <div v-else-if="selectedStudent.name && selectedStudent.name.trim()" 
                     class="letter-avatar" 
                     :style="getLetterAvatarStyle(selectedStudent.name)">
                  {{ selectedStudent.name.charAt(0).toUpperCase() }}
                </div>
                <v-icon v-else size="48">mdi-account</v-icon>
              </v-avatar>
            </div>
            
            <v-divider vertical class="d-none d-md-block mr-6"></v-divider>
            
            <!-- 右侧：详细信息 -->
            <div class="flex-grow-1">
              <v-row>
                <v-col cols="12" md="6">
                  <div class="text-subtitle-2 text-medium-emphasis mb-1">用户名</div>
                  <div class="text-subtitle-1 mb-3">{{ selectedStudent.username }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-subtitle-2 text-medium-emphasis mb-1">状态</div>
                  <v-chip
                    :color="getStatusColor(selectedStudent.status)"
                    size="small"
                  >
                    {{ getStatusText(selectedStudent.status) }}
                  </v-chip>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-subtitle-2 text-medium-emphasis mb-1">邮箱</div>
                  <div class="text-subtitle-1 mb-3">{{ selectedStudent.email || '未设置' }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="text-subtitle-2 text-medium-emphasis mb-1">班级</div>
                  <div class="text-subtitle-1 mb-3">{{ selectedStudent.class || '未设置' }}</div>
                </v-col>
                <v-col cols="12">
                  <div class="text-subtitle-2 text-medium-emphasis mb-1">注册日期</div>
                  <div class="text-subtitle-1 mb-3">{{ formatDate(selectedStudent.create_time) || '未知' }}</div>
                </v-col>
                <v-col cols="12">
                  <div class="text-subtitle-2 text-medium-emphasis mb-1">选修课程</div>
                  <div v-if="studentCourses.length > 0">
                    <v-chip
                      v-for="course in studentCourses"
                      :key="course.id"
                      class="ma-1"
                      color="primary"
                      variant="outlined"
                    >
                      {{ course.name }}
                    </v-chip>
                  </div>
                  <div v-else class="text-subtitle-1 text-grey">暂无选修课程</div>
                </v-col>
              </v-row>
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="primary" 
            variant="text" 
            @click="manageCourses(selectedStudent)"
          >
            管理课程
          </v-btn>
          <v-btn 
            color="primary" 
            variant="text" 
            @click="editStudent(selectedStudent)"
          >
            编辑信息
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 编辑学生信息弹窗 -->
    <v-dialog v-model="showEditDialog" max-width="600">
      <v-card>
        <v-card-title class="text-h5 py-4 px-6">
          编辑学生信息
          <v-spacer></v-spacer>
          <v-btn icon @click="showEditDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="py-4 px-6" v-if="editingStudent">
          <v-form ref="editStudentForm" @submit.prevent="saveStudentEdit">
            <v-text-field
              v-model="editingStudent.name"
              label="姓名"
              required
              variant="outlined"
              class="mb-3"
              :error-messages="nameError"
              @input="clearNameError"
            ></v-text-field>
            <v-text-field
              v-model="editingStudent.user_number"
              label="学号"
              required
              variant="outlined"
              class="mb-3"
              hint="学号用于学生身份识别"
              persistent-hint
              :error-messages="userNumberError"
              @input="clearUserNumberError"
            ></v-text-field>
            <v-text-field
              v-model="editingStudent.email"
              label="邮箱"
              required
              variant="outlined"
              class="mb-3"
              type="email"
              :error-messages="emailError"
              @input="clearEmailError"
            ></v-text-field>
            <v-select
              v-model="editingStudent.status"
              :items="statusOptions"
              label="状态"
              required
              variant="outlined"
              class="mb-3"
              :error-messages="statusError"
              @update:model-value="clearStatusError"
            ></v-select>
            <v-text-field
              v-model="editingStudent.password"
              label="重置密码"
              type="password"
              variant="outlined"
              class="mb-3"
              hint="留空表示不修改密码"
              persistent-hint
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey-darken-1" 
            variant="text" 
            @click="showEditDialog = false"
          >
            取消
          </v-btn>
          <v-btn 
            color="primary" 
            @click="saveStudentEdit"
            :loading="savingStudent"
          >
            保存修改
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 管理课程弹窗 -->
    <v-dialog v-model="showManageCoursesDialog" max-width="800">
      <v-card>
        <v-card-title class="text-h5 py-4 px-6">
          管理学生课程
          <v-spacer></v-spacer>
          <v-btn icon @click="showManageCoursesDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="py-4 px-6" v-if="selectedStudent">
          <div class="mb-4">
            <div class="text-subtitle-1 font-weight-bold mb-2">{{ selectedStudent.name }} 已选课程</div>
            <v-chip-group>
              <v-chip
                v-for="course in studentCourses"
                :key="course.id"
                class="ma-1"
                color="primary"
                closable
                @click:close="removeStudentCourse(course.id)"
              >
                {{ course.name }}
              </v-chip>
            </v-chip-group>
            <div v-if="studentCourses.length === 0" class="text-subtitle-2 text-grey">
              该学生暂未选修任何课程
            </div>
          </div>
          
          <v-divider class="my-4"></v-divider>
          
          <div>
            <div class="text-subtitle-1 font-weight-bold mb-2">添加课程</div>
            <v-autocomplete
              v-model="selectedCoursesToAdd"
              :items="availableCourses"
              item-title="name"
              item-value="id"
              label="选择要添加的课程"
              multiple
              chips
              variant="outlined"
              class="mb-3"
            ></v-autocomplete>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey-darken-1" 
            variant="text" 
            @click="showManageCoursesDialog = false"
          >
            取消
          </v-btn>
          <v-btn 
            color="primary" 
            @click="saveCourseAssignments"
            :loading="assigningCourses"
          >
            保存课程设置
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 预览导入数据弹窗 -->
    <v-dialog v-model="showImportPreviewDialog" max-width="900">
      <v-card>
        <v-card-title class="text-h5 py-4 px-6">
          预览导入数据
          <v-spacer></v-spacer>
          <v-btn icon @click="showImportPreviewDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="py-4 px-6">
          <v-alert
            v-if="importPreviewData.invalidRecords && importPreviewData.invalidRecords.length > 0"
            type="warning"
            class="mb-4"
          >
            发现 {{ importPreviewData.invalidRecords.length }} 条无效数据，这些数据将被跳过。
          </v-alert>
          
          <div class="text-subtitle-1 font-weight-bold mb-2">
            有效数据 ({{ importPreviewData.validStudents?.length || 0 }} 条)
          </div>
          
          <v-table class="mb-4">
            <thead>
              <tr>
                <th>姓名</th>
                <th>学号</th>
                <th>邮箱</th>
                <th>课程</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(student, index) in importPreviewData.validStudents" :key="index">
                <td>{{ student.name }}</td>
                <td>{{ student.user_number }}</td>
                <td>{{ student.email }}</td>
                <td>{{ student.courseName }}</td>
              </tr>
            </tbody>
          </v-table>
          
          <div v-if="importPreviewData.invalidRecords && importPreviewData.invalidRecords.length > 0">
            <div class="text-subtitle-1 font-weight-bold mb-2">
              无效数据 ({{ importPreviewData.invalidRecords.length }} 条)
            </div>
            <v-table>
              <thead>
                <tr>
                  <th>行号</th>
                  <th>原因</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(record, index) in importPreviewData.invalidRecords" :key="index">
                  <td>{{ record.row }}</td>
                  <td>{{ record.reason }}</td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn 
            color="grey-darken-1" 
            variant="text" 
            @click="showImportPreviewDialog = false"
          >
            取消
          </v-btn>
          <v-btn 
            color="primary" 
            @click="confirmImportStudents"
            :loading="importingStudents"
            :disabled="!importPreviewData.validStudents || importPreviewData.validStudents.length === 0"
          >
            确认导入 {{ importPreviewData.validStudents?.length || 0 }} 名学生
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
  <div class="test">.</div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue';
import studentService from '../../api/studentService';
import courseService from '../../api/courseService';
import { useSnackbar } from '../../stores/snackbarStore';

export default {
  name: 'StudentManagement',
  setup() {
    const snackbar = useSnackbar();
    
    return {
      snackbar
    };
  },
  data() {
    return {
      searchQuery: '',
      isDragging: false,
      importingFile: null,
      importProgress: 0,
      showSingleImport: false,
      showDeleteDialog: false,
      showStudentDetail: false,
      showEditDialog: false,
      showManageCoursesDialog: false,
      showImportPreviewDialog: false,
      singleStudent: {
        name: '',
        email: '',
        user_number: 'S',  // 初始化为大写S
        courseId: null
      },
      currentClass: 'all',
      currentSort: 'user_number',
      loading: false,
      addingStudent: false,
      deletingStudent: false,
      savingStudent: false,
      assigningCourses: false,
      importingStudents: false,
      studentToDelete: null,
      selectedStudent: null,
      editingStudent: null,
      studentCourses: [],
      availableCourses: [],
      selectedCoursesToAdd: [],
      importPreviewData: {},

      // 表格头部定义
      headers: [
        { title: '头像', key: 'avatar', align: 'center', sortable: false, width: '80px' },
        { title: '姓名', key: 'name', align: 'start', sortable: true },
        { title: '学号', key: 'user_number', align: 'start', sortable: true },
        { title: '课程', key: 'courses', align: 'start', sortable: false },
        { title: '状态', key: 'status', align: 'center', sortable: true },
        { title: '邮箱', key: 'email', align: 'start', sortable: false },
        { title: '注册日期', key: 'create_time', align: 'start', sortable: true },
        { title: '操作', key: 'actions', align: 'center', sortable: false, width: '120px' }
      ],

      // 课程筛选选项
      courseFilterOptions: [
        { title: '所有学生', value: 'all' }
      ],

      // 排序选项
      sortOptions: [
        { title: '按学号排序', value: 'user_number' },
        { title: '按注册日期排序', value: 'create_time' },
        { title: '按状态排序', value: 'status' }
      ],

      // 状态选项
      statusOptions: [
        { title: '在读', value: 'active' },
        { title: '已毕业', value: 'graduated' },
        { title: '休学', value: 'suspended' },
        { title: '已转学', value: 'transferred' }
      ],

      // 学生数据
      students: [],
      loadingCourses: false,
      
      // 表单错误状态
      nameError: [],
      userNumberError: [],
      emailError: [],
      statusError: []
    }
  },
  computed: {
    // 计算总学生数
    totalStudents() {
      return this.totalItems;
    }
  },
  async mounted() {
    this.fetchStudents();
    this.fetchCourseFilterOptions(); // 获取课程筛选选项
    // 注意：fetchCourseFilterOptions和fetchAvailableCourses实际上调用同一个API
    // 为了避免重复调用，我们可以合并这两个功能
  },
  methods: {
    // 获取课程筛选选项
    async fetchCourseFilterOptions() {
      this.loadingCourses = true;
      try {
        const response = await studentService.getAvailableCourses();
        
        if (response.data && response.data.code === 200) {
          const courseList = response.data.data || [];
          
          // 更新课程筛选选项
          this.courseFilterOptions = [
            { title: '所有学生', value: 'all' },
            ...courseList.map(course => ({ 
              title: `${course.code} - ${course.name}`, 
              value: course.id 
            }))
          ];
          
          // 同时更新可选课程列表（用于单独导入）
          this.availableCourses = courseList.map(course => ({
            id: course.id,
            code: course.code,
            name: course.name,
            displayName: `${course.code} - ${course.name}` // 显示格式：课程代码 - 课程名称
          }));
        }
      } catch (error) {
        this.snackbar.show({
          text: '获取课程列表失败',
          color: 'error'
        });
        // 保持默认选项
        this.availableCourses = [];
      } finally {
        this.loadingCourses = false;
      }
    },
    // 处理表格更新（分页、排序等）
    handleTableUpdate(options) {
      // 处理分页
      this.currentPage = options.page || 1;
      this.itemsPerPage = options.itemsPerPage || 10;
      
      // 处理排序
      if (options.sortBy && options.sortBy.length > 0) {
        this.currentSort = options.sortBy[0].key;
        this.sortDirection = options.sortBy[0].order;
      }
      
      // 重新加载数据
      this.fetchStudents();
    },
    
    // 搜索学生
    searchStudents() {
      // 重置为第一页并重新加载
      this.currentPage = 1; 
      this.fetchStudents();
    },
    
    // 文件拖放处理
    onFileDrop(event) {
      this.isDragging = false;
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        this.processFile(files[0]);
      }
    },
    
    // 文件选择处理
    onFileSelected(event) {
      const files = event.target.files;
      if (files.length > 0) {
        this.processFile(files[0]);
      }
    },
    
    // 处理导入文件
    async processFile(file) {
      // 检查文件类型
      const validTypes = [
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'application/csv',
        'text/plain' // 有些CSV可能被识别为文本
      ];
      
      const fileType = file.type;
      const fileExt = file.name.split('.').pop().toLowerCase();
      
      if (!validTypes.includes(fileType) && !['xlsx', 'xls', 'csv'].includes(fileExt)) {
        this.snackbar.show({
          text: '请上传Excel或CSV文件',
          color: 'error'
        });
        return;
      }
      
      // 开始上传
      this.importingFile = file;
      this.importProgress = 0;
      
      try {
        // 准备FormData
        const formData = new FormData();
        formData.append('file', file);
        
        // 模拟上传进度
        const timer = setInterval(() => {
          this.importProgress += 10;
          if (this.importProgress >= 90) {
            clearInterval(timer);
          }
        }, 200);
        
        // 上传文件
        const response = await studentService.uploadStudentList(formData);
        
        // 清除定时器并设置为100%
        clearInterval(timer);
        this.importProgress = 100;
        
        // 显示导入预览
        if (response.data && response.data.code === 200) {
          this.importPreviewData = response.data.data;
          setTimeout(() => {
            this.importingFile = null;
            this.showImportPreviewDialog = true;
          }, 500);
        } else {
          throw new Error(response.data?.message || '文件解析失败');
        }
      } catch (error) {
        this.snackbar.show({
          text: '文件上传失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
        this.importingFile = null;
        this.importProgress = 0;
      }
    },
    
    // 确认批量导入学生
    async confirmImportStudents() {
      this.importingStudents = true;
      
      try {
        // 检查数据是否存在
        if (!this.importPreviewData.validStudents || this.importPreviewData.validStudents.length === 0) {
          throw new Error('没有有效的学生数据可导入');
        }
        
        // 发送有效学生数据进行导入
        const response = await studentService.importStudents({
          students: this.importPreviewData.validStudents
        });
        
        if (response.data && response.data.code === 200) {
          this.snackbar.show({
            text: `成功导入 ${response.data.data?.successCount || 0} 名学生`,
            color: 'success'
          });
          
          // 关闭预览窗口并刷新列表
          this.showImportPreviewDialog = false;
          this.fetchStudents();
        } else {
          throw new Error(response.data?.message || '导入失败');
        }
      } catch (error) {
        this.snackbar.show({
          text: '导入学生失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
      } finally {
        this.importingStudents = false;
      }
    },
    
    // 取消导入
    cancelImport() {
      this.importingFile = null;
      this.importProgress = 0;
    },
    
    // 单独导入学生
    async importSingleStudent() {
      // 验证表单
      if (!this.singleStudent.name || !this.singleStudent.email || !this.singleStudent.courseId || !this.singleStudent.user_number) {
        this.snackbar.show({
          text: '请填写所有必填字段',
          color: 'error'
        });
        return;
      }
      
      this.addingStudent = true;
      
      try {
        // 准备学生数据
        const studentData = {
          username: this.singleStudent.name.trim(), // 直接使用name作为username
          email: this.singleStudent.email.trim(),
          user_number: this.singleStudent.user_number.trim(),
          courseId: this.singleStudent.courseId
        };
        
        // 调用API添加学生
        const response = await studentService.addStudent(studentData);
        
        if (response.data && response.data.code === 200) {
          const result = response.data.data;
          let message = '学生添加并选课成功';
          if (result.isNewStudent) {
            message = '新学生创建并选课成功';
          } else {
            message = '学生已存在，选课成功';
          }
          
          this.snackbar.show({
            text: message,
            color: 'success'
          });
          
          // 使用新的重置方法
          this.resetSingleStudentForm();
          this.showSingleImport = false;
          
          // 刷新学生列表
          await this.fetchStudents();
        } else {
          throw new Error(response.data?.message || '添加失败');
        }
      } catch (error) {
        this.snackbar.show({
          text: '添加学生失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
      } finally {
        this.addingStudent = false;
      }
    },
    
    // 下载模板
    downloadTemplate() {
      // 创建一个临时链接并触发下载 - 使用新的CSV格式
      const headers = ['name(姓名)', 'email(邮箱)', 'user_number(学号)', 'course(课程)'];
      const csvContent = headers.join(',') + '\n' + 
                       '张三,zhangsan@example.com,S202500001,PY101\n' +
                       '李四,lisi@example.com,S202500002,CS-B201\n' +
                       '王五,wangwu@example.com,S202500003,NetworkApp';
      
      // 添加 BOM 头，确保 Excel 能正确识别 UTF-8 编码
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '学生导入模板.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      this.snackbar.show({
        text: '模板下载成功',
        color: 'success'
      });
    },
    
    // 查看学生详情
    async viewStudent(student) {
      this.selectedStudent = {...student};
      this.showStudentDetail = true;
      
      try {
        // 获取学生详细信息
        const response = await studentService.getStudentDetails(student.id);
        
        if (response.data && response.data.code === 200) {
          this.selectedStudent = response.data.data;
          
          // 获取学生课程
          this.fetchStudentCourses(student.id);
        }
      } catch (error) {
        this.snackbar.show({
          text: '获取学生详情失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
      }
    },
    
    // 获取学生课程
    async fetchStudentCourses(studentId) {
      try {
        const response = await studentService.getStudentCourses(studentId);
        
        if (response.data && response.data.code === 200) {
          this.studentCourses = response.data.data || [];
        }
      } catch (error) {
        this.snackbar.show({
          text: '获取学生课程失败',
          color: 'error'
        });
        this.studentCourses = [];
      }
    },
    
    // 管理课程
    async manageCourses(student) {
      this.showStudentDetail = false;
      this.showManageCoursesDialog = true;
      
      try {
        // 获取所有课程
        const coursesResponse = await courseService.getCourses();
        
        if (coursesResponse.data && coursesResponse.data.code === 200) {
          // 获取所有课程
          this.availableCourses = coursesResponse.data.data.list || [];
          
          // 获取学生已选课程
          await this.fetchStudentCourses(student.id);
          
          // 初始化已选课程IDs
          this.selectedCoursesToAdd = this.studentCourses.map(course => course.id);
        }
      } catch (error) {
        this.snackbar.show({
          text: '获取课程列表失败',
          color: 'error'
        });
      }
    },
    
    // 保存课程分配
    async saveCourseAssignments() {
      if (!this.selectedStudent) return;
      
      this.assigningCourses = true;
      
      try {
        // 调用API保存课程分配
        const response = await studentService.assignCourses(
          this.selectedStudent.id, 
          this.selectedCoursesToAdd
        );
        
        if (response.data && response.data.code === 200) {
          this.snackbar.show({
            text: '课程分配已保存',
            color: 'success'
          });
          
          // 关闭弹窗
          this.showManageCoursesDialog = false;
          
          // 更新学生课程显示
          await this.fetchStudentCourses(this.selectedStudent.id);
        } else {
          throw new Error(response.data?.message || '保存失败');
        }
      } catch (error) {
        this.snackbar.show({
          text: '保存课程分配失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
      } finally {
        this.assigningCourses = false;
      }
    },
    
    // 移除学生课程
    removeStudentCourse(courseId) {
      // 从选中课程中移除
      const index = this.selectedCoursesToAdd.indexOf(courseId);
      if (index !== -1) {
        this.selectedCoursesToAdd.splice(index, 1);
      }
    },
    
    // 编辑学生信息
    editStudent(student) {
      // 关闭详情弹窗（如果打开）
      this.showStudentDetail = false;
      
      // 复制学生数据到编辑对象
      this.editingStudent = {
        id: student.id,
        name: student.username || student.name, // 使用username作为name
        user_number: student.user_number || '',
        email: student.email || '',
        status: student.status || 'active',
        password: '' // 清空密码字段
      };
      
      // 清除错误状态
      this.clearAllErrors();
      
      // 显示编辑弹窗
      this.showEditDialog = true;
    },
    
    // 保存学生编辑
    async saveStudentEdit() {
      if (!this.editingStudent) return;
      
      // 清除之前的错误信息
      this.clearAllErrors();
      
      // 验证表单
      let hasError = false;
      
      if (!this.editingStudent.name || this.editingStudent.name.trim() === '') {
        this.nameError = ['姓名是必填字段'];
        hasError = true;
      }
      
      if (!this.editingStudent.user_number || this.editingStudent.user_number.trim() === '') {
        this.userNumberError = ['学号是必填字段'];
        hasError = true;
      }
      
      if (!this.editingStudent.email || this.editingStudent.email.trim() === '') {
        this.emailError = ['邮箱是必填字段'];
        hasError = true;
      } else if (!this.isValidEmail(this.editingStudent.email)) {
        this.emailError = ['请输入有效的邮箱地址'];
        hasError = true;
      }
      
      if (!this.editingStudent.status) {
        this.statusError = ['状态是必填字段'];
        hasError = true;
      }
      
      if (hasError) {
        this.snackbar.show({
          text: '请检查并填写所有必填字段',
          color: 'error'
        });
        return;
      }
      
      this.savingStudent = true;
      
      try {
        // 准备要更新的数据
        const updateData = {
          username: this.editingStudent.name.trim(), // 使用name作为username
          email: this.editingStudent.email.trim(),
          user_number: this.editingStudent.user_number.trim(),
          status: this.editingStudent.status
        };
        
        // 如果提供了密码，也更新密码
        if (this.editingStudent.password && this.editingStudent.password.trim() !== '') {
          updateData.password = this.editingStudent.password.trim();
        }
        
        console.log('更新学生数据:', updateData);
        
        // 调用API更新学生
        const response = await studentService.updateStudent(
          this.editingStudent.id,
          updateData
        );
        
        if (response.data && response.data.code === 200) {
          this.snackbar.show({
            text: '学生信息已更新',
            color: 'success'
          });
          
          // 关闭编辑弹窗
          this.showEditDialog = false;
          
          // 刷新学生列表
          await this.fetchStudents();
          
          // 如果详情弹窗是打开的，也刷新详情
          if (this.showStudentDetail && this.selectedStudent && this.selectedStudent.id === this.editingStudent.id) {
            await this.viewStudent(this.editingStudent);
          }
        } else {
          throw new Error(response.data?.message || '更新失败');
        }
      } catch (error) {
        console.error('更新学生信息失败:', error);
        this.snackbar.show({
          text: '更新学生信息失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
      } finally {
        this.savingStudent = false;
      }
    },
    
    // 确认删除学生
    confirmDeleteStudent(student) {
      this.studentToDelete = student;
      this.showDeleteDialog = true;
    },
    
    // 删除学生
    async deleteStudent() {
      if (!this.studentToDelete) return;
      
      this.deletingStudent = true;
      
      try {
        // 调用API删除学生
        const response = await studentService.deleteStudent(this.studentToDelete.id);
        
        if (response.data && response.data.code === 200) {
          this.snackbar.show({
            text: '学生已成功删除',
            color: 'success'
          });
          
          // 关闭删除确认弹窗
          this.showDeleteDialog = false;
          this.studentToDelete = null;
          
          // 刷新学生列表
          this.fetchStudents();
          
          // 如果详情弹窗是打开的且是当前删除的学生，关闭详情弹窗
          if (this.showStudentDetail && this.selectedStudent && this.selectedStudent.id === this.studentToDelete.id) {
            this.showStudentDetail = false;
          }
        } else {
          throw new Error(response.data?.message || '删除失败');
        }
      } catch (error) {
        this.snackbar.show({
          text: '删除学生失败: ' + (error.message || '未知错误'),
          color: 'error'
        });
      } finally {
        this.deletingStudent = false;
      }
    },
    
    // 获取状态对应的文本
    getStatusText(status) {
      const statusMap = {
        'active': '在读',
        'graduated': '已毕业',
        'suspended': '休学',
        'transferred': '已转学'
      };
      return statusMap[status] || status;
    },
    
    // 获取状态对应的颜色
    getStatusColor(status) {
      const colorMap = {
        'active': 'success',
        'graduated': 'primary',
        'suspended': 'warning',
        'transferred': 'grey'
      };
      return colorMap[status] || 'grey';
    },
    
    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    },
    
    // 获取学生列表
    async fetchStudents() {
      this.loading = true;
      try {
        // 准备查询参数
        const params = {
          page: 1,
          size: 100,
          sort: this.currentSort,
          keyword: this.searchQuery || undefined,
          courseId: this.currentClass !== 'all' ? this.currentClass : undefined
        };

        const response = await studentService.getStudents(params);
        if (response.data && response.data.code === 200) {
          let students = response.data.data.list || [];
          
          // 根据排序方式对学生列表进行排序
          students.sort((a, b) => {
            switch (this.currentSort) {
              case 'user_number':
                return (a.user_number || '').localeCompare(b.user_number || '');
              case 'create_time':
                return new Date(b.create_time) - new Date(a.create_time);
              case 'status':
                return a.status.localeCompare(b.status);
              default:
                return 0;
            }
          });

          // 处理学生数据
          this.students = students.map(student => ({
            ...student,
            name: student.username, // 只使用 username 作为显示名称
            user_number: student.user_number || '' // 确保 user_number 有值
          }));
          this.totalItems = response.data.data.total || students.length;
        }
      } catch (error) {
        console.error('获取学生列表失败:', error);
        this.snackbar.show({
          text: '获取学生列表失败',
          color: 'error'
        });
        this.students = [];
      } finally {
        this.loading = false;
      }
    },

    // 获取随机颜色 - 与Header组件保持一致
    getRandomColor(seed) {
      const colors = [
        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
        '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
      ];
      const index = seed.charCodeAt(0) % colors.length;
      return colors[index];
    },

    // 生成字母头像样式
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
      console.error('StudentManagement avatar error for:', item.name || item.username || 'unknown');
      // Vue 3 中直接设置属性即可实现响应式
      item.avatarLoadError = true;
      // 隐藏错误的图片元素
      event.target.style.display = 'none';
    },

    // 处理头像加载成功
    handleAvatarLoad(event, item) {
      console.log('StudentManagement avatar loaded for:', item.name || item.username || 'unknown');
      // Vue 3 中直接设置属性即可实现响应式
      item.avatarLoadError = false;
      event.target.style.display = 'block';
    },

    // 监听排序变化
    watchSort() {
      this.fetchStudents();
    },

    // 处理学号输入框获得焦点
    handleUserNumberFocus() {
      if (!this.singleStudent.user_number) {
        this.singleStudent.user_number = 'S';
      }
    },

    // 处理学号输入
    handleUserNumberInput(value) {
      // 如果用户删除了所有内容，重新添加S
      if (!value) {
        this.singleStudent.user_number = 'S';
        return;
      }
      
      // 确保第一个字符始终是大写S
      if (!value.startsWith('S')) {
        this.singleStudent.user_number = 'S' + value.replace(/^S/i, '');
      }
    },

    // 重置表单时确保学号字段为'S'
    resetSingleStudentForm() {
      this.singleStudent = {
        name: '',
        email: '',
        user_number: 'S',
        courseId: null
      };
    },

    // 添加错误处理方法
    clearNameError() {
      this.nameError = [];
    },
    clearUserNumberError() {
      this.userNumberError = [];
    },
    clearEmailError() {
      this.emailError = [];
    },
    clearStatusError() {
      this.statusError = [];
    },
    clearAllErrors() {
      this.nameError = [];
      this.userNumberError = [];
      this.emailError = [];
      this.statusError = [];
    },
    isValidEmail(email) {
      // 简单的邮箱格式验证
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
  },
  watch: {
    currentSort: 'watchSort'
  }
}
</script>

<style scoped>
.test{
  width: 100%;
  height: 100%;
  background-color: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #f8f9fa;
}
.student-management {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.pa-4{
  width: 100%;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;

  /* border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden; */
}

.content-card > .v-card-text {
  overflow-y: auto;
  flex: 1;
}

.search-field {
  max-width: 300px;
}

/* 导入区域样式 */
.import-area {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 2px dashed rgba(0, 0, 0, 0.12);
  border-radius: 8px;
  transition: all 0.3s ease;
  background-color: #f8f9fa;
}

.import-area.drag-over {
  border-color: #6f23d1;
  background-color: #f0f4ff;
  box-shadow: 0 0 10px rgba(111, 35, 209, 0.1);
}

.import-inner {
  text-align: center;
  width: 100%;
  padding: 20px;
}

.import-progress {
  width: 100%;
  padding: 20px;
}

/* 表格样式优化 */
.student-table {
  border-radius: 0;
}

:deep(.v-data-table) {
  background-color: transparent;
}

:deep(.v-data-table-header) {
  background-color: #f8f9fa;
}

:deep(.v-data-table-header th) {
  font-weight: 600;
  color: #212529;
  white-space: nowrap;
}

:deep(.v-data-table-footer) {
  background-color: #fff;
}

/* 响应式优化 */
@media (max-width: 600px) {
  .search-field {
    max-width: 100%;
  }
  :deep(.v-data-table) {
    width: 100%;
    overflow-x: auto;
  }
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