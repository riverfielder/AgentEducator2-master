import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useVoiceInput() {
  const isRecording = ref(false)
  let recognition: any = null

  const toggleVoiceInput = (onResult: (transcript: string) => void) => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      ElMessage.warning('当前浏览器不支持语音识别')
      return
    }

    if (!recognition) {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      recognition = new SpeechRecognition()
      recognition.lang = 'zh-CN'
      recognition.continuous = true
      recognition.interimResults = false
      
      recognition.onresult = (event: any) => {
        if (event.results && event.results.length > 0) {
          let transcript = ''
          for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript
          }
          onResult(transcript)
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

    if (isRecording.value) {
      recognition.stop()
      isRecording.value = false
    } else {
      recognition.start()
      isRecording.value = true
    }
  }

  return {
    isRecording,
    toggleVoiceInput
  }
}

export function useImageUpload() {
  const uploadedImage = ref<string | null>(null)

  const handleImageUpload = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const imageData = e.target?.result as string
        if (imageData) {
          uploadedImage.value = imageData
          resolve(imageData)
        }
      }
      reader.readAsDataURL(file)
    })
  }

  const removeImage = () => {
    uploadedImage.value = null
  }

  return {
    uploadedImage,
    handleImageUpload,
    removeImage
  }
}
