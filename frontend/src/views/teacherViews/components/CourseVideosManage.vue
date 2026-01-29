<template>
  <v-container fluid class="pa-4 teacher-container">
    <v-card class="content-card">
      <!-- 视频管理卡片 -->
      <v-card-title class="d-flex align-center py-4 px-6">
        课程视频管理
        <v-tooltip location="top">
          <template v-slot:activator="{ props }">
            <v-btn icon variant="text" v-bind="props" class="ms-2">
              <v-icon>mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>管理课程关联的视频，可以重命名、删除或添加视频</span>
        </v-tooltip>
        <v-spacer></v-spacer>
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="搜索视频..."
          single-line
          hide-details
          density="compact"
          class="search-field me-4"
          clear-icon="mdi-close-circle"
          clearable
          @update:model-value="filterVideos"
        ></v-text-field>
        <v-btn
          color="primary"
          prepend-icon="mdi-upload"
          @click="navigateToUpload"
          class="me-2"
        >
          上传视频
        </v-btn>
        <v-btn
          color="success"
          prepend-icon="mdi-graph-outline"
          @click="generateKnowledgeGraph"
          class="me-2"
          :loading="knowledgeGraphLoading"
        >
          生成知识图谱
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openNewChapterDialog"
          class="me-2"
        >
          新建章节
        </v-btn>
        <v-menu v-if="selectedVideos.length > 0">
          <template v-slot:activator="{ props }">
            <v-btn
              color="secondary"
              prepend-icon="mdi-dots-vertical"
              v-bind="props"
            >
              批量操作 ({{ selectedVideos.length }})
            </v-btn>
          </template>
          <v-list>
            <v-list-item @click="confirmBatchProcess">
              <template v-slot:prepend>
                <v-icon>mdi-cog</v-icon>
              </template>
              <v-list-item-title>批量处理</v-list-item-title>
            </v-list-item>
            <v-list-item @click="confirmBatchDelete">
              <template v-slot:prepend>
                <v-icon>mdi-link-off</v-icon>
              </template>
              <v-list-item-title>批量解除关联</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </v-card-title>
      <v-divider></v-divider>
      
      <v-card-text class="pa-4 scrollable-content">
        <!-- 加载状态 -->
        <div v-if="loading" class="d-flex justify-center align-center pa-8">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
          <span class="ms-4">加载视频数据中...</span>
        </div>
        
        <!-- 视频列表 -->
        <div v-else>
          <!-- 视频总数和全选 -->
          <div class="d-flex align-center mb-4">
            <div class="text-body-1 flex-grow-1">
              共找到 <b>{{ filteredVideos.length }}</b> 个视频
            </div>
            <v-checkbox
              v-if="filteredVideos.length > 0"
              v-model="selectAll"
              label="全选"
              hide-details
              density="compact"
              @change="handleSelectAll"
            ></v-checkbox>
          </div>
          
          <!-- 视频列表 - 网格布局 -->
          <v-row v-if="filteredVideos.length > 0">
            <v-col cols="12">
              <!-- 插入模式提示 -->
              <v-alert
                v-if="isInsertingChapter"
                type="info"
                variant="tonal"
                closable
                class="mb-4"
                @click:close="cancelInsertChapter"
              >
                点击视频之间的位置来插入章节"{{ insertPosition?.title }}"
              </v-alert>

              <v-list>
                <!-- 顶部插入点 -->
                <div
                  v-if="isInsertingChapter"
                  class="insert-point pa-2 text-center"
                  @click="handleChapterInsert(0)"
                >
                  <v-icon color="primary">mdi-plus-circle</v-icon>
                  <span class="text-primary ms-2">在此处插入章节</span>
                </div>

                <template v-for="(item, index) in filteredVideos" :key="item.id || index">
                  <!-- 章节标题 -->
                  <v-list-subheader
                    v-if="item.isChapter"
                    class="d-flex align-center py-3 bg-grey-lighten-4"
                  >
                    <div class="text-h6">第{{ item.chapterNumber }}章：{{ item.title }}</div>
                  </v-list-subheader>

                  <!-- 视频项 -->
                  <template v-else>
                    <v-list-item
                      :value="item.id"
                      class="mb-2"
                      rounded="lg"
                    >
                      <template v-slot:prepend>
                        <v-checkbox
                          v-model="selectedVideos"
                          :value="item.id"
                          hide-details
                          density="compact"
                        ></v-checkbox>
                      </template>

                      <v-list-item-title class="text-h6">
                        {{ item.title }}
                      </v-list-item-title>

                      <v-list-item-subtitle>
                        时长：{{ formatDuration(item.duration) }} | 上传时间：{{ formatDate(item.uploadTime) }}
                      </v-list-item-subtitle>

                      <template v-slot:append>
                        <v-btn
                          variant="text"
                          color="info"
                          @click="showVideoDetails(item)"
                          class="me-2"
                        >
                          <v-icon>mdi-information</v-icon>
                          详情
                        </v-btn>
                        <v-btn
                          variant="text"
                          color="primary"
                          @click="showRenameDialog(item)"
                          class="me-2"
                        >
                          <v-icon>mdi-pencil</v-icon>
                          重命名
                        </v-btn>
                        <v-btn
                          variant="text"
                          color="warning"
                          @click="processVideo(item)"
                          class="me-2"
                        >
                          <v-icon>mdi-cog</v-icon>
                          处理视频
                        </v-btn>

                        <v-btn
                          variant="text"
                          color="error"
                          @click="confirmDeleteVideo(item)"
                        >
                          <v-icon>mdi-delete</v-icon>
                          删除
                        </v-btn>
                      </template>
                    </v-list-item>

                    <!-- 插入点 -->
                    <div
                      v-if="isInsertingChapter"
                      class="insert-point pa-2 text-center"
                      @click="handleChapterInsert(index + 1)"
                    >
                      <v-icon color="primary">mdi-plus-circle</v-icon>
                      <span class="text-primary ms-2">在此处插入章节</span>
                    </div>
                  </template>
                </template>
              </v-list>
            </v-col>
          </v-row>
          
          <!-- 空状态 -->
          <v-row v-else class="fill-height align-center justify-center">
            <v-col cols="12" class="text-center pa-12">
              <v-icon size="64" color="grey">mdi-video-off</v-icon>
              <div class="text-h6 mt-4 text-grey">暂无视频</div>
              <div class="text-body-1 mt-2 text-grey">
                您可以点击"上传视频"按钮为本课程添加视频
              </div>
              <v-btn
                color="primary"
                class="mt-4"
                @click="navigateToUpload"
              >
                上传视频
              </v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
      
    </v-card>
    <!-- 章节管理卡片 -->
    <v-card class="content-card mt-4">
      <v-card-title class="d-flex align-center py-4 px-6">
        资料管理
        <v-tooltip location="top">
          <template v-slot:activator="{ props }">
            <v-btn icon variant="text" v-bind="props" class="ms-2">
              <v-icon>mdi-information-outline</v-icon>
            </v-btn>
          </template>
          <span>管理课程相关资料</span>
        </v-tooltip>
        <v-spacer></v-spacer>
      </v-card-title>
      <v-divider></v-divider>
      
      <v-card-text class="pa-4 scrollable-content">
        <!-- 章节列表 -->
        <div v-if="!chapters.length" class="text-center pa-4">
          暂无章节，请添加章节
        </div>
        <v-expansion-panels v-else multiple>
          <v-expansion-panel
            v-for="chapter in chapters"
            :key="chapter.id"
            :value="chapter.id"
          >
            <v-expansion-panel-title>
              <div class="d-flex align-center">
                <span class="text-h6">第{{ chapter.chapterNumber }}章：{{ chapter.title }}</span>
              </div>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <!-- 拖放区域 -->
              <div
                class="drop-zone pa-4"
                :class="{ 'drag-over': isDragging }"
                @dragenter.prevent="handleDragEnter"
                @dragleave.prevent="handleDragLeave"
                @dragover.prevent
                @drop.prevent="(e) => handleFileDrop(e, chapter.id)"
              >
                <div v-if="!chapter.documents?.length" class="text-center">
                  <v-icon size="48" color="grey">mdi-file-upload-outline</v-icon>
                  <div class="text-body-1 mt-2">暂无材料，拖拽文件到此处上传</div>
                </div>
                <v-row v-else>
                  <v-col v-for="doc in chapter.documents" :key="doc.id" cols="12" sm="6" md="4">
                    <v-card variant="outlined">
                      <v-card-title class="text-truncate">
                        {{ doc.title }}
                      </v-card-title>
                      <v-card-text>
                        <div class="text-caption">{{ formatFileSize(doc.fileSize) }}</div>
                        <div class="text-caption">{{ formatDate(doc.uploadTime) }}</div>
                      </v-card-text>
                      <v-card-actions>
                        <v-btn
                          variant="text"
                          color="primary"
                          :href="doc.fileUrl"
                          target="_blank"
                        >
                          下载
                        </v-btn>
                        <v-btn
                          variant="text"
                          color="error"
                          @click="handleDocumentDelete(chapter.id, doc.id)"
                        >
                          删除
                        </v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
    
    <!-- 重命名对话框 -->
    <v-dialog v-model="showRenameModal" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          重命名视频
          <v-spacer></v-spacer>
          <v-btn icon @click="closeRenameDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <v-form ref="renameForm">
            <v-text-field
              v-model="videoEdit.title"
              label="视频标题"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              required
            ></v-text-field>
            <v-textarea
              v-model="videoEdit.description"
              label="视频描述"
              variant="outlined"
              density="comfortable"
              rows="4"
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeRenameDialog">取消</v-btn>
          <v-btn color="primary" @click="saveVideoInfo">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
      <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteModal" max-width="400">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          解除视频关联
          <v-spacer></v-spacer>
          <v-btn icon @click="closeDeleteDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="warning"
            size="64"
            class="mb-4"
          >
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要解除视频 <strong>{{ videoToDelete?.title }}</strong> 与该课程的关联吗？
          </div>
          <div class="text-caption text-warning mt-2">
            注意：如果该视频不再与任何课程关联，系统将会删除视频文件。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeDeleteDialog">取消</v-btn>
          <v-btn color="error" @click="deleteVideo">解除关联</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 批量删除确认对话框 -->
    <v-dialog v-model="showBatchDeleteModal" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          批量解除视频关联
          <v-spacer></v-spacer>
          <v-btn icon @click="closeBatchDeleteDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="warning"
            size="64"
            class="mb-4"
          >
            mdi-alert-circle
          </v-icon>
          <div class="text-body-1">
            您确定要批量解除 <strong>{{ selectedVideos.length }}</strong> 个视频与该课程的关联吗？
          </div>
          <div class="text-caption text-warning mt-2">
            注意：如果这些视频不再与任何课程关联，系统将会删除相应视频文件。
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeBatchDeleteDialog">取消</v-btn>
          <v-btn color="error" @click="batchDeleteVideos" :loading="batchProcessing">批量解除关联</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 批量处理确认对话框 -->
    <v-dialog v-model="showBatchProcessModal" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          批量处理视频
          <v-spacer></v-spacer>
          <v-btn icon @click="closeBatchProcessDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4 text-center">
          <v-icon
            color="info"
            size="64"
            class="mb-4"
          >
            mdi-cog
          </v-icon>          <div class="text-body-1">
            您确定要批量处理 <strong>{{ selectedVideos.length }}</strong> 个视频吗？
            <span v-if="searchQuery" class="text-caption d-block mt-1">
              (当前搜索筛选：{{ filteredVideos.filter(v => selectedVideos.includes(v.id)).length }} 个视频)
            </span>
          </div>
          <div class="text-caption mt-2">
            处理包括：提取关键帧、OCR文字识别、语音识别等步骤，可能需要一些时间。
          </div>          <v-alert
            v-if="selectedVideos.length > 10"
            type="warning"
            variant="tonal"
            class="mt-3"
            density="compact"
          >
            您选择了较多视频进行处理，处理过程可能需要一些时间，请耐心等待。
          </v-alert>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeBatchProcessDialog">取消</v-btn>
          <v-btn color="primary" @click="batchProcessVideos" :loading="batchProcessing">
            开始处理
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
      <!-- 批量处理进度对话框 -->
    <v-dialog v-model="showBatchProgressModal" persistent max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          批量处理进度
        </v-card-title>
        <v-card-text class="pa-4">
          <div class="text-body-1 mb-2">
            已处理：{{ processedCount }}/{{ selectedVideos.length }} 个视频
          </div>
          <v-progress-linear
            v-model="batchProgress"
            height="20"
            color="primary"
            striped
          >
            <template v-slot:default>
              {{ Math.round(batchProgress) }}%
            </template>
          </v-progress-linear>
          
          <div class="mt-4">
            <div v-for="(status, index) in processingStatus" :key="index" class="d-flex align-center mb-1">
              <v-icon :color="status.color" size="small" class="me-2">{{ status.icon }}</v-icon>
              <span :class="{'text-caption': true, [status.textClass]: true}">{{ status.message }}</span>
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="closeBatchProgressDialog" :disabled="batchProcessing">
            {{ batchProcessing ? '处理中...' : '完成' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 强制重新生成知识图谱确认对话框 -->
    <v-dialog v-model="showForceRegenerateDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          知识图谱生成冲突
          <v-spacer></v-spacer>
          <v-btn icon @click="closeForceRegenerateDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-4">
          <v-icon color="warning" size="64" class="mb-4 d-block mx-auto"></v-icon>
          <div class="text-center">
            <div class="text-body-1 mb-3">
              该课程已有知识图谱生成任务正在进行中
            </div>            <div v-if="pendingKnowledgeGraphTask" class="text-caption text-medium-emphasis mb-3">
              任务状态：{{ pendingKnowledgeGraphTask.status }}<br>
              开始时间：{{ formatDateTime(pendingKnowledgeGraphTask.start_time) }}<br>
              进度：{{ Math.round((pendingKnowledgeGraphTask.progress || 0) * 100) }}%
            </div>
            <div class="text-body-2">
              您可以选择等待当前任务完成，或强制重新生成（这将终止当前任务并删除已有的知识图谱数据）。
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeForceRegenerateDialog">
            等待完成
          </v-btn>          <v-btn color="warning" @click="forceRegenerateKnowledgeGraph" :loading="knowledgeGraphLoading">
            强制重新生成
          </v-btn>
        </v-card-actions>
      </v-card>    </v-dialog>    <!-- 视频处理设置对话框 -->
    <v-dialog v-model="showProcessSettingsModal" max-width="800">
      <v-card>
        <v-card-title class="text-h5 pa-4">
          视频处理设置
          <v-spacer></v-spacer>
          <v-btn icon @click="closeProcessSettingsDialog">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-4">
          <!-- 加载状态 -->
          <div v-if="loadingProcessingStatus" class="text-center py-4">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <div class="mt-2">正在获取视频处理状态...</div>
          </div>

          <!-- 视频处理表单 -->
          <div v-else>
            <!-- 批量操作工具栏 -->
            <div v-if="processFormData.videos.length > 1" class="mb-4">
              <v-card variant="outlined" class="pa-3">
                <v-card-subtitle class="pa-0 mb-2">批量操作</v-card-subtitle>
                <div class="d-flex flex-wrap gap-2">
                  <v-btn size="small" variant="outlined" @click="setBatchAllSteps(true)">
                    全选所有步骤
                  </v-btn>
                  <v-btn size="small" variant="outlined" @click="setBatchAllSteps(false)">
                    取消所有步骤
                  </v-btn>
                  <v-divider vertical class="mx-2"></v-divider>
                  <v-btn 
                    v-for="step in processingSteps" 
                    :key="'batch-' + step.value"
                    size="small" 
                    variant="outlined" 
                    @click="setBatchStep(step.value, true)"
                  >
                    批量启用{{ step.label }}
                  </v-btn>
                </div>
              </v-card>
            </div>

            <!-- 预览模式开关 -->
            <div class="mb-4">
              <v-switch
                v-model="processFormData.previewMode"
                color="primary"
                label="预览模式"
                hint="预览模式下将执行所有处理步骤但不保存到数据库，仅生成处理日志"
                persistent-hint
              ></v-switch>
            </div>

            <!-- 视频列表 -->
            <div class="mb-4">
              <v-card-subtitle class="pa-0 mb-2">
                视频列表 ({{ processFormData.videos.length }} 个视频)
              </v-card-subtitle>
              
              <div v-for="(video, index) in processFormData.videos" :key="video.id" class="mb-3">
                <v-card variant="outlined">
                  <v-card-title class="pa-3 text-subtitle-1">
                    {{ video.title }}
                    <v-spacer></v-spacer>
                    <v-chip 
                      size="small" 
                      :color="getSelectedStepsCount(video) > 0 ? 'primary' : 'default'"
                    >
                      已选择: {{ getSelectedStepsCount(video) }}
                    </v-chip>
                  </v-card-title>
                  
                  <!-- 当前处理状态 -->
                  <v-card-text class="pa-3 pt-0">
                    <div class="mb-2 text-caption text-medium-emphasis">当前处理状态:</div>
                    <div class="d-flex flex-wrap gap-2 mb-3">
                      <v-chip 
                        v-for="(status, stepName) in video.status" 
                        :key="stepName"
                        size="small"
                        :color="status ? 'success' : 'default'"
                        :variant="status ? 'flat' : 'outlined'"
                      >
                        <v-icon 
                          :icon="status ? 'mdi-check-circle' : 'mdi-circle-outline'" 
                          size="small" 
                          class="mr-1"
                        ></v-icon>
                        {{ getStepDisplayName(stepName) }}
                      </v-chip>
                    </div>
                    
                    <!-- 步骤选择 -->
                    <div class="mb-2 text-caption text-medium-emphasis">选择要处理的步骤:</div>
                    <div class="d-flex flex-wrap gap-2">
                      <v-checkbox
                        v-for="step in processingSteps"
                        :key="step.value"
                        v-model="video.steps[step.value]"
                        :label="step.label"
                        :disabled="processFormData.previewMode"
                        density="compact"
                        hide-details
                        class="flex-0-0"
                      >
                        <template v-slot:label>
                          <div class="d-flex align-center">
                            <v-icon :icon="step.icon" size="small" class="mr-1"></v-icon>
                            <span class="text-caption">{{ step.label }}</span>
                          </div>
                        </template>
                      </v-checkbox>
                    </div>
                    
                    <!-- 重置按钮 -->
                    <div class="mt-2">
                      <v-btn 
                        size="small" 
                        variant="text" 
                        @click="resetVideoSteps(index)"
                        append-icon="mdi-refresh"
                      >
                        重置为默认
                      </v-btn>
                    </div>
                  </v-card-text>
                </v-card>
              </div>
            </div>

            <!-- 处理提示 -->
            <div class="text-caption text-medium-emphasis">
              <div v-if="!processFormData.previewMode">
                * 未选择步骤将跳过处理。已处理的步骤可以重新执行以更新数据。
              </div>
              <div v-else>
                * 预览模式下将执行所有步骤，但不保存到数据库
              </div>
            </div>
          </div>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="closeProcessSettingsDialog">取消</v-btn>
          <v-btn 
            color="primary" 
            @click="submitProcessSettings"
            :disabled="!processFormData.previewMode && !hasAnySelectedSteps"
            :loading="loadingProcessingStatus"
          >
            {{ processFormData.previewMode ? '开始预览' : '开始处理' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 新建章节对话框 -->
    <v-dialog v-model="newChapterDialog" max-width="500px" persistent>
      <v-card>
        <v-card-title>新建章节</v-card-title>
        <v-card-text>
          <v-form ref="chapterForm" v-model="chapterFormValid">
            <v-text-field
              v-model="newChapter.chapterNumber"
              label="章节序号"
              type="number"
              :rules="[v => !!v || '请输入章节序号']"
              required
              hide-details="auto"
              class="mb-4"
            ></v-text-field>
            <v-text-field
              v-model="newChapter.title"
              label="章节标题"
              :rules="[v => !!v || '请输入章节标题']"
              required
              hide-details="auto"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            variant="text"
            @click="closeNewChapterDialog"
            :disabled="loading"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="createChapter"
            :loading="loading"
            :disabled="!chapterFormValid"
          >
            确定
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 添加 Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.text }}
      
      <template v-slot:actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>

  </v-container>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { chapterService } from '../../../api/chapterService';
import videoService from '../../../api/videoService';
import knowledgeMapService from '../../../api/knowledgeMapService';
import uploadService from '../../../api/uploadService';

// 获取路由和参数
const router = useRouter();
const route = useRoute();
const courseId = ref(route.params.id || null); // 从路由参数获取课程ID

// 状态管理
const loading = ref(false);
const videos = ref([]);
const filteredVideos = ref([]);
const searchQuery = ref('');
const selectAll = ref(false);

// 视频编辑相关
const showRenameModal = ref(false);
const videoEdit = reactive({
  id: null,
  title: '',
  description: ''
});

// 视频删除相关
const showDeleteModal = ref(false);
const videoToDelete = ref(null);

// 视频处理相关
const processingVideoId = ref(null);
const checkingStatus = ref(false);

// 批量选择相关
const selectedVideos = ref([]);
const showBatchDeleteModal = ref(false);
const showBatchProcessModal = ref(false);
const showBatchProgressModal = ref(false);
const batchProcessing = ref(false);
const batchProgress = ref(0);
const processedCount = ref(0);
const processingStatus = ref([]);

// 视频处理设置相关
const showProcessSettingsModal = ref(false);
const loadingProcessingStatus = ref(false);

// 处理步骤选项
const processingSteps = ref([
  {
    value: 'keyframes',
    label: '关键帧提取',
    icon: 'mdi-image-multiple',
    description: '提取视频关键帧用于封面和缩略图生成'
  },
  {
    value: 'ocr',
    label: 'OCR文字识别',
    icon: 'mdi-text-recognition',
    description: '识别视频中的文字内容，生成文本索引'
  },
  {
    value: 'asr',
    label: 'ASR语音识别',
    icon: 'mdi-microphone',
    description: '将视频中的语音转换为文字，生成字幕'
  },
  {
    value: 'vector',
    label: '向量化处理',
    icon: 'mdi-vector-triangle',
    description: '将文本内容向量化，用于语义搜索和问答'
  },
  {
    value: 'summary',
    label: '智能摘要',
    icon: 'mdi-text-box-outline',
    description: '生成视频内容的智能摘要和知识点'
  }
]);

// 处理表单数据
const processFormData = ref({
  videos: [], // 视频列表，每个视频包含 { id, title, steps: { keyframes: true, ocr: false, ... }, status: { keyframes: true, ocr: false, ... } }
  previewMode: false
});

// 知识图谱相关
const knowledgeGraphLoading = ref(false);
const showForceRegenerateDialog = ref(false);
const pendingKnowledgeGraphTask = ref(null);
// 移除最大并发处理任务数限制
const processingInterval = ref(null); // 轮询间隔ID

// 章节相关状态
const chapters = ref([]);
const newChapterDialog = ref(false);
const chapterFormValid = ref(false);
const newChapter = ref({
  chapterNumber: '',
  title: ''
});

// 视频选择状态处理
const isVideoSelected = (videoId) => {
  return selectedVideos.value.includes(videoId);
};

// 切换视频选择状态
const toggleVideoSelection = (videoId) => {
  const index = selectedVideos.value.indexOf(videoId);
  if (index === -1) {
    selectedVideos.value.push(videoId);
  } else {
    selectedVideos.value.splice(index, 1);
  }
};

// 全选/取消全选
const handleSelectAll = () => {
  if (selectAll.value) {
    // 全选当前筛选结果中的所有视频
    const filteredIds = filteredVideos.value.map(video => video.id);
    
    // 合并现有选择和筛选结果中的ID（去重）
    const existingSelectedIds = selectedVideos.value.filter(id => 
      !filteredVideos.value.some(video => video.id === id)
    );
    
    selectedVideos.value = [...existingSelectedIds, ...filteredIds];
  } else {
    // 仅从选择中移除当前筛选结果的视频
    if (searchQuery.value) {
      const filteredIds = filteredVideos.value.map(video => video.id);
      selectedVideos.value = selectedVideos.value.filter(id => !filteredIds.includes(id));
    } else {
      // 没有筛选时，取消所有选择
      selectedVideos.value = [];
    }
  }
};

// 监听选中视频变化，更新全选状态
watch(selectedVideos, (newVal) => {
  // 如果当前筛选结果中的所有视频都被选中，则全选为true，否则为false
  selectAll.value = filteredVideos.value.length > 0 && 
                    filteredVideos.value.every(video => selectedVideos.value.includes(video.id));
}, { deep: true });

// 监听筛选结果变化，可能需要重新计算全选状态
watch(filteredVideos, () => {
  // 如果当前筛选结果中的所有视频都被选中，则全选为true，否则为false
  selectAll.value = filteredVideos.value.length > 0 && 
                    filteredVideos.value.every(video => selectedVideos.value.includes(video.id));
}, { deep: true });

// 方法
// 获取视频列表
const fetchVideos = async () => {
  loading.value = true;
  
  try {
    const response = await videoService.getVideos({
      courseId: courseId.value,
      page: 1,
      pageSize: 100 // 设置一个较大的值，获取所有视频
    });
    
    if (response.data && response.data.code === 200) {
      videos.value = response.data.data.list || [];
      filterVideos(); // 初始化筛选结果
    } else {
      throw new Error(response.data.message || '获取视频列表失败');
    }
  } catch (error) {
    console.error('获取视频列表失败:', error);
    ElMessage.error('获取视频列表失败: ' + (error.message || '未知错误'));
  } finally {
    loading.value = false;
  }
};

// 筛选视频
const filterVideos = () => {
  if (!searchQuery.value) {
    filteredVideos.value = [...videos.value];
    return;
  }
  
  const query = searchQuery.value.toLowerCase();
  filteredVideos.value = videos.value.filter(item => {
    if (item.isChapter) {
      return item.title.toLowerCase().includes(query);
    }
    return item.title.toLowerCase().includes(query) || 
           (item.description && item.description.toLowerCase().includes(query));
  });
};

// 格式化时间长度
const formatDuration = (seconds) => {
  if (!seconds) return '00:00';
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 跳转到上传页面
const navigateToUpload = () => {
  router.push({
    name: 'VideosUpload',
    query: { courseId: courseId.value }
  });
};

// 生成知识图谱
const generateKnowledgeGraph = async (forceRegenerate = false) => {
  // 处理可能传入的事件对象
  if (typeof forceRegenerate === 'object' && forceRegenerate !== null) {
    forceRegenerate = false; // 如果传入的是事件对象，则默认为 false
  }
  
  if (!courseId.value) {
    ElMessage.error('课程ID无效');
    return;
  }
  
  try {
    knowledgeGraphLoading.value = true;
    
    const response = await knowledgeMapService.generateKnowledgeGraph({
      courseId: courseId.value,
      forceRegenerate: forceRegenerate,
      incremental: true // 默认使用增量模式
    });
    
    if (response.data.code === 200) {
      ElMessage.success('知识图谱生成任务已启动，请稍后查看结果');
    } else {
      throw new Error(response.data.msg || '生成失败');
    }
  } catch (error) {
    console.error('生成知识图谱失败:', error);
    
    // 检查是否是409冲突状态码（已有任务在进行中）
    if (error.response && error.response.status === 409) {
      // 保存任务信息并显示强制重新生成对话框
      pendingKnowledgeGraphTask.value = error.response.data.data;
      showForceRegenerateDialog.value = true;
    } else {
      ElMessage.error('生成知识图谱失败: ' + (error.message || '未知错误'));
    }
  } finally {
    knowledgeGraphLoading.value = false;
  }
};

// 强制重新生成知识图谱
const forceRegenerateKnowledgeGraph = async () => {
  showForceRegenerateDialog.value = false;
  await generateKnowledgeGraph(true);
};

// 关闭强制重新生成对话框
const closeForceRegenerateDialog = () => {
  showForceRegenerateDialog.value = false;
  pendingKnowledgeGraphTask.value = null;
};

// 查看视频详情
const showVideoDetails = (video) => {
  router.push(`/video/${video.id}`);
};

// 打开重命名对话框
const showRenameDialog = (video) => {
  Object.assign(videoEdit, {
    id: video.id,
    title: video.title,
    description: video.description || ''
  });
  showRenameModal.value = true;
};

// 关闭重命名对话框
const closeRenameDialog = () => {
  showRenameModal.value = false;
};

// 保存视频信息
const saveVideoInfo = async () => {
  if (!videoEdit.title) {
    ElMessage.warning('视频标题不能为空');
    return;
  }
  
  try {
    const response = await videoService.updateVideo(videoEdit.id, {
      title: videoEdit.title,
      description: videoEdit.description
    });
    
    if (response.data && response.data.code === 200) {
      // 更新本地数据
      const index = videos.value.findIndex(v => v.id === videoEdit.id);
      if (index !== -1) {
        videos.value[index] = {
          ...videos.value[index],
          title: videoEdit.title,
          description: videoEdit.description
        };
      }
      
      // 更新筛选结果
      filterVideos();
      
      // 关闭对话框
      closeRenameDialog();
      
      ElMessage.success('视频信息更新成功');
    } else {
      throw new Error(response.data.message || '更新视频信息失败');
    }
  } catch (error) {
    console.error('更新视频信息失败:', error);
    ElMessage.error('更新视频信息失败: ' + (error.message || '未知错误'));
  }
};

// 确认删除视频
const confirmDeleteVideo = (video) => {
  videoToDelete.value = video;
  showDeleteModal.value = true;
};

// 关闭删除对话框
const closeDeleteDialog = () => {
  showDeleteModal.value = false;
  videoToDelete.value = null;
};

// 删除视频
const deleteVideo = async () => {
  if (!videoToDelete.value) return;
  
  try {
    const response = await videoService.deleteVideo(videoToDelete.value.id);
    
    if (response.data && response.data.code === 200) {
      // 从列表中移除
      videos.value = videos.value.filter(v => v.id !== videoToDelete.value.id);
      
      // 更新筛选结果
      filterVideos();
      
      // 关闭对话框
      closeDeleteDialog();
      
      ElMessage.success('视频已成功解除关联');
    } else {
      throw new Error(response.data.message || '解除视频关联失败');
    }
  } catch (error) {
    console.error('解除视频关联失败:', error);
    ElMessage.error('解除视频关联失败: ' + (error.message || '未知错误'));
  }
};

// 处理视频
const processVideo = async (video) => {
  if (!video || !video.id) return;
  
  // 判断是否正在处理
  if (processingVideoId.value === video.id) {
    ElMessage.info('视频正在处理中，请稍候...');
    return;
  }
  
  // 打开处理设置表单，传入单个视频
  await openProcessSettingsForm([video]);
};

// 获取步骤显示名称
const getStepDisplayName = (stepName) => {
  const stepMap = {
    keyframes: '关键帧提取',
    ocr: 'OCR文字识别',
    asr: 'ASR语音识别',
    vector: '向量化处理',
    summary: '智能摘要'
  };
  return stepMap[stepName] || stepName;
};

// 打开处理设置表单
const openProcessSettingsForm = async (videoList) => {
  if (!videoList || videoList.length === 0) {
    ElMessage.warning('没有要处理的视频');
    return;
  }
  
  loadingProcessingStatus.value = true;
  showProcessSettingsModal.value = true;
  
  try {
    // 初始化表单数据
    processFormData.value = {
      videos: [],
      previewMode: false
    };
    
    // 为每个视频初始化步骤设置
    for (const video of videoList) {
      // 初始化视频的处理设置
      const videoData = {
        id: video.id,
        title: video.title,
        status: {
          keyframes: false,
          ocr: false,
          asr: false,
          vector: false,
          summary: false
        },
        steps: {
          keyframes: true, // 默认选择所有步骤
          ocr: true,
          asr: true,
          vector: true,
          summary: true
        }
      };
      
      processFormData.value.videos.push(videoData);
    }
    
    console.log('处理设置表单已初始化:', {
      videoCount: processFormData.value.videos.length,
      formData: processFormData.value
    });
    
  } catch (error) {
    console.error('初始化处理设置表单失败:', error);
    ElMessage.error('初始化处理设置失败: ' + (error.message || '未知错误'));
  } finally {
    loadingProcessingStatus.value = false;
  }
};

// 批量设置所有视频的某个步骤
const setBatchStep = (stepName, enabled) => {
  processFormData.value.videos.forEach(video => {
    video.steps[stepName] = enabled;
  });
  console.log(`批量设置步骤 ${stepName} 为 ${enabled}`);
};

// 批量设置所有视频的所有步骤
const setBatchAllSteps = (enabled) => {
  processFormData.value.videos.forEach(video => {
    processingSteps.value.forEach(step => {
      video.steps[step.value] = enabled;
    });
  });
  console.log(`批量设置所有步骤为 ${enabled}`);
};

// 重置单个视频的步骤设置
const resetVideoSteps = (videoIndex) => {
  const video = processFormData.value.videos[videoIndex];
  if (video) {
    // 重置为默认值：处理未完成的步骤
    processingSteps.value.forEach(step => {
      video.steps[step.value] = !video.status[step.value];
    });
    console.log(`重置视频 ${video.title} 的步骤设置`);
  }
};

// 获取选中的处理步骤数量
const getSelectedStepsCount = (video) => {
  return processingSteps.value.filter(step => video.steps[step.value]).length;
};

// 检查是否有任何视频选择了处理步骤
const hasAnySelectedSteps = computed(() => {
  return processFormData.value.videos.some(video => 
    processingSteps.value.some(step => video.steps[step.value])
  );
});



// 关闭处理设置对话框
const closeProcessSettingsDialog = () => {
  showProcessSettingsModal.value = false;
  processFormData.value = {
    videos: [],
    previewMode: false
  };
};

// 提交处理设置
const submitProcessSettings = async () => {
  if (!hasAnySelectedSteps.value && !processFormData.value.previewMode) {
    ElMessage.warning('请至少选择一个处理步骤，或启用预览模式');
    return;
  }
  
  // 显示进度对话框
  showBatchProgressModal.value = true;
  batchProcessing.value = true;
  batchProgress.value = 0;
  processedCount.value = 0;
  
  const processingType = processFormData.value.previewMode ? '预览处理' : '处理';
  processingStatus.value = [
    {
      icon: 'mdi-information-outline',
      color: 'info',
      textClass: 'text-info',
      message: `正在启动${processingType}任务...`
    }
  ];
  
  const videosToProcess = processFormData.value.videos.filter(video => 
    processFormData.value.previewMode || processingSteps.value.some(step => video.steps[step.value])
  );
  
  const totalVideos = videosToProcess.length;
  const videoStatus = new Map();
  
  // 更新处理状态显示
  const updateProcessingStatus = () => {
    const statusList = [];
    
    // 添加当前处理中的任务
    if (videoStatus.has('current')) {
      statusList.push({
        icon: 'mdi-cog',
        color: 'info',
        textClass: 'text-info',
        message: videoStatus.get('current').message
      });
    }
    
    // 添加成功完成的任务（最多显示5个）
    let successCount = 0;
    videoStatus.forEach((status, videoId) => {
      if (videoId !== 'current' && status.status === 'success' && successCount < 5) {
        statusList.push({
          icon: 'mdi-check',
          color: 'success',
          textClass: 'text-success',
          message: status.message
        });
        successCount++;
      }
    });
    
    // 添加失败的任务（全部显示）
    videoStatus.forEach((status, videoId) => {
      if (videoId !== 'current' && status.status === 'error') {
        statusList.push({
          icon: 'mdi-alert',
          color: 'error',
          textClass: 'text-error',
          message: status.message
        });
      }
    });
    
    // 添加排队中的任务数量
    const remainingCount = totalVideos - processedCount.value - 1;
    if (remainingCount > 0) {
      statusList.push({
        icon: 'mdi-timer-sand',
        color: 'grey',
        textClass: 'text-medium-emphasis',
        message: `${remainingCount} 个视频等待${processingType}...`
      });
    }
    
    processingStatus.value = statusList;
  };
  
  // 按顺序处理所有视频
  for (let i = 0; i < videosToProcess.length; i++) {
    const video = videosToProcess[i];
    
    // 更新当前处理状态
    videoStatus.set('current', {
      status: 'processing',
      message: `${processingType}中：${video.title} (${i + 1}/${totalVideos})`
    });
    updateProcessingStatus();
    
    try {
      // 构建请求数据
      let selectedSteps = [];
      if (!processFormData.value.previewMode) {
        selectedSteps = processingSteps.value
          .filter(step => video.steps[step.value])
          .map(step => step.value);
      }
      
      const requestData = {
        processing_steps: processFormData.value.previewMode ? null : selectedSteps,
        preview_mode: processFormData.value.previewMode
      };
      
      console.log(`${processingType}视频请求数据:`, {
        videoId: video.id,
        videoTitle: video.title,
        processing_steps: requestData.processing_steps,
        preview_mode: requestData.preview_mode
      });
      
      const response = await videoService.processVideoWithSettings(video.id, requestData);
      
      if (response.data && response.data.code === 200) {
        // 处理成功
        videoStatus.set(video.id, {
          status: 'success',
          message: `${processingType}成功：${video.title}`
        });
        
        // 更新进度
        processedCount.value++;
        batchProgress.value = (processedCount.value / totalVideos) * 100;
      } else {
        // 处理失败
        videoStatus.set(video.id, {
          status: 'error',
          message: `${processingType}失败：${video.title} - ${response.data.message || '未知错误'}`
        });
      }
    } catch (error) {
      console.error(`${processingType}视频失败:`, error);
      videoStatus.set(video.id, {
        status: 'error',
        message: `${processingType}失败：${video.title} - ${error.message || '未知错误'}`
      });
    }
    
    // 更新状态显示
    updateProcessingStatus();
  }
  
  // 处理完成
  batchProcessing.value = false;
  videoStatus.delete('current');
  processingStatus.value.unshift({
    icon: 'mdi-check-circle',
    color: 'success',
    textClass: 'text-success',
    message: `${processingType}完成，共${processingType} ${processedCount.value} 个视频`
  });
  updateProcessingStatus();
  
  // 关闭设置对话框
  closeProcessSettingsDialog();
};

// 确认批量处理
const confirmBatchProcess = async () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择要处理的视频');
    return;
  }
  
  // 获取选中的视频对象
  const selectedVideoObjects = videos.value.filter(video => selectedVideos.value.includes(video.id));
  
  // 打开处理设置表单
  await openProcessSettingsForm(selectedVideoObjects);
};

// 批量处理视频（使用新的表单设置）
const batchProcessVideos = async () => {
  showBatchProcessModal.value = false;
  
  // 使用当前表单设置执行处理
  await submitProcessSettings();
};

// 确认批量删除
const confirmBatchDelete = () => {
  if (selectedVideos.value.length === 0) {
    ElMessage.warning('请先选择要删除的视频');
    return;
  }
  showBatchDeleteModal.value = true;
};

// 批量删除视频
const batchDeleteVideos = async () => {
  if (selectedVideos.value.length === 0) return;
  
  batchProcessing.value = true;
  
  try {
    const deletePromises = selectedVideos.value.map(videoId => 
      videoService.deleteVideo(videoId)
    );
    
    const results = await Promise.allSettled(deletePromises);
    
    let successCount = 0;
    let failCount = 0;
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.data?.code === 200) {
        successCount++;
        // 从本地列表中移除成功删除的视频
        const videoId = selectedVideos.value[index];
        videos.value = videos.value.filter(v => v.id !== videoId);
      } else {
        failCount++;
      }
    });
    
    // 更新筛选结果
    filterVideos();
    
    // 清空选择
    selectedVideos.value = [];
    
    // 关闭对话框
    closeBatchDeleteDialog();
    
    // 显示结果
    if (failCount === 0) {
      ElMessage.success(`成功解除 ${successCount} 个视频的关联`);
    } else {
      ElMessage.warning(`解除关联完成：成功 ${successCount} 个，失败 ${failCount} 个`);
    }
  } catch (error) {
    console.error('批量解除视频关联失败:', error);
    ElMessage.error('批量解除视频关联失败: ' + (error.message || '未知错误'));
  } finally {
    batchProcessing.value = false;
  }
};

// 关闭批量处理对话框
const closeBatchProcessDialog = () => {
  showBatchProcessModal.value = false;
};

// 关闭批量删除对话框
const closeBatchDeleteDialog = () => {
  showBatchDeleteModal.value = false;
};

// 关闭批量进度对话框
const closeBatchProgressDialog = () => {
  showBatchProgressModal.value = false;
  // 重置状态
  batchProgress.value = 0;
  processedCount.value = 0;
  processingStatus.value = [];
  selectedVideos.value = [];
};

// 获取章节列表
const fetchChapters = async () => {
  try {
    loading.value = true;
    const response = await chapterService.getCourseChapters(courseId.value);
    if (response.data.code === 200) {
      chapters.value = response.data.data;
    }
  } catch (error) {
    console.error('获取章节列表失败:', error);
    showMessage('获取章节列表失败', 'error');
  } finally {
    loading.value = false;
  }
};

// 打开新建章节对话框
const openNewChapterDialog = () => {
  newChapter.value = {
    chapterNumber: '',
    title: ''
  };
  newChapterDialog.value = true;
};

// 关闭新建章节对话框
const closeNewChapterDialog = () => {
  newChapterDialog.value = false;
  newChapter.value = {
    chapterNumber: '',
    title: ''
  };
};

// 创建新章节
const createChapter = async () => {
  if (!chapterFormValid.value) return;
  
  try {
    loading.value = true;
    
    // 创建新章节对象
    const newChapterData = {
      id: Date.now(), // 临时ID
      chapterNumber: parseInt(newChapter.value.chapterNumber),
      title: newChapter.value.title,
      documents: [], // 初始化空文档列表
      createTime: new Date().toISOString()
    };
    
    // 添加到章节列表
    chapters.value.push(newChapterData);
    
    // 按章节序号排序
    chapters.value.sort((a, b) => a.chapterNumber - b.chapterNumber);
    // 进入插入模式
    isInsertingChapter.value = true;
    
    // 关闭对话框
    closeNewChapterDialog();
    
    showMessage('请选择要插入章节的位置', 'info');
      
      
    const response = await chapterService.createChapter({
      courseId: props.courseId,
      chapterNumber: newChapterData.chapterNumber,
      title: newChapterData.title
    });
    if (response.data.code === 200) {
      showMessage('章节创建成功', 'success');
    } else {
      showMessage('章节创建失败', 'error');
    }
    // 保存章节数据以供后续插入
    insertPosition.value = newChapterData;
  } catch (error) {
    console.error('创建章节失败:', error);
    showMessage(error.message || '创建章节失败', 'error');
  } finally {
    loading.value = false;
  }
};

// 添加插入章节的处理函数
const handleChapterInsert = (index) => {
  if (!isInsertingChapter.value || !insertPosition.value) return;
  
  try {
    // 创建一个新的数组，包含所有当前的视频
    const updatedVideos = [...videos.value];
    
    // 在指定位置插入章节
    updatedVideos.splice(index, 0, {
      id: `chapter-${Date.now()}`, // 为章节生成一个唯一ID
      isChapter: true,
      ...insertPosition.value
    });
    
    // 更新视频列表
    videos.value = updatedVideos;
    
    // 更新筛选后的列表
    filterVideos();
    
    // 退出插入模式
    isInsertingChapter.value = false;
    insertPosition.value = null;
    
    showMessage('章节插入成功', 'success');
  } catch (error) {
    console.error('插入章节失败:', error);
    showMessage('插入章节失败', 'error');
  }
};

// 取消插入模式
const cancelInsertChapter = () => {
  isInsertingChapter.value = false;
  insertPosition.value = null;
  showMessage('已取消插入章节', 'info');
};

// 上传文件
const uploadFiles = async (files, chapterId) => {
  try {
    loading.value = true;
    
    // 找到对应的章节
    const chapter = chapters.value.find(c => c.id === chapterId);
    if (!chapter) {
      throw new Error('章节不存在');
    }
    
    // 处理每个文件
    for (const file of files) {
      // 创建文档对象
      const newDocument = {
        id: Date.now() + Math.random(), // 临时ID
        title: file.name,
        fileUrl: URL.createObjectURL(file), // 创建临时URL
        fileType: file.name.split('.').pop().toLowerCase(),
        fileSize: file.size,
        uploadTime: new Date().toISOString()
      };
      
      // 添加到章节的文档列表
      if (!chapter.documents) {
        chapter.documents = [];
      }
      chapter.documents.push(newDocument);
    }
    
    showMessage('文件上传成功', 'success');
    

    const uploadPromises = files.map(file => {
    return uploadService.uploadDocumentToChapter(file, props.courseId, chapterId);
    });
    await Promise.all(uploadPromises);
  } catch (error) {
    console.error('文件上传失败:', error);
    showMessage(error.message || '文件上传失败', 'error');
  } finally {
    loading.value = false;
  }
};

// 删除文档
const handleDocumentDelete = async (chapterId, documentId) => {
  try {
    // 找到对应的章节
    const chapter = chapters.value.find(c => c.id === chapterId);
    if (!chapter) {
      throw new Error('章节不存在');
    }
    
    // 从文档列表中移除
    chapter.documents = chapter.documents.filter(doc => doc.id !== documentId);
    
    showMessage('文件删除成功', 'success');
    
    // TODO: 后续添加与后端的交互
    // await uploadService.deleteDocument(documentId);
  } catch (error) {
    console.error('文件删除失败:', error);
    showMessage(error.message || '文件删除失败', 'error');
  }
};

// 格式化文件大小
const formatFileSize = (size) => {
  if (size < 1024) return size + ' B';
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB';
  return (size / (1024 * 1024)).toFixed(2) + ' MB';
};

// 处理拖放离开
const handleDragLeave = () => {
  isDragging.value = false;
};

// 处理拖放进入
const handleDragEnter = () => {
  isDragging.value = true;
};

// 处理文件拖放
const handleFileDrop = async (event, chapterId) => {
  isDragging.value = false;
  
  if (!event.dataTransfer?.files) return;
  
  const files = Array.from(event.dataTransfer.files);
  await uploadFiles(files, chapterId);
};

// 初始化
onMounted(async () => {
  await fetchVideos();
  await fetchChapters();
});

// 监听课程ID变化
watch(() => courseId.value, async (newVal) => {
  if (newVal) {
    await fetchChapters();
  }
});

// 在 setup 中添加新的响应式变量
const isInsertingChapter = ref(false);
const insertPosition = ref(null);

// 添加 snackbar 状态
const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
});

// 添加显示消息的函数
const showMessage = (text, type = 'success') => {
  snackbar.text = text;
  snackbar.color = type;
  snackbar.show = true;
};
</script>

<style scoped>
.content-card {
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.scrollable-content {
  overflow-y: auto;
  max-height: calc(100vh - 200px); /* 调整最大高度，为两个卡片预留空间 */
  flex-grow: 1;
}

.video-card {
  transition: transform 0.2s;
}

.video-card:hover {
  transform: scale(1.02);
}

.video-card.selected {
  border: 2px solid rgb(var(--v-theme-primary));
  box-shadow: 0 4px 12px rgba(var(--v-theme-primary), 0.2);
}

.video-thumbnail {
  position: relative;
}

.video-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.875rem;
}

.search-field {
  max-width: 400px;
}

.text-truncate-2 {
  display: -webkit-box;
  display: box;
  -webkit-box-orient: vertical;
  box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.pa-4 {
  padding: 16px !important;
}

.video-checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
}

.video-thumbnail img:hover {
  cursor: pointer;
}

.drop-zone {
  border: 2px dashed rgba(var(--v-theme-primary), 0.4);
  border-radius: 8px;
  transition: all 0.3s ease;
  min-height: 200px;
}

.drop-zone-active {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.doc-card {
  transition: transform 0.2s;
}

.doc-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.insert-point {
  cursor: pointer;
  border: 2px dashed rgba(var(--v-theme-primary), 0.4);
  border-radius: 8px;
  margin: 8px 0;
  transition: all 0.3s ease;
}

.insert-point:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
  border-color: rgb(var(--v-theme-primary));
}

.chapter-header {
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-left: 4px solid rgb(var(--v-theme-primary));
  margin: 16px 0;
  padding: 12px;
  border-radius: 4px;
}
</style>