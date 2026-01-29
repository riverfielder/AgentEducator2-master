import { ref, watch } from 'vue'
import type { Reference } from '../types/chat'

export function useReferenceManager() {
  const qaMode = ref('general') // 'general', 'video', 'course', 'all'
  const selectedReferences = ref<Reference[]>([])

  // 智能问答模式切换
  const updateQaMode = () => {
    if (selectedReferences.value.length === 0) {
      qaMode.value = 'general'
      return
    }

    const courses = selectedReferences.value.filter(ref => ref.type === 'course')
    const videos = selectedReferences.value.filter(ref => ref.type === 'video')
    
    if (videos.length === 1 && courses.length === 0) {
      // 单个视频 -> 视频模式
      qaMode.value = 'video'
    } else if (courses.length === 1) {
      // 单个课程 -> 课程模式
      qaMode.value = 'course'
    } else if (videos.length > 1 && courses.length === 0) {
      // 多个视频，检查是否同一课程
      const courseIds = [...new Set(videos.map(v => v.courseId).filter(id => id))]
      if (courseIds.length === 1) {
        // 同一课程的多个视频 -> 课程模式
        qaMode.value = 'course'
      } else {
        // 跨课程来源 -> 全平台模式
        qaMode.value = 'all'
      }
    } else {
      // 混合引用或跨课程来源 -> 全平台模式
      qaMode.value = 'all'
    }
  }

  // 添加引用
  const addReference = (reference: Reference) => {
    const existingRef = selectedReferences.value.find(ref => 
      ref.type === reference.type && ref.id === reference.id
    )
    
    if (!existingRef) {
      selectedReferences.value.push(reference)
      updateQaMode()
    }
  }

  // 清除所有引用
  const clearAllReferences = () => {
    selectedReferences.value = []
    qaMode.value = 'general'
  }

  // 移除单个引用
  const removeReference = (ref: Reference) => {
    const index = selectedReferences.value.findIndex(r => r.type === ref.type && r.id === ref.id)
    if (index > -1) {
      selectedReferences.value.splice(index, 1)
      updateQaMode()
    }
  }

  // 监听引用变化自动更新模式
  watch(selectedReferences, () => {
    updateQaMode()
  }, { deep: true })

  return {
    qaMode,
    selectedReferences,
    addReference,
    clearAllReferences,
    removeReference,
    updateQaMode
  }
}
