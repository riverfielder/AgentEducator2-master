<template>
  <v-card class="course-card" @click="navigateToCourse">    <v-img
      :src="thumbnail"
      :alt="title"
      height="280"
      cover
    >
      <template v-slot:placeholder>
        <v-row
          class="fill-height ma-0"
          align="center"
          justify="center"
        >
          <v-progress-circular
            indeterminate
            color="primary"
          ></v-progress-circular>
        </v-row>
      </template>
    </v-img>

    <v-card-text>
      <div class="d-flex justify-space-between align-center mb-2">
        <v-chip
          size="small"
          color="primary"
          variant="tonal"
        >
          {{ duration }}
        </v-chip>        <div class="d-flex align-center" v-if="rating">
          <v-icon size="small" color="warning" class="mr-1">mdi-star</v-icon>
          <span class="text-caption">{{ rating }}</span>
        </div>
      </div>

      <v-card-title class="text-subtitle-1 pa-0">{{ title }}</v-card-title>      <div class="d-flex align-center mt-2">        <v-avatar size="24" class="mr-2" color="grey-lighten-3">
          <img 
            v-if="teacherInfo?.avatar && !(teacherInfo as any)?.avatarLoadError" 
            :src="teacherInfo?.avatar" 
            @error="handleAvatarError($event, teacherInfo)"
            @load="handleAvatarLoad($event, teacherInfo)"
            style="width: 100%; height: 100%; object-fit: cover;" 
          />
          <div v-else-if="teacherInfo?.name && teacherInfo?.name.trim()" 
               class="letter-avatar" 
               :style="getLetterAvatarStyle(teacherInfo?.name)">
            {{ teacherInfo?.name.charAt(0).toUpperCase() }}
          </div>
          <v-icon v-else size="16">mdi-account</v-icon>
        </v-avatar>
        <span class="text-caption">{{ teacher }}</span>
        <v-divider vertical class="mx-2"></v-divider>
        <template v-if="category && category.length">
          <v-chip v-for="cat in category" :key="cat" size="x-small" color="primary" class="mr-1">{{ cat }}</v-chip>
        </template>
        <template v-else>
          <span class="text-caption">未分类</span>
        </template>
      </div>

      <div class="d-flex align-center mt-2">
        <v-icon size="small" color="grey" class="mr-1">mdi-account-group</v-icon>
        <span class="text-caption">{{ students }}人在学</span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import courseService from '../api/courseService'
import type { TeacherInfo } from '../types/course'

const router = useRouter()

const props = defineProps<{
  id: string
  thumbnail: string
  title: string
  duration: string
  students: number
  rating?: number // 使评分可选
  teacher: string
  teacherInfo?: TeacherInfo
  category?: string[]
  description: string
}>()

// 头像处理方法
const getRandomColor = (username: string): string => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#16a085'
  ]
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const getLetterAvatarStyle = (username: string) => {
  if (!username || !username.trim()) {
    return {
      backgroundColor: '#95a5a6',
      color: 'white',
      fontSize: '12px',
      fontWeight: 'bold',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100%'
    }
  }
  
  const bgColor = getRandomColor(username)
  return {
    backgroundColor: bgColor,
    color: 'white',
    fontSize: '12px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    height: '100%'
  }
}

const handleAvatarError = (event: Event, teacherInfo: any) => {
  console.log('Avatar load error for teacher:', teacherInfo?.name)
  if (teacherInfo) {
    teacherInfo.avatarLoadError = true
  }
}

const handleAvatarLoad = (event: Event, teacherInfo: any) => {
  console.log('Avatar loaded successfully for teacher:', teacherInfo?.name)
  if (teacherInfo) {
    teacherInfo.avatarLoadError = false
  }
}

// 点击课程卡片导航到课程首页
const navigateToCourse = () => {
  console.log('导航到课程首页, 课程ID:', props.id)
    router.push(`/course/${props.id}`)
}
</script>
<style scoped>
.course-card {
  cursor: pointer;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 25px 0 rgba(0, 0, 0, 0.1);
}

/* 字母头像样式 */
.letter-avatar {
  border-radius: 50%;
  background: linear-gradient(135deg, var(--bg-color, #3498db), var(--bg-color-light, #5dade2));
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.letter-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>
