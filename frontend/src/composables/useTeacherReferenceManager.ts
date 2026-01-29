import { ref, watch } from 'vue'
import type { Reference } from '../types/chat'

export function useTeacherReferenceManager() {
  // 教师端QA模式：包含教师专用模式
  const qaMode = ref('teacher_general') // 'teacher_general', 'course_analysis', 'student_insights', 'content_generation', 'all'
  const selectedReferences = ref<Reference[]>([])

  // 教师端智能问答模式切换
  const updateQaMode = () => {
    if (selectedReferences.value.length === 0) {
      qaMode.value = 'teacher_general'
      return
    }

    const courses = selectedReferences.value.filter(ref => ref.type === 'course')
    const videos = selectedReferences.value.filter(ref => ref.type === 'video')
    const hasMultipleTypes = courses.length > 0 && videos.length > 0
    
    // 教师端模式判断逻辑
    if (courses.length === 1 && videos.length === 0) {
      // 单个课程 -> 课程分析模式
      qaMode.value = 'course_analysis'
    } else if (videos.length > 0 && courses.length === 0) {
      // 只有视频引用 -> 内容分析模式
      qaMode.value = 'content_analysis'
    } else if (hasMultipleTypes || courses.length > 1) {
      // 多种类型或多个课程 -> 综合分析模式
      qaMode.value = 'all'
    } else {
      // 其他情况 -> 通用教师模式
      qaMode.value = 'teacher_general'
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
    qaMode.value = 'teacher_general'
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