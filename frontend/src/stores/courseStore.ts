import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { Course } from '../types/course';

export const useCourseStore = defineStore('course', () => {
  const courses = ref<Course[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  function setCourses(newCourses: Course[]) {
    courses.value = newCourses;
  }

  return { 
    courses, 
    loading, // 如果也想全局管理加载状态
    error,   // 如果也想全局管理错误状态
    setCourses 
  };
}); 