<template>
  <div class="ai-chat-container">
    <div class="chat-messages-container" ref="chatHistory">
      <!-- 消息列表 -->
      <template v-if="currentChat.messages.length > 0">
        <div v-for="(message, index) in currentChat.messages" :key="index" class="mb-3 message-wrapper">
          
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="user-message-container">
            <div class="d-flex align-center justify-end mb-1">
              <v-avatar color="grey-lighten-1" size="24" class="ms-2">
                <v-icon color="white" size="14">mdi-account</v-icon>
              </v-avatar>
            </div>
            <div class="user-message-bubble">
              <div class="text-body-2">{{ message.content }}</div>
            </div>
          </div>
            <!-- AI消息 -->
          <div v-else class="ai-message-container">
            <div class="d-flex align-center mb-1">
              <v-avatar color="primary" size="24" class="me-2">
                <v-icon color="white" size="14">mdi-robot</v-icon>
              </v-avatar>
              <div class="text-caption text-medium-emphasis">AI Agent助手</div>
            </div>
            
            <!-- AI消息气泡 -->
            <div class="ai-message-bubble"> <!-- 线性穿插的消息片段显示 -->
              <div v-if="message.messageSegments && message.messageSegments.length > 0" class="message-segments">
                
                <!-- 按时间顺序排列所有片段 -->
                <template v-for="(segment, segIndex) in getSortedSegments(message)" :key="segment.id">
                    <!-- 工具调用片段 - 扁平化显示 -->
                  <div v-if="segment.type === 'tool_call' && !segment.hideCompletely" class="tool-call-segment mb-2">
                    <!-- 成功完成后的简洁显示 -->
                    <div v-if="segment.isComplete && !segment.showDetailed" class="tool-call-compact">
                      <v-fade-transition>
                        <div class="d-flex align-center px-3 py-2 tool-success-banner"
                          @click="segment.showDetailed = true">
                          <v-avatar size="20" :color="segment.toolInfo?.tool_color || 'primary'" class="me-2"
                            variant="flat">
                            <v-icon :icon="segment.toolInfo?.tool_icon || 'mdi-tools'" size="12" color="white" />
                          </v-avatar>
                          <span class="text-body-2 me-1">{{ segment.toolInfo?.tool_name }}</span>
                          <v-icon icon="mdi-check-circle" color="success" size="16" class="mr-1" />
                          
                          <!-- 简洁模式下的文档数量显示 -->
                          <v-chip v-if="segment.toolResult?.documents_count" color="info" size="x-small"
                            variant="outlined" class="ml-2">
                            <v-icon start size="x-small">mdi-file-document</v-icon>
                            {{ segment.toolResult.documents_count }}
                          </v-chip>
                        </div>
                      </v-fade-transition>
                    </div>
                      <!-- 执行中或详细显示 -->
                    <div v-else class="tool-call-detailed">
                      <div class="d-flex align-center mb-2">
                        <v-avatar :color="segment.toolInfo?.tool_color || 'primary'" size="22" class="me-3"
                          variant="flat">
                          <v-icon :icon="segment.toolInfo?.tool_icon || 'mdi-tools'" size="14" color="white" />
                        </v-avatar>
                        <span class="text-subtitle-2 font-weight-medium">{{ segment.toolInfo?.tool_name }}</span>
                        <v-spacer />
                        
                        <!-- 折叠按钮（仅在完成状态显示） -->
                        <v-btn v-if="segment.isComplete" icon="mdi-chevron-up" size="x-small" variant="text"
                          @click="segment.showDetailed = false" class="me-1" />

                        <v-chip :color="segment.isComplete ? 'success' : 'primary'" variant="flat" size="small"
                          class="ms-1">
                          <v-icon :icon="segment.isComplete ? 'mdi-check' : 'mdi-loading mdi-spin'" start
                            size="x-small" />
                          {{ segment.isComplete ? '已完成' : '执行中' }}
                        </v-chip>
                      </div>
                      
                      <div class="text-caption text-medium-emphasis mb-2">
                        {{ segment.toolInfo?.description }}
                      </div>
                      
                      <!-- 工具上下文信息 -->
                      <div v-if="segment.toolInfo?.context" class="tool-context-chips mb-2">
                        <v-chip v-for="(value, key) in segment.toolInfo.context" :key="String(key)" size="x-small"
                          variant="outlined" color="grey" class="me-1 mb-1">
                          {{ formatContextInfo(String(key), value) }}
                        </v-chip>
                      </div>
                      <!-- 执行进度 -->
                      <v-progress-linear v-if="!segment.isComplete" indeterminate
                        :color="segment.toolInfo?.tool_color || 'primary'" height="2" class="mt-1" />

                      <!-- 执行结果（仅在完成时显示） -->
                      <div v-if="segment.isComplete && segment.toolResult" class="tool-result-info mt-2">
                        <div class="d-flex align-center text-caption text-medium-emphasis">
                          <v-icon :icon="segment.toolResult.success ? 'mdi-check-circle' : 'mdi-alert-circle'"
                            :color="segment.toolResult.success ? 'success' : 'error'" size="12" class="me-1" />
                          <span>{{ segment.toolResult.message }}</span>
                          <v-spacer />
                          <span v-if="segment.toolResult.execution_time">
                            {{ Math.round(segment.toolResult.execution_time) }}ms
                          </span>
                    </div>

                        <div v-if="segment.toolResult.documents_count" class="text-caption text-medium-emphasis mt-1">
                          找到 {{ segment.toolResult.documents_count }} 个相关文档
                        </div>
                      </div>
                    </div>
                  </div><!-- 工具结果片段 - 只显示失败情况 -->
                  <div v-if="segment.type === 'tool_result' && !segment.toolResult?.success"
                    class="tool-result-segment mb-3">
                    <div class="tool-result-error">
                      <div class="d-flex align-center mb-2">
                        <v-icon icon="mdi-alert-circle" color="error" size="16" class="me-2" />
                        <span class="text-caption font-weight-medium text-error">
                          执行失败
                        </span>
                        <v-spacer />
                        <span v-if="segment.toolResult?.execution_time" class="text-caption text-medium-emphasis">
                          {{ Math.round(segment.toolResult.execution_time) }}ms
                        </span>
                      </div>
                      
                      <div class="text-caption mb-1 text-error">
                        {{ segment.toolResult?.message }}
                      </div>
                    </div>
                  </div>
                  
                  <!-- 内容片段 -->
                  <div v-else-if="segment.type === 'content'" class="content-segment mb-2">
                    <div class="text-body-2 markdown-body" v-html="processMessageContent(segment.content || '')"
                         @click="handleCitationClick">
                    </div>
                  </div>
                  
                </template>
              </div>
              
              <!-- 等待状态和处理过程（仅在没有内容且正在输入时显示） -->
              <div v-if="!message.content && index === currentChat.messages.length - 1 && isTyping" 
                   class="typing-container">
                <!-- 显示当前处理状态 -->
                <div v-if="currentStatus || currentToolInfo" class="ai-thinking-status">
                  <!-- 工具执行状态显示 -->
                  <div v-if="currentToolInfo" class="tool-execution-status mb-3">
                    <div class="d-flex align-center mb-2">
                      <v-avatar :color="currentToolInfo.tool_color || 'primary'" size="20" class="me-2">
                        <v-icon :icon="currentToolInfo.tool_icon || 'mdi-tools'" size="12" color="white" />
                      </v-avatar>
                      <span class="text-subtitle-2 font-weight-medium">{{ currentToolInfo.tool_name }}</span>
                      <v-spacer />
                      <v-chip :color="getToolStatusColor(currentToolInfo.status)" variant="flat" size="x-small"
                        class="ms-2">
                        <v-icon :icon="getToolStatusIcon(currentToolInfo.status)" start size="x-small" />
                        {{ getToolStatusText(currentToolInfo.status) }}
                      </v-chip>
                    </div>
                    
                    <div class="text-caption text-medium-emphasis mb-2">
                      {{ currentToolInfo.description }}
                    </div>
                    
                    <!-- 工具上下文信息 -->
                    <div v-if="currentToolInfo.context" class="tool-context-chips">
                      <v-chip v-for="(value, key) in currentToolInfo.context" :key="String(key)" size="x-small"
                        variant="outlined" color="grey" class="me-1 mb-1">
                        {{ formatContextInfo(String(key), value) }}
                      </v-chip>
                    </div>
                    
                    <!-- 执行进度 -->
                    <v-progress-linear v-if="currentToolInfo.status === 'running'" indeterminate
                      :color="currentToolInfo.tool_color || 'primary'" height="2" class="mt-2" />
                  </div>
                  
                  <!-- 通用状态显示 -->
                  <div v-else-if="currentStatus" class="d-flex align-center mb-2">
                    <v-progress-circular indeterminate size="16" width="2" color="primary" class="me-2" />
                    <span class="status-text">{{ currentStatus }}</span>
                  </div>
                  
                  <!-- 状态统计信息 -->
                  <div v-if="statusStats" class="status-stats-inline">
                    <v-chip v-if="statusStats.document_count" size="x-small" color="blue-grey" variant="outlined"
                      class="me-1 mb-1">
                      <v-icon start size="x-small">mdi-file-document</v-icon>
                      {{ statusStats.document_count }} 文档
                    </v-chip>
                    <v-chip v-if="statusStats.tokens" size="x-small" color="green" variant="outlined" class="me-1 mb-1">
                      <v-icon start size="x-small">mdi-counter</v-icon>
                      {{ statusStats.tokens }} Token
                    </v-chip>
                    <v-chip v-if="statusStats.sources" size="x-small" color="orange" variant="outlined"
                      class="me-1 mb-1">
                      <v-icon start size="x-small">mdi-link</v-icon>
                      {{ statusStats.sources }} 引用
                    </v-chip>
                  </div>
                </div>
                
                <!-- 默认思考状态 -->
                <div v-else class="default-thinking">
                  <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                  </div>
                  <span class="typing-text"></span>
                </div>
              </div>              <!-- 消息内容 (仅在历史消息中没有messageSegments时显示) -->
              <div v-if="message.content && (!message.messageSegments || message.messageSegments.length === 0) && !message.isStreaming"
                class="ai-message-content">
                <div class="text-body-2 markdown-body" v-html="processMessageContent(message.content)"
                     @click="handleCitationClick">
                </div>
              </div>
            </div>
              <!-- 引用来源 -->
            <div v-if="message.sources && message.sources.length > 0" class="sources-container">
              <v-btn size="small" variant="elevated" density="compact" color="blue-grey-lighten-4"
                prepend-icon="mdi-bookmark-multiple" @click="toggleSourcesVisibility(message)"
                class="sources-toggle mb-2" elevation="2">
                <span class="text-blue-grey-darken-3 font-weight-medium">
                  {{ message.sources.length }} 个引用来源
                </span>
                <v-icon end size="small" color="blue-grey-darken-2">
                  {{ message.showSources ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                </v-icon>
              </v-btn>
              
              <v-expand-transition>
                <div v-if="message.showSources" class="sources-list">
                  <v-card v-for="source in message.sources" :key="source.index" class="mb-3 source-card elevation-2"
                    variant="outlined">
                    <div class="source-header">
                      <v-chip size="small" color="primary" class="source-index">
                        <v-icon start size="x-small">mdi-numeric-{{ source.index }}-circle</v-icon>
                        {{ source.index }}
                      </v-chip>
                      <div class="source-meta">
                        <h4 class="source-title">
                          <template v-if="source.type === 'document'">
                            {{ source.document_title || '未知文档' }}
                          </template>
                          <template v-else>
                            {{ source.video_title || '未知视频' }}
                          </template>
                        </h4>
                        <div class="source-time" v-if="source.type === 'video'">
                          <v-icon size="small" color="blue-grey" class="me-1">mdi-clock-outline</v-icon>
                          <span class="text-blue-grey-darken-1 text-caption">{{ source.time_formatted }}</span>
                        </div>
                        <div class="source-info" v-else-if="source.type === 'document'">
                          <v-icon size="small" color="blue-grey" class="me-1">mdi-file-document-outline</v-icon>
                          <span class="text-blue-grey-darken-1 text-caption">
                            <template v-if="source.page_number">第{{ source.page_number }}页</template>
                            <template v-else-if="source.segment_number">第{{ source.segment_number }}段</template>
                            <template v-else>文档片段</template>
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div class="source-content-wrapper">
                      <div class="source-content">
                        <v-icon class="quote-icon" color="blue-grey-lighten-2">mdi-format-quote-open</v-icon>
                        <p class="source-text">{{ source.content }}</p>
                      </div>
                    </div>
                    
                    <v-card-actions class="source-actions">
                      <v-spacer></v-spacer>                      <v-btn v-if="source.type === 'video'" variant="flat" color="primary" size="small" 
                        prepend-icon="mdi-play-circle" 
                        @click="source.video_id && source.time_point && jumpToVideoTimepoint(source.video_id, source.time_point)"
                        class="jump-btn">
                        播放此段
                      </v-btn>
                      <v-btn v-else-if="source.type === 'document'" variant="flat" color="primary" size="small" 
                        prepend-icon="mdi-file-document-outline" 
                        @click="jumpToDocument(source)"
                        class="jump-btn">
                        查看文档
                      </v-btn>
                    </v-card-actions>
                  </v-card>
                </div>
              </v-expand-transition>
            </div>
            
            <!-- Agent工具执行历史 -->
            <div
              v-if="message.role === 'assistant' && message.content && index === currentChat.messages.length - 1 && toolExecutionHistory.length > 0"
              class="tools-history-container">
              <v-btn size="x-small" variant="text" density="compact" color="secondary" prepend-icon="mdi-tools"
                @click="toggleToolsHistoryVisibility(message)" class="tools-toggle mb-1">
                工具执行记录 ({{ toolExecutionHistory.length }})
                <v-icon end size="small">{{ message.showToolsHistory ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </v-btn>
              
              <v-expand-transition>
                <div v-if="message.showToolsHistory" class="tools-history-list">
                  <v-timeline density="compact" side="end" class="tools-timeline">
                    <v-timeline-item v-for="(historyItem, idx) in toolExecutionHistory" :key="historyItem.id"
                      :dot-color="historyItem.type === 'start' ? 'primary' : (historyItem.result?.success ? 'success' : 'error')"
                      size="x-small" class="mb-2">
                      <template v-slot:icon>
                        <v-icon 
                          :icon="historyItem.type === 'start' ? historyItem.tool.tool_icon : (historyItem.result?.success ? 'mdi-check' : 'mdi-alert')"
                          size="12" />
                      </template>
                      
                      <v-card variant="outlined" density="compact" class="tool-history-card">
                        <v-card-item class="pa-2">
                          <v-card-title class="text-caption">
                            <v-chip :color="historyItem.tool.tool_color || 'primary'" size="x-small" class="me-2">
                              {{ historyItem.tool.tool_name }}
                            </v-chip>
                            <span class="text-caption">
                              {{ historyItem.type === 'start' ? '开始执行' : '执行完成' }}
                            </span>
                          </v-card-title>
                          <v-card-subtitle class="text-caption text-medium-emphasis pt-1">
                            {{ formatTime(historyItem.timestamp) }}
                          </v-card-subtitle>
                        </v-card-item>
                        
                        <v-card-text v-if="historyItem.result" class="pa-2 pt-0">
                          <div class="text-caption">
                            <v-chip :color="historyItem.result.success ? 'success' : 'error'" size="x-small"
                              class="me-1">
                              {{ historyItem.result.success ? '成功' : '失败' }}
                            </v-chip>
                            {{ historyItem.result.message }}
                          </div>
                          
                          <div v-if="historyItem.result.documents_count" class="mt-1">
                            <v-chip size="x-small" color="blue-grey" variant="outlined">
                              <v-icon start size="x-small">mdi-file-document</v-icon>
                              {{ historyItem.result.documents_count }} 个文档
                            </v-chip>
                          </div>
                        </v-card-text>
                      </v-card>
                    </v-timeline-item>
                  </v-timeline>
                </div>
              </v-expand-transition>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="d-flex flex-column align-center justify-center h-100">
          <v-icon color="primary" size="48" class="mb-3">mdi-robot-outline</v-icon>
          <h3 class="text-subtitle-1 text-center mb-2">AI Agent助手</h3>
          <p class="text-caption text-medium-emphasis text-center mb-4">
            智能推理引擎，自动选择最合适的工具和策略来回答您的问题
          </p>
          
          <!-- 预设问题胶囊 -->
          <div class="preset-questions-container">
            <h4 class="preset-questions-title">💬 试试这些问题开始对话</h4>
            <div class="preset-questions-chips">
              <v-chip
                v-for="question in displayedQuestions"
                :key="question"
                class="preset-question-chip"
                color="primary"
                variant="outlined"
                size="small"
                @click="selectPresetQuestion(question)"
              >
                {{ question }}
              </v-chip>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="chat-input-container">
      <v-divider></v-divider>
      
      <!-- 合并的操作和模式选择区域 -->
      <div class="chat-controls-row">
        <div class="d-flex align-center justify-space-between w-100">
          <!-- 左侧：操作按钮 -->
          <div class="d-flex align-center">
            <v-btn prepend-icon="mdi-plus" color="success" @click="createNewChat" size="x-small" class="me-2">
              新对话
            </v-btn>
            <v-btn prepend-icon="mdi-history" color="primary" variant="outlined" @click="showHistoryDrawer = true"
              size="x-small">
              历史对话
            </v-btn>
          </div> <!-- 右侧：Agent模式状态显示 -->
          <div class="d-flex align-center">
              <v-icon size="small" class="me-2 text-primary">mdi-robot</v-icon>
            <span class="text-caption text-primary font-weight-medium">智能Agent</span>
            <v-btn icon size="x-small" variant="text" @click="showAgentSettings = true" class="ms-2">
              <v-icon size="small">mdi-cog</v-icon>
            </v-btn>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="ai-input-row">
        <div class="ai-input-actions">
          <v-btn icon :color="isRecording ? 'primary' : 'grey'" @click="toggleVoiceInput" class="ai-input-btn-small">
            <v-icon size="small">{{ isRecording ? 'mdi-microphone' : 'mdi-microphone-outline' }}</v-icon>
          </v-btn>
        </div> <v-textarea v-model="userInput" placeholder="请输入您的问题，AI Agent将智能选择最佳工具为您解答..." rows="2" auto-grow
          density="compact" hide-details variant="outlined" class="ai-input-textarea-large"
          @keydown.enter.prevent="sendMessage" :disabled="isTyping" ref="inputField"></v-textarea>
        <v-btn color="primary" icon @click="sendMessage" class="ai-input-send-btn"
          :disabled="!userInput.trim() || isTyping" size="small">
          <v-icon size="small">mdi-send</v-icon>
        </v-btn>
      </div>
    </div>
    
    <!-- 历史对话抽屉 -->
    <v-navigation-drawer v-model="showHistoryDrawer" location="left" temporary width="320">
      <v-toolbar color="primary" class="text-white">
        <v-toolbar-title>历史对话</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="showHistoryDrawer = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>
      
      <v-list>
        <v-list-item v-if="historyLoading" class="d-flex justify-center">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </v-list-item>
        
        <template v-else-if="chatHistoryList.length > 0">
          <v-list-item v-for="chat in chatHistoryList" :key="chat.id" @click="loadHistoryChat(chat)"
            :class="{ 'bg-primary-lighten-5': currentChat.id === chat.id }" class="mb-1">
            <template v-slot:prepend>
              <v-icon :color="chat.video_id ? 'blue' : 'green'">
                {{ chat.video_id ? 'mdi-video-outline' : 'mdi-chat-outline' }}
              </v-icon>
            </template>
            
            <v-list-item-title class="text-truncate">
              {{ chat.title }}
            </v-list-item-title>
            
            <v-list-item-subtitle class="text-caption">
              {{ formatDate(chat.updated_at) }} · {{ chat.message_count }}条消息
            </v-list-item-subtitle>
            
            <template v-slot:append>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props"></v-btn>
                </template>
                <v-list density="compact">
                  <v-list-item @click="editSessionTitle(chat)">
                    <template v-slot:prepend>
                      <v-icon size="small">mdi-pencil</v-icon>
                    </template>
                    <v-list-item-title>重命名</v-list-item-title>
                  </v-list-item>
                  <v-list-item @click="deleteHistoryChat(chat.id)">
                    <template v-slot:prepend>
                      <v-icon size="small" color="error">mdi-delete</v-icon>
                    </template>
                    <v-list-item-title class="text-error">删除</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </template>
          </v-list-item>
        </template>
        
        <v-list-item v-else>
          <v-list-item-title class="text-body-2 text-grey text-center">
            暂无历史对话
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>
    
    <!-- 重命名对话框 -->
    <v-dialog v-model="showEditDialog" max-width="400">
      <v-card>
        <v-card-title>重命名对话</v-card-title>
        <v-card-text>
          <v-text-field v-model="editTitle" label="对话标题" variant="outlined" hide-details
            density="compact"></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showEditDialog = false">取消</v-btn>
          <v-btn color="primary" @click="updateSessionTitle">保存</v-btn> </v-card-actions>
      </v-card>
    </v-dialog>
      <!-- Agent设置对话框 -->
    <v-dialog v-model="showAgentSettings" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="me-2">mdi-robot</v-icon>
          AI Agent配置
        </v-card-title>
        <v-card-text>
          <div class="mb-4">
            <h4 class="text-subtitle-1 mb-2">Agent模式说明</h4>
            <p class="text-body-2 text-grey-darken-1">
              Agent模式采用智能推理引擎，能够自动选择最合适的工具和策略来回答您的问题。
              系统已针对教育场景进行优化配置。
            </p>
          </div>
          
          <v-divider class="mb-4" />
            <div v-if="editableAgentConfig">
            <h4 class="text-subtitle-1 mb-3">配置信息</h4>
            <v-row>
              <v-col cols="12">
                <v-text-field v-model.number="editableAgentConfig.max_iterations" label="最大推理轮数" type="number" min="1"
                  max="20" density="compact" variant="outlined" hint="Agent执行任务时的最大推理轮数，建议设置为10" persistent-hint />
              </v-col>
            </v-row>
            
            <h4 class="text-subtitle-1 mt-4 mb-3">工具配置</h4>
            <v-row>
              <v-col cols="12" v-for="(config, toolName) in editableAgentConfig.tool_configs" :key="toolName">
                <v-card variant="outlined" density="compact">
                  <v-card-text class="pa-3">
                    <div class="d-flex align-center justify-space-between mb-2">
                      <span class="text-subtitle-2">{{ getToolDisplayName(String(toolName)) }}</span>
                      <v-switch v-model="config.enabled" color="primary" density="compact" hide-details />
                    </div>
                    <div v-if="config.enabled && config.top_k !== undefined">
                      <v-text-field v-model.number="config.top_k" label="检索数量 (top_k)" type="number" min="1" max="20"
                        density="compact" variant="outlined" hide-details hint="每次检索返回的相关内容数量" persistent-hint />
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
          <div v-else class="text-center py-4">
            <v-progress-circular indeterminate color="primary" />
            <p class="text-caption mt-2">加载配置中...</p>
          </div>
        </v-card-text> <v-card-actions>
          <v-btn color="grey" variant="text" @click="resetAgentConfigEdit">重置</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="showAgentSettings = false">取消</v-btn>
          <v-btn color="primary" variant="elevated" @click="saveAgentConfig">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAIChat } from '../composables/useAIChat'

// 属性定义
const props = defineProps<{
  videoId?: string
  courseId?: string
  documentId?: string
  autoPrompt?: string  // 添加自动对话的提示词prop
}>()

// 事件
const emit = defineEmits(['jump-to-timepoint', 'jump-to-video-timepoint', 'jump-to-document-segment', 'update:autoPrompt'])

// 使用主要的 composable
const {
  // 基础状态
  userInput,
  chatHistory,
  inputField,
  sessionId,
  isTyping,
  isRecording,
  
  // 聊天相关
  currentChat,
  createNewChat,
  sendMessage,
  
  // 消息处理
  getSortedSegments,
  processMessageContent,
  handleCitationClick,
  toggleSourcesVisibility,
  toggleToolsHistoryVisibility,
  formatTime,
  
  // 工具相关
  currentToolInfo,
  toolExecutionHistory,
  getToolStatusColor,
  getToolStatusIcon,
  getToolStatusText,
  formatContextInfo,
  
  // 状态相关
  currentStatus,
  statusStats,
  showStatus,
  
  // 历史记录
  chatHistoryList,
  historyLoading,
  showHistoryDrawer,
  showEditDialog,
  editTitle,
  editingChatId,
  loadHistoryChat,
  deleteHistoryChat,
  editSessionTitle,
  updateSessionTitle,
  formatDate,
  
  // 语音输入
  toggleVoiceInput,
  
  // Agent配置
  agentConfig,
  editableAgentConfig,
  showAgentSettings,
  saveAgentConfig,
  resetAgentConfigEdit,
  getToolDisplayName,
  
  // 跳转功能
  jumpToTimepoint,
  jumpToVideoTimepoint,
  jumpToDocument
} = useAIChat(props, emit)

// 预设问题数据

const presetQuestions = [
  '这节课说了什么？',
  '这节课在课程中的地位如何？',
  '能推荐一些相关的作业吗？',
  '为了学好这节课，我最好先学习哪些内容？'
]
const displayedQuestions = ref<string[]>([])

// 获取随机问题
const getRandomQuestions = () => {
  const shuffled = [...presetQuestions].sort(() => 0.5 - Math.random())
  return shuffled.slice(0, 3)
}

// 选择预设问题
const selectPresetQuestion = (question: string) => {
  userInput.value = question
  sendMessage()
}

// 初始化显示的问题
onMounted(() => {
  displayedQuestions.value = getRandomQuestions()
})

// 声明Window扩展类型
declare global {
  interface Window {
    webkitSpeechRecognition?: any;
    SpeechRecognition?: any;
  }
}
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  min-height: 300px; /* 设置最小高度 */
  position: relative;
}

/* 状态栏样式 */
.status-bar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  margin: 8px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-text {
  font-size: 14px;
  font-weight: 500;
}

.status-stats {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  opacity: 0.9;
}

.stats-item {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.chat-messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  padding-right: 4px;
  min-height: 0; /* 重要：允许弹性收缩 */
  height: 100%; /* 确保占满可用高度 */
}

/* 消息容器样式 */
.message-wrapper {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 用户消息样式 */
.user-message-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-left: 20%;
}

.user-message-bubble {
  background-color: rgb(var(--v-theme-primary));
  color: white;
  border-radius: 12px 12px 3px 12px;
  padding: 16px 20px;
  max-width: 100%;
  word-break: break-word;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* AI消息样式 */
.ai-message-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-right: 20%;
}

.ai-message-bubble {
  background-color: #f5f5f5;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 12px 12px 12px 3px;
  padding: 10px 16px 10px 36px;
  max-width: 100%;
  word-break: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 等待状态样式 */
.typing-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 2px;
  min-height: 32px;
}

/* AI思考中状态显示 */
.ai-thinking-status {
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 8px 12px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.status-stats-inline {
  display: flex;
  flex-wrap: wrap;
  margin-top: 4px;
  gap: 4px;
}

.default-thinking {
  display: flex;
  align-items: center;
  gap: 8px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 3px;
}

.typing-dot {
  width: 6px;
  height: 6px;
  background-color: #666;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {

  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

.typing-text {
  color: #666;
  font-size: 12px;
  font-style: italic;
}

/* 引用来源样式 */
.sources-container {
  margin-top: 12px;
  margin-left: 26px;
  max-width: calc(100% - 26px);
}

.sources-toggle {
  border-radius: 20px;
  text-transform: none;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.sources-toggle:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.sources-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 4px 0;
}

.source-card {
  border-radius: 12px;
  border: 1px solid #e3f2fd;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.source-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #2196f3 0%, #1976d2 100%);
}

.source-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(33,150,243,0.15);
  border-color: #bbdefb;
}

.source-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 16px 8px 20px;
}

.source-index {
  flex-shrink: 0;
  font-weight: 600;
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(33,150,243,0.3);
}

.source-meta {
  flex: 1;
  min-width: 0;
}

.source-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a237e;
  margin: 0 0 4px 0;
  line-height: 1.3;
  word-break: break-word;
}

.source-time {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.source-content-wrapper {
  padding: 0 16px 8px 20px;
}

.source-content {
  position: relative;
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px 12px 40px;
  border: 1px solid #e8eaf6;
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
}

.quote-icon {
  position: absolute;
  top: 8px;
  left: 12px;
  font-size: 16px;
}

.source-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #424242;
  white-space: pre-wrap;
  word-break: break-word;
  font-style: italic;
}

.source-actions {
  padding: 8px 16px 12px 20px;
}

.jump-btn {
  border-radius: 20px;
  text-transform: none;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(25,118,210,0.2);
  transition: all 0.3s ease;
}

.jump-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(25,118,210,0.3);
}

/* 引用标记样式 */
:deep(.citation-ref) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.75em;
  vertical-align: super;
  color: #3498db;
  font-weight: 500;
  margin: 0 1px;
  transition: all 0.2s;
  text-decoration: none;
  padding: 0 2px;
  border-radius: 3px;
}

:deep(.citation-ref:hover) {
  background-color: rgba(52, 152, 219, 0.1);
  color: #2980b9;
  text-decoration: underline;
}

/* 空状态 */
.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 输入区域样式 */
.chat-input-container {
  margin-top: auto;
  background-color: white;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.chat-controls-row {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background-color: rgba(0, 0, 0, 0.01);
}

.ai-input-row {
  display: flex;
  align-items: flex-end;
  padding: 8px 12px;
  gap: 8px;
  background: #fff;
}

.ai-input-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}

.ai-input-btn-small {
  width: 28px;
  height: 28px;
  min-width: 28px;
  min-height: 28px;
  border-radius: 4px;
  margin: 0;
  padding: 0;
}

.ai-input-textarea-large {
  flex: 1;
  min-height: 36px;
  font-size: 14px;
  margin: 0 6px;
}

.ai-input-send-btn {
  width: 32px;
   height: 32px;
  min-width: 32px;
  min-height: 32px;
  border-radius: 6px;
  margin-left: 0;
  margin-bottom: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-selector {
  min-width: 120px;
  max-width: 160px;
}

/* 消息列表滚动条样式 */
.chat-messages-container::-webkit-scrollbar {
  width: 4px;
}

.chat-messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages-container::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.15);
  border-radius: 2px;
}

.chat-messages-container::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.25);
}

/* 预设问题胶囊样式 */
.preset-questions-container {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 16px;
  margin: 16px 0;
  max-width: 600px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(25, 118, 210, 0.1);
  text-align: left;
}

.preset-questions-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #1976d2, #42a5f5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
  text-align: left;
  letter-spacing: 0.5px;
}

.preset-questions-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-start;
}

.preset-question-chip {
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 14px;
  font-weight: 500;
  border-radius: 20px !important;
  padding: 8px 16px !important;
  height: auto !important;
  min-height: 36px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.preset-question-chip:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 16px rgba(25, 118, 210, 0.25);
  background: linear-gradient(135deg, #1976d2, #42a5f5) !important;
  color: white !important;
  border-color: transparent !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-controls-row {
    padding: 6px 8px;
  }
  
  .chat-controls-row .d-flex:first-child {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .mode-selector {
    min-width: 100px;
    max-width: 140px;
  }
  
  .ai-input-row {
    padding: 6px 8px;
  }
  
  .preset-questions-container {
    margin: 12px 0;
    padding: 16px;
    max-width: 100%;
  }
  
  .preset-questions-title {
    font-size: 16px;
    margin-bottom: 12px;
  }
  
  .preset-questions-chips {
    gap: 8px;
  }
  
  .preset-question-chip {
    font-size: 13px !important;
    padding: 6px 12px !important;
    min-height: 32px;
  }
}

@media (max-width: 480px) {
  .chat-controls-row .d-flex:first-child {
    flex-direction: column;
    align-items: stretch;
  }
  
  .chat-controls-row .d-flex:first-child>div {
    justify-content: center;
    margin-bottom: 4px;
  }

    .mode-selector {
    min-width: 80px;
    max-width: 120px;
  }
}

/* 消息片段样式 */
.message-segments {
  margin-bottom: 8px;
}

.tool-call-segment {
  background: rgba(var(--v-theme-primary), 0.08);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  animation: segmentSlideIn 0.3s ease-out;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.1);
}

.tool-result-segment {
  background: rgba(var(--v-theme-surface), 0.8);
  border-left: 3px solid;
  border-radius: 6px;
  padding: 10px 12px;
  margin: 6px 0 12px 20px;
  animation: segmentSlideIn 0.3s ease-out;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.tool-result-segment {
  border-left-color: var(--v-theme-success);
}

.tool-result-segment.error {
  border-left-color: var(--v-theme-error);
  background: rgba(var(--v-theme-error), 0.08);
  box-shadow: 0 1px 4px rgba(var(--v-theme-error), 0.1);
}

.ai-message-content {
  margin-top: 8px;
  animation: contentFadeIn 0.5s ease-out;
}

@keyframes segmentSlideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
    max-height: 0;
  }

  to {
    opacity: 1;
    transform: translateX(0);
    max-height: 200px;
  }
}

@keyframes contentFadeIn {
  from {
    opacity: 0;
    transform: translateY(5px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tool-call-header {
  position: relative;
}

.tool-context-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tool-result-content {
  font-size: 13px;
}

/* 活跃工具调用的脉冲效果增强 */
.tool-call-segment:not(.complete) {
  position: relative;
  overflow: hidden;
  background: rgba(var(--v-theme-primary), 0.1);
  border-color: rgba(var(--v-theme-primary), 0.25);
}

.tool-call-segment:not(.complete)::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(var(--v-theme-primary), 0.15), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }

  100% {
    left: 100%;
  }
}

/* 美化进度条 */
.v-progress-linear {
  border-radius: 1px;
}

/* 工具调用扁平化样式 */
.tool-success-banner {
  background: rgba(var(--v-theme-success), 0.12);
  border: 1px solid rgba(var(--v-theme-success), 0.15);
  border-radius: 28px;
  margin: 2px 0;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(var(--v-theme-success), 0.1);
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }

  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}

.hide-tool-segment {
  animation: fadeOut 0.5s forwards;
}

.tool-success-banner:hover {
  background: rgba(var(--v-theme-success), 0.18);
  cursor: pointer;
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(var(--v-theme-success), 0.15);
}

.tool-call-compact {
  margin: 4px 0 6px;
}

.tool-call-detailed {
  background: rgba(var(--v-theme-surface-variant), 0.7);
  border: 1px solid rgba(var(--v-theme-outline), 0.15);
  border-radius: 12px;
  padding: 12px 14px;
  margin: 4px 0 10px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.expand-btn {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.expand-btn:hover {
  opacity: 1;
}

/* 工具结果简洁样式 */
.tool-result-success .success-info {
  margin: 4px 0;
}

.tool-result-error {
  background: rgba(var(--v-theme-error), 0.08);
  border: 1px solid rgba(var(--v-theme-error), 0.25);
  border-radius: 6px;
  padding: 8px;
  box-shadow: 0 1px 4px rgba(var(--v-theme-error), 0.1);
}

/* 工具结果成功/失败状态 */
.tool-result-segment .v-icon {
  margin-right: 6px;
}

/* 工具执行状态样式（保留原有逻辑） */
.tool-execution-status {
  background: rgba(var(--v-theme-surface-bright), 0.08);
  border: 1px solid rgba(var(--v-theme-outline), 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  animation: slideIn 0.3s ease-out;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.ai-thinking-status {
  padding: 8px 12px;
  background: rgba(var(--v-theme-primary), 0.08);
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-primary));
  box-shadow: 0 1px 4px rgba(var(--v-theme-primary), 0.1);
}

/* 成功状态样式 */
.tool-execution-status.success {
  border-color: rgba(var(--v-theme-success), 0.4);
  background: rgba(var(--v-theme-success), 0.08);
  box-shadow: 0 2px 6px rgba(var(--v-theme-success), 0.1);
}

/* 错误状态样式 */
.tool-execution-status.error {
  border-color: rgba(var(--v-theme-error), 0.4);
  background: rgba(var(--v-theme-error), 0.08);
  box-shadow: 0 2px 6px rgba(var(--v-theme-error), 0.1);
}

/* 模式帮助提示样式 */
.mode-help-tooltip {
  max-width: 300px;
  font-size: 12px;
  line-height: 1.4;
  padding: 8px;
}

/* 内容片段样式 */
.content-segment {
  padding: 4px 0;
  margin: 8px 0;
  animation: contentFadeIn 0.4s ease-out;
}

.content-segment .markdown-body {
  font-size: 15px;
  line-height: 1.6;
}

/* ReAct推理过程样式（developer模式） */
.react-thinking {
  background: rgba(var(--v-theme-info), 0.08);
  border: 1px solid rgba(var(--v-theme-info), 0.2);
  border-left: 3px solid rgb(var(--v-theme-info));
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  box-shadow: 0 1px 4px rgba(var(--v-theme-info), 0.1);
}

/* 美化工具调用卡片 */
.tool-call-segment {
  border-left: 4px solid;
  border-left-color: var(--tool-color, rgb(var(--v-theme-primary)));
  transition: all 0.3s ease;
}

.tool-call-segment:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 工具结果的成功/失败状态颜色 */
.tool-result-segment.success {
  border-left-color: rgb(var(--v-theme-success));
  background: rgba(var(--v-theme-success), 0.08);
  box-shadow: 0 1px 4px rgba(var(--v-theme-success), 0.1);
}

.tool-result-segment.error {
  border-left-color: rgb(var(--v-theme-error));
  background: rgba(var(--v-theme-error), 0.08);
  box-shadow: 0 1px 4px rgba(var(--v-theme-error), 0.1);
}

/* 响应式优化 */
@media (max-width: 600px) {
  .mode-help-tooltip {
    max-width: 250px;
    font-size: 11px;
  }
  
  .content-segment {
    padding: 8px;
    margin: 4px 0;
  }
  
  .tool-call-segment {
    padding: 8px;
  }
}
</style>