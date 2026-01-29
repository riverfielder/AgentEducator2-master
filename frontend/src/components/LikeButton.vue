<template>
  <div class="like-button" @click="handleLike">
    <div class="like-icon" :class="{ 'liked': isLiked }">
      <v-icon
        :color="isLiked ? '#ff4081' : '#757575'"
        size="24"
        class="heart-icon"
      >
        {{ isLiked ? 'mdi-heart' : 'mdi-heart-outline' }}
      </v-icon>
      <div class="ripple-effect" v-if="showRipple"></div>
    </div>
    <span class="like-count" :class="{ 'liked': isLiked }">{{ count }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  initialCount?: number
  initialLiked?: boolean
}>()

const emit = defineEmits<{
  'update:count': [count: number]
  'update:liked': [liked: boolean]
}>()

const count = ref(props.initialCount || 0)
const isLiked = ref(props.initialLiked || false)
const showRipple = ref(false)

// 监听 props 变化
watch(() => props.initialCount, (newCount) => {
  if (newCount !== undefined) count.value = newCount
})

watch(() => props.initialLiked, (newLiked) => {
  if (newLiked !== undefined) isLiked.value = newLiked
})

const handleLike = () => {
  isLiked.value = !isLiked.value
  count.value += isLiked.value ? 1 : -1
  
  // 触发更新事件
  emit('update:count', count.value)
  emit('update:liked', isLiked.value)
  
  // 添加涟漪效果
  showRipple.value = true
  setTimeout(() => {
    showRipple.value = false
  }, 1000)
}
</script>

<style scoped>
.like-button {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 8px 12px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.like-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.like-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.like-icon.liked {
  transform: scale(1.1);
}

.heart-icon {
  transition: all 0.3s ease;
}

.like-count {
  margin-left: 8px;
  font-size: 14px;
  color: #757575;
  transition: all 0.3s ease;
}

.like-count.liked {
  color: #ff4081;
}

.ripple-effect {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: rgba(255, 64, 129, 0.2);
  animation: ripple 1s ease-out;
}

@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}
</style> 