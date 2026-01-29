import type { Ref } from 'vue'
import type { Chat } from './useChatMessages'
import type { Source } from '@/types/chat'
import { useRouter } from 'vue-router'

export function useCitationHandler(
  currentChat: Ref<Chat>,
  jumpToVideoTimepoint: (videoId: string, seconds: number) => void,
  jumpToDocumentSegment?: (documentId: string, segmentNumber: number) => void,
  navigateToSource?: (source: Source) => void
) {
  const router = useRouter()

  // 处理引用标记点击事件
  const handleCitationClick = (event: MouseEvent) => {
    const target = event.target as HTMLElement

    // 检查是否点击的是引用标记
    if (target && target.classList.contains('citation-ref')) {
      event.preventDefault()
      event.stopPropagation()

      // 获取引用编号
      const index = parseInt(target.getAttribute('data-index') || '0', 10)
      if (index === 0) return

      // 查找对应的消息和源 - 从最新的消息开始查找
      let foundSource: Source | null = null
      
      // 倒序遍历消息，优先查找最新的引用源
      for (let i = currentChat.value.messages.length - 1; i >= 0; i--) {
        const message = currentChat.value.messages[i]
        if (message.role === 'assistant' && message.sources) {
          const source = message.sources.find((s: Source) => s.index === index)
          if (source) {
            foundSource = source
            break
          }
        }
      }

      if (foundSource) {
        // 如果提供了navigateToSource函数，直接调用它
        if (navigateToSource) {
          navigateToSource(foundSource)
        } else {
          // 保持原有的逻辑作为后备
          // 处理视频源
          if (foundSource.video_id && foundSource.time_point !== undefined) {
            jumpToVideoTimepoint(foundSource.video_id, foundSource.time_point)
          }
          // 处理文档源
          else if (foundSource.document_id && foundSource.segment_number !== undefined) {
            if (jumpToDocumentSegment) {
              jumpToDocumentSegment(foundSource.document_id, foundSource.segment_number)
            } else {
              // 如果没有提供跳转函数，则导航到文档查看器
              router.push({
                path: `/document/${foundSource.document_id}`,
                query: { segment: foundSource.segment_number.toString() }
              })
            }
          }
        }
      }
    }
  }

  // 处理引用标记悬停事件
  const handleCitationHover = (event: MouseEvent) => {
    const target = event.target as HTMLElement

    if (target && target.classList.contains('citation-ref')) {
      const index = parseInt(target.getAttribute('data-index') || '0', 10)
      if (index === 0) return

      // 查找对应的引用源 - 从最新的消息开始查找
      let foundSource: Source | null = null
      
      for (let i = currentChat.value.messages.length - 1; i >= 0; i--) {
        const message = currentChat.value.messages[i]
        if (message.role === 'assistant' && message.sources) {
          const source = message.sources.find((s: Source) => s.index === index)
          if (source) {
            foundSource = source
            break
          }
        }
      }

      if (foundSource) {
        // 创建悬停提示内容
        let tooltipContent = ''
        if (foundSource.video_id) {
          tooltipContent = `视频: ${foundSource.video_title || '未知视频'}\n时间: ${foundSource.time_formatted}`
        } else if (foundSource.document_id) {
          tooltipContent = `文档: ${foundSource.document_title || '未知文档'}`
          if (foundSource.page_number) {
            tooltipContent += `\n页码: 第${foundSource.page_number}页`
          } else if (foundSource.segment_number) {
            tooltipContent += `\n段落: 第${foundSource.segment_number}段`
          }
        }
        
        // 更新title属性
        target.setAttribute('title', tooltipContent)
      }
    }
  }

  // 处理引用标记鼠标离开事件
  const handleCitationLeave = (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (target && target.classList.contains('citation-ref')) {
      // 恢复默认提示
      target.setAttribute('title', '点击查看引用来源')
    }
  }

  // 跳转到指定时间点
  const jumpToTimepoint = (seconds: number, emit: any) => {
    emit('jump-to-timepoint', seconds)
  }

  return {
    handleCitationClick,
    handleCitationHover,
    handleCitationLeave,
    jumpToTimepoint
  }
}
