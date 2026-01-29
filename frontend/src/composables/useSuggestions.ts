import { ref, nextTick } from 'vue'
import type { Suggestion } from '../types/chat'
import globalSearchService from '../api/globalSearchService'

export function useSuggestions() {
  const showSuggestions = ref(false)
  const suggestionsList = ref<Suggestion[]>([])
  const selectedSuggestionIndex = ref(0)
  const suggestionsPosition = ref({ top: 0, left: 0 })
  const isSearchingVideos = ref(false)
  const currentAtQuery = ref('')
  const atStartPosition = ref(0)

  // 显示建议下拉框
  const showSuggestionsDropdown = (textarea: HTMLTextAreaElement) => {
    const rect = textarea.getBoundingClientRect()
    const lineHeight = 24
    const padding = 16
    
    const lines = textarea.value.substring(0, textarea.selectionStart).split('\n').length
    const top = rect.top + padding + (lines - 1) * lineHeight + lineHeight
    
    suggestionsPosition.value = {
      top: Math.min(top, window.innerHeight - 300),
      left: rect.left + padding
    }
    
    showSuggestions.value = true
  }

  // 隐藏建议
  const hideSuggestions = () => {
    showSuggestions.value = false
    suggestionsList.value = []
    selectedSuggestionIndex.value = 0
    currentAtQuery.value = ''
  }

  // 搜索建议
  const searchSuggestions = async (query: string, courseId?: string) => {
    try {
      isSearchingVideos.value = true
      suggestionsList.value = []

      // 使用新的全局搜索API
      const searchResults = await globalSearchService.searchForSuggestions(query, courseId)
      
      const suggestions: Suggestion[] = []

      // 转换搜索结果为建议格式
      searchResults.forEach((item: any) => {
        if (item.type === 'course') {
          const displayText = item.text || item.name || item.title
          suggestions.push({
            id: item.id,
            type: 'course',
            name: displayText,
            text: displayText,
            description: item.description
          })
        } else if (item.type === 'video') {
          const displayText = item.text || item.title || item.name
          suggestions.push({
            id: item.id,
            type: 'video',
            name: displayText,
            text: displayText,
            description: item.description,
            courseName: item.course_name,
            courseId: item.course_id
          })
        } else if (item.type === 'document') {
          const displayText = item.text || item.title || item.name
          suggestions.push({
            id: item.id,
            type: 'document',
            name: displayText,
            text: displayText,
            description: item.description,
            courseName: item.course_name,
            courseId: item.course_id
          })
        } else if (item.type === 'keyword') {
          const displayText = item.text || item.name || item.title
          suggestions.push({
            id: item.id,
            type: 'keyword',
            name: displayText,
            text: displayText,
            description: item.description,
            category: item.category
          })
        }
      })

      suggestionsList.value = suggestions
      selectedSuggestionIndex.value = 0
    } catch (error: any) {
      console.error('搜索建议失败:', error)
      if (error.response && error.response.status === 401) {
        console.warn('用户未登录，无法获取课程列表')
      }
    } finally {
      isSearchingVideos.value = false
    }
  }
  // 处理输入框输入事件
  const handleTextareaInput = (event: Event, userInput: string, textareaElement: HTMLTextAreaElement) => {
    // 安全检查：确保传入的参数有效
    if (!textareaElement) {
      hideSuggestions()
      return
    }

    const textarea = textareaElement
    const value = textarea.value || '' // 确保value不为undefined
    const cursorPos = textarea.selectionStart || 0 // 确保cursorPos不为undefined

    // 安全检查：确保value是字符串
    if (typeof value !== 'string') {
      hideSuggestions()
      return
    }

    // 查找最近的 @ 符号位置
    const beforeCursor = value.substring(0, cursorPos)
    const lastAtIndex = beforeCursor.lastIndexOf('@')
    
    if (lastAtIndex === -1) {
      hideSuggestions()
      return
    }

    // 检查 @ 符号后面是否有空格或其他分隔符
    const afterAt = beforeCursor.substring(lastAtIndex + 1)
    if (/\s/.test(afterAt)) {
      hideSuggestions()
      return
    }

    // 提取查询词
    currentAtQuery.value = afterAt
    atStartPosition.value = lastAtIndex

    // 如果查询词长度大于0，显示建议
    if (currentAtQuery.value.length >= 0) {
      showSuggestionsDropdown(textarea)
      searchSuggestions(currentAtQuery.value)
    } else {
      hideSuggestions()
    }
  }
  // 处理建议选择
  const onSuggestionClick = (suggestion: Suggestion, userInput: string, textareaRef: any) => {
    if (!textareaRef.value || !suggestion) return

    const textarea = textareaRef.value as any
    const textareaElement = textarea.$el ? textarea.$el.querySelector('textarea') : textarea
    if (!textareaElement) return

    // 安全检查：确保userInput是字符串
    const inputValue = userInput || ''
    if (typeof inputValue !== 'string') return

    // 替换 @ 查询部分
    const beforeAt = inputValue.substring(0, atStartPosition.value)
    const afterQuery = inputValue.substring(atStartPosition.value + 1 + currentAtQuery.value.length)
    
    const newValue = beforeAt + `@${suggestion.name} ` + afterQuery

    // 设置光标位置
    const newPosition = beforeAt.length + suggestion.name.length + 2
    nextTick(() => {
      textareaElement.focus()
      textareaElement.setSelectionRange(newPosition, newPosition)
    })

    hideSuggestions()
    
    return {
      newValue,
      suggestion
    }
  }

  // 处理键盘导航
  const handleSuggestionKeyDown = (event: KeyboardEvent) => {
    if (!showSuggestions.value) return false

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault()
        selectedSuggestionIndex.value = Math.min(
          selectedSuggestionIndex.value + 1,
          suggestionsList.value.length - 1
        )
        return true
      case 'ArrowUp':
        event.preventDefault()
        selectedSuggestionIndex.value = Math.max(selectedSuggestionIndex.value - 1, 0)
        return true
      case 'Enter':
        event.preventDefault()
        if (suggestionsList.value[selectedSuggestionIndex.value]) {
          return suggestionsList.value[selectedSuggestionIndex.value]
        }
        return true
      case 'Escape':
        event.preventDefault()
        hideSuggestions()
        return true
    }
    return false
  }

  return {
    showSuggestions,
    suggestionsList,
    selectedSuggestionIndex,
    suggestionsPosition,
    isSearchingVideos,
    currentAtQuery,
    atStartPosition,
    showSuggestionsDropdown,
    hideSuggestions,
    searchSuggestions,
    handleTextareaInput,
    onSuggestionClick,
    handleSuggestionKeyDown
  }
}
