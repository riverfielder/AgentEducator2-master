import { computed } from 'vue'
import { jwtDecode } from 'jwt-decode'
import { parseJwt } from '@/utils/jwt'

/**
 * 用户角色判断组合式函数
 * @returns 返回一个计算属性，判断用户是否为教师或管理员
 */
export function useTeacherRole() {
  return computed(() => {
    const token = localStorage.getItem('wendao_token')
    let role = ''
    if (token) {
      try {
        const payload: any = jwtDecode(token)
        role = payload.role || ''
      } catch (e) {
        const payload = parseJwt(token)
        role = payload?.role || ''
      }
    } else {
      role = localStorage.getItem('wendao_user_role') || ''
    }
    return role === 'teacher' || role === 'admin'
  })
}
