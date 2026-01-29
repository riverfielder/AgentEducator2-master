import { ref, onBeforeUnmount } from 'vue'
import type { Ref } from 'vue'
import { ElMessage } from 'element-plus'

declare global {
  interface Window {
    webkitSpeechRecognition?: any
    SpeechRecognition?: any
  }
}

export function useVoiceInput(userInput: Ref<string>) {
  const isRecording = ref(false)
  let recognition: any = null

  // 初始化语音识别
  const initVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition
      recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.lang = 'zh-CN'
      recognition.interimResults = false

      recognition.onresult = (event: any) => {
        if (event.results && event.results.length > 0) {
          let transcript = ''
          for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript
          }
          userInput.value = transcript
        }
      }

      recognition.onerror = () => {
        isRecording.value = false
      }

      recognition.onend = () => {
        if (isRecording.value) {
          recognition.start()
        }
      }
    }
  }

  // 切换语音输入
  const toggleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      ElMessage.warning('当前浏览器不支持语音识别')
      return
    }

    if (!recognition) {
      initVoiceRecognition()
    }

    if (isRecording.value) {
      recognition.stop()
      isRecording.value = false
    } else {
      recognition.start()
      isRecording.value = true
    }
  }

  // 组件卸载时清理
  onBeforeUnmount(() => {
    if (recognition && isRecording.value) {
      recognition.stop()
    }
  })

  return {
    isRecording,
    toggleVoiceInput,
    initVoiceRecognition
  }
}
