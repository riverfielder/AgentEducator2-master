<template>
  <div class="knowledge-point-mastery">
    <!-- 掌握程度圆形进度条 -->
    <div class="mastery-circle" v-if="displayMode === 'circle'">
      <el-progress 
        type="circle" 
        :percentage="Math.round((masteryLevel || 0) * 100)"
        :color="getMasteryColor(masteryLevel || 0)"
        :width="size"
        :stroke-width="strokeWidth"
      >
        <template #default="{ percentage }">
          <div class="mastery-text">
            <div class="percentage">{{ percentage }}%</div>
            <div class="level" v-if="showLabel">{{ getMasteryLabel(masteryLevel || 0) }}</div>
          </div>
        </template>
      </el-progress>
    </div>

    <!-- 掌握程度线性进度条 -->
    <div class="mastery-linear" v-else-if="displayMode === 'linear'">
      <div class="mastery-header" v-if="showTitle">
        <span class="title">{{ title || '掌握程度' }}</span>
        <span class="percentage">{{ Math.round((masteryLevel || 0) * 100) }}%</span>
      </div>
      <el-progress 
        :percentage="Math.round((masteryLevel || 0) * 100)"
        :color="getMasteryColor(masteryLevel || 0)"
        :stroke-width="strokeWidth"
        :show-text="false"
      />
      <div class="mastery-label" v-if="showLabel">
        <span class="level">{{ getMasteryLabel(masteryLevel || 0) }}</span>
      </div>
    </div>

    <!-- 掌握程度详细信息 -->
    <div class="mastery-details" v-else-if="displayMode === 'detailed'">
      <div class="detail-header">
        <div class="main-progress">
          <el-progress 
            type="circle" 
            :percentage="Math.round((masteryLevel || 0) * 100)"
            :color="getMasteryColor(masteryLevel || 0)"
            :width="size"
            :stroke-width="strokeWidth"
          >
            <template #default="{ percentage }">
              <div class="mastery-text">
                <div class="percentage">{{ percentage }}%</div>
                <div class="level">{{ getMasteryLabel(masteryLevel || 0) }}</div>
              </div>
            </template>
          </el-progress>
        </div>
        
        <div class="breakdown" v-if="masteryInfo">
          <div class="breakdown-item">
            <span class="label">教学材料:</span>
            <div class="progress-wrapper">
              <el-progress 
                :percentage="Math.round((masteryInfo.material_score || 0) * 100)"
                :stroke-width="4"
                :show-text="false"
                color="#409eff"
              />
              <span class="value">{{ Math.round((masteryInfo.material_score || 0) * 100) }}%</span>
            </div>
          </div>
          
          <div class="breakdown-item">
            <span class="label">
              练习表现:
              <el-tooltip v-if="!getHasExercises()" content="该知识点暂无作业，此维度不参与计算" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </span>
            <div class="progress-wrapper">
              <el-progress 
                :percentage="getHasExercises() ? Math.round((masteryInfo.exercise_score || 0) * 100) : 0"
                :stroke-width="4"
                :show-text="false"
                :color="getHasExercises() ? '#67c23a' : '#e5e7eb'"
              />
              <span class="value" :class="{ 'text-muted': !getHasExercises() }">
                {{ getHasExercises() ? Math.round((masteryInfo.exercise_score || 0) * 100) + '%' : '无作业' }}
              </span>
            </div>
          </div>
          
          <div class="breakdown-item">
            <span class="label">
              子知识点:
              <el-tooltip v-if="!getHasSubKnowledge()" content="该知识点无子知识点，此维度不参与计算" placement="top">
                <el-icon class="info-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </span>
            <div class="progress-wrapper">
              <el-progress 
                :percentage="getHasSubKnowledge() ? Math.round((masteryInfo.child_contribution || 0) * 100) : 0"
                :stroke-width="4"
                :show-text="false"
                :color="getHasSubKnowledge() ? '#e6a23c' : '#e5e7eb'"
              />
              <span class="value" :class="{ 'text-muted': !getHasSubKnowledge() }">
                {{ getHasSubKnowledge() ? Math.round((masteryInfo.child_contribution || 0) * 100) + '%' : '无子知识点' }}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="detail-footer" v-if="masteryInfo">
        <div class="meta-info">
          <span class="last-updated">最后更新: {{ formatDate(masteryInfo.last_updated) }}</span>
          <el-button 
            v-if="showRefresh" 
            @click="$emit('refresh')" 
            :loading="refreshing"
            type="text" 
            size="small"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 简化模式 -->
    <div class="mastery-simple" v-else>
      <div class="simple-content">
        <div class="simple-progress">
          <el-progress 
            :percentage="Math.round((masteryLevel || 0) * 100)"
            :color="getMasteryColor(masteryLevel || 0)"
            :stroke-width="6"
            :show-text="false"
          />
        </div>
        <div class="simple-text">
          <span class="percentage">{{ Math.round((masteryLevel || 0) * 100) }}%</span>
          <span class="level" v-if="showLabel">{{ getMasteryLabel(masteryLevel || 0) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Refresh, InfoFilled } from '@element-plus/icons-vue'

// Props
const props = defineProps({
  // 掌握程度值 (0-1)
  masteryLevel: {
    type: Number,
    default: 0
  },
  // 详细掌握程度信息
  masteryInfo: {
    type: Object,
    default: null
  },
  // 显示模式: circle, linear, detailed, simple
  displayMode: {
    type: String,
    default: 'circle',
    validator: (value) => ['circle', 'linear', 'detailed', 'simple'].includes(value)
  },
  // 圆形进度条大小
  size: {
    type: Number,
    default: 80
  },
  // 进度条粗细
  strokeWidth: {
    type: Number,
    default: 6
  },
  // 是否显示标签
  showLabel: {
    type: Boolean,
    default: true
  },
  // 是否显示标题
  showTitle: {
    type: Boolean,
    default: false
  },
  // 标题文本
  title: {
    type: String,
    default: ''
  },
  // 是否显示刷新按钮
  showRefresh: {
    type: Boolean,
    default: false
  },
  // 刷新状态
  refreshing: {
    type: Boolean,
    default: false
  }
})

// Events
const emit = defineEmits(['refresh'])

// 方法
const getMasteryColor = (level) => {
  if (level >= 0.9) return '#67c23a'  // 优秀 - 绿色
  if (level >= 0.7) return '#409eff'  // 良好 - 蓝色
  if (level >= 0.5) return '#e6a23c'  // 一般 - 橙色
  if (level >= 0.3) return '#f56c6c'  // 较差 - 红色
  return '#909399'                     // 很差 - 灰色
}

const getMasteryLabel = (level) => {
  if (level >= 0.9) return '优秀'
  if (level >= 0.7) return '良好'
  if (level >= 0.5) return '一般'
  if (level >= 0.3) return '较差'
  return '再接再厉'
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 判断是否有作业
const getHasExercises = () => {
  if (!props.masteryInfo?.calculation_details) return true // 默认显示
  try {
    const details = typeof props.masteryInfo.calculation_details === 'string' 
      ? JSON.parse(props.masteryInfo.calculation_details) 
      : props.masteryInfo.calculation_details
    return details.has_exercises !== false
  } catch {
    return true
  }
}

// 判断是否有子知识点
const getHasSubKnowledge = () => {
  if (!props.masteryInfo?.calculation_details) return true // 默认显示
  try {
    const details = typeof props.masteryInfo.calculation_details === 'string' 
      ? JSON.parse(props.masteryInfo.calculation_details) 
      : props.masteryInfo.calculation_details
    return details.has_sub_knowledge !== false
  } catch {
    return true
  }
}
</script>

<style scoped>
.knowledge-point-mastery {
  display: inline-block;
}

/* 圆形模式 */
.mastery-circle {
  display: flex;
  justify-content: center;
  align-items: center;
}

.mastery-text {
  text-align: center;
}

.mastery-text .percentage {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.mastery-text .level {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1;
}

/* 线性模式 */
.mastery-linear {
  width: 100%;
}

.mastery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.mastery-header .title {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.mastery-header .percentage {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
}

.mastery-label {
  text-align: center;
  margin-top: 8px;
}

.mastery-label .level {
  font-size: 12px;
  color: #909399;
}

/* 详细模式 */
.mastery-details {
  width: 100%;
}

.detail-header {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.main-progress {
  flex-shrink: 0;
}

.breakdown {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.breakdown-item .label {
  min-width: 80px;
  font-size: 14px;
  color: #606266;
}

.progress-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.breakdown-item .value {
  min-width: 40px;
  font-size: 12px;
  color: #303133;
  font-weight: 500;
  text-align: right;
}

.detail-footer {
  border-top: 1px solid #e4e7ed;
  padding-top: 12px;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-updated {
  font-size: 12px;
  color: #909399;
}

/* 简化模式 */
.mastery-simple {
  width: 100%;
}

.simple-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.simple-progress {
  flex: 1;
}

.simple-text {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 60px;
}

.simple-text .percentage {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.simple-text .level {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
  line-height: 1;
}

/* 其他样式 */
.text-muted {
  color: #999 !important;
}

.info-icon {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
  cursor: help;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .main-progress {
    align-self: center;
  }
  
  .breakdown-item {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }
  
  .breakdown-item .label {
    min-width: auto;
  }
  
  .breakdown-item .value {
    text-align: left;
  }
}
</style>