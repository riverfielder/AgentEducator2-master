<template>
  <div class="avatar-upload-container">
    <div class="avatar-preview" @click="triggerFileInput">
      <img 
        v-if="avatarUrl && !avatarLoadError" 
        :src="avatarUrl" 
        @error="handleAvatarError" 
        class="avatar-image" 
      />
      <div v-else class="letter-avatar" :style="letterAvatarStyle">
        {{ firstLetter }}
      </div>
      <div class="avatar-overlay">
        <i class="fas fa-camera"></i>
        <span>更换头像</span>
      </div>
    </div>
    
    <input
      type="file"
      ref="fileInput"
      @change="handleFileChange"
      accept="image/*"
      class="file-input"
    />
    
    <div v-if="uploading" class="upload-progress">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      </div>
      <span>上传中 {{ uploadProgress }}%</span>
    </div>
    
    <div v-if="errorMsg" class="error-message">
      {{ errorMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useUserStore } from '../stores/userStore';
import uploadService from '../api/uploadService';


// 属性定义
const props = defineProps({
  username: {
    type: String,
    default: ''
  },
  initialAvatar: {
    type: String,
    default: ''
  },
  size: {
    type: Number,
    default: 100
  }
});

// 事件
const emit = defineEmits(['avatar-updated']);

// 状态
const avatarLoadError = ref(false);
const avatarUrl = computed(() => {
  if (avatarLoadError.value) return '';  // 如果头像加载失败，返回空字符串以显示首字母头像
  const avatar = props.initialAvatar || '';
  if (!avatar) return '';
  // 如果已经是完整URL，直接返回
  if (avatar.startsWith('http')) return avatar;
  // 否则添加baseURL
  return `${avatar}`;
});
const fileInput = ref(null);
const uploading = ref(false);
const uploadProgress = ref(0);
const errorMsg = ref('');
const userStore = useUserStore();

// 计算属性
const firstLetter = computed(() => {
  return props.username ? props.username.charAt(0).toUpperCase() : 'U';
});

// 获取随机颜色
const getRandomColor = (seed) => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
  ];
  const index = seed.charCodeAt(0) % colors.length;
  return colors[index];
};

const letterAvatarStyle = computed(() => {
  const color = getRandomColor(props.username || 'U');
  return {
    backgroundColor: color,
    width: `${props.size}px`,
    height: `${props.size}px`,
    fontSize: `${props.size / 2}px`,
    lineHeight: `${props.size}px`,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    color: 'white',
    fontWeight: 'bold',
    textTransform: 'uppercase'
  };
});

// 方法
const triggerFileInput = () => {
  resetAvatarError();  // 重置头像加载错误状态
  fileInput.value.click();
};

const handleFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // 验证文件是图片
  if (!file.type.startsWith('image/')) {
    errorMsg.value = '请选择图片文件';
    return;
  }
  
  // 验证文件大小 (最大2MB)
  if (file.size > 2 * 1024 * 1024) {
    errorMsg.value = '图片大小不能超过2MB';
    return;
  }
  
  // 重置错误信息
  errorMsg.value = '';
  uploading.value = true;
  resetAvatarError();  // 重置头像加载错误状态
  
  try {
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      uploadProgress.value += 10;
      if (uploadProgress.value >= 90) clearInterval(progressInterval);
    }, 200);
    
    // 调用上传API
    const response = await uploadService.uploadAvatar(formData);
    
    clearInterval(progressInterval);
    uploadProgress.value = 100;
    
    if (response.data.code === 200) {
      const newAvatarUrl = response.data.data.avatar;
      console.log("上传成功，新头像URL:", newAvatarUrl);
      
      // 更新用户Store中的头像
      userStore.updateAvatar(newAvatarUrl);
      
      // 触发头像已更新事件
      emit('avatar-updated', newAvatarUrl);
      
      // 延迟重置上传状态，让用户看到100%
      setTimeout(() => {
        uploading.value = false;
        uploadProgress.value = 0;
      }, 500);
    } else {
      throw new Error(response.data.message || '上传失败');
    }
  } catch (error) {
    clearInterval(progressInterval);
    uploading.value = false;
    uploadProgress.value = 0;
    errorMsg.value = error.message || '上传过程中出错';
    console.error('上传头像失败:', error);
  }
};

// 处理头像加载错误
const handleAvatarError = (e) => {
  console.error('AvatarUpload img error', e);
  avatarLoadError.value = true;
};

// 重置头像加载错误状态
const resetAvatarError = () => {
  avatarLoadError.value = false;
};

// 监听initialAvatar的变化
watch(() => props.initialAvatar, () => {
  resetAvatarError();  // 当initialAvatar变化时重置错误状态
});

// 初始化
onMounted(() => {
  resetAvatarError();  // 组件挂载时重置错误状态
});
</script>

<style scoped>
.avatar-upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px 0;
}

.avatar-preview {
  position: relative;
  width: v-bind('props.size + "px"');
  height: v-bind('props.size + "px"');
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  border: 4px solid rgba(255, 255, 255, 0.9);
}

.avatar-preview:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  border-color: rgba(102, 126, 234, 0.4);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.3s ease;
}

.avatar-preview:hover .avatar-image {
  transform: scale(1.1);
}

.letter-avatar {
  border-radius: 50%;
  text-transform: uppercase;
  position: relative;
  overflow: hidden;
}

.letter-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255,255,255,0.1) 0%, 
    rgba(255,255,255,0) 50%, 
    rgba(0,0,0,0.1) 100%);
  pointer-events: none;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.8) 0%, 
    rgba(118, 75, 162, 0.8) 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  opacity: 0;
  transition: all 0.3s ease;
  backdrop-filter: blur(8px);
}

.avatar-overlay i {
  font-size: 1.8rem;
  margin-bottom: 8px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.avatar-overlay span {
  font-size: 0.85rem;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
}

.avatar-preview:hover .avatar-overlay {
  opacity: 1;
}

.file-input {
  display: none;
}

.upload-progress {
  width: 100%;
  max-width: 200px;
  margin-top: 16px;
  text-align: center;
}

.progress-bar {
  height: 8px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 8px;
  position: relative;
}

.progress-bar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, 
    transparent 25%, 
    rgba(255,255,255,0.3) 25%, 
    rgba(255,255,255,0.3) 50%, 
    transparent 50%, 
    transparent 75%, 
    rgba(255,255,255,0.3) 75%);
  background-size: 20px 20px;
  animation: move 1s linear infinite;
}

@keyframes move {
  0% { background-position: 0 0; }
  100% { background-position: 20px 0; }
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255,255,255,0.3) 0%, 
    rgba(255,255,255,0) 50%, 
    rgba(255,255,255,0.3) 100%);
}

.upload-progress span {
  font-size: 0.875rem;
  font-weight: 600;
  color: #667eea;
  text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}

.error-message {
  color: #e74c3c;
  font-size: 0.875rem;
  font-weight: 500;
  margin-top: 12px;
  padding: 8px 16px;
  background: rgba(231, 76, 60, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(231, 76, 60, 0.2);
  text-align: center;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}
</style>
