<template>
  <div class="chat-history">
    <div class="history-section">
      <div class="d-flex align-center px-4 py-3">
        <div class="text-subtitle-1 font-weight-medium">历史对话</div>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          small
          @click="$emit('new-chat')"
          class="new-chat-btn"
        >
          <v-icon left>mdi-plus</v-icon>
          新对话
        </v-btn>
      </div>
      
      <v-list nav dense class="history-list">
        <!-- 通用对话分组 -->
        <div v-if="generalChats.length > 0">
          <v-subheader class="px-4 text-primary font-weight-bold">
            <v-icon left size="small" color="primary">mdi-robot</v-icon>
            通用AI对话
          </v-subheader>
          <ChatHistoryItem
            v-for="chat in generalChats"
            :key="chat.id || chat.title"
            :chat="chat"
            :is-active="currentChat && currentChat.id === chat.id"
            icon="mdi-robot"
            icon-color="primary"
            @click="$emit('select-chat', chat)"
            @edit="$emit('edit-chat', chat)"
            @delete="$emit('delete-chat', chat)"
          />
        </div>

        <!-- 视频对话分组 -->
        <div v-if="videoChats.length > 0">
          <v-divider v-if="generalChats.length > 0" class="my-2"></v-divider>
          <v-subheader class="px-4 text-secondary font-weight-bold">
            <v-icon left size="small" color="secondary">mdi-play-circle</v-icon>
            视频对话
          </v-subheader>
          <ChatHistoryItem
            v-for="chat in videoChats"
            :key="chat.id || chat.title"
            :chat="chat"
            :is-active="currentChat && currentChat.id === chat.id"
            icon="mdi-play-circle"
            icon-color="secondary"
            @click="$emit('select-chat', chat)"
            @edit="$emit('edit-chat', chat)"
            @delete="$emit('delete-chat', chat)"
          />
        </div>

        <!-- 课程对话分组 -->
        <div v-if="courseChats.length > 0">
          <v-divider v-if="generalChats.length > 0 || videoChats.length > 0" class="my-2"></v-divider>
          <v-subheader class="px-4 text-warning font-weight-bold">
            <v-icon left size="small" color="warning">mdi-book-open-variant</v-icon>
            课程对话
          </v-subheader>
          <ChatHistoryItem
            v-for="chat in courseChats"
            :key="chat.id || chat.title"
            :chat="chat"
            :is-active="currentChat && currentChat.id === chat.id"
            icon="mdi-book-open-variant"
            icon-color="warning"
            @click="$emit('select-chat', chat)"
            @edit="$emit('edit-chat', chat)"
            @delete="$emit('delete-chat', chat)"
          />
        </div>
        
        <!-- 如果没有任何对话 -->
        <div v-if="chatHistory.length === 0" class="text-center py-4">
          <v-icon size="48" color="grey">mdi-chat-outline</v-icon>
          <div class="text-caption text-grey mt-2">暂无历史对话</div>
        </div>
      </v-list>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ChatHistoryItem from '../../components/ai/ChatHistoryItem.vue'
import type { Chat } from '../../types/chat'

interface Props {
  chatHistory: Chat[]
  currentChat: Chat | null
}

const props = defineProps<Props>()

defineEmits<{
  'new-chat': []
  'select-chat': [chat: Chat]
  'edit-chat': [chat: Chat]
  'delete-chat': [chat: Chat]
}>()

// 计算属性：按类型分组聊天历史
const generalChats = computed(() => props.chatHistory.filter(chat => chat.type === 'general'))
const videoChats = computed(() => props.chatHistory.filter(chat => chat.type === 'video'))
const courseChats = computed(() => props.chatHistory.filter(chat => chat.type === 'course'))
</script>

<style scoped>
.chat-history {
  height: 100%;
  border-right: 1px solid #f0f0f0;
  overflow: hidden;
}

.history-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 300px);
}

.new-chat-btn {
  text-transform: none;
}
</style>
