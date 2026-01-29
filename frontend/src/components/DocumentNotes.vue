<template>
  <div class="document-notes">
    <!-- 笔记头部 -->
    <div class="notes-header">
      <div class="d-flex align-center justify-space-between mb-3">
        <div class="d-flex align-center">
          <v-icon color="primary" class="me-2">mdi-note-text</v-icon>
          <span class="text-subtitle-1 font-weight-medium">文档随笔</span>
        </div>
        <v-chip
          size="small"
          color="grey"
          variant="tonal"
        >
          {{ notes.length }} 条随笔
        </v-chip>
      </div>
    </div>

    <!-- 新建笔记区域 -->
    <div class="add-note-section mb-4">
      <v-textarea
        v-model="newNoteContent"
        placeholder="在此处添加随笔..."
        hide-details
        rows="3"
        variant="outlined"
        density="comfortable"
        class="mb-2"
      ></v-textarea>
      
      <div class="d-flex align-center justify-space-between">
        <div class="d-flex align-center">
          <!-- 笔记类型标签 -->
          <v-btn-toggle
            v-model="newNoteType"
            mandatory
            density="compact"
            class="me-2"
          >
            <v-btn size="small" value="note" class="text-caption">
              <v-icon size="14" class="me-1">mdi-note-outline</v-icon>
              随笔
            </v-btn>
            <v-btn size="small" value="question" class="text-caption">
              <v-icon size="14" class="me-1">mdi-help-circle-outline</v-icon>
              疑问
            </v-btn>
            <v-btn size="small" value="important" class="text-caption">
              <v-icon size="14" class="me-1">mdi-star-outline</v-icon>
              重点
            </v-btn>
          </v-btn-toggle>
        </div>
        
        <v-btn
          color="primary"
          size="small"
          variant="elevated"
          :disabled="!newNoteContent.trim()"
          @click="addNote"
        >
          <v-icon size="16" class="me-1">mdi-plus</v-icon>
          添加随笔
        </v-btn>
      </div>
    </div>

    <v-divider class="mb-4"></v-divider>

    <!-- 笔记列表 -->
    <div class="notes-list">
      <!-- 空状态 -->
      <div v-if="notes.length === 0" class="empty-state text-center py-8">
        <v-icon size="48" color="grey-lighten-2">mdi-note-plus-outline</v-icon>
        <p class="text-grey mt-2 mb-0">还没有随笔</p>
        <p class="text-caption text-grey">为这个文档添加第一条随笔吧！</p>
      </div>

      <!-- 笔记项 -->
      <v-card
        v-for="(note, index) in sortedNotes"
        :key="note.id"
        variant="outlined"
        class="note-item mb-3"
        :class="getNoteColorClass(note.type)"
      >
        <v-card-text class="pb-2">
          <!-- 笔记内容 -->
          <div class="note-content mb-2">
            <div v-if="editingNoteId === note.id">
              <v-textarea
                v-model="editingContent"
                hide-details
                rows="3"
                variant="outlined"
                density="compact"
                @keydown.ctrl.enter="saveNote(note.id)"
                @keydown.esc="cancelEdit"
              ></v-textarea>
              <div class="d-flex justify-end mt-2 gap-2">
                <v-btn
                  size="small"
                  variant="text"
                  @click="cancelEdit"
                >
                  取消
                </v-btn>
                <v-btn
                  size="small"
                  color="primary"
                  variant="elevated"
                  @click="saveNote(note.id)"
                >
                  保存
                </v-btn>
              </div>
            </div>
            <div v-else class="note-text">
              {{ note.content }}
            </div>
          </div>

          <!-- 笔记元信息 -->
          <div class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <!-- 类型图标 -->
              <v-chip
                size="x-small"
                :color="getNoteTypeColor(note.type)"
                variant="tonal"
                class="me-2"
              >
                <v-icon size="12" :icon="getNoteTypeIcon(note.type)" class="me-1"></v-icon>
                {{ getNoteTypeText(note.type) }}
              </v-chip>
              
              <!-- 时间 -->
              <span class="text-caption text-grey">
                {{ formatTime(note.createdAt) }}
              </span>
            </div>

            <!-- 操作按钮 -->
            <div class="note-actions">
              <v-btn
                size="x-small"
                variant="text"
                icon="mdi-pencil"
                @click="startEdit(note)"
                title="编辑"
              ></v-btn>
              <v-btn
                size="x-small"
                variant="text"
                icon="mdi-delete"
                color="error"
                @click="deleteNote(note.id)"
                title="删除"
              ></v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </div>

    <!-- 清空所有笔记 -->
    <div v-if="notes.length > 0" class="mt-4 text-center">
      <v-btn
        size="small"
        variant="text"
        color="error"
        @click="clearAllNotes"
      >
        <v-icon size="16" class="me-1">mdi-trash-can-outline</v-icon>
        清空所有随笔
      </v-btn>
    </div>

    <!-- 确认删除对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除所有随笔吗？此操作无法撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showDeleteDialog = false">取消</v-btn>
          <v-btn color="error" variant="elevated" @click="confirmClearAll">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

// Props
const props = defineProps<{
  documentId: string
}>()

// 笔记接口
interface Note {
  id: string
  content: string
  type: 'note' | 'question' | 'important'
  createdAt: string
  updatedAt: string
}

// 响应式数据
const notes = ref<Note[]>([])
const newNoteContent = ref('')
const newNoteType = ref<'note' | 'question' | 'important'>('note')
const editingNoteId = ref<string | null>(null)
const editingContent = ref('')
const showDeleteDialog = ref(false)

// 计算属性
const sortedNotes = computed(() => {
  return [...notes.value].sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )
})

// 存储key
const storageKey = computed(() => `document_notes_${props.documentId}`)

// 加载笔记
const loadNotes = () => {
  try {
    const stored = localStorage.getItem(storageKey.value)
    if (stored) {
      notes.value = JSON.parse(stored)
    }
  } catch (error) {
    console.error('加载笔记失败:', error)
    notes.value = []
  }
}       

// 保存笔记到本地存储
const saveNotesToStorage = () => {
  try {
    localStorage.setItem(storageKey.value, JSON.stringify(notes.value))
  } catch (error) {
    console.error('保存笔记失败:', error)
  }
}

// 添加新笔记
const addNote = () => {
  if (!newNoteContent.value.trim()) return

  const newNote: Note = {
    id: Date.now().toString(),
    content: newNoteContent.value.trim(),
    type: newNoteType.value,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }

  notes.value.unshift(newNote)
  newNoteContent.value = ''
  saveNotesToStorage()
}

// 开始编辑笔记
const startEdit = (note: Note) => {
  editingNoteId.value = note.id
  editingContent.value = note.content
}

// 取消编辑
const cancelEdit = () => {
  editingNoteId.value = null
  editingContent.value = ''
}

// 保存编辑的笔记
const saveNote = (noteId: string) => {
  const noteIndex = notes.value.findIndex(n => n.id === noteId)
  if (noteIndex !== -1 && editingContent.value.trim()) {
    notes.value[noteIndex].content = editingContent.value.trim()
    notes.value[noteIndex].updatedAt = new Date().toISOString()
    saveNotesToStorage()
  }
  cancelEdit()
}

// 删除笔记
const deleteNote = (noteId: string) => {
  const index = notes.value.findIndex(n => n.id === noteId)
  if (index !== -1) {
    notes.value.splice(index, 1)
    saveNotesToStorage()
  }
}

// 清空所有笔记
const clearAllNotes = () => {
  showDeleteDialog.value = true
}

const confirmClearAll = () => {
  notes.value = []
  saveNotesToStorage()
  showDeleteDialog.value = false
}

// 获取笔记类型颜色
const getNoteTypeColor = (type: string) => {
  switch (type) {
    case 'question': return 'orange'
    case 'important': return 'red'
    default: return 'blue'
  }
}

// 获取笔记类型图标
const getNoteTypeIcon = (type: string) => {
  switch (type) {
    case 'question': return 'mdi-help-circle'
    case 'important': return 'mdi-star'
    default: return 'mdi-note-text'
  }
}

// 获取笔记类型文本
const getNoteTypeText = (type: string) => {
  switch (type) {
    case 'question': return '疑问'
    case 'important': return '重点'
    default: return '笔记'
  }
}

// 获取笔记卡片颜色类
const getNoteColorClass = (type: string) => {
  switch (type) {
    case 'question': return 'note-question'
    case 'important': return 'note-important'
    default: return 'note-default'
  }
}

// 格式化时间
const formatTime = (timeStr: string) => {
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7) return `${days}天前`
    
    return date.toLocaleDateString('zh-CN')
  } catch (error) {
    return '未知时间'
  }
}

// 监听文档ID变化，重新加载笔记
watch(() => props.documentId, () => {
  loadNotes()
}, { immediate: true })

// 组件挂载时加载笔记
onMounted(() => {
  loadNotes()
})
</script>

<style scoped>
.document-notes {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.notes-header {
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
  padding-bottom: 8px;
}

.add-note-section {
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  padding: 12px;
}

.note-item {
  transition: all 0.2s ease;
}

.note-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.note-default {
  border-left: 4px solid rgb(var(--v-theme-primary));
}

.note-question {
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.note-important {
  border-left: 4px solid rgb(var(--v-theme-error));
}

.note-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.note-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.note-item:hover .note-actions {
  opacity: 1;
}

.empty-state {
  border: 2px dashed rgb(var(--v-theme-surface-variant));
  border-radius: 8px;
}

/* 滚动条样式 */
.document-notes::-webkit-scrollbar {
  width: 6px;
}

.document-notes::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.document-notes::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.document-notes::-webkit-scrollbar-thumb:hover {
  background: #aaa;
}
</style> 