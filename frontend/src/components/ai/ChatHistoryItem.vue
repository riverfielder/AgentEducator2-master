<template>
  <v-list-item
    :class="{ 'active': isActive }"
    @click="$emit('click')"
  >
    <template v-slot:prepend>
      <v-icon size="small" :color="iconColor">{{ icon }}</v-icon>
    </template>
    
    <v-list-item-title class="chat-title">
      {{ chat.title }}
    </v-list-item-title>
    <v-list-item-subtitle class="chat-time">
      <div v-if="chat.videoInfo" class="text-caption">
        视频: {{ chat.videoInfo.title }}
      </div>
      <div v-if="chat.courseInfo" class="text-caption">
        课程: {{ chat.courseInfo.name }}
      </div>
      <div class="text-caption">{{ chat.time }}</div>
    </v-list-item-subtitle>
    
    <!-- 操作菜单 -->
    <template v-slot:append>
      <v-menu offset-y>
        <template v-slot:activator="{ props }">
          <v-btn
            icon
            size="small"
            v-bind="props"
            @click.stop
            class="chat-menu-btn"
          >
            <v-icon size="16">mdi-dots-vertical</v-icon>
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item @click="$emit('edit')">
            <v-list-item-title>
              <v-icon left size="16">mdi-pencil</v-icon>
              编辑标题
            </v-list-item-title>
          </v-list-item>
          <v-list-item @click="$emit('delete')" class="text-error">
            <v-list-item-title>
              <v-icon left size="16">mdi-delete</v-icon>
              删除对话
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </template>
  </v-list-item>
</template>

<script setup lang="ts">
import type { Chat } from '../../types/chat'

interface Props {
  chat: Chat
  isActive: boolean
  icon: string
  iconColor: string
}

defineProps<Props>()

defineEmits<{
  click: []
  edit: []
  delete: []
}>()
</script>

<style scoped>
.chat-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-time {
  font-size: 12px;
  color: #95a5a6;
}

.chat-menu-btn {
  opacity: 0;
  transition: opacity 0.2s;
}

.v-list-item:hover .chat-menu-btn {
  opacity: 1;
}

.v-list-item.active .chat-menu-btn {
  opacity: 1;
}
</style>
