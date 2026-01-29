&lt;template&gt;
  &lt;v-dialog v-model="dialog" max-width="1200px" persistent&gt;
    &lt;v-card class="schedule-dialog"&gt;
      &lt;v-card-title class="d-flex align-center py-4 px-6 bg-primary text-white"&gt;
        &lt;v-icon start&gt;mdi-calendar-check&lt;/v-icon&gt;
        课程日程
        &lt;v-spacer&gt;&lt;/v-spacer&gt;
        &lt;v-btn icon variant="text" @click="closeDialog"&gt;
          &lt;v-icon&gt;mdi-close&lt;/v-icon&gt;
        &lt;/v-btn&gt;
      &lt;/v-card-title&gt;
      
      &lt;v-card-text class="pa-0"&gt;
        &lt;!-- 工具栏 --&gt;
        &lt;v-toolbar flat color="grey-lighten-4"&gt;
          &lt;v-btn-toggle v-model="viewType" mandatory&gt;
            &lt;v-btn value="month" size="small"&gt;月视图&lt;/v-btn&gt;
            &lt;v-btn value="week" size="small"&gt;周视图&lt;/v-btn&gt;
            &lt;v-btn value="day" size="small"&gt;日视图&lt;/v-btn&gt;
          &lt;/v-btn-toggle&gt;
          
          &lt;v-spacer&gt;&lt;/v-spacer&gt;
          
          &lt;v-btn variant="text" @click="goToToday"&gt;今天&lt;/v-btn&gt;
          &lt;v-btn icon @click="previousPeriod"&gt;
            &lt;v-icon&gt;mdi-chevron-left&lt;/v-icon&gt;
          &lt;/v-btn&gt;
          &lt;v-btn icon @click="nextPeriod"&gt;
            &lt;v-icon&gt;mdi-chevron-right&lt;/v-icon&gt;
          &lt;/v-btn&gt;
          
          &lt;span class="text-h6 mx-4"&gt;{{ currentDateTitle }}&lt;/span&gt;
        &lt;/v-toolbar&gt;
        
        &lt;!-- 统计概览 --&gt;
        &lt;v-row class="pa-4" dense&gt;
          &lt;v-col v-for="(stat, index) in scheduleStats" :key="index" cols="3"&gt;
            &lt;v-card variant="flat" :color="stat.color" class="text-white"&gt;
              &lt;v-card-text class="pa-3 text-center"&gt;
                &lt;v-icon size="24" class="mb-2"&gt;{{ stat.icon }}&lt;/v-icon&gt;
                &lt;div class="text-h6 font-weight-bold"&gt;{{ stat.value }}&lt;/div&gt;
                &lt;div class="text-caption"&gt;{{ stat.label }}&lt;/div&gt;
              &lt;/v-card-text&gt;
            &lt;/v-card&gt;
          &lt;/v-col&gt;
        &lt;/v-row&gt;
        
        &lt;v-divider&gt;&lt;/v-divider&gt;
        
        &lt;!-- 日历视图 --&gt;
        &lt;div class="calendar-container pa-4"&gt;
          &lt;div v-if="loading" class="text-center py-8"&gt;
            &lt;v-progress-circular indeterminate color="primary"&gt;&lt;/v-progress-circular&gt;
            &lt;p class="mt-2"&gt;加载课程日程中...&lt;/p&gt;
          &lt;/div&gt;
          
          &lt;div v-else-if="error" class="text-center py-8"&gt;
            &lt;v-alert type="error" variant="tonal"&gt;{{ error }}&lt;/v-alert&gt;
            &lt;v-btn @click="fetchSchedule" color="primary" class="mt-4"&gt;重试&lt;/v-btn&gt;
          &lt;/div&gt;
          
          &lt;div v-else class="schedule-grid"&gt;
            &lt;!-- 月视图 --&gt;
            &lt;div v-if="viewType === 'month'" class="month-view"&gt;
              &lt;div class="weekdays"&gt;
                &lt;div v-for="day in weekdays" :key="day" class="weekday"&gt;{{ day }}&lt;/div&gt;
              &lt;/div&gt;
              &lt;div class="month-grid"&gt;
                &lt;div
                  v-for="date in monthDates"
                  :key="date.dateStr"
                  class="date-cell"
                  :class="{
                    'other-month': !date.isCurrentMonth,
                    'today': date.isToday,
                    'has-events': date.events.length &gt; 0
                  }"
                &gt;
                  &lt;div class="date-number"&gt;{{ date.day }}&lt;/div&gt;
                  &lt;div class="events"&gt;
                    &lt;div
                      v-for="event in date.events.slice(0, 3)"
                      :key="event.id"
                      class="event-item"
                      :style="{ backgroundColor: event.color }"
                      @click="showEventDetails(event)"
                    &gt;
                      {{ event.title }}
                    &lt;/div&gt;
                    &lt;div v-if="date.events.length &gt; 3" class="more-events"&gt;
                      +{{ date.events.length - 3 }} 更多
                    &lt;/div&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/div&gt;
            
            &lt;!-- 周视图和日视图 --&gt;
            &lt;div v-else class="week-day-view"&gt;
              &lt;div class="time-column"&gt;
                &lt;div v-for="hour in hours" :key="hour" class="time-slot"&gt;
                  {{ hour }}:00
                &lt;/div&gt;
              &lt;/div&gt;
              &lt;div class="days-column"&gt;
                &lt;div class="day-headers"&gt;
                  &lt;div
                    v-for="date in currentWeekDates"
                    :key="date.dateStr"
                    class="day-header"
                    :class="{ 'today': date.isToday }"
                  &gt;
                    &lt;div class="day-name"&gt;{{ date.dayName }}&lt;/div&gt;
                    &lt;div class="day-number"&gt;{{ date.day }}&lt;/div&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
                &lt;div class="day-grid"&gt;
                  &lt;div
                    v-for="date in currentWeekDates"
                    :key="date.dateStr"
                    class="day-column"
                  &gt;
                    &lt;div v-for="hour in hours" :key="hour" class="hour-slot"&gt;
                      &lt;div
                        v-for="event in getEventsForDateTime(date.dateStr, hour)"
                        :key="event.id"
                        class="event-block"
                        :style="{ backgroundColor: event.color }"
                        @click="showEventDetails(event)"
                      &gt;
                        {{ event.title }}
                      &lt;/div&gt;
                    &lt;/div&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            &lt;/div&gt;
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/v-card-text&gt;
    &lt;/v-card&gt;
    
    &lt;!-- 课程详情对话框 --&gt;
    &lt;v-dialog v-model="eventDialog" max-width="500px"&gt;
      &lt;v-card v-if="selectedEvent"&gt;
        &lt;v-card-title class="bg-primary text-white"&gt;
          &lt;v-icon start&gt;mdi-book-open-page-variant&lt;/v-icon&gt;
          {{ selectedEvent.title }}
        &lt;/v-card-title&gt;
        &lt;v-card-text class="pa-6"&gt;
          &lt;div class="mb-4"&gt;
            &lt;v-chip :color="selectedEvent.color" variant="flat" class="mb-2"&gt;
              {{ getStatusText(selectedEvent.status) }}
            &lt;/v-chip&gt;
          &lt;/div&gt;
          
          &lt;div class="info-row mb-3"&gt;
            &lt;v-icon start&gt;mdi-clock-outline&lt;/v-icon&gt;
            {{ formatEventTime(selectedEvent) }}
          &lt;/div&gt;
          
          &lt;div class="info-row mb-3"&gt;
            &lt;v-icon start&gt;mdi-account-tie&lt;/v-icon&gt;
            教师：{{ selectedEvent.teacher }}
          &lt;/div&gt;
          
          &lt;div class="info-row mb-3"&gt;
            &lt;v-icon start&gt;mdi-account-group&lt;/v-icon&gt;
            学生人数：{{ selectedEvent.enrolledCount }}
          &lt;/div&gt;
          
          &lt;div class="info-row mb-3"&gt;
            &lt;v-icon start&gt;mdi-video-outline&lt;/v-icon&gt;
            视频数量：{{ selectedEvent.videoCount }}
          &lt;/div&gt;
          
          &lt;div class="info-row mb-3"&gt;
            &lt;v-icon start&gt;mdi-map-marker&lt;/v-icon&gt;
            地点：{{ selectedEvent.location }}
          &lt;/div&gt;
          
          &lt;div v-if="selectedEvent.description" class="mb-3"&gt;
            &lt;v-icon start&gt;mdi-text&lt;/v-icon&gt;
            {{ selectedEvent.description }}
          &lt;/div&gt;
        &lt;/v-card-text&gt;
        &lt;v-card-actions&gt;
          &lt;v-spacer&gt;&lt;/v-spacer&gt;
          &lt;v-btn @click="eventDialog = false"&gt;关闭&lt;/v-btn&gt;
          &lt;v-btn
            color="primary"
            @click="goToCourseDetail(selectedEvent.extendedProps.courseId)"
          &gt;
            查看详情
          &lt;/v-btn&gt;
        &lt;/v-card-actions&gt;
      &lt;/v-card&gt;
    &lt;/v-dialog&gt;
  &lt;/v-dialog&gt;
&lt;/template&gt;

&lt;script&gt;
import teacherDashboardService from '../api/teacherDashboardService'
import { showErrorMessage } from '../utils/notification'

export default {
  name: 'CourseSchedule',
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
      viewType: 'month',
      currentDate: new Date(),
      scheduleEvents: [],
      scheduleStats: [],
      selectedEvent: null,
      eventDialog: false,
      weekdays: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
      hours: Array.from({ length: 14 }, (_, i) => i + 8) // 8:00 - 21:00
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
    },
    
    currentDateTitle() {
      const year = this.currentDate.getFullYear()
      const month = this.currentDate.getMonth() + 1
      
      if (this.viewType === 'month') {
        return `${year}年${month}月`
      } else if (this.viewType === 'week') {
        const weekStart = this.getWeekStart(this.currentDate)
        const weekEnd = new Date(weekStart)
        weekEnd.setDate(weekEnd.getDate() + 6)
        return `${weekStart.getFullYear()}年${weekStart.getMonth() + 1}月${weekStart.getDate()}日 - ${weekEnd.getMonth() + 1}月${weekEnd.getDate()}日`
      } else {
        return `${year}年${month}月${this.currentDate.getDate()}日`
      }
    },
    
    monthDates() {
      const year = this.currentDate.getFullYear()
      const month = this.currentDate.getMonth()
      const firstDay = new Date(year, month, 1)
      const lastDay = new Date(year, month + 1, 0)
      
      // 获取月份开始的星期几
      const startWeekday = firstDay.getDay()
      
      // 计算需要显示的日期范围
      const startDate = new Date(firstDay)
      startDate.setDate(startDate.getDate() - startWeekday)
      
      const dates = []
      const today = new Date()
      
      for (let i = 0; i &lt; 42; i++) { // 6周 * 7天
        const date = new Date(startDate)
        date.setDate(date.getDate() + i)
        
        const dateStr = this.formatDate(date)
        const events = this.getEventsForDate(dateStr)
        
        dates.push({
          date,
          day: date.getDate(),
          dateStr,
          isCurrentMonth: date.getMonth() === month,
          isToday: this.isSameDay(date, today),
          events
        })
      }
      
      return dates
    },
    
    currentWeekDates() {
      const weekStart = this.getWeekStart(this.currentDate)
      const dates = []
      const today = new Date()
      
      for (let i = 0; i &lt; 7; i++) {
        const date = new Date(weekStart)
        date.setDate(date.getDate() + i)
        
        dates.push({
          date,
          day: date.getDate(),
          dayName: this.weekdays[i],
          dateStr: this.formatDate(date),
          isToday: this.isSameDay(date, today)
        })
      }
      
      return dates
    }
  },
  watch: {
    dialog(newVal) {
      if (newVal) {
        this.fetchSchedule()
      }
    },
    
    viewType() {
      this.fetchSchedule()
    },
    
    currentDate() {
      this.fetchSchedule()
    }
  },
  methods: {
    async fetchSchedule() {
      try {
        this.loading = true
        this.error = null
          if (!localStorage.getItem('wendao_token')) {
          throw new Error('未登录')
        }
        
        // 计算日期范围
        let startDate, endDate
        
        if (this.viewType === 'month') {
          const year = this.currentDate.getFullYear()
          const month = this.currentDate.getMonth()
          startDate = new Date(year, month, 1)
          endDate = new Date(year, month + 1, 0)
        } else if (this.viewType === 'week') {
          startDate = this.getWeekStart(this.currentDate)
          endDate = new Date(startDate)
          endDate.setDate(endDate.getDate() + 6)
        } else {
          startDate = new Date(this.currentDate)
          endDate = new Date(this.currentDate)
        }
        
        const response = await teacherDashboardService.getSchedule({
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString(),
          view_type: this.viewType
        })
        
        if (response.data.code === 200) {
          this.scheduleEvents = response.data.data.events
          this.updateScheduleStats(response.data.data.summary)
        } else {
          throw new Error(response.data.message || '获取课程日程失败')
        }
      } catch (error) {
        console.error('获取课程日程失败:', error)
        this.error = error.message || '获取课程日程失败'
      } finally {
        this.loading = false
      }
    },
    
    updateScheduleStats(summary) {
      this.scheduleStats = [
        {
          label: '总课程数',
          value: summary.totalCourses,
          icon: 'mdi-book-multiple',
          color: 'primary'
        },
        {
          label: '今日课程',
          value: summary.todayCourses,
          icon: 'mdi-calendar-today',
          color: 'success'
        },
        {
          label: '进行中',
          value: summary.activeCourses,
          icon: 'mdi-play-circle',
          color: 'warning'
        },
        {
          label: '即将开始',
          value: summary.upcomingCourses,
          icon: 'mdi-clock-outline',
          color: 'info'
        }
      ]
    },
    
    getEventsForDate(dateStr) {
      return this.scheduleEvents.filter(event =&gt; {
        const eventDate = new Date(event.start)
        return this.formatDate(eventDate) === dateStr
      })
    },
    
    getEventsForDateTime(dateStr, hour) {
      return this.scheduleEvents.filter(event =&gt; {
        const eventDate = new Date(event.start)
        return this.formatDate(eventDate) === dateStr && eventDate.getHours() === hour
      })
    },
    
    showEventDetails(event) {
      this.selectedEvent = event
      this.eventDialog = true
    },
    
    goToCourseDetail(courseId) {
      this.eventDialog = false
      this.closeDialog()
      this.$router.push(`/courses/${courseId}`)
    },
    
    previousPeriod() {
      const newDate = new Date(this.currentDate)
      
      if (this.viewType === 'month') {
        newDate.setMonth(newDate.getMonth() - 1)
      } else if (this.viewType === 'week') {
        newDate.setDate(newDate.getDate() - 7)
      } else {
        newDate.setDate(newDate.getDate() - 1)
      }
      
      this.currentDate = newDate
    },
    
    nextPeriod() {
      const newDate = new Date(this.currentDate)
      
      if (this.viewType === 'month') {
        newDate.setMonth(newDate.getMonth() + 1)
      } else if (this.viewType === 'week') {
        newDate.setDate(newDate.getDate() + 7)
      } else {
        newDate.setDate(newDate.getDate() + 1)
      }
      
      this.currentDate = newDate
    },
    
    goToToday() {
      this.currentDate = new Date()
    },
    
    closeDialog() {
      this.dialog = false
    },
    
    // 工具方法
    formatDate(date) {
      return date.toISOString().split('T')[0]
    },
    
    isSameDay(date1, date2) {
      return this.formatDate(date1) === this.formatDate(date2)
    },
    
    getWeekStart(date) {
      const d = new Date(date)
      const day = d.getDay()
      const diff = d.getDate() - day
      return new Date(d.setDate(diff))
    },
    
    formatEventTime(event) {
      const start = new Date(event.start)
      const end = new Date(event.end)
      
      return `${start.toLocaleString('zh-CN', {
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })} - ${end.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      })}`
    },
    
    getStatusText(status) {
      const statusMap = {
        'active': '进行中',
        'upcoming': '即将开始',
        'completed': '已结束'
      }
      return statusMap[status] || '未知状态'
    }
  }
}
&lt;/script&gt;

&lt;style scoped&gt;
.schedule-dialog {
  border-radius: 12px;
}

.calendar-container {
  max-height: 600px;
  overflow-y: auto;
}

/* 月视图样式 */
.month-view {
  width: 100%;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: #e0e0e0;
  border-radius: 8px 8px 0 0;
}

.weekday {
  background-color: #f5f5f5;
  padding: 12px;
  text-align: center;
  font-weight: 500;
  color: #666;
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: #e0e0e0;
  border-radius: 0 0 8px 8px;
}

.date-cell {
  background-color: white;
  min-height: 100px;
  padding: 8px;
  position: relative;
  cursor: pointer;
}

.date-cell:hover {
  background-color: #f0f4ff;
}

.date-cell.other-month {
  background-color: #fafafa;
  color: #ccc;
}

.date-cell.today {
  background-color: #e3f2fd;
}

.date-cell.has-events {
  border-left: 3px solid #2196f3;
}

.date-number {
  font-weight: 500;
  margin-bottom: 4px;
}

.events {
  space-y: 2px;
}

.event-item {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  color: white;
  margin-bottom: 2px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-item:hover {
  opacity: 0.8;
}

.more-events {
  font-size: 10px;
  color: #666;
  text-align: center;
  padding: 2px;
}

/* 周视图和日视图样式 */
.week-day-view {
  display: flex;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.time-column {
  width: 80px;
  border-right: 1px solid #e0e0e0;
}

.time-slot {
  height: 60px;
  padding: 8px;
  border-bottom: 1px solid #e0e0e0;
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
}

.days-column {
  flex: 1;
}

.day-headers {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
}

.day-header {
  flex: 1;
  padding: 12px;
  text-align: center;
  border-right: 1px solid #e0e0e0;
}

.day-header.today {
  background-color: #e3f2fd;
  color: #1976d2;
}

.day-name {
  font-size: 12px;
  color: #666;
}

.day-number {
  font-size: 18px;
  font-weight: 500;
  margin-top: 4px;
}

.day-grid {
  display: flex;
}

.day-column {
  flex: 1;
  border-right: 1px solid #e0e0e0;
}

.hour-slot {
  height: 60px;
  border-bottom: 1px solid #e0e0e0;
  padding: 4px;
  position: relative;
}

.event-block {
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  font-size: 12px;
  cursor: pointer;
  margin-bottom: 2px;
}

.event-block:hover {
  opacity: 0.8;
}

/* 详情对话框样式 */
.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
&lt;/style&gt;
