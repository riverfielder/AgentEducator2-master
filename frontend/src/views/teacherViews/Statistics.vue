<template>
  <div class="statistics-view">
    <v-container fluid class="pa-4 teacher-container">
      <v-card class="content-card mb-4">
        <v-card-title class="d-flex align-center py-4 px-6">
          <div class="d-flex align-center">
            <v-icon color="primary" class="mr-2">mdi-chart-areaspline</v-icon>
            <span class="text-h5">教学数据统计</span>
          </div>
          <v-spacer></v-spacer>
          
          <!-- 顶部筛选器 -->
          <div class="d-flex align-center">
            <v-select
              v-model="selectedCourse"
              :items="courses"
              item-title="name"
              item-value="id"
              label="选择课程"
              hide-details
              variant="outlined"
              density="compact"
              class="mr-2"
              style="min-width: 200px;"
              prepend-inner-icon="mdi-book-open-variant"
              @update:modelValue="loadStatistics"
            ></v-select>
            
            <v-select
              v-model="timePeriod"
              :items="timePeriods"
              label="时间周期"
              hide-details
              variant="outlined"
              density="compact"
              class="mr-2"
              style="width: 150px;"
              prepend-inner-icon="mdi-calendar-range"
              @update:modelValue="loadStatistics"
            ></v-select>
            
            <v-btn color="primary" @click="refreshData" class="ml-2">
              <v-icon start>mdi-refresh</v-icon>
              刷新
            </v-btn>
          </div>
        </v-card-title>
        
        <v-divider></v-divider>        <v-card-text class="pa-4 statistics-content">
          <!-- 概览卡片区域 -->
          <div class="overview-section">
            <v-row>
              <v-col v-for="(stat, index) in overviewStats" :key="index" cols="12" sm="6" md="3">
                <v-card
                  class="overview-card"
                  :color="stat.color"
                  rounded="lg"
                  elevation="3"
                  hover
                >
                  <v-card-text class="d-flex align-center pa-4 white--text">
                    <div class="stat-icon" :class="`stat-${index + 1}`">
                      <v-icon color="white" size="32">{{ stat.icon }}</v-icon>
                    </div>
                    <div class="ml-4">
                      <div class="text-h4 font-weight-bold">{{ stat.value }}</div>
                      <div class="text-body-2">{{ stat.label }}</div>
                      <div class="d-flex align-center mt-1">
                        <v-icon size="small" :color="stat.trend === 'up' ? 'light-green-accent-4' : 'red-accent-2'">
                          {{ stat.trend === 'up' ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                        </v-icon>
                        <span class="text-caption ml-1" :class="stat.trend === 'up' ? 'light-green-accent-4--text' : 'red-accent-2--text'">
                          {{ stat.change }}
                        </span>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
          <!-- 图表区域 -->
          <div class="charts-section mt-6">
            <v-row>
              <!-- 学生活跃度趋势图 -->
              <v-col cols="12" md="8">
                <v-card class="chart-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="primary" class="mr-2">mdi-chart-line</v-icon>
                    学生活跃度趋势
                    <v-spacer></v-spacer>
                    <v-btn-toggle
                      v-model="activityTimeRange"
                      mandatory
                      density="compact"
                      color="primary"
                      variant="outlined"
                    >
                      <v-btn value="week">
                        周
                      </v-btn>
                      <v-btn value="month">
                        月
                      </v-btn>
                    </v-btn-toggle>
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div ref="activeStudentsChart" class="chart-container"></div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- 知识点掌握度模块已移除 -->
              
              <!-- 视频观看排行 -->
              <v-col cols="12" md="6">
                <v-card class="chart-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="primary" class="mr-2">mdi-video</v-icon>
                    视频观看排行
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div ref="videoViewsChart" class="chart-container"></div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- 学习时长分布 -->
              <v-col cols="12" md="6">
                <StudyTimeChart 
                  :time-data="studyTimeDistribution" 
                  :loading="studyTimeLoading"
                />
              </v-col>
              
              <!-- 掌握最好知识点 -->
              <v-col cols="12" md="6">
                <v-card class="knowledge-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="success" class="mr-2">mdi-star</v-icon>
                    掌握最好知识点
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div v-if="loading" class="d-flex justify-center pa-4">
                      <v-progress-circular indeterminate color="primary"></v-progress-circular>
                    </div>
                    <div v-else-if="bestMasteredKnowledge.length === 0" class="text-center pa-4 text-grey">
                      <v-icon size="48" color="grey-lighten-1">mdi-information-outline</v-icon>
                      <div class="mt-2">暂无知识点数据</div>
                    </div>
                    <div v-else>
                      <v-list density="compact">
                        <v-list-item
                          v-for="(item, index) in bestMasteredKnowledge"
                          :key="item.keyword_id"
                          class="knowledge-item px-0"
                          @click="navigateToKnowledgeDetail(item.keyword_id)"
                          style="cursor: pointer;"
                        >
                          <template v-slot:prepend>
                            <v-chip
                              :color="index === 0 ? 'success' : index === 1 ? 'success-lighten-1' : 'success-lighten-2'"
                              size="small"
                              class="mr-3"
                            >
                              {{ index + 1 }}
                            </v-chip>
                          </template>
                          <v-list-item-title class="knowledge-name">{{ item.name }}</v-list-item-title>
                          <v-list-item-subtitle class="knowledge-category">{{ item.category_chinese || item.category }}</v-list-item-subtitle>
                          <template v-slot:append>
                            <div class="text-right">
                              <div class="knowledge-percentage">{{ item.mastery_percentage }}%</div>
                              <div class="knowledge-count text-caption">{{ item.student_count }}人</div>
                            </div>
                          </template>
                        </v-list-item>
                      </v-list>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              
              <!-- 掌握较差知识点 -->
              <v-col cols="12" md="6">
                <v-card class="knowledge-card" elevation="2" rounded="lg">
                  <v-card-title class="chart-title py-3 px-6">
                    <v-icon color="warning" class="mr-2">mdi-alert</v-icon>
                    掌握较差知识点
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text class="pa-4">
                    <div v-if="loading" class="d-flex justify-center pa-4">
                      <v-progress-circular indeterminate color="primary"></v-progress-circular>
                    </div>
                    <div v-else-if="worstMasteredKnowledge.length === 0" class="text-center pa-4 text-grey">
                      <v-icon size="48" color="grey-lighten-1">mdi-information-outline</v-icon>
                      <div class="mt-2">暂无知识点数据</div>
                    </div>
                    <div v-else>
                      <v-list density="compact">
                        <v-list-item
                          v-for="(item, index) in worstMasteredKnowledge"
                          :key="item.keyword_id"
                          class="knowledge-item px-0"
                          @click="navigateToKnowledgeDetail(item.keyword_id)"
                          style="cursor: pointer;"
                        >
                          <template v-slot:prepend>
                            <v-chip
                              :color="index === 0 ? 'warning' : index === 1 ? 'warning-lighten-1' : 'warning-lighten-2'"
                              size="small"
                              class="mr-3"
                            >
                              {{ index + 1 }}
                            </v-chip>
                          </template>
                          <v-list-item-title class="knowledge-name">{{ item.name }}</v-list-item-title>
                          <v-list-item-subtitle class="knowledge-category">{{ item.category_chinese || item.category }}</v-list-item-subtitle>
                          <template v-slot:append>
                            <div class="text-right">
                              <div class="knowledge-percentage">{{ item.mastery_percentage }}%</div>
                              <div class="knowledge-count text-caption">{{ item.student_count }}人</div>
                            </div>
                          </template>
                        </v-list-item>
                      </v-list>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
          <!-- 学生学习情况表格 -->
          <div class="data-tables-section mt-6">
            <v-card elevation="2" rounded="lg">
              <v-card-title class="py-3 px-6">
                <v-icon color="primary" class="mr-2">mdi-account-group</v-icon>
                学生学习情况
                <v-spacer></v-spacer>
                <v-text-field
                  v-model="search"
                  append-inner-icon="mdi-magnify"
                  label="搜索学生"
                  single-line
                  hide-details
                  density="compact"
                  style="max-width: 300px;"
                ></v-text-field>
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="pa-0">
                <v-data-table
                  :headers="studentHeaders"
                  :items="studentData"
                  :search="search"
                  :items-per-page="5"
                  hover
                  class="student-table"
                >
                  <template v-slot:item.progress="{ item }">
                    <v-progress-linear
                      :model-value="item.progress"
                      color="primary"
                      height="12"
                      rounded
                      striped
                    >
                      <template v-slot:default="{ value }">
                        <span class="progress-text">{{ Math.ceil(value) }}%</span>
                      </template>
                    </v-progress-linear>
                  </template>
                  
                  <template v-slot:item.lastActive="{ item }">
                    <span :class="getActivityClass(item.lastActive)">{{ item.lastActive }}</span>
                  </template>
                  
                  <template v-slot:item.actions="{ item }">
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click="viewStudentDetails(item)"
                    >
                      <v-icon>mdi-eye</v-icon>
                    </v-btn>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import courseService from '../../api/courseService';
import { useRouter } from 'vue-router';
import knowledgeMapService from '../../api/knowledgeMapService';
import StudyTimeChart from '../../components/charts/StudyTimeChart.vue';

// 不需要单独注册组件，echarts已经包含所有必要组件

const router = useRouter();
const activeStudentsChart = ref(null);
const masteryChart = ref(null);
const videoViewsChart = ref(null);
const courseCompletionChart = ref(null);
const search = ref('');
const loading = ref(false);
const studyTimeLoading = ref(false);
const selectedCourse = ref('');
const timePeriod = ref('month');
const activityTimeRange = ref('week');

// 图表实例引用
const chartsInstances = {
  activeStudents: null,
  mastery: null,
  videoViews: null
};

// 新增的图表数据
const studyTimeDistribution = ref([]);

// 知识点掌握度数据
const bestMasteredKnowledge = ref([]);
const worstMasteredKnowledge = ref([]);

// 课程下拉选项
const courses = ref([]);

// 时间周期选项
const timePeriods = [
  { value: 'week', title: '本周' },
  { value: 'month', title: '本月' },
  { value: 'semester', title: '本学期' }
];

// 模拟数据 - 总览统计
const overviewStats = ref([
  {
    label: '总学生人数',
    value: '256',
    icon: 'mdi-account-group',
    color: 'indigo',
    trend: 'up',
    change: '12% 增长',
  },
  {
    label: '活跃学生',
    value: '183',
    icon: 'mdi-account-check',
    color: 'teal',
    trend: 'up',
    change: '8% 增长',
  },
  {
    label: '视频观看次数',
    value: '1,354',
    icon: 'mdi-video-outline',
    color: 'deep-purple',
    trend: 'up',
    change: '24% 增长',
  }
]);

// 学生学习情况表格
const studentHeaders = [
  { title: '学生姓名', key: 'name', align: 'start', sortable: true },
  { title: '学号', key: 'studentId', align: 'start', sortable: true },
  { title: '教学材料进度', key: 'progress', align: 'center', sortable: true },
  { title: '视频完成数', key: 'completedVideos', align: 'center', sortable: true },
  { title: '文档完成数', key: 'completedDocs', align: 'center', sortable: true },
  { title: '学习时长', key: 'avgWatchTime', align: 'center', sortable: true },
  { title: '最近活跃', key: 'lastActive', align: 'center', sortable: true },
  { title: '操作', key: 'actions', align: 'center', sortable: false }
];

const studentData = ref([
  { 
    id: '1', 
    name: '张三', 
    studentId: '2023001', 
    progress: 87, 
    completedVideos: 18, 
    completedDocs: 12,
    avgWatchTime: '2小时45分钟',
    lastActive: '今天' 
  },
  { 
    id: '2', 
    name: '李四', 
    studentId: '2023002', 
    progress: 65, 
    completedVideos: 13, 
    completedDocs: 8,
    avgWatchTime: '1小时32分钟',
    lastActive: '昨天' 
  },
  { 
    id: '3', 
    name: '王五', 
    studentId: '2023003', 
    progress: 92, 
    completedVideos: 20, 
    completedDocs: 15,
    avgWatchTime: '3小时27分钟',
    lastActive: '今天' 
  },
  { 
    id: '4', 
    name: '赵六', 
    studentId: '2023004', 
    progress: 45, 
    completedVideos: 9, 
    completedDocs: 5,
    avgWatchTime: '58分钟',
    lastActive: '3天前' 
  },
  { 
    id: '5', 
    name: '钱七', 
    studentId: '2023005', 
    progress: 78, 
    completedVideos: 16, 
    completedDocs: 11,
    avgWatchTime: '2小时15分钟',
    lastActive: '今天' 
  },
  { 
    id: '6', 
    name: '孙八', 
    studentId: '2023006', 
    progress: 33, 
    completedVideos: 7, 
    completedDocs: 3,
    avgWatchTime: '45分钟',
    lastActive: '1周前' 
  },
  { 
    id: '7', 
    name: '周九', 
    studentId: '2023007', 
    progress: 59, 
    completedVideos: 12, 
    completedDocs: 7,
    avgWatchTime: '1小时20分钟',
    lastActive: '2天前' 
  }
]);

// 根据最近活跃时间设置样式
const getActivityClass = (lastActive) => {
  if (lastActive === '今天') return 'green--text';
  if (lastActive === '昨天') return 'blue--text';
  if (lastActive.includes('天前') && parseInt(lastActive) <= 3) return 'orange--text';
  return 'grey--text';
};

// 查看学生详情
const viewStudentDetails = (item) => {
  router.push(`/students/details/${item.id}`);
};

// 跳转到知识点详情页面
const navigateToKnowledgeDetail = (keywordId) => {
  if (selectedCourse.value) {
    router.push({
      path: `/teacher-knowledge-detail/${keywordId}`,
      query: {
        course_id: selectedCourse.value
      }
    });
  } else {
    console.warn('未选择课程，无法跳转到知识点详情页面');
  }
};

// 初始化学生活跃度趋势图表
const initActiveStudentsChart = () => {
  if (!activeStudentsChart.value) return;
  
  // 销毁已有实例
  if (chartsInstances.activeStudents) {
    chartsInstances.activeStudents.dispose();
  }
  
  // 创建图表实例
  chartsInstances.activeStudents = echarts.init(activeStudentsChart.value);
  
  // 模拟数据
  const weekData = {
    xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    series: [
      {
        name: '活跃学生数',
        data: [120, 132, 101, 134, 90, 70, 85]
      },
      {
        name: '视频观看次数',
        data: [220, 182, 191, 234, 290, 130, 150]
      }
    ]
  };
  
  const monthData = {
    xAxis: Array.from({length: 30}, (_, i) => `${i+1}日`),
    series: [
      {
        name: '活跃学生数',
        data: Array.from({length: 30}, () => Math.floor(Math.random() * 100 + 50))
      },
      {
        name: '视频观看次数',
        data: Array.from({length: 30}, () => Math.floor(Math.random() * 200 + 100))
      }
    ]
  };
  
  const data = activityTimeRange.value === 'week' ? weekData : monthData;
  
  // 配置选项
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['活跃学生数', '视频观看次数'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        position: 'left',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470C6'
          }
        },
        axisLabel: {
          formatter: '{value}'
        }
      },
      {
        type: 'value',
        name: '次数',
        position: 'left',
        show: false,
        axisLine: {
          show: true,
          lineStyle: {
            color: '#91CC75'
          }
        },
        axisLabel: {
          formatter: '{value}'
        }
      }
    ],
    series: [
      {
        name: '活跃学生数',
        type: 'bar',
        data: data.series[0].data,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#5470C6' },
              { offset: 1, color: '#91CC75' }
            ]
          }
        },
        yAxisIndex: 0,
        barWidth: activityTimeRange.value === 'week' ? '40%' : '60%'
      },
      {
        name: '视频观看次数',
        type: 'line',
        smooth: true,
        data: data.series[1].data,
        itemStyle: {
          color: '#EE6666'
        },
        yAxisIndex: 1
      }
    ],
    animationDuration: 1500
  };
  
  // 设置选项并渲染图表
  chartsInstances.activeStudents.setOption(option);
};

// 初始化知识点掌握度图表
const initMasteryChart = async () => {
  if (!masteryChart.value) {
    return;
  }
  
  try {
    // 先销毁已有实例
    if (chartsInstances.mastery) {
      chartsInstances.mastery.dispose();
    }
    
    // 创建新实例
    chartsInstances.mastery = echarts.init(masteryChart.value);
    
    // 先展示模拟数据
    const mockData = [
      { name: '张同学', value: 75.5 },
      { name: '李同学', value: 52.3 },
      { name: '王同学', value: 38.7 },
      { name: '赵同学', value: 65.2 },
      { name: '陈同学', value: 12.8 },
      { name: '周同学', value: 48.4 },
      { name: '吴同学', value: 25.6 },
      { name: '刘同学', value: 32.1 },
      { name: '孙同学', value: 38.9 },
      { name: '杨同学', value: 25.3 }
    ];
    
    // 更新图表的函数
    const updateChart = (data, isLoading = false) => {
      // 按掌握度排序
      const sortedData = [...data].sort((a, b) => b.value - a.value);
      
      // 取前10名
      const displayData = sortedData.slice(0, 10);
      
      // 配置图表选项
      const option = {
        title: {
          text: '学生平均知识点掌握度' + (isLoading ? ' (加载中...)' : ''),
          left: 'center',
          top: 10
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: '{b}: {c}%'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: 40,
          containLabel: true
        },
        xAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: {
            formatter: '{value}%'
          }
        },
        yAxis: {
          type: 'category',
          data: displayData.map(item => item.name).reverse(),
          axisLabel: {
            formatter: function(value) {
              if (value.length > 12) {
                return value.substring(0, 12) + '...';
              }
              return value;
            }
          }
        },
        series: [
          {
            name: '掌握度',
            type: 'bar',
            data: displayData.map(item => ({
              value: item.value,
              itemStyle: {
                color: item.value >= 90 ? '#67C23A' :
                       item.value >= 70 ? '#409EFF' :
                       item.value >= 50 ? '#E6A23C' : '#F56C6C'
              }
            })).reverse(),
            label: {
              show: true,
              position: 'right',
              formatter: '{c}%'
            }
          }
        ]
      };
      
      chartsInstances.mastery.setOption(option);
    };
    
    // 如果没有学生数据，显示暂无数据
    if (studentData.value.length === 0) {
      chartsInstances.mastery.setOption({
        title: {
          text: '暂无数据',
          left: 'center',
          top: 'middle'
        }
      });
      return;
    }
    
    // 先显示模拟数据
    updateChart(mockData, true);
    
    // 获取所有学生的掌握度数据
    const studentMasteryData = [];
    
    // 逐个获取学生数据
    for (const student of studentData.value) {
      const response = await knowledgeMapService.getMasteryOverview(student.id);
      
      if (response.data.code === 200) {
        const rawData = response.data.data || {};
        if (rawData.average_mastery) {
          studentMasteryData.push({
            name: student.name || `学生${student.id.substring(0, 4)}`,
            value: parseFloat(rawData.average_mastery).toFixed(1),
            studentId: student.id
          });
        }
      }
    }
    
    // 所有数据获取完成后，更新图表
    if (studentMasteryData.length > 0) {
      updateChart(studentMasteryData);
    }
    
  } catch (error) {
    console.error('获取知识点掌握度数据失败:', error);
  }
};

// 初始化视频观看排行图表
const initVideoViewsChart = () => {
  if (!videoViewsChart.value) return;
  
  // 销毁已有实例
  if (chartsInstances.videoViews) {
    chartsInstances.videoViews.dispose();
  }
  
  // 创建图表实例
  chartsInstances.videoViews = echarts.init(videoViewsChart.value);
  
  // 配置选项
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: [
        '第一章：课程介绍',
        '第二章：基础概念',
        '第三章：进阶技巧',
        '第四章：实战应用',
        '第五章：设计模式',
        '第六章：最佳实践',
        '第七章：总结展望'
      ].reverse(),
      axisLabel: {
        formatter: function (value) {
          if (value.length > 10) {
            return value.substring(0, 10) + '...';
          }
          return value;
        }
      }
    },
    series: [
      {
        name: '观看次数',
        type: 'bar',
        data: [235, 210, 198, 175, 142, 98, 76].reverse(),
        itemStyle: {
          color: {
            type: 'linear',
            x: 1, y: 0, x2: 0, y2: 0,
            colorStops: [
              { offset: 0, color: '#6f23d1' },
              { offset: 0.5, color: '#a35eea' },
              { offset: 1, color: '#d49fff' }
            ]
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c} 次'
        },
        animationDelay: function (idx) {
          return idx * 100 + 100;
        }
      }
    ],
    animationEasing: 'elasticOut',
    animationDelayUpdate: function (idx) {
      return idx * 5;
    }
  };
  
  // 设置选项并渲染图表
  chartsInstances.videoViews.setOption(option);
};

// 初始化学习时长分布数据
const initStudyTimeDistribution = () => {
  studyTimeDistribution.value = [
    { name: '<30分钟', value: 35 },
    { name: '30-60分钟', value: 52 },
    { name: '1-2小时', value: 65 },
    { name: '2-3小时', value: 38 },
    { name: '>3小时', value: 25 }
  ];
};

// 使用真实数据更新图表
const updateChartsWithRealData = (data) => {
  // 更新活跃学生趋势图
  if (data.trend_data && data.trend_data.length > 0) {
    updateActiveStudentsChart(data.trend_data);
  } else {
    initActiveStudentsChart();
  }
  
  // 更新知识点掌握度图表
  initMasteryChart();
  
  // 更新视频观看排行图
  if (data.video_ranking) {
    updateVideoViewsChart(data.video_ranking);
  } else {
    initVideoViewsChart();
  }
  
  // 更新学习时长分布图
  if (data.study_time_distribution) {
    studyTimeDistribution.value = data.study_time_distribution;
  } else {
    initStudyTimeDistribution();
  }
  
  // 学习时长分布数据加载完成，关闭加载状态
  studyTimeLoading.value = false;
};

// 加载统计数据
const loadStatistics = async () => {
  loading.value = true;
  studyTimeLoading.value = true;
  
  try {
    // 调用统计数据API
    const response = await courseService.getStatisticsOverview({
      course_id: selectedCourse.value,
      time_period: timePeriod.value
    });
    
    if (response.data.code === 200) {
      const data = response.data.data;
      
      // 更新总览统计数据
      overviewStats.value = data.overview_stats || [];
      
      // 更新学生数据
      studentData.value = data.student_data || [];
      
      // 等待DOM更新后再初始化图表
      await nextTick();
      
      // 更新图表数据
      updateChartsWithRealData(data);
    } else {
      console.error('API响应失败:', response.data.message);
      initAllCharts();
    }
    
    // 加载知识点掌握度数据
    await loadKnowledgeMastery();
    
  } catch (error) {
    console.error('加载统计数据失败:', error);
    // 如果API调用失败，使用模拟数据
    initAllCharts();
  } finally {
    loading.value = false;
    studyTimeLoading.value = false;
  }
};

// 使用真实数据更新活跃学生图表
const updateActiveStudentsChart = (trendData) => {
  if (!activeStudentsChart.value) return;
  
  if (chartsInstances.activeStudents) {
    chartsInstances.activeStudents.dispose();
  }
  
  chartsInstances.activeStudents = echarts.init(activeStudentsChart.value);
  
  const xAxisData = trendData.map(item => item.date.substring(5)); // 只显示月-日
  const activeStudentsData = trendData.map(item => item.active_students);
  const videoViewsData = trendData.map(item => item.video_views);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['活跃学生数', '视频观看次数'],
      top: 'bottom'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisTick: {
        alignWithLabel: true
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        position: 'left',
        axisLine: {
          show: true,
          lineStyle: {
            color: '#5470C6'
          }
        }
      },
      {
          type: 'value',
          name: '次数',
          position: 'left',
          show: false,
          axisLine: {
            show: true,
            lineStyle: {
              color: '#91CC75'
            }
          }
        }
    ],
    series: [
      {
        name: '活跃学生数',
        type: 'bar',
        data: activeStudentsData,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#5470C6' },
              { offset: 1, color: '#91CC75' }
            ]
          }
        },
        yAxisIndex: 0
      },
      {
        name: '视频观看次数',
        type: 'line',
        smooth: true,
        data: videoViewsData,
        itemStyle: {
          color: '#EE6666'
        },
        yAxisIndex: 1
      }
    ],
    animationDuration: 1500
  };
  
  chartsInstances.activeStudents.setOption(option);
};

// 使用真实数据更新视频观看排行图
const updateVideoViewsChart = (rankingData) => {
  if (!videoViewsChart.value) return;
  
  if (chartsInstances.videoViews) {
    chartsInstances.videoViews.dispose();
  }
  
  chartsInstances.videoViews = echarts.init(videoViewsChart.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: rankingData.map(item => item.name).reverse(),
      axisLabel: {
        formatter: function (value) {
          if (value.length > 10) {
            return value.substring(0, 10) + '...';
          }
          return value;
        }
      }
    },
    series: [
      {
        name: '观看次数',
        type: 'bar',
        data: rankingData.map(item => item.views).reverse(),
        itemStyle: {
          color: {
            type: 'linear',
            x: 1, y: 0, x2: 0, y2: 0,
            colorStops: [
              { offset: 0, color: '#6f23d1' },
              { offset: 0.5, color: '#a35eea' },
              { offset: 1, color: '#d49fff' }
            ]
          }
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c} 次'
        },
        animationDelay: function (idx) {
          return idx * 100 + 100;
        }
      }
    ],
    animationEasing: 'elasticOut'
  };
  
  chartsInstances.videoViews.setOption(option);
};

// 刷新数据
const refreshData = () => {
  loadStatistics();
};

// 初始化所有图表
const initAllCharts = () => {
  initActiveStudentsChart();
  initMasteryChart();
  initVideoViewsChart();
  initStudyTimeDistribution();
  // 初始化完成后关闭学习时长分布的加载状态
  studyTimeLoading.value = false;
};

// 监听时间范围变化，更新活跃度图表
watch(activityTimeRange, () => {
  initActiveStudentsChart();
});

// 监听窗口大小变化，调整图表大小
const handleResize = () => {
  Object.values(chartsInstances).forEach(chart => {
    chart && chart.resize();
  });
};

// 加载教师课程列表
const loadTeacherCourses = async () => {
  try {
    const response = await courseService.getTeacherCourses();
    if (response.data.code === 200) {
      courses.value = response.data.data;
      // 自动选择第一个课程作为默认选中课程
      if (courses.value.length > 0 && !selectedCourse.value) {
        selectedCourse.value = courses.value[0].id;
      }
    } else {
      console.error('获取课程列表失败:', response.data.message);
    }
  } catch (error) {
    console.error('加载课程列表失败:', error);
  }
};

// 加载知识点掌握度数据
const loadKnowledgeMastery = async () => {
  if (!selectedCourse.value) {
    bestMasteredKnowledge.value = [];
    worstMasteredKnowledge.value = [];
    return;
  }
  
  try {
    const response = await courseService.getCourseKnowledgeMastery(selectedCourse.value);
    if (response.data.code === 200) {
      const data = response.data.data;
      bestMasteredKnowledge.value = data.best_mastered || [];
      worstMasteredKnowledge.value = data.worst_mastered || [];
    } else {
      console.error('获取知识点掌握情况失败:', response.data.message);
      bestMasteredKnowledge.value = [];
      worstMasteredKnowledge.value = [];
    }
  } catch (error) {
    console.error('加载知识点掌握情况失败:', error);
    bestMasteredKnowledge.value = [];
    worstMasteredKnowledge.value = [];
  }
};

// 监听课程选择变化，重新加载统计数据和知识点数据
watch(selectedCourse, () => {
  if (selectedCourse.value) {
    loadStatistics();
  }
});

// 监听时间周期变化，重新加载统计数据
watch(timePeriod, () => {
  if (selectedCourse.value) {
    loadStatistics();
  }
});

// 生命周期钩子
onMounted(async () => {
  // 先加载课程列表
  await loadTeacherCourses();
  
  // 等待DOM更新
  await nextTick();
  
  // 初始化图表
  setTimeout(() => {
    initAllCharts();
  }, 100);
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize);
  
  // 加载统计数据
  loadStatistics();
});

onBeforeUnmount(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize);
  
  // 销毁所有图表实例
  Object.values(chartsInstances).forEach(chart => {
    chart && chart.dispose();
  });
});
</script>

<style scoped>
.statistics-view {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.content-card {
  height: 100%;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-card > .v-card-text {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.statistics-content {
  flex: 1;
  overflow-y: auto;
}

.overview-card {
  transition: transform 0.3s, box-shadow 0.3s;
  border-radius: 12px;
  overflow: hidden;
}

.overview-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
}

.chart-card {
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
}

.chart-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.chart-container {
  width: 100%;
  height: 350px;
}

.chart-title {
  font-weight: 500;
}

.trend.up {
  color: #4caf50;
}

.trend.down {
  color: #f44336;
}

.student-table {
  border-radius: 0 0 12px 12px;
  overflow: hidden;
}

.student-table :deep(.v-data-table) {
  max-height: 400px;
  overflow-y: auto;
}

.progress-text {
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
}

/* 手机端适配 */
@media (max-width: 960px) {
  .chart-container {
    height: 300px;
  }
  
  .overview-section .v-col {
    padding: 8px;
  }
}

@media (max-width: 600px) {
  .chart-container {
    height: 250px;
  }
  
  .stat-icon {
    width: 48px;
    height: 48px;
  }
}

/* 添加动画效果 */
.overview-card {
  animation: fadeInUp 0.5s ease-out;
}

.chart-card {
  animation: fadeIn 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.stat-1 {
  animation-delay: 0.1s;
}

.stat-2 {
  animation-delay: 0.2s;
}

.stat-3 {
  animation-delay: 0.3s;
}

.stat-4 {
  animation-delay: 0.4s;
}

.knowledge-card {
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
}

.knowledge-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.knowledge-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  transition: background-color 0.2s ease, transform 0.2s ease;
  border-radius: 8px;
  margin: 2px 0;
}

.knowledge-item:hover {
  background-color: rgba(25, 118, 210, 0.08);
  transform: translateX(4px);
}

.knowledge-item:last-child {
  border-bottom: none;
}

.knowledge-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.knowledge-category {
  font-size: 0.8rem;
  color: #666;
}

.knowledge-percentage {
  font-weight: 600;
  font-size: 0.9rem;
  color: #1976d2;
}

.knowledge-count {
  color: #999;
}
</style>