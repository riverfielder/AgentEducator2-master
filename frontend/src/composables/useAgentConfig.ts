import { ref, watch } from 'vue'
import qaService from '../api/qaService'

export function useAgentConfig() {
  const agentConfig = ref<any>(null)
  const editableAgentConfig = ref<any>(null)
  const showAgentSettings = ref(false)

  // 加载Agent配置
  const loadAgentConfig = async () => {
    try {
      const response = await qaService.getAgentConfig()
      if (response.data && response.data.code === 200) {
        agentConfig.value = response.data.data

        // 确保所有工具都启用且设置合理的默认值
        if (agentConfig.value.tool_configs) {
          Object.keys(agentConfig.value.tool_configs).forEach(toolName => {
            agentConfig.value.tool_configs[toolName].enabled = true
            if (agentConfig.value.tool_configs[toolName].top_k === undefined) {
              agentConfig.value.tool_configs[toolName].top_k = 5
            }
          })
        }

        // 设置最大迭代次数为10
        agentConfig.value.max_iterations = 10
        agentConfig.value.agent_mode_enabled = true

        // 创建编辑用的副本
        editableAgentConfig.value = JSON.parse(JSON.stringify(agentConfig.value))

        // 自动保存配置以确保设置生效
        await saveAgentConfig()
      }
    } catch (error) {
      console.error('加载Agent配置失败:', error)
    }
  }

  // 保存Agent配置
  const saveAgentConfig = async () => {
    try {
      const response = await qaService.updateAgentConfig(editableAgentConfig.value)
      if (response.data && response.data.code === 200) {
        agentConfig.value = JSON.parse(JSON.stringify(editableAgentConfig.value))
        console.log('Agent配置已保存')
        showAgentSettings.value = false
      }
    } catch (error) {
      console.error('保存Agent配置失败:', error)
    }
  }

  // 重置Agent配置编辑
  const resetAgentConfigEdit = () => {
    if (agentConfig.value) {
      editableAgentConfig.value = JSON.parse(JSON.stringify(agentConfig.value))
    }
  }

  // 获取工具显示名称
  const getToolDisplayName = (toolName: string) => {
    const toolNames: Record<string, string> = {
      'video_search': '视频检索',
      'course_search': '课程检索',
      'general_search': '通用检索',
      'general_knowledge': '通用知识'
    }
    return toolNames[toolName] || toolName
  }

  // 监听Agent设置对话框打开，加载配置
  watch(showAgentSettings, (newValue) => {
    if (newValue) {
      if (!agentConfig.value) {
        loadAgentConfig()
      } else {
        resetAgentConfigEdit()
      }
    }
  })

  return {
    agentConfig,
    editableAgentConfig,
    showAgentSettings,
    loadAgentConfig,
    saveAgentConfig,
    resetAgentConfigEdit,
    getToolDisplayName
  }
}
