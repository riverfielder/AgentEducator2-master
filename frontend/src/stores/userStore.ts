import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useUserStore = defineStore('user', () => {
  const userId = ref(localStorage.getItem('wendao_user_id') || '');
  const username = ref(localStorage.getItem('wendao_user_name') || '');
  const userRole = ref(localStorage.getItem('wendao_user_role') || '');
  const avatar = ref(localStorage.getItem('wendao_avatar') || '');

  function updateUserInfo(userInfo: any) {
    userId.value = userInfo.id;
    username.value = userInfo.name || '';
    userRole.value = userInfo.role || '';
    avatar.value = userInfo.avatar || '';
    
    // 更新localStorage
    localStorage.setItem('wendao_user_id', userId.value);
    localStorage.setItem('wendao_user_name', username.value);
    localStorage.setItem('wendao_user_role', userRole.value);
    localStorage.setItem('wendao_avatar', avatar.value);
  }
  
  function updateAvatar(newAvatar: string) {
    avatar.value = newAvatar;
    localStorage.setItem('wendao_avatar', newAvatar);
  }
  
  function clearUserInfo() {
    userId.value = '';
    username.value = '';
    userRole.value = '';
    avatar.value = '';
    
    localStorage.removeItem('wendao_user_id');
    localStorage.removeItem('wendao_user_name');
    localStorage.removeItem('wendao_user_role');
    localStorage.removeItem('wendao_avatar');
    localStorage.removeItem('wendao_token');
  }
  
  return {
    userId,
    username,
    userRole,
    avatar,
    updateUserInfo,
    updateAvatar,
    clearUserInfo
  };
});
