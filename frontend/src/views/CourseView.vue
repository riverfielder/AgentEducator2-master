<template>
  <div class="course-redirect">
    <v-container fluid class="d-flex align-center justify-center" style="height: 100vh;">
      <v-card class="pa-6 text-center" max-width="400" elevation="8">
        <v-card-text>
          <v-progress-circular
            indeterminate
            size="64"
            color="primary"
            class="mb-4"
          ></v-progress-circular>
          <h3 class="text-h6 mb-2">正在加载课程</h3>
          <p class="text-grey">正在获取课程信息并跳转到第一个视频...</p>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import courseService from '../api/courseService'
import videoService from '../api/videoService'

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  const courseId = route.params.courseId as string
  
  if (!courseId) {
    router.push('/')
    return
  }

  try {
    // 获取课程详情
    const courseResponse = await courseService.getCourseDetails(courseId)
    
    if (courseResponse.data?.code === 200) {
      const course = courseResponse.data.data
      
      // 获取该课程的视频列表
      const videosResponse = await videoService.getVideos({ 
        courseId: courseId,
        page: 1,
        pageSize: 1,
        sortBy: 'order' // 按顺序排序
      })
      
      if (videosResponse.data?.code === 200 && videosResponse.data.data.list?.length > 0) {
        const firstVideo = videosResponse.data.data.list[0]
        
        // 跳转到第一个视频
        router.replace(`/course/${courseId}/video/${firstVideo.id}`)
      } else {
        // 没有视频，显示错误消息并跳转回首页
        console.error('该课程暂无视频')
        setTimeout(() => {
          router.push('/')
        }, 2000)
      }
    } else {
      // 课程不存在
      console.error('课程不存在')
      setTimeout(() => {
        router.push('/')
      }, 2000)
    }
  } catch (error) {
    console.error('获取课程信息失败:', error)
    setTimeout(() => {
      router.push('/')
    }, 2000)
  }
})
</script>

<style scoped>
.course-redirect {
  background: #f5f5f5;
  min-height: 100vh;
}
</style>
