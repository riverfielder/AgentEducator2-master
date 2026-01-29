<template>
  <div class="notebook">
    <v-container fluid class="pa-0">
      <v-row class="ma-0">
        <!-- 左侧笔记列表 -->
        <v-col cols="3" sm="3" md="3" lg="2" xl="2" class="pa-2">
          <v-card class="sidebar-card" elevation="2">
            <v-card-title class="sidebar-header">
              <v-icon color="primary" class="mr-2">mdi-note-text</v-icon>
              我的笔记
              <v-spacer></v-spacer>
              <v-btn
                icon
                size="small"
                color="primary"
                variant="text"
                @click="createNewNote"
                class="new-note-fab"
              >
                <v-icon>mdi-plus</v-icon>
              </v-btn>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="px-2 py-2">
              <v-text-field
                v-model="search"
                density="compact"
                variant="outlined"
                placeholder="搜索笔记..."
                prepend-inner-icon="mdi-magnify"
                hide-details
                class="mb-3"
                clearable
              ></v-text-field>
              
              <!-- 笔记统计 -->
              <div class="note-stats mb-3">
                <v-chip size="small" color="primary" variant="tonal">
                  {{ filteredNotes.length }} 篇笔记
                </v-chip>
              </div>
              
              <v-list
                nav
                density="compact"
                class="note-list"
                :selected="[selectedNoteId]"
                color="primary"
              >
                <v-list-item
                  v-for="note in filteredNotes"
                  :key="note.id"
                  :value="note.id"
                  :active="selectedNoteId === note.id"
                  class="note-item"
                  @click="selectNote(note)"
                  rounded="lg"
                >
                  <template v-slot:prepend>
                    <v-avatar size="32" color="primary" variant="tonal">
                      <v-icon size="16">mdi-file-document-outline</v-icon>
                    </v-avatar>
                  </template>
                  
                  <v-list-item-title class="note-title">
                    {{ truncate(note.title, 20) }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="note-meta">
                    <div class="d-flex flex-column">
                      <span v-if="note.course" class="course-tag">{{ note.course }}</span>
                      <span class="time-tag">{{ formatTime(note.updateTime) }}</span>
                    </div>
                  </v-list-item-subtitle>
                  
                  <template v-slot:append>
                    <v-menu location="bottom end">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          icon
                          size="small"
                          variant="text"
                          v-bind="props"
                          @click.stop
                          class="note-menu-btn"
                        >
                          <v-icon size="16">mdi-dots-vertical</v-icon>
                        </v-btn>
                      </template>
                      <v-list density="compact">
                        <v-list-item @click="duplicateNote(note.id)" prepend-icon="mdi-content-copy">
                          <v-list-item-title>复制</v-list-item-title>
                        </v-list-item>
                        <v-list-item @click="exportNote(note.id)" prepend-icon="mdi-download">
                          <v-list-item-title>导出</v-list-item-title>
                        </v-list-item>
                        <v-divider></v-divider>
                        <v-list-item @click="deleteNote(note.id)" prepend-icon="mdi-delete" class="text-error">
                          <v-list-item-title>删除</v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </v-menu>
                  </template>
                </v-list-item>
              </v-list>
              
              <!-- 空状态 -->
              <div v-if="filteredNotes.length === 0" class="empty-state">
                <v-icon size="48" color="grey-lighten-2">mdi-note-plus-outline</v-icon>
                <p class="text-grey text-center mt-2 mb-0">
                  {{ search ? '未找到匹配的笔记' : '还没有笔记，点击右上角添加第一篇笔记吧！' }}
                </p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>        <v-col cols="9" sm="9" md="9" lg="10" xl="10" class="pa-2">
          <v-card class="editor-card">            
            <v-card-title class="editor-header px-6">
              <div class="editor-title-row">
                <v-text-field
                  v-model="currentNote.title"
                  placeholder="笔记标题"
                  hide-details
                  variant="outlined"
                  density="compact"
                  class="title-input"
                ></v-text-field>
                
                <div class="editor-toolbar">
                  <!-- 格式化工具栏 -->
                  <v-btn-toggle v-model="selectedTools" multiple density="compact" variant="outlined" class="mr-2">
                    <v-btn size="small" value="bold" @click="insertFormat('**', '**')" title="加粗">
                      <v-icon size="16">mdi-format-bold</v-icon>
                    </v-btn>
                    <v-btn size="small" value="italic" @click="insertFormat('*', '*')" title="斜体">
                      <v-icon size="16">mdi-format-italic</v-icon>
                    </v-btn>
                    <v-btn size="small" value="underline" @click="insertFormat('<u>', '</u>')" title="下划线">
                      <v-icon size="16">mdi-format-underline</v-icon>
                    </v-btn>
                    <v-btn size="small" value="strikethrough" @click="insertFormat('~~', '~~')" title="删除线">
                      <v-icon size="16">mdi-format-strikethrough</v-icon>
                    </v-btn>
                  </v-btn-toggle>
                                    
                  <!-- 视图模式切换 -->
                  <v-btn-toggle v-model="editorMode" mandatory density="compact" class="mr-2">
                    <v-btn size="small" value="preview" title="预览模式">
                      <v-icon size="16">mdi-eye</v-icon>
                    </v-btn>
                    <v-btn size="small" value="source" title="编辑模式">
                      <v-icon size="16">mdi-code-tags</v-icon>
                    </v-btn>
                    <v-btn size="small" value="split" title="分栏模式">
                      <v-icon size="16">mdi-view-split-vertical</v-icon>
                    </v-btn>
                  </v-btn-toggle>

                  <!-- 操作按钮 -->
                  <v-btn
                    color="primary"
                    size="small"
                    variant="elevated"
                    @click="saveNote"
                    class="mr-1"
                  >
                    <v-icon size="16" class="mr-1">mdi-content-save</v-icon>
                    保存
                  </v-btn>
                  <v-btn
                    color="success"
                    size="small"
                    variant="elevated"
                    @click="createNewNote"
                  >
                    <v-icon size="16" class="mr-1">mdi-plus</v-icon>
                    新建
                  </v-btn>
                </div>
              </div>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text class="editor-content px-6">
              <div class="editor-main">
                <!-- 分栏模式 -->
                <template v-if="editorMode === 'split'">
                  <v-row class="editor-split ma-0">
                    <!-- 左侧编辑区 -->
                    <v-col cols="6" class="pa-2 editor-pane">
                      <div class="editor-wrapper">
                        <v-textarea
                          ref="textareaRef"
                          v-model="currentNote.content"
                          placeholder="输入Markdown源代码... 使用 @ 可以引用课程或视频"
                          hide-details
                          auto-grow
                          rows="20"
                          class="note-textarea monospace"
                          @input="handleTextareaInput"
                          @keydown="handleKeyDown"
                        ></v-textarea>
                        
                        <!-- @ 引用建议下拉框 -->
                        <div
                          v-if="showSuggestions"
                          class="suggestions-dropdown"
                          :style="{
                            position: 'fixed',
                            top: suggestionsPosition.top + 'px',
                            left: suggestionsPosition.left + 'px',
                            zIndex: 1000
                          }"
                        >
                          <v-card class="suggestions-card" elevation="8">
                            <v-card-text class="pa-0">
                              <div v-if="isSearchingVideos" class="suggestion-loading">
                                <v-progress-circular indeterminate size="16" class="mr-2"></v-progress-circular>
                                <span class="text-caption">搜索视频中...</span>
                              </div>
                              <div
                                v-for="(suggestion, index) in suggestionsList"
                                :key="`${suggestion.type}-${suggestion.id}`"
                                class="suggestion-item"
                                :class="{ 'suggestion-selected': index === selectedSuggestionIndex }"
                                @click="onSuggestionClick(suggestion)"
                                @mouseenter="selectedSuggestionIndex = index"
                              >
                                <div class="suggestion-content">
                                  <div class="suggestion-header">
                                    <v-icon 
                                      :color="getSuggestionIconColor(suggestion.type)"
                                      size="small"
                                      class="mr-2"
                                    >
                                      {{ getSuggestionIcon(suggestion.type) }}
                                    </v-icon>
                                    <span class="suggestion-title">{{ suggestion.text || suggestion.name }}</span>
                                  </div>
                                  <div v-if="suggestion.description" class="suggestion-description">
                                    {{ truncate(suggestion.description, 50) }}
                                  </div>
                                  <div v-if="suggestion.courseName" class="suggestion-course">
                                    来自课程: {{ suggestion.courseName }}
                                  </div>
                                </div>
                              </div>
                              <div v-if="suggestionsList.length === 0 && !isSearchingVideos" class="suggestion-empty">
                                <span class="text-caption text-grey">没有找到匹配的课程或视频</span>
                              </div>
                            </v-card-text>
                            <v-divider></v-divider>
                            <v-card-actions class="pa-2">
                              <span class="text-caption text-grey">
                                使用 ↑↓ 选择，Enter 确认，Esc 取消
                              </span>
                            </v-card-actions>
                          </v-card>
                        </div>
                      </div>
                    </v-col>
                    
                    <!-- 分隔线 -->
                    <v-divider vertical></v-divider>
                    
                    <!-- 右侧预览区 -->
                    <v-col cols="6" class="pa-2 preview-pane">
                      <div class="preview-content split-preview">
                        <div v-html="renderedContent"></div>
                      </div>
                    </v-col>
                  </v-row>
                </template>
                
                <!-- 源代码模式 -->
                <template v-else-if="editorMode === 'source'">
                  <div class="editor-wrapper">
                    <v-textarea
                      ref="textareaRef"
                      v-model="currentNote.content"
                      placeholder="输入Markdown源代码... 使用 @ 可以引用课程或视频"
                      hide-details
                      auto-grow
                      rows="15"
                      class="note-textarea monospace"
                      @input="handleTextareaInput"
                      @keydown="handleKeyDown"
                    ></v-textarea>
                    
                    <!-- @ 引用建议下拉框 -->
                    <div
                      v-if="showSuggestions"
                      class="suggestions-dropdown"
                      :style="{
                        position: 'fixed',
                        top: suggestionsPosition.top + 'px',
                        left: suggestionsPosition.left + 'px',
                        zIndex: 1000
                      }"
                    >
                      <v-card class="suggestions-card" elevation="8">
                        <v-card-text class="pa-0">
                          <div v-if="isSearchingVideos" class="suggestion-loading">
                            <v-progress-circular indeterminate size="16" class="mr-2"></v-progress-circular>
                            <span class="text-caption">搜索视频中...</span>
                          </div>
                          <div
                            v-for="(suggestion, index) in suggestionsList"
                            :key="`${suggestion.type}-${suggestion.id}`"
                            class="suggestion-item"
                            :class="{ 'suggestion-selected': index === selectedSuggestionIndex }"
                            @click="onSuggestionClick(suggestion)"
                            @mouseenter="selectedSuggestionIndex = index"
                          >
                            <div class="suggestion-content">
                              <div class="suggestion-header">
                                <v-icon 
                                  :color="suggestion.type === 'course' ? 'primary' : 'secondary'"
                                  size="small"
                                  class="mr-2"
                                >
                                  {{ suggestion.type === 'course' ? 'mdi-book-open-variant' : 'mdi-play-circle' }}
                                </v-icon>
                                <span class="suggestion-title">{{ suggestion.text || suggestion.name }}</span>
                              </div>
                              <div v-if="suggestion.description" class="suggestion-description">
                                {{ truncate(suggestion.description, 50) }}
                              </div>
                              <div v-if="suggestion.courseName" class="suggestion-course">
                                来自课程: {{ suggestion.courseName }}
                              </div>
                            </div>
                          </div>
                          <div v-if="suggestionsList.length === 0 && !isSearchingVideos" class="suggestion-empty">
                            <span class="text-caption text-grey">没有找到匹配的课程或视频</span>
                          </div>
                        </v-card-text>
                        <v-divider></v-divider>
                        <v-card-actions class="pa-2">
                          <span class="text-caption text-grey">
                            使用 ↑↓ 选择，Enter 确认，Esc 取消
                          </span>
                        </v-card-actions>
                      </v-card>
                    </div>
                  </div>
                </template>
                <!-- 预览模式 -->
                <template v-else>
                  <div class="preview-content">
                    <div v-html="renderedContent"></div>
                  </div>
                </template>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { marked } from 'marked'
import courseService from '../api/courseService'
import videoService from '../api/videoService'
import globalSearchService from '../api/globalSearchService'

const search = ref('')
const editorMode = ref('preview')
const selectedTools = ref([])
const notes = ref<any[]>([])
const selectedNoteId = ref<number | null>(null)
const currentNote = ref({
  id: null as number | null,
  title: '',
  content: '',
  course: '',
  updateTime: ''
})
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// @ 引用功能相关状态
const showSuggestions = ref(false)
const suggestionsPosition = ref({ top: 0, left: 0 })
const suggestionsList = ref<any[]>([])
const selectedSuggestionIndex = ref(-1)
const currentQuery = ref('')
const cursorPosition = ref(0)
const isSearchingVideos = ref(false)

onMounted(() => {
  const storedNotes = localStorage.getItem('notes')
  if (storedNotes) {
    notes.value = JSON.parse(storedNotes)
    if (notes.value.length > 0) {
      selectedNoteId.value = notes.value[0].id
    } else {
      selectedNoteId.value = null
    }
  } else {
    notes.value = []
    selectedNoteId.value = null
  }
  
  marked.setOptions({
    gfm: true,
    breaks: true
  })
})

watch(notes, (newNotes) => {
  localStorage.setItem('notes', JSON.stringify(newNotes))
}, { deep: true })

watch(selectedNoteId, (newId) => {
  const noteToSelect = notes.value.find(note => note.id === newId)
  if (noteToSelect) {
    currentNote.value = { ...noteToSelect }
  } else if (notes.value.length > 0) {
    currentNote.value = { ...notes.value[0] }
    selectedNoteId.value = notes.value[0].id
  } else {
    currentNote.value = { id: null, title: '', content: '', course: '', updateTime: '' }
  }
}, { immediate: true })

const filteredNotes = computed(() => {
  if (!search.value) {
    return notes.value
  }
  const lowerSearch = search.value.toLowerCase()
  return notes.value.filter(note =>
    note.title.toLowerCase().includes(lowerSearch) ||
    note.content.toLowerCase().includes(lowerSearch)
  )
})

const selectNote = (note: any) => {
  if (note && note.id) {
    selectedNoteId.value = note.id
    const selectedNote = notes.value.find(n => n.id === note.id)
    if (selectedNote) {
      currentNote.value = { ...selectedNote }
    }
  }
}

const renderedContent = computed(() => {
  try {
    if (!currentNote.value.content) return '';
    
    // 处理 @ 引用，将其转换为可点击的链接
    let content = currentNote.value.content;
    
    // 匹配 @[显示文本](course:id) 格式的课程引用
    content = content.replace(/@\[([^\]]+)\]\(course:([^)]+)\)/g, (match, text, id) => {
      return `<a href="#" class="reference-link course-link" data-type="course" data-id="${id}" onclick="handleReferenceClick('course', '${id}', event)">${text}</a>`;
    });
    
    // 匹配 @[显示文本](video:id) 格式的视频引用
    content = content.replace(/@\[([^\]]+)\]\(video:([^)]+)\)/g, (match, text, id) => {
      return `<a href="#" class="reference-link video-link" data-type="video" data-id="${id}" onclick="handleReferenceClick('video', '${id}', event)">${text}</a>`;
    });
    
    // 匹配 @[显示文本](document:id) 格式的文档引用
    content = content.replace(/@\[([^\]]+)\]\(document:([^)]+)\)/g, (match, text, id) => {
      return `<a href="#" class="reference-link document-link" data-type="document" data-id="${id}" onclick="handleReferenceClick('document', '${id}', event)">${text}</a>`;
    });
    
    // 匹配 @[显示文本](keyword:id) 格式的知识点引用
    content = content.replace(/@\[([^\]]+)\]\(keyword:([^)]+)\)/g, (match, text, id) => {
      return `<a href="#" class="reference-link keyword-link" data-type="keyword" data-id="${id}" onclick="handleReferenceClick('keyword', '${id}', event)">${text}</a>`;
    });
    
    return marked.parse(content) as string;
  } catch (error) {
    console.error('Error rendering Markdown:', error);
    return '<p>Error rendering Markdown.</p>';
  }
});

// 处理引用点击
const handleReferenceClick = (type: string, id: string, event: Event) => {
  event.preventDefault();
  
  if (type === 'course') {
    // 导航到课程页面，会自动跳转到第一个视频
    window.open(`/course/${id}`, '_blank');
  } else if (type === 'video') {
    // 导航到视频页面 - 需要先获取视频详情获取课程ID
    navigateToVideo(id);
  } else if (type === 'document') {
    // 导航到文档页面
    navigateToDocument(id);
  } else if (type === 'keyword') {
    // 导航到知识点相关页面或显示知识点详情
    navigateToKeyword(id);
  }
}

const navigateToVideo = async (videoId: string) => {
  try {
    const response = await videoService.getVideoDetail(videoId);
    if (response.data?.code === 200) {
      const video = response.data.data;
      if (video.courseId) {
        window.open(`/course/${video.courseId}/video/${videoId}`, '_blank');
      } else {
        console.error('视频没有关联的课程');
      }
    }
  } catch (error) {
    console.error('获取视频详情失败:', error);
  }
}

const navigateToDocument = (documentId: string) => {
  window.open(`/document/${documentId}`, '_blank');
}

const navigateToKeyword = (keywordId: string) => {
  window.open(`/knowledge-point/${keywordId}`, '_blank');
}

// 将方法暴露到全局，供 onclick 使用
  if (typeof window !== 'undefined') {
    window.handleReferenceClick = handleReferenceClick;
    window.navigateToDocument = navigateToDocument;
    window.navigateToKeyword = navigateToKeyword;
  }

const createNewNote = () => {
  const newNoteData = {
    id: Date.now(),
    title: '新笔记',
    content: '',
    course: '',
    updateTime: new Date().toLocaleString()
  }
  notes.value.unshift(newNoteData)
  selectedNoteId.value = newNoteData.id
  currentNote.value = { ...newNoteData }
}

const saveNote = () => {
  if (!currentNote.value || currentNote.value.id === null) {
    console.error('Cannot save note, current note is invalid.')
    return
  }

  const noteIndex = notes.value.findIndex(note => note.id === currentNote.value.id)
  const now = new Date().toLocaleString()

  if (noteIndex !== -1) {
    notes.value[noteIndex] = { ...currentNote.value, updateTime: now }
  } else {
    const newNoteWithData = { ...currentNote.value, updateTime: now, id: currentNote.value.id || Date.now() }
    notes.value.unshift(newNoteWithData)
    selectedNoteId.value = newNoteWithData.id
  }
}

const deleteNote = (noteId: number) => {
  const noteIndex = notes.value.findIndex(note => note.id === noteId)
  if (noteIndex !== -1) {
    notes.value.splice(noteIndex, 1)
    
    if (selectedNoteId.value === noteId) {
      selectedNoteId.value = notes.value.length > 0 ? notes.value[0].id : null
      if (selectedNoteId.value !== null) {
        const newSelectedNote = notes.value.find(n => n.id === selectedNoteId.value)
        if (newSelectedNote) {
          currentNote.value = { ...newSelectedNote }
        }
      } else {
        currentNote.value = { id: null, title: '', content: '', course: '', updateTime: '' }
      }
    }
  }
}

const truncate = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// 获取建议类型对应的图标
const getSuggestionIcon = (type: string) => {
  switch (type) {
    case 'course':
      return 'mdi-book-open-variant'
    case 'video':
      return 'mdi-play-circle'
    case 'document':
      return 'mdi-file-document'
    case 'keyword':
      return 'mdi-tag'
    default:
      return 'mdi-help-circle'
  }
}

// 获取建议类型对应的颜色
const getSuggestionIconColor = (type: string) => {
  switch (type) {
    case 'course':
      return 'primary'  // 蓝色
    case 'video':
      return 'pink'     // 粉色
    case 'document':
      return 'orange'   // 橙色
    case 'keyword':
      return 'green'    // 绿色
    default:
      return 'grey'
  }
}

// @ 引用功能相关方法
const handleTextareaInput = async (event: Event) => {
  const textarea = event.target as HTMLTextAreaElement
  const value = textarea.value
  const cursor = textarea.selectionStart
  cursorPosition.value = cursor

  // 检查是否输入了 @
  const beforeCursor = value.substring(0, cursor)
  const match = beforeCursor.match(/@([^@\s]*)$/)
  
  if (match) {
    const query = match[1]
    currentQuery.value = query
    
    if (query.length >= 0) { // 即使是空查询也显示建议
      await searchSuggestions(query)
      showSuggestions.value = true
      updateSuggestionsPosition(textarea, match.index! + 1) // +1 跳过 @
    }
  } else {
    hideSuggestions()
  }
}

const searchSuggestions = async (query: string) => {
  try {
    suggestionsList.value = []
    selectedSuggestionIndex.value = -1
    isSearchingVideos.value = true

    // 使用全局搜索API获取建议
    const suggestions = await globalSearchService.searchForSuggestions(query)
    
    // 转换为组件需要的格式
    const formattedSuggestions = suggestions.map((suggestion: any) => {
      let displayText = ''
      switch (suggestion.type) {
        case 'course':
          displayText = `[课程] ${suggestion.text}`
          break
        case 'keyword':
          displayText = `[知识点] ${suggestion.text}${suggestion.category ? ` - ${suggestion.category}` : ''}`
          break
        case 'video':
          displayText = `[视频] ${suggestion.text}`
          break
        case 'document':
          displayText = `[文档] ${suggestion.text}`
          break
        default:
          displayText = suggestion.text
      }
      
      return {
        type: suggestion.type,
        id: suggestion.id || suggestion.text,
        name: suggestion.text,
        text: suggestion.text, // 保持兼容性
        description: suggestion.category || '',
        course_name: suggestion.type === 'course' ? suggestion.text : '',
        displayText
      }
    })
    
    suggestionsList.value = formattedSuggestions.slice(0, 8) // 限制建议数量
    isSearchingVideos.value = false
  } catch (error) {
    console.error('搜索建议失败:', error)
    isSearchingVideos.value = false
  }
}

const updateSuggestionsPosition = (textarea: HTMLTextAreaElement, atPosition: number) => {
  const rect = textarea.getBoundingClientRect()
  const style = window.getComputedStyle(textarea)
  
  // 获取 @ 之前的文本
  const textBeforeAt = textarea.value.substring(0, atPosition)
  const lines = textBeforeAt.split('\n')
  const currentLineIndex = lines.length - 1
  const currentLineText = lines[currentLineIndex] || ''
  
  // 创建测量元素来计算当前行文本宽度
  const measureSpan = document.createElement('span')
  measureSpan.style.position = 'absolute'
  measureSpan.style.visibility = 'hidden'
  measureSpan.style.whiteSpace = 'pre'
  measureSpan.style.font = style.font
  measureSpan.style.fontSize = style.fontSize
  measureSpan.style.fontFamily = style.fontFamily
  measureSpan.style.fontWeight = style.fontWeight
  measureSpan.style.letterSpacing = style.letterSpacing
  measureSpan.textContent = currentLineText
  
  document.body.appendChild(measureSpan)
  const textWidth = measureSpan.getBoundingClientRect().width
  document.body.removeChild(measureSpan)
  
  // 计算基本位置信息
  const lineHeight = parseInt(style.lineHeight) || parseInt(style.fontSize) * 1.4
  const paddingLeft = parseInt(style.paddingLeft) || 12
  const paddingTop = parseInt(style.paddingTop) || 12
  
  // 设置面板位置：在当前行右侧，往左偏移更多
  suggestionsPosition.value = {
    top: rect.top + paddingTop + (currentLineIndex * lineHeight) + lineHeight + 8,
    left: rect.left + paddingLeft + textWidth - 50  // 往左移动60像素
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (!showSuggestions.value || suggestionsList.value.length === 0) return

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      selectedSuggestionIndex.value = Math.min(
        selectedSuggestionIndex.value + 1,
        suggestionsList.value.length - 1
      )
      break
    case 'ArrowUp':
      event.preventDefault()
      selectedSuggestionIndex.value = Math.max(
        selectedSuggestionIndex.value - 1,
        -1
      )
      break
    case 'Enter':
      if (selectedSuggestionIndex.value >= 0) {
        event.preventDefault()
        selectSuggestion(suggestionsList.value[selectedSuggestionIndex.value])
      }
      break
    case 'Escape':
      event.preventDefault()
      hideSuggestions()
      break
  }
}

const selectSuggestion = (suggestion: any) => {
  if (!textareaRef.value || !suggestion) return

  const textarea = textareaRef.value
  const value = textarea.value
  const cursor = cursorPosition.value

  // 找到 @ 的位置
  const beforeCursor = value.substring(0, cursor)
  const match = beforeCursor.match(/@([^@\s]*)$/)
  
  if (match) {
    const atIndex = match.index!
    const beforeAt = value.substring(0, atIndex)
    const afterCursor = value.substring(cursor)
    
    // 根据类型生成不同的引用格式
    let reference = ''
    const suggestionText = suggestion.text || suggestion.name || suggestion.displayText || '未知'
    const suggestionId = suggestion.id || ''
    const suggestionType = suggestion.type || 'unknown'
    
    // 确保文本不为空
    if (!suggestionText || suggestionText.trim() === '') {
      console.warn('建议文本为空:', suggestion)
      hideSuggestions()
      return
    }
    
    if (suggestionType === 'course') {
      reference = `@[${suggestionText}](course:${suggestionId})`
    } else if (suggestionType === 'keyword') {
      reference = `@[${suggestionText}](keyword:${suggestionId})`
    } else if (suggestionType === 'video') {
      reference = `@[${suggestionText}](video:${suggestionId})`
    } else if (suggestionType === 'document') {
      reference = `@[${suggestionText}](document:${suggestionId})`
    } else {
      // 如果类型不匹配，使用默认格式
      reference = `@[${suggestionText}](${suggestionType}:${suggestionId})`
    }
    
    const newValue = beforeAt + reference + afterCursor
    currentNote.value.content = newValue
    
    // 设置光标位置到引用后面
    nextTick(() => {
      if (reference && reference.length > 0) {
        const newCursorPos = atIndex + reference.length
        textarea.setSelectionRange(newCursorPos, newCursorPos)
        //插入空格，避免再次出发引用菜单
        textarea.value = newValue + ' '
        currentNote.value.content = textarea.value
        textarea.focus()
      }
    })
  }
  hideSuggestions()
}

const hideSuggestions = () => {
  showSuggestions.value = false
  suggestionsList.value = []
  selectedSuggestionIndex.value = -1
  currentQuery.value = ''
}

// 点击建议项
const onSuggestionClick = (suggestion: any) => {
  selectSuggestion(suggestion)
}

// 格式化时间显示
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) {
      return '今天'
    } else if (days === 1) {
      return '昨天'
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return date.toLocaleDateString()
    }
  } catch {
    return timeStr
  }
}

// 复制笔记
const duplicateNote = (noteId: number) => {
  const originalNote = notes.value.find(note => note.id === noteId)
  if (originalNote) {
    const duplicatedNote = {
      ...originalNote,
      id: Date.now(),
      title: `${originalNote.title} - 副本`,
      updateTime: new Date().toLocaleString()
    }
    notes.value.unshift(duplicatedNote)
  }
}

// 导出笔记
const exportNote = (noteId: number) => {
  const note = notes.value.find(n => n.id === noteId)
  if (note) {
    const content = `# ${note.title}\n\n${note.content}`
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${note.title}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

// 扩展Window接口以包含我们的自定义方法
declare global {
  interface Window {
    handleReferenceClick: (type: string, id: string, event: Event) => void;
    navigateToDocument: (documentId: string) => void;
    navigateToKeyword: (keywordId: string) => void;
  }
}

// 文本格式化方法
const insertFormat = (startTag: string, endTag: string) => {
  if (!textareaRef.value) return

  // 获取实际的textarea元素
  let textarea: HTMLTextAreaElement | null = null
  
  if (textareaRef.value instanceof HTMLTextAreaElement) {
    textarea = textareaRef.value
  } else if ((textareaRef.value as any)?.$el) {
    // 处理Vue组件的情况
    textarea = (textareaRef.value as any).$el.querySelector('textarea')
  } else if ((textareaRef.value as any)?.querySelector) {
    // 处理可能的DOM元素
    textarea = (textareaRef.value as any).querySelector('textarea')
  }
  
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = textarea.value.substring(start, end)
  
  let newText = ''
  if (selectedText) {
    // 如果有选中文本，在选中文本前后添加格式标签
    newText = startTag + selectedText + endTag
  } else {
    // 如果没有选中文本，插入格式标签并将光标放在中间
    newText = startTag + endTag
  }
  
  // 更新内容
  const beforeSelection = textarea.value.substring(0, start)
  const afterSelection = textarea.value.substring(end)
  const newContent = beforeSelection + newText + afterSelection
  
  currentNote.value.content = newContent
  
  // 在下一个tick中设置光标位置
  nextTick(() => {
    if (selectedText) {
      // 如果有选中文本，将光标放在格式化文本之后
      const newCursorPos = start + newText.length
      textarea!.setSelectionRange(newCursorPos, newCursorPos)
    } else {
      // 如果没有选中文本，将光标放在开始和结束标签之间
      const cursorPos = start + startTag.length
      textarea!.setSelectionRange(cursorPos, cursorPos)
    }
    textarea!.focus()
  })
}
</script>

<style scoped>
.notebook {
  height: 100%;
  width: 100%;
}

.sidebar-card {
  height: calc(100vh - 150px);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  background: #7c44dc;
  color: white;
  font-weight: 600;
  padding: 16px 20px;
}

.sidebar-header .v-icon {
  color: white !important;
}

.new-note-fab {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
}

.new-note-fab:hover {
  background: rgba(255, 255, 255, 0.3);
}

.note-stats {
  text-align: center;
}

.note-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.note-item {
  border-radius: 12px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.note-item:hover {
  background-color: #f8f9fa;
  border-color: #e9ecef;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.note-item.v-list-item--active {
  background: #c57de1;
  color: white;
}

.note-item.v-list-item--active .note-title,
.note-item.v-list-item--active .note-meta {
  color: white;
}

.note-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 4px;
}

.note-meta {
  font-size: 11px;
  opacity: 0.8;
}

.course-tag {
  background: rgba(25, 118, 210, 0.1);
  color: #1976d2;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 500;
  margin-bottom: 2px;
  display: inline-block;
}

.time-tag {
  font-size: 10px;
  opacity: 0.7;
}

.note-menu-btn {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.note-item:hover .note-menu-btn {
  opacity: 1;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9e9e9e;
}

.editor-card {
  height: calc(100vh - 150px);
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.editor-header {
  background: #ffffff;
  border-bottom: 1px solid #e9ecef;
  padding: 16px 24px;
}

.editor-title-row {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.title-input {
  font-size: 24px;
  font-weight: 700;
  max-width: 500px;
  flex: 1;
  position: relative;
}

.title-input :deep(.v-field) {
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.title-input :deep(.v-field):hover {
  border-color: #1976d2;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.1);
}

.title-input :deep(.v-field):focus-within {
  border-color: #1976d2;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.title-input :deep(.v-field__input) {
  font-size: 24px;
  font-weight: 700;
  padding: 16px 20px;
  color: #2c3e50;
  background: transparent;
}

.title-input :deep(.v-field__input)::placeholder {
  color: #9e9e9e;
  font-weight: 600;
}

.title-input :deep(.v-field__outline) {
  display: none;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-content {
  flex: 1;
  padding: 0;
  background-color: #fff;
  overflow-y: auto;
}

.editor-main {
  height: 100%;
}

.editor-split {
  height: 100%;
  display: flex;
}

.editor-pane,
.preview-pane {
  height: calc(100vh - 300px);
  flex: 1;
}

.editor-pane {
  border-right: 1px solid #e9ecef;
}

.editor-wrapper {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.note-textarea {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.6;
  height: 100%;
  min-height: 500px;
  flex: 1;
}

.note-textarea :deep(.v-field__input) {
  min-height: 500px;
  padding: 20px;
}

.monospace {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
}

.preview-content {
  padding: 20px;
  font-size: 14px;
  line-height: 1.8;
  overflow-y: auto;
  height: 100%;
  background: #fafafa;
  border-radius: 8px;
  margin: 8px;
}

.split-preview {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  height: calc(100% - 16px);
  overflow-y: auto;
}

/* 预览内容样式 */
.preview-content :deep(h1),
.preview-content :deep(h2),
.preview-content :deep(h3),
.preview-content :deep(h4),
.preview-content :deep(h5),
.preview-content :deep(h6) {
  margin-top: 1.5em;
  margin-bottom: 0.8em;
  font-weight: 700;
  color: #2c3e50;
}

.preview-content :deep(h1) {
  font-size: 2.2em;
  border-bottom: 3px solid #1976d2;
  padding-bottom: 0.3em;
}

.preview-content :deep(h2) {
  font-size: 1.8em;
  border-bottom: 2px solid #95a5a6;
  padding-bottom: 0.3em;
}

.preview-content :deep(h3) {
  font-size: 1.5em;
  color: #1976d2;
}

.preview-content :deep(p) {
  margin-bottom: 1.2em;
  color: #34495e;
}

.preview-content :deep(ul),
.preview-content :deep(ol) {
  margin-bottom: 1.2em;
  padding-left: 2em;
}

.preview-content :deep(li) {
  margin-bottom: 0.5em;
}

.preview-content :deep(blockquote) {
  margin: 1.5em 0;
  padding: 1em 1.5em;
  border-left: 4px solid #1976d2;
  color: #666;
  background: #f8f9fa;
  border-radius: 0 8px 8px 0;
  font-style: italic;
}

.preview-content :deep(code) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  background: #f1f3f4;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  color: #d73a49;
  font-weight: 500;
}

.preview-content :deep(pre) {
  background: #2d3748;
  color: #e2e8f0;
  padding: 1.5em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1.5em 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.preview-content :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: inherit;
  display: block;
  white-space: pre;
  color: #e2e8f0;
}

.preview-content :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5em auto;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.preview-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preview-content :deep(th),
.preview-content :deep(td) {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.preview-content :deep(th) {
  background: #1976d2;
  color: white;
  font-weight: 600;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #1976d2;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #1565c0;
}

.same-size-btn {
  min-width: 80px;
  height: 40px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  text-transform: none;
}

/* @ 引用功能样式 */
.suggestions-dropdown {
  max-width: 450px;
  min-width: 350px;
}

.suggestions-card {
  max-height: 350px;
  overflow-y: auto;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s ease;
}

.suggestion-item:hover,
.suggestion-selected {
  background: #f8f9fa;
  transform: translateX(4px);
}

.suggestion-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.suggestion-header {
  display: flex;
  align-items: center;
  font-weight: 600;
}

.suggestion-title {
  flex: 1;
  font-size: 14px;
  color: #2d3748;
}

.suggestion-description {
  font-size: 12px;
  color: #718096;
  margin-left: 28px;
  line-height: 1.4;
}

.suggestion-course {
  font-size: 11px;
  color: #a0aec0;
  margin-left: 28px;
  font-style: italic;
}

.suggestion-loading {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  color: #718096;
}

.suggestion-empty {
  padding: 20px;
  text-align: center;
  color: #a0aec0;
}

/* 预览模式中的引用链接样式 */
.preview-content :deep(.reference-link) {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s ease;
  margin: 0 2px;
  position: relative;
  overflow: hidden;
}

.preview-content :deep(.reference-link):before {
  content: '@';
  margin-right: 3px;
  font-weight: 700;
}

.preview-content :deep(.course-link) {
  background: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.preview-content :deep(.course-link):hover {
  background: #bbdefb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

.preview-content :deep(.video-link) {
  background: #f3e5f5;
  color: #7b1fa2;
  border: 1px solid #e1bee7;
}

.preview-content :deep(.video-link):hover {
  background: #e1bee7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(123, 31, 162, 0.3);
}

.preview-content :deep(.document-link) {
  background: #fff3e0;
  color: #ff9800;
  border: 1px solid #ffcc02;
}

.preview-content :deep(.document-link):hover {
  background: #ffcc02;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.3);
}

.preview-content :deep(.keyword-link) {
  background: #e8f5e8;
  color: #4caf50;
  border: 1px solid #a5d6a7;
}

.preview-content :deep(.keyword-link):hover {
  background: #a5d6a7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .editor-split {
    flex-direction: column;
  }
  
  .editor-pane,
  .preview-pane {
    height: 50vh;
  }
}

@media (max-width: 768px) {
  .sidebar-card {
    height: calc(100vh - 120px);
  }
  
  .editor-card {
    height: calc(100vh - 120px);
  }
  
  .title-input {
    font-size: 18px;
  }
  
  .editor-actions {
    flex-wrap: wrap;
    gap: 4px;
  }
    .same-size-btn {
    min-width: 60px;
    height: 32px;
    font-size: 12px;
  }
}
</style>