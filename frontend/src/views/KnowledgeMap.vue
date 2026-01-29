<!-- 知识图谱页面 -->
<template>  <v-container fluid class="knowledge-map-container fill-height pa-4">
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4" elevation="0">
          <v-card-text class="d-flex align-center py-2">
            <div>
              <h1 class="text-h4 font-weight-bold" style="color: #6f23d1;">知识图谱</h1>
              <p class="text-subtitle-1 text-medium-emphasis mt-1 mb-0">
                探索课程知识体系，掌握学习进度，提升专业能力
              </p>
            </div>
            
            <!-- 沉浸模式切换按钮
            <v-spacer></v-spacer>
            <v-btn
              v-if="currentTab === 'knowledge'"
              :color="isImmersiveMode ? 'error' : 'primary'"
              :icon="isImmersiveMode ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
              variant="outlined"
              @click="toggleImmersiveMode"
              class="mr-2"
            >
            </v-btn> -->
          </v-card-text>
        </v-card>
        
        <!-- 沉浸模式全屏遮罩 -->
        <v-overlay
          v-model="isImmersiveMode"
          class="immersive-overlay"
          z-index="9999"
          persistent
        >
          <v-fade-transition>
            <div v-if="isImmersiveMode" class="immersive-container">
              <!-- 沉浸模式头部控制栏 -->
              <div class="immersive-header">
                <div class="d-flex align-center">
                  <v-icon color="white" class="mr-2">mdi-graph</v-icon>
                  <span class="text-white text-h6">知识图谱 - 沉浸模式</span>
                </div>
                
                <!-- 筛选控件 -->
                <div class="d-flex align-center">
                  <v-text-field
                    v-model="nodeFilter"
                    placeholder="搜索节点..."
                    variant="outlined"
                    density="compact"
                    hide-details
                    prepend-inner-icon="mdi-magnify"
                    clearable
                    class="mr-4"
                    style="width: 300px;"
                    color="white"
                    bg-color="rgba(255,255,255,0.1)"
                  />
                  <v-btn
                    icon="mdi-fullscreen-exit"
                    color="white"
                    variant="text"
                    @click="exitImmersiveMode"
                  />
                </div>
              </div>
                <!-- 沉浸模式图谱容器 -->
              <div 
                id="immersive-graph-container" 
                class="immersive-graph"
                :style="{ height: 'calc(100vh - 80px)' }"
              ></div>
              
              <!-- 沉浸模式下的知识点详情 -->
              <v-slide-x-transition>
                <v-card 
                  v-if="isImmersiveMode && selectedNode" 
                  class="immersive-detail-card"
                  elevation="12"
                >
                  <v-card-title class="text-h6 pa-4 d-flex align-center">
                    <span class="flex-grow-1">{{ selectedNode.name }}</span>
                    <v-chip
                      :color="getNodeTypeColor(String(selectedNode.category || 'core_concept'))"
                      size="small"
                      class="ml-2"
                    >
                      {{ getNodeTypeName(String(selectedNode.category || 'core_concept')) }}
                    </v-chip>
                    <v-btn
                      icon="mdi-eye"
                      variant="text"
                      size="small"
                      @click="goToKnowledgePointDetail(selectedNode.id)"
                      class="ml-2"
                      title="查看详情"
                    />
                    <v-btn
                      icon="mdi-close"
                      variant="text"
                      size="small"
                      @click="selectedNode = null"
                      class="ml-2"
                    />
                  </v-card-title>
                  
                  <v-card-text class="pa-4 pt-0">
                    <v-divider class="mb-3" />
                    
                    <p class="text-body-1 mb-3">{{ selectedNode.description || '暂无描述' }}</p>
                    
                    <!-- 节点关系 -->
                    <div v-if="selectedNode && nodeFeatures.length > 0" class="mb-4">
                      <div class="d-flex align-center mb-2">
                        <v-icon color="primary" class="mr-2">mdi-star-outline</v-icon>
                        <span class="text-subtitle-2 font-weight-medium">知识点关系</span>
                      </div>
                      <v-list density="compact" class="bg-transparent pa-0">
                        <v-list-item
                          v-for="(feature, index) in nodeFeatures"
                          :key="index"
                          class="px-0"
                        >
                          <template v-slot:prepend>
                            <v-icon size="small" :color="getRelationConfig(feature.type).color" class="mr-2">
                              mdi-arrow-right-thin
                            </v-icon>
                          </template>
                          <v-list-item-title class="text-body-2">
                            {{ feature.description }}
                          </v-list-item-title>
                        </v-list-item>
                      </v-list>
                    </div>
                    
                    <!-- 边的描述信息 -->
                    <div v-if="selectedEdgeInfo" class="mb-4">
                      <div class="d-flex align-center justify-space-between mb-2">
                        <div class="d-flex align-center">
                          <v-icon color="primary" class="mr-2">mdi-arrow-decision</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">关系描述</span>
                        </div>
                        <!-- 删除关系按钮，仅教师可见 -->
                        <v-btn
                          v-if="isTeacher"
                          color="error"
                          size="small"
                          variant="text"
                          prepend-icon="mdi-delete"
                          @click="showDeleteRelationSelectDialog = true"
                        >
                          删除关系
                        </v-btn>
                      </div>
                      <v-card variant="outlined" class="pa-3">
                        <div class="d-flex align-center mb-2">
                          <span class="text-body-2">{{ selectedEdgeInfo.source }} → {{ selectedEdgeInfo.target }}</span>
                          <v-chip
                            :color="getRelationConfig(selectedEdgeInfo.relation_type || 'related').color"
                            size="small"
                            class="ml-2"
                          >
                            {{ getRelationConfig(selectedEdgeInfo.relation_type || 'related').name }}
                          </v-chip>
                        </div>
                        <p class="text-body-2 mb-0">{{ selectedEdgeInfo.description || '暂无关系描述' }}</p>
                      </v-card>
                    </div>
                    
                    <!-- 相关视频列表 -->
                    <div v-if="selectedNode.relatedVideos?.length" class="mb-4">
                      <div class="d-flex align-center justify-space-between mb-2">
                        <div class="d-flex align-center">
                          <v-icon color="primary" class="mr-2">mdi-video-outline</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">相关视频</span>
                        </div>
                        <v-btn
                          color="primary"
                          size="small"
                          variant="text"
                          prepend-icon="mdi-robot"
                          @click="askAI(selectedNode)"
                        >
                          问AI
                        </v-btn>
                      </div>
                      <v-list density="compact" class="bg-transparent pa-0">
                        <v-list-item
                          v-for="video in selectedNode.relatedVideos"
                          :key="video.id"
                          @click="jumpToVideo(video.id, video.courseId)"
                          class="rounded-lg mb-1"
                          hover
                        >
                          <template v-slot:prepend>
                            <v-icon size="small" color="primary" class="mr-2">mdi-play-circle</v-icon>
                          </template>
                          
                          <v-list-item-title class="text-body-2">{{ video.title }}</v-list-item-title>
                          
                          <v-list-item-subtitle class="mt-1">
                            <div class="d-flex align-center text-caption">
                              <span class="text-primary">{{ video.courseName }}</span>
                              <v-icon size="12" class="mx-1">mdi-circle-small</v-icon>
                              <span class="mr-2">
                                <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                                {{ video.viewCount }}
                              </span>
                              <span>
                                <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                                {{ formatDuration(video.duration) }}
                              </span>
                            </div>
                          </v-list-item-subtitle>
                        </v-list-item>
                      </v-list>
                    </div>
                    
                    <!-- 前置知识点 -->
                    <v-chip-group v-if="selectedNode.prerequisites?.length" class="mb-0">
                      <v-chip
                        v-for="prereq in selectedNode.prerequisites"
                        :key="prereq"
                        size="small"
                        color="#6f23d1"
                        variant="outlined"
                      >
                        {{ prereq }}
                      </v-chip>
                    </v-chip-group>
                  </v-card-text>
                </v-card>
              </v-slide-x-transition>
            </div>
          </v-fade-transition>
        </v-overlay>
        
        <!-- 标签页切换 -->
        <v-card class="rounded-lg">
          <v-tabs
            v-model="currentTab"
            color="#6f23d1"
            align-tabs="center"
            class="px-4"
            slider-color="#6f23d1"
            height="56"
          >
            <v-tab value="knowledge" class="text-subtitle-1">
              <v-icon start>mdi-graph</v-icon>
              课程知识图谱
            </v-tab>            <v-tab value="knowledgeList" class="text-subtitle-1">
              <v-icon start>mdi-format-list-bulleted</v-icon>
              知识列表
            </v-tab>
          </v-tabs>

          <v-divider></v-divider>

          <v-card-text class="pa-6">
            <v-window v-model="currentTab">
              <!-- 课程知识图谱 -->
              <v-window-item value="knowledge">
                <v-row>
                  <v-col cols="12" md="3">
                    <v-select
                      v-model="selectedCourse"
                      :items="courseOptions"
                      item-title="name"
                      item-value="id"
                      label="选择课程"
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      class="rounded-lg"
                    >
                      <template v-slot:prepend>
                        <v-icon color="#6f23d1">mdi-book-open-variant</v-icon>
                      </template>
                    </v-select>
                  </v-col>
                  
                  <v-col cols="12" md="4">
                    <v-text-field
                      v-model="nodeFilter"
                      placeholder="搜索节点..."
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      prepend-inner-icon="mdi-magnify"
                      clearable
                    />
                  </v-col>
                  
                  <v-col cols="12" md="3">
                    <v-btn
                      v-if="selectedCourse && selectedCourse !== 'platform'"
                      color="#6f23d1"
                      variant="outlined"
                      @click="viewPlatformGraph"
                      prepend-icon="mdi-sitemap"
                      block
                    >
                      查看平台知识图谱
                    </v-btn>
                    <v-btn
                      v-else-if="selectedCourse === 'platform'"
                      color="#6f23d1"
                      variant="outlined"
                      @click="backToCourseGraph"
                      prepend-icon="mdi-arrow-left"
                      block
                    >
                      返回课程图谱
                    </v-btn>
                  </v-col>

                  
                  
                  <v-col cols="12" md="2">
                    <v-btn
                      color="primary"
                      variant="outlined"
                      @click="enterImmersiveMode"
                      prepend-icon="mdi-fullscreen"
                      block
                    >
                      沉浸模式
                    </v-btn>
                  </v-col>

                  <!-- 新增：添加节点按钮 -->
                  <v-col cols="12" md="2">
                    <v-btn
                     v-if="isTeacher"
                      color="success"
                      variant="outlined"
                      @click="addNode"
                      prepend-icon="mdi-plus"
                      block
                    >
                      添加节点
                    </v-btn>
                  </v-col>
                  <!-- 新增：添加关系按钮，仅教师可见 -->
                  <v-col cols="12" md="2">
                    <v-btn
                      v-if="isTeacher"
                      color="info"
                      variant="outlined"
                      @click="showRelationDialog = true"
                      prepend-icon="mdi-link-plus"
                      block
                    >
                      添加关系
                    </v-btn>
                  </v-col>
                  <!-- 新增：删除节点按钮，仅教师可见且选中节点时可用 -->
                  <v-col cols="12" md="2">
                    <v-btn
                      v-if="isTeacher"
                      color="error"
                      variant="outlined"
                      :disabled="!selectedNode"
                      @click="deleteNodeDialog = true"
                      prepend-icon="mdi-delete"
                      block
                    >
                      删除节点
                    </v-btn>
                  </v-col>
                  <!-- 新增：删除关系按钮，仅教师可见且选中边时可用 -->
                  <v-col cols="12" md="2">
                    <v-btn
                      v-if="isTeacher"
                      color="error"
                      variant="outlined"
                      @click="openDeleteRelationDialog"
                      prepend-icon="mdi-link-off"
                      block
                    >
                      删除关系
                    </v-btn>
                  </v-col>
                  <!-- 新增：生成知识图谱按钮，仅教师可见 -->
                  <v-col cols="12" md="2">
                    <v-btn
                      v-if="isTeacher"
                      color="primary"
                      variant="outlined"
                      @click="showGenerateDialog = true"
                      :loading="generateLoading"
                      prepend-icon="mdi-graph"
                      block
                    >
                      生成知识图谱
                    </v-btn>
                  </v-col>
                </v-row>

                <!-- 图例和控制面板 -->
                <v-row class="mt-4">
                  <v-col cols="12">
                    <v-card variant="outlined" class="legend-panel">
                      <v-card-text class="py-3">
                        <v-row>
                          <!-- 节点类型图例 -->
                          <v-col cols="12" md="6">
                            <div class="legend-section">
                              <h4 class="text-subtitle-2 mb-2">
                                <v-icon class="mr-1" size="18">mdi-circle</v-icon>
                                节点类型
                              </h4>
                              <div class="d-flex flex-wrap gap-2">
                                <v-chip
                                  v-for="category in nodeCategories"
                                  :key="category.code"
                                  :color="category.color"
                                  size="small"
                                  variant="flat"
                                  class="legend-chip"
                                >
                                  <div 
                                    class="legend-node-dot"
                                    :style="{ backgroundColor: category.color }"
                                  ></div>
                                  {{ category.name }}
                                </v-chip>
                              </div>
                            </div>
                          </v-col>
                          
                          <!-- 关系类型图例 -->
                          <v-col cols="12" md="6">
                            <div class="legend-section">
                              <h4 class="text-subtitle-2 mb-2">
                                <v-icon class="mr-1" size="18">mdi-arrow-right</v-icon>
                                关系类型
                              </h4>
                              <div class="d-flex flex-wrap gap-2">
                                <v-chip
                                  v-for="relation in relationTypes"
                                  :key="relation.type"
                                  :color="relation.color"
                                  size="small"
                                  variant="outlined"
                                  class="legend-chip"
                                >
                                  <div 
                                    class="relation-line-sample" 
                                    :style="{ 
                                      borderColor: relation.color,
                                      borderStyle: relation.lineStyle || 'solid'
                                    }"
                                  ></div>
                                  {{ relation.name }}
                                </v-chip>
                              </div>
                            </div>
                          </v-col>
                        </v-row>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- 知识图谱容器 -->
                <div class="mt-4" style="position: relative;">
                  <!-- 加载状态 -->
                  <div v-if="loading.knowledge" class="loading-overlay">
                    <div class="text-center">
                      <v-progress-circular indeterminate color="#6f23d1" size="64"></v-progress-circular>
                      <p class="text-subtitle-1 mt-4">正在加载知识图谱...</p>
                    </div>
                  </div>
                  
                  <!-- 空状态 -->
                  <div v-if="!selectedCourse && !loading.knowledge" class="empty-state">
                    <div class="text-center">
                      <v-icon size="64" color="grey">mdi-graph-outline</v-icon>
                      <p class="text-subtitle-1 mt-4 text-medium-emphasis">请选择课程查看知识图谱</p>
                    </div>
                  </div>

                  <!-- 知识图谱容器 -->
                  <div 
                    id="knowledge-graph-container" 
                    class="graph-container"
                    :class="{ 'filtered': nodeFilter }"
                  ></div>
                </div>

                <!-- 知识点详情 -->
                <v-expand-transition>
                  <v-card v-if="selectedNode" id="node-detail-card" class="mt-4" variant="outlined">
                    <v-card-title class="text-h6 pa-4">
                      {{ selectedNode.name }}
                      <v-chip
                        :color="getNodeTypeColor(String(selectedNode.category || 'core_concept'))"
                        size="small"
                        class="ml-2"
                      >
                         {{ getNodeTypeName(String(selectedNode.category || 'core_concept')) }}
                      </v-chip>
                      <v-spacer></v-spacer>
                      <v-btn
                        color="success"
                        size="small"
                        variant="outlined"
                        @click="goToKnowledgePointDetail(selectedNode.id)"
                        prepend-icon="mdi-eye"
                        class="ml-2"
                      >
                        查看详情
                      </v-btn>
                      <v-btn
                      v-if="isTeacher"
                        color="primary"
                        size="small"
                        variant="outlined"
                        @click="editNode(selectedNode)"
                        class="ml-2"
                      >
                        编辑节点
                      </v-btn>
                    </v-card-title>
                    <v-card-text class="pt-2">
                      <p class="text-body-1">{{ selectedNode.description || '暂无描述' }}</p>
                      
                      <!-- 节点特点 -->
                      <div v-if="selectedNode && nodeFeatures.length > 0" class="mt-4">
                        <div class="d-flex align-center mb-2">
                          <v-icon color="primary" class="mr-2">mdi-star-outline</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">知识点关系</span>
                        </div>
                        <v-list density="compact" class="bg-transparent pa-0">
                          <v-list-item
                            v-for="(feature, index) in nodeFeatures"
                            :key="index"
                            class="px-0"
                          >
                            <template v-slot:prepend>
                              <v-icon size="small" :color="getRelationConfig(feature.type).color" class="mr-2">
                                mdi-arrow-right-thin
                              </v-icon>
                            </template>
                            <v-list-item-title class="text-body-2">
                              {{ feature.description }}
                            </v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </div>
                      
                      <!-- 边的描述信息 -->
                      <div v-if="selectedEdgeInfo" class="mt-4">
                        <div class="d-flex align-center mb-2">
                          <v-icon color="primary" class="mr-2">mdi-arrow-decision</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">关系描述</span>
                        </div>
                        <v-card variant="outlined" class="pa-3">
                          <div class="d-flex align-center mb-2">
                            <span class="text-body-2">{{ selectedEdgeInfo.source }} → {{ selectedEdgeInfo.target }}</span>
                            <v-chip
                              :color="getRelationConfig(selectedEdgeInfo.relation_type || 'related').color"
                              size="small"
                              class="ml-2"
                            >
                              {{ getRelationConfig(selectedEdgeInfo.relation_type || 'related').name }}
                            </v-chip>
                          </div>
                          <p class="text-body-2 mb-0">{{ selectedEdgeInfo.description || '暂无关系描述' }}</p>
                        </v-card>
                      </div>
                      
                      <!-- 相关视频列表 -->
                      <div v-if="selectedNode.relatedVideos?.length" class="mt-4">
                        <div class="d-flex align-center justify-space-between mb-2">
                          <div class="d-flex align-center">
                            <v-icon color="primary" class="mr-2">mdi-video-outline</v-icon>
                            <span class="text-subtitle-2 font-weight-medium">相关视频</span>
                          </div>
                          <v-btn
                            color="primary"
                            size="small"
                            variant="text"
                            prepend-icon="mdi-robot"
                            @click="askAI(selectedNode)"
                          >
                            问AI
                          </v-btn>
                        </div>
                        <v-list density="compact" class="bg-transparent pa-0">
                          <v-list-item
                            v-for="video in selectedNode.relatedVideos"
                            :key="video.id"
                            @click="jumpToVideo(video.id, video.courseId)"
                            class="rounded-lg mb-1"
                            hover
                          >
                            <template v-slot:prepend>
                              <v-icon size="small" color="primary" class="mr-2">mdi-play-circle</v-icon>
                            </template>
                            
                            <v-list-item-title class="text-body-2">{{ video.title }}</v-list-item-title>
                            
                            <v-list-item-subtitle class="mt-1">
                              <div class="d-flex align-center text-caption">
                                <span class="text-primary">{{ video.courseName }}</span>
                                <v-icon size="12" class="mx-1">mdi-circle-small</v-icon>
                                <span class="mr-2">
                                  <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                                  {{ video.viewCount }}
                                </span>
                                <span>
                                  <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                                  {{ formatDuration(video.duration) }}
                                </span>
                              </div>
                            </v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </div>
                      
                      <!-- 相关文档列表 -->
                      <div v-if="selectedNode.relatedDocuments?.length" class="mt-4">
                        <div class="d-flex align-center mb-2">
                          <v-icon color="secondary" class="mr-2">mdi-file-document-outline</v-icon>
                          <span class="text-subtitle-2 font-weight-medium">相关文档</span>
                        </div>
                        <v-list density="compact" class="bg-transparent pa-0">
                          <v-list-item
                            v-for="document in selectedNode.relatedDocuments"
                            :key="document.id"
                            @click="jumpToDocument(document.id, document.courseId)"
                            class="rounded-lg mb-1"
                            hover
                          >
                            <template v-slot:prepend>
                              <v-icon size="small" color="secondary" class="mr-2">mdi-file-document</v-icon>
                            </template>
                            
                            <v-list-item-title class="text-body-2">{{ document.title }}</v-list-item-title>
                            
                            <v-list-item-subtitle class="mt-1">
                              <div class="d-flex align-center text-caption">
                                <span class="text-secondary">{{ document.courseName }}</span>
                                <v-icon size="12" class="mx-1">mdi-circle-small</v-icon>
                                <span class="mr-2">
                                  <v-icon size="12" class="mr-1">mdi-file-outline</v-icon>
                                  {{ document.fileType?.toUpperCase() }}
                                </span>
                                <span>
                                  <v-icon size="12" class="mr-1">mdi-database-outline</v-icon>
                                  {{ formatFileSize(document.fileSize) }}
                                </span>
                              </div>
                            </v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </div>
                      
                      <!-- 前置知识点 -->
                      <v-chip-group v-if="selectedNode.prerequisites?.length" class="mt-3">
                        <v-chip
                          v-for="prereq in selectedNode.prerequisites"
                          :key="prereq"
                          size="small"
                          color="#6f23d1"
                          variant="outlined"
                        >
                          {{ prereq }}
                        </v-chip>
                      </v-chip-group>
                    </v-card-text>
                  </v-card>
                </v-expand-transition>
              </v-window-item>              <!-- 知识列表 -->
              <v-window-item value="knowledgeList">
                <KnowledgeList :course-id="selectedCourse" :is-teacher="isTeacher" />
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 节点新增/编辑对话框 -->
    <v-dialog v-model="showNodeDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          {{ isEditNode ? '编辑节点' : '添加节点' }}
        </v-card-title>
        <v-card-text>
          <v-form>
            <v-text-field
              v-model="nodeForm.name"
              label="节点名称"
              required
            />
            <v-select
              v-model="nodeForm.category"
              :items="nodeCategories"
              :item-title="(item: any) => getNodeTypeName(item.code)"
              item-value="code"
              label="节点类型"
              required
              persistent-hint
              :hint="isEditNode"
            />
            <v-textarea
              v-model="nodeForm.description"
              label="节点描述"
              rows="3"
            />
            <!-- 新增：关联课程多选 -->
            <v-select
              v-model="nodeForm.courseIds"
              :items="courseOptions"
              item-title="name"
              item-value="id"
              label="关联课程"
              multiple
              chips
              clearable
              class="mb-3"
            />
            <!-- 新增：关联视频多选 -->
            <v-select
              v-model="nodeForm.videoIds"
              :items="videoOptions"
              item-title="title"
              item-value="id"
              label="关联视频"
              multiple
              chips
              clearable
              class="mb-3"
            />
            <!-- 新增：关联文档多选 -->
            <v-select
              v-model="nodeForm.documentIds"
              :items="documentOptions"
              item-title="title"
              item-value="id"
              label="关联文档"
              multiple
              chips
              clearable
              class="mb-3"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showNodeDialog = false">取消</v-btn>
          <v-btn color="primary" @click="saveNode">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 视频选择对话框 -->
    <v-dialog v-model="showVideoDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          选择要跳转的视频
          <div class="text-caption text-medium-emphasis mt-1">
            以下视频中包含关于"{{ pendingKeyword }}"的内容
          </div>
        </v-card-title>
        <v-card-text class="pt-2">
          <v-radio-group v-model="selectedVideo" density="compact">
            <v-radio
              v-for="video in selectedNode?.relatedVideos"
              :key="video.id"
              :value="video"
              color="primary"
              class="mb-3"
            >
              <template v-slot:label>
                <div class="video-option">
                  <div class="text-subtitle-2 mb-1">{{ video.title }}</div>
                  <div class="text-caption text-medium-emphasis d-flex align-center flex-wrap">
                    <span class="d-flex align-center me-3">
                      <v-icon size="12" class="mr-1">mdi-school</v-icon>
                      {{ video.courseName }}
                    </span>
                    <span class="d-flex align-center me-3">
                      <v-icon size="12" class="mr-1">mdi-eye-outline</v-icon>
                      {{ video.viewCount || 0 }}次观看
                    </span>
                    <span class="d-flex align-center">
                      <v-icon size="12" class="mr-1">mdi-clock-outline</v-icon>
                      {{ formatDuration(video.duration) }}
                    </span>
                  </div>
                </div>
              </template>
            </v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            variant="text"
            @click="showVideoDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="handleVideoSelect(selectedVideo)"
            :disabled="!selectedVideo"
          >
            确定
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 添加关系对话框 -->
    <v-dialog v-model="showRelationDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">添加关系</v-card-title>
        <v-card-text>
          <v-form>
            <v-autocomplete
              v-model="relationForm.sourceKeywordId"
              :items="keywordOptions"
              item-title="label"
              item-value="value"
              label="源知识点"
              required
              clearable
              auto-select-first
            />
            <v-autocomplete
              v-model="relationForm.targetKeywordId"
              :items="keywordOptions"
              item-title="label"
              item-value="value"
              label="目标知识点"
              required
              clearable
              auto-select-first
            />
            <v-select
              v-model="relationForm.relationType"
              :items="relationTypesOptions"
              item-title="label"
              item-value="value"
              label="关系类型"
              required
            />
            <v-slider
              v-model="relationForm.strength"
              :min="0"
              :max="1"
              :step="0.1"
              label="关系强度"
              class="mt-4"
            />
            <v-textarea
              v-model="relationForm.description"
              label="关系描述"
              rows="2"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showRelationDialog = false">取消</v-btn>
          <v-btn color="primary" @click="addRelation">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除关系选择对话框 -->
    <v-dialog v-model="showDeleteRelationSelectDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">选择要删除的关系</v-card-title>
        <v-card-text>
          <v-form>
            <v-autocomplete
              v-model="deleteRelationForm.sourceKeywordId"
              :items="keywordOptions"
              item-title="label"
              item-value="value"
              label="源知识点"
              clearable
              auto-select-first
            />
            <v-autocomplete
              v-model="deleteRelationForm.targetKeywordId"
              :items="keywordOptions"
              item-title="label"
              item-value="value"
              label="目标知识点"
              clearable
              auto-select-first
            />
          </v-form>
          <div v-if="relationCandidates.length > 0" class="mt-4">
            <v-list>
              <v-list-item
                v-for="(rel, index) in relationCandidates"
                :key="index"
              >
                <v-list-item-title>
  {{ getRelationConfig(rel.relation_type).name }}
                  <v-chip
                    small
                    :color="getRelationConfig(rel.relation_type).color"
                    class="ml-2"
                  >
                    {{ rel.strength }}强度
                  </v-chip>
                </v-list-item-title>
                <template v-slot:append>
                  <v-btn
                    icon
                    color="error"
                    @click="deleteRelation(rel.id)"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </div>
          <div v-else-if="deleteRelationForm.sourceKeywordId && deleteRelationForm.targetKeywordId && relationCandidates.length === 0" class="mt-4">
            <v-alert
              type="info"
              variant="tonal"
              class="text-center pa-6"
              border="start"
              border-color="info"
            >
              <template v-slot:prepend>
                <v-icon size="large" color="info">mdi-graph-outline</v-icon>
              </template>
              <div class="text-h6 mb-2">暂无关系</div>
              <div class="text-body-2 text-medium-emphasis">
                "{{ keywordOptions.find(k => k.value === deleteRelationForm.sourceKeywordId)?.label }}" 与 "{{ keywordOptions.find(k => k.value === deleteRelationForm.targetKeywordId)?.label }}" 之间未找到任何关系
              </div>
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showDeleteRelationSelectDialog = false">取消</v-btn>
          <v-btn
            color="primary"
            @click="fetchRelations"
            :disabled="!deleteRelationForm.sourceKeywordId || !deleteRelationForm.targetKeywordId"
          >
            查询关系
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除节点确认对话框 -->
    <v-dialog v-model="deleteNodeDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6 pa-4">确认删除节点</v-card-title>
        <v-card-text class="pa-4">
          <p class="text-body-1 mb-4">
            确定要删除节点"{{ selectedNode?.name }}"?
          </p>
          <v-btn
            color="error"
            variant="outlined"
            @click="deleteNode"
            block
          >
            删除节点
          </v-btn>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteNodeDialog = false">取消</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <!-- 生成知识图谱配置对话框 -->
    <v-dialog v-model="showGenerateDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          <v-icon class="mr-2">mdi-graph</v-icon>
          生成知识图谱
        </v-card-title>
        <v-card-text class="pa-4">
          <v-form ref="generateForm">
            <v-row>
              <v-col cols="12">
                <v-switch
                  v-model="generateOptions.forceRegenerate"
                  label="强制重新生成"
                  color="warning"
                  hide-details
                >
                  <template v-slot:append>
                    <v-tooltip location="top">
                      <template v-slot:activator="{ props }">
                        <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                      </template>
                      <span>删除现有知识图谱数据，重新生成完整的知识图谱</span>
                    </v-tooltip>
                  </template>
                </v-switch>
              </v-col>
              <v-col cols="12">
                <v-switch
                  v-model="generateOptions.incremental"
                  label="增量模式"
                  color="primary"
                  hide-details
                  :disabled="generateOptions.forceRegenerate"
                >
                  <template v-slot:append>
                    <v-tooltip location="top">
                      <template v-slot:activator="{ props }">
                        <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                      </template>
                      <span>只处理新增的内容，保留已有的知识图谱数据。会自动处理孤立知识点。</span>
                    </v-tooltip>
                  </template>
                </v-switch>
              </v-col>
              <v-col cols="12" v-if="generateOptions.forceRegenerate">
                <v-alert type="warning" variant="outlined" class="mb-0">
                  <v-icon slot="prepend">mdi-alert</v-icon>
                  <strong>警告：</strong>强制重新生成将删除所有现有的知识图谱数据，包括手动添加的节点和关系。
                </v-alert>
              </v-col>
              <v-col cols="12" v-if="generateOptions.incremental && !generateOptions.forceRegenerate">
                <v-alert type="info" variant="outlined" class="mb-0">
                  <v-icon slot="prepend">mdi-information</v-icon>
                  增量模式将自动检测并处理孤立的知识点，建立新的关联关系。
                </v-alert>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="showGenerateDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            @click="confirmGenerateKnowledgeGraph"
            :loading="generateLoading"
          >
            开始生成
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 强制删除确认对话框 -->
<v-dialog v-model="showForceDeleteDialog" max-width="400">
  <v-card>
    <v-card-title class="text-h6 pa-4">强制删除节点</v-card-title>
    <v-card-text class="pa-4">
      <p class="text-body-1 mb-4">
        该节点存在关联关系，是否<strong class="text-error">强制删除</strong>？
      </p>
      <v-btn
        color="error"
        variant="outlined"
        @click="forceDeleteNode"
        block
      >
        强制删除
      </v-btn>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn text @click="showForceDeleteDialog = false">取消</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>

<!-- 删除关系确认对话框 -->
<v-dialog v-model="deleteRelationDialog" max-width="400">
  <v-card>
    <v-card-title class="text-h6 pa-4">确认删除关系</v-card-title>
    <v-card-text class="pa-4">
      <p class="text-body-1 mb-4" v-if="selectedEdgeInfo">
        确定要删除从 <strong>{{ selectedEdgeInfo.source }}</strong> 到 <strong>{{ selectedEdgeInfo.target }}</strong> 的关系吗？
      </p>
      <v-btn
        color="error"
        variant="outlined"
        @click="deleteRelation"
        block
      >
        删除关系
      </v-btn>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn text @click="deleteRelationDialog = false">取消</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
<v-dialog v-model="showKnowledgeDialog" max-width="800">
  <v-card>
    <v-card-title class="text-h6 pa-4">知识列表</v-card-title>
    <v-card-text>
      <Knowledge />
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn text @click="showKnowledgeDialog = false">关闭</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
  </v-container>
</template>



<script setup lang="ts">
const props = defineProps<{ courseId?: string }>()
import { ref, onMounted, watch, computed, nextTick, onBeforeUnmount } from 'vue'
import type { KnowledgeNode, LearningPath, SkillNode, GraphNode } from '../api/knowledgeMapService'
import knowledgeMapService from '../api/knowledgeMapService'
import type { Ref } from 'vue'
import courseService from '../api/courseService'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart, RadarChart } from 'echarts/charts'
import { useSnackbar } from '../stores/snackbarStore' // 使用项目内置消息通知
import { useTeacherRole } from '../composables/useAuth'
import KnowledgeList from '../views/KnowledgeList.vue'

// 详情页相关变量
const knowledgePoint = ref<any>(null)
const relatedVideos = ref<any[]>([])
const relatedDocuments = ref<any[]>([])
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
} from 'echarts/components'


const showKnowledgeDialog = ref(false)

// 类型定义
interface Course {
  id: string
  name: string
}

interface GraphLink {
  id: string
  source: string
  target: string
  type?: string
  label?: string
  relation_type?: string
  lineStyle?: {
    opacity?: number
    width?: number
  }
  strength?: number
  description?: string
}

// 节点类型颜色映射（与前端约定文档一致）
const CATEGORY_COLORS = {
  core_concept: '#ff6b6b',
  main_module: '#4ecdc4',
  specific_point: '#45b7d1'
}

// 获取节点类型颜色
function getNodeTypeColor(category: string) {
  // 如果category是数字，将其转换为对应的code
  if (!isNaN(Number(category))) {
    const mapping = [
      'core_concept',    // 0 - 一级知识点
      'main_module',     // 1 - 二级知识点
      'specific_point'   // 2 - 三级知识点
    ];
    const index = Number(category);
    if (index >= 0 && index < mapping.length) {
      category = mapping[index];
    }
  }
  
  return CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || '#cccccc'
}

// 获取节点类型名称
function getNodeTypeName(category: string) {
  // 如果category是数字，直接返回对应的中文名称
  if (!isNaN(Number(category))) {
    const mapping = [
      '一级知识点',    // 0
      '二级知识点',    // 1
      '三级知识点'     // 2
    ];
    const index = Number(category);
    if (index >= 0 && index < mapping.length) {
      return mapping[index];
    }
  }
  
  // 如果是字符串code，则查找对应的名称
  const cat = nodeCategories.value.find(c => c.code === category)
  return cat ? cat.name : category
}

// 注册 ECharts 组件
echarts.use([
  CanvasRenderer,
  GraphChart,
  RadarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent
])

// 初始化消息通知
const snackbar = useSnackbar()
const router = useRouter()
const route = useRoute()

// 使用组合式函数
const isTeacher = useTeacherRole()

onMounted(() => {
  // 其他 onMounted 逻辑...
})

// true 表示教师，false 表示普通用户
// 实际项目请替换为真实的用户角色判断

// 状态管理
const currentTab = ref('knowledge')
//const selectedCourse = ref('platform')

const selectedCourse = ref<string | null>(null)

// 监听 props.courseId 和 route.query.courseId，变化时同步 selectedCourse 并自动获取课程详情
watch(
  [() => props.courseId, () => route.query.courseId],
  async ([propsCourseId, queryCourseId]) => {
    // 优先使用 props.courseId，如果没有则使用 route.query.courseId
    const courseId = propsCourseId || (typeof queryCourseId === 'string' ? queryCourseId : null)
    if (courseId) {
      selectedCourse.value = courseId
      // 获取课程详情（用于视频选项）
      try {
        const res = await courseService.getCourseDetails(courseId)
        if (res?.data?.code === 200) {
          courseDetail.value = res.data.data
        } else {
          courseDetail.value = null
        }
      } catch {
        courseDetail.value = null
      }
    }
  },
  { immediate: true }
)
const selectedNode = ref<GraphNode | null>(null)
const nodeFilter = ref('')
const isImmersiveMode = ref(false)
const loading = ref({
  knowledge: false
})

// 生成知识图谱加载状态
const generateLoading = ref(false)

// 生成知识图谱配置对话框
const showGenerateDialog = ref(false)
const generateOptions = ref({
  forceRegenerate: false,
  incremental: true
})

// 图表实例
let knowledgeChart: echarts.ECharts | null = null
let immersiveChart: echarts.ECharts | null = null

// 课程数据
const courses = ref<Course[]>([])

// 图例配置
const nodeCategories = ref([
  { code: 'core_concept', name: '一级知识点', color: CATEGORY_COLORS.core_concept, icon: 'mdi-star' },
  { code: 'main_module', name: '二级知识点', color: CATEGORY_COLORS.main_module, icon: 'mdi-puzzle' },
  { code: 'specific_point', name: '三级知识点', color: CATEGORY_COLORS.specific_point, icon: 'mdi-lightbulb' }
])

const relationTypes = ref([
  { 
    type: 'prerequisite', 
    name: '前置关系', 
    color: '#e74c3c',
    lineStyle: 'solid'
  },
  { 
    type: 'related', 
    name: '相关关系', 
    color: '#3498db',
    lineStyle: 'dotted'
  },
  { 
    type: 'contains', 
    name: '包含关系', 
    color: '#2ecc71',
    lineStyle: 'solid'
  }
])

// 获取关系类型配置
function getRelationConfig(type: string) {
  return (
    relationTypes.value.find((r) => r.type === type) || {
      type: 'related',
      name: '相关关系',
      color: '#607D8B',
      lineStyle: 'dotted'
    }
  )
}



// 新增/编辑节点弹窗状态
const showNodeDialog = ref(false)
const isEditNode = ref(false)
interface NodeForm {
  id: string
  name: string
  category: string
  description: string
  courseIds?: string[]
  videoIds?: string[]
  documentIds?: string[] // 新增：关联文档
}
const nodeForm = ref<NodeForm>({
  id: '',
  name: '',
  category: '',
  description: '',
  courseIds: [],
  videoIds: [],
  documentIds: []
}) as Ref<NodeForm>

// 课程详情数据
const courseDetail = ref<any>(null)

// 存储所有选中课程的详情数据
const coursesDetail = ref<any[]>([])

// 监听节点表单中的课程选择，自动获取所有选中课程的详情
watch(
  () => nodeForm.value.courseIds,
  async (newVal) => {
    console.log('监听到课程变更:', newVal)
    if (Array.isArray(newVal) && newVal.length > 0) {
      try {
        // 获取所有选中课程的详情
        const detailsPromises = newVal.map(courseId => courseService.getCourseDetails(courseId))
        const responses = await Promise.all(detailsPromises)
        
        // 处理所有课程详情数据
        coursesDetail.value = responses
          .filter(res => res?.data?.code === 200)
          .map(res => res.data.data)
        
        // 打印每个课程的视频和文档信息
        coursesDetail.value.forEach((detail, index) => {
          console.log(`课程 ${newVal[index]} 的详情:`, detail)
          if (Array.isArray(detail.videos)) {
            console.log(`课程 ${newVal[index]} 的视频：`, detail.videos)
          }
          if (Array.isArray(detail.documents)) {
            console.log(`课程 ${newVal[index]} 的文档：`, detail.documents)
          } else {
            console.warn(`课程 ${newVal[index]} 的文档数据不是数组或不存在：`, detail.documents)
          }
        })
      } catch (error) {
        console.error('获取课程详情失败:', error)
        coursesDetail.value = []
      }
    } else {
      coursesDetail.value = []
    }
  },
  { immediate: true }
)

// 关联视频选项：从所有选中课程的 videos 字段提取
const videoOptions = computed(() => {
  const allVideos: { id: string; title: string }[] = []
  coursesDetail.value.forEach(detail => {
    if (detail && Array.isArray(detail.videos)) {
      detail.videos.forEach((video: any) => {
        // 避免重复添加相同的视频
        if (!allVideos.some(v => v.id === video.id)) {
          allVideos.push({
            id: video.id,
            title: `${video.title} (${detail.name})`  // 添加课程名称以区分
          })
        }
      })
    }
  })
  return allVideos
})

// 关联文档选项：从所有选中课程的 documents 字段提取
const documentOptions = computed(() => {
  const allDocuments: { id: string; title: string }[] = []
  coursesDetail.value.forEach(detail => {
    if (detail && Array.isArray(detail.documents)) {
      detail.documents.forEach((doc: any) => {
        // 避免重复添加相同的文档
        if (!allDocuments.some(d => d.id === doc.id)) {
          allDocuments.push({
            id: doc.id,
            title: `${doc.title} (${detail.name})`  // 添加课程名称以区分
          })
        }
      })
    }
  })
  return allDocuments
})

// 保存节点加载状态
const saveNodeLoading = ref(false)

// 打开添加节点弹窗
const addNode = async () => {
  isEditNode.value = false
  nodeForm.value = {
    id: '',
    name: '',
    category: '',
    description: '',
    // 默认选择当前课程
    courseIds: selectedCourse.value && selectedCourse.value !== 'platform' ? [selectedCourse.value] : undefined,
    videoIds: undefined,
    documentIds: undefined
  }
  showNodeDialog.value = true
}

// 打开编辑节点弹窗
const editNode = async (node: any) => {
  isEditNode.value = true
  // 如果在详情页中，使用详情页已获取的节点信息
  if (route.name === 'KnowledgePointDetail' && knowledgePoint.value?.id === node.id) {
    nodeForm.value = {
      id: knowledgePoint.value.id,
      name: knowledgePoint.value.name,
      category: String(knowledgePoint.value.category),
      description: knowledgePoint.value.description,
      courseIds: selectedCourse.value && selectedCourse.value !== 'platform' ? [selectedCourse.value] : [],
      videoIds: relatedVideos.value?.map((video: any) => video.id) || [],
      documentIds: relatedDocuments.value?.map((doc: any) => doc.id) || []
    }
  } else {
    // 否则使用传入的节点基本信息
    nodeForm.value = {
      id: node.id,
      name: node.name,
      category: String(node.category),
      description: node.description,
      courseIds: selectedCourse.value && selectedCourse.value !== 'platform' ? [selectedCourse.value] : [],
      videoIds: node.relatedVideos?.map((video: any) => video.id) || [],
      documentIds: node.relatedDocuments?.map((doc: any) => doc.id) || []
    }
  }
  showNodeDialog.value = true
}

// 保存节点（新增或编辑）
const saveNode = async () => {
  if (saveNodeLoading.value) return
  try {
    // 表单验证
    if (!nodeForm.value.name?.trim()) {
      snackbar.show({ text: '请填写知识点名称', color: 'error' })
      return
    }
    // 只在新增节点时检查category是否为空
    if (!isEditNode.value && !nodeForm.value.category) {
      snackbar.show({ text: '请选择知识点分类', color: 'error' })
      return
    }
    if (!nodeForm.value.courseIds?.length) {
      snackbar.show({ text: '请选择关联课程', color: 'error' })
      return
    }

    saveNodeLoading.value = true
    console.log('保存节点，表单数据：', nodeForm.value)

    const payload = {
      name: nodeForm.value.name.trim(),
      category: nodeForm.value.category, // 直接使用选中的值
      description: nodeForm.value.description?.trim() || '',
      courseIds: nodeForm.value.courseIds || [],
      videoIds: nodeForm.value.videoIds || [],
      documentIds: nodeForm.value.documentIds || []
    }
    
    // 确保category字段在编辑模式下有值
    if (isEditNode.value && !payload.category) {
      // 从原始节点数据中获取category
      const originalNode = actualGraphData.value.nodes.find((n: any) => n.id === nodeForm.value.id)
      if (originalNode) {
        payload.category = normalizeCategory(originalNode.category)
      }
    }
    
    // 确保category是字符串类型
    if (payload.category && typeof payload.category !== 'string') {
      payload.category = String(payload.category)
    }
    
    console.log('保存节点，处理后的数据：', payload)
    
    let res;
    if (isEditNode.value) {
      // 编辑节点
      console.log(`开始更新节点 ${nodeForm.value.id}`)
      res = await knowledgeMapService.updateKeyword(nodeForm.value.id, payload)
      console.log('节点更新响应：', res)
    } else {
      // 新增节点
      console.log('开始创建新节点')
      res = await knowledgeMapService.createKeyword(payload)
      console.log('节点创建响应：', res)
    }

    // 检查响应结构，兼容不同的成功响应格式
    // 如果响应包含数据且没有明确的错误码，则认为成功
    const isSuccess = res?.data?.code === 200 || res?.status === 200 || res?.data?.success === true || 
                     (res?.data && typeof res.data === 'object' && res.data.keyword && !res.data.error) ||
                     (res && typeof res === 'object' && res.keyword && !res.error && !res.code)
    
    console.log('响应成功判断:', {
      hasCode200: res?.data?.code === 200,
      hasStatus200: res?.status === 200,
      hasSuccess: res?.data?.success === true,
      hasKeywordData: res?.data && typeof res.data === 'object' && res.data.keyword && !res.data.error,
      hasDirectKeywordData: res && typeof res === 'object' && res.keyword && !res.error && !res.code,
      finalResult: isSuccess,
      responseData: res?.data,
      directResponse: res
    })
    
    if (isSuccess) {
      snackbar.show({ 
        text: isEditNode.value ? '节点更新成功' : '节点添加成功', 
        color: 'success' 
      })
      showNodeDialog.value = false
      console.log(selectedCourse.value);
      // 重新加载图谱并在加载后打印
      if (selectedCourse.value === 'platform') {
        console.log('开始重新加载平台知识图谱')
        await fetchPlatformKnowledgeGraph()
        nextTick(() => {
          console.log('平台知识图谱加载成功：', actualGraphData.value)
        })
      } else if (selectedCourse.value) {
        console.log(`开始重新加载课程 ${selectedCourse.value} 的知识图谱`)
        await fetchCourseKnowledgeGraph(selectedCourse.value)
        nextTick(() => {
          console.log('课程知识图谱加载成功：', actualGraphData.value)
        })
      }
    } else {
      const errorMsg = res?.data?.msg || (isEditNode.value ? '节点更新失败' : '节点添加失败')
      console.error('保存节点失败：', errorMsg, res)
      snackbar.show({ 
        text: errorMsg, 
        color: 'error' 
      })
    }
  } catch (err: any) {
    if (err?.response?.data?.code === 409) {
      // 处理知识点已存在的情况
      const existingKeyword = err?.response?.data?.data?.existing_keyword
      const hint = err?.response?.data?.data?.hint
      snackbar.show({ 
        text: `${err?.response?.data?.msg}${hint ? `，${hint}` : ''}`, 
        color: 'warning' 
      })
    } else {
      snackbar.show({ 
        text: err?.response?.data?.msg || err?.message || '操作失败', 
        color: 'error' 
      })
    }
  } finally {
    saveNodeLoading.value = false
  }
}

// 获取课程列表
const fetchCourses = async () => {
  try {
    const response = await courseService.getCourses()
    if (response.data.code === 200) {
      courses.value = response.data.data.list.map((course: any) => ({
        id: course.id,
        name: course.name
      }))
      
      if (courses.value.length > 0 && !selectedCourse.value) {
        selectedCourse.value = courses.value[0].id
      }
    } else {
      console.error('获取课程列表失败:', response.data.msg)
    }
  } catch (error) {
    console.error('获取课程列表出错:', error)
    // 如果API失败，使用示例数据作为fallback
    courses.value = [
      { id: '1', name: '计算机网络'
        
       },
      { id: '2', name: '操作系统' },
      { id: '3', name: '数据结构' }
    ]
  }
}

// 计算属性：课程选项（包含平台图谱选项）
const courseOptions = computed(() => {
  const options = [...courses.value]
  options.unshift({ id: 'platform', name: '平台知识图谱（所有课程）' })
  return options
})

// 沉浸模式控制
const enterImmersiveMode = () => {
  isImmersiveMode.value = true
  nextTick(() => {
    initImmersiveChart()
  })
}

const exitImmersiveMode = () => {
  isImmersiveMode.value = false
  if (immersiveChart) {
    immersiveChart.dispose()
    immersiveChart = null
  }
}

const toggleImmersiveMode = () => {
  if (isImmersiveMode.value) {
    exitImmersiveMode()
  } else {
    enterImmersiveMode()
  }
}

// 查看平台知识图谱
const viewPlatformGraph = () => {
  selectedCourse.value = 'platform'
}

// 返回课程图谱
const backToCourseGraph = () => {
  if (courses.value.length > 0) {
    selectedCourse.value = courses.value[0].id
  }
}

// category 兼容映射函数：数字转 code，字符串 code 保持不变
function normalizeCategory(category: string | number): string {
  if (typeof category === 'string') {
    // 兼容后端返回中文名的情况
    if (category === '一级知识点') return 'core_concept';
    if (category === '二级知识点') return 'main_module';
    if (category === '三级知识点') return 'specific_point';
    return category;
  }
  // 兼容数字类型（如 0/1/2）
  const mapping = [
    'core_concept',    // 0 - 一级知识点
    'main_module',     // 1 - 二级知识点
    'specific_point'   // 2 - 三级知识点
  ];
  if (typeof category === 'number' && mapping[category]) {
    return mapping[category];
  }
  return 'core_concept'; // 默认
}

// 新增：统一后端返回的图谱数据结构，确保 category 字段为 code 字符串
function normalizeGraphData(graphData: any) {
  if (!graphData) return graphData;
  return {
    ...graphData,
    nodes: (graphData.nodes || []).map((node: any) => ({
      ...node,
      category: normalizeCategory(node.category)
    })),
    links: (graphData.links || []).map((link: any) => ({
      ...link
    }))
  };
}

// 获取课程知识图谱数据
const fetchCourseKnowledgeGraph = async (courseId: string) => {
  if (!courseId || courseId === 'platform') return
  loading.value.knowledge = true
  try {
    const response = await knowledgeMapService.getCourseKnowledgeGraph(courseId)
    if (response.data.code === 200) {
      let graphData = response.data.data
      console.log('后端返回的知识图谱数据:', graphData)
      if (graphData && graphData.nodes && graphData.links && graphData.nodes.length > 0) {
        graphData = normalizeGraphData(graphData)
        actualGraphData.value = graphData
        nextTick(() => {
          initKnowledgeChart()
        })
      } else {
        console.warn('课程知识图谱数据为空，使用示例数据')
        actualGraphData.value = null
        nextTick(() => {
          initKnowledgeChart()
        })
      }
    } else {
      throw new Error(response.data.msg || '获取课程知识图谱失败')
    }
  } catch (error: any) {
    console.error('获取课程知识图谱失败:', error)
    // 如果API失败，使用示例数据作为fallback
    actualGraphData.value = null
    nextTick(() => {
      initKnowledgeChart()
    })
  } finally {
    loading.value.knowledge = false
  }
}

const fetchPlatformKnowledgeGraph = async () => {
  loading.value.knowledge = true
  try {
    const response = await knowledgeMapService.getPlatformKnowledgeGraph()
    if (response.data.code === 200) {
      let graphData = response.data.data
      if (graphData && graphData.nodes && graphData.links && graphData.nodes.length > 0) {
        graphData = normalizeGraphData(graphData)
        actualGraphData.value = graphData
        nextTick(() => {
          initKnowledgeChart()
        })
      } else {
        console.warn('平台知识图谱数据为空，使用示例数据')
        actualGraphData.value = null
        nextTick(() => {
          initKnowledgeChart()
        })
      }
    } else {
      throw new Error(response.data.msg || '获取平台知识图谱失败')
    }
  } catch (error: any) {
    console.error('获取平台知识图谱失败:', error)
    // 如果API失败，使用示例数据作为fallback
    actualGraphData.value = null
    nextTick(() => {
      initKnowledgeChart()
    })
  } finally {
    loading.value.knowledge = false
  }
}

// 示例数据（作为fallback）
const sampleGraphData = {
  nodes: [
    { id: '1', name: '计算机网络', symbolSize: 60, category: 'core_concept', description: '计算机网络的基础概念和原理' },
    { id: '2', name: 'TCP/IP协议', symbolSize: 50, category: 'main_module', description: 'TCP/IP协议栈详解' },
    { id: '3', name: '网络安全', symbolSize: 50, category: 'main_module', description: '网络安全基础知识' },
    { id: '4', name: 'HTTP协议', symbolSize: 45, category: 'specific_point', description: 'HTTP协议详解' },
    { id: '5', name: 'TCP协议', symbolSize: 45, category: 'specific_point', description: 'TCP协议机制' },
    { id: '6', name: 'IP协议', symbolSize: 45, category: 'specific_point', description: 'IP协议原理' },
    { id: '7', name: '加密算法', symbolSize: 45, category: 'specific_point', description: '常用加密算法' },
    { id: '8', name: '防火墙', symbolSize: 45, category: 'specific_point', description: '防火墙技术与应用' },
    { id: '9', name: 'SSL/TLS', symbolSize: 40, category: 'specific_point', description: 'SSL/TLS安全协议' },
    { id: '10', name: '网络编程', symbolSize: 40, category: 'specific_point', description: 'Socket网络编程' }
  ],
  links: [
    { source: '1', target: '2', type: 'prerequisite' },
    { source: '1', target: '3', type: 'prerequisite' },
    { source: '2', target: '4', type: 'dependency' },
    { source: '2', target: '5', type: 'composition' },
    { source: '2', target: '6', type: 'composition' },
    { source: '3', target: '7', type: 'dependency' },
    { source: '3', target: '8', type: 'association' },
    { source: '7', target: '9', type: 'prerequisite' },
    { source: '2', target: '10', type: 'prerequisite' },
    { source: '4', target: '9', type: 'association' }
  ]
}

// 实际的图谱数据
const actualGraphData = ref<any>(null)

const filteredGraphData = computed(() => {
  const sourceData = actualGraphData.value || sampleGraphData

  if (!nodeFilter.value || nodeFilter.value.trim() === '') {
    // 没有搜索时全部为普通节点
    return {
      nodes: sourceData.nodes.map((node: any) => ({ ...node, highlight: false })),
      links: sourceData.links
    }
  }

  const searchTerm = nodeFilter.value.toLowerCase().trim()

  // 直接命中的节点
  const matchedNodes = sourceData.nodes.filter((node: any) =>
    node.name.toLowerCase().includes(searchTerm)
  )
  if (matchedNodes.length === 0) {
    return { nodes: [], links: [] }
  }

  const matchedNodeIds = new Set(matchedNodes.map((node: any) => node.id))
  const relatedNodeIds = new Set(matchedNodeIds)

  sourceData.links.forEach((link: any) => {
    if (matchedNodeIds.has(link.source)) {
      relatedNodeIds.add(link.target)
    }
    if (matchedNodeIds.has(link.target)) {
      relatedNodeIds.add(link.source)
    }
  })

  // 标记节点类型
  const filteredNodes = sourceData.nodes
    .filter((node: any) => relatedNodeIds.has(node.id))
    .map((node: any) => ({
      ...node,
      highlight: matchedNodeIds.has(node.id) ? true : false
    }))

  const filteredLinks = sourceData.links.filter(
    (link: any) => relatedNodeIds.has(link.source) && relatedNodeIds.has(link.target)
  )

  return {
    nodes: filteredNodes,
    links: filteredLinks
  }
})

// 获取图表配置
const getChartOption = (data: any) => {
  return {
    title: {
      text: selectedCourse.value === 'platform' ? '平台知识图谱' : '课程知识图谱',
      left: 'center',
      top: 20,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#6f23d1'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params: any) {
        if (params.dataType === 'node') {
          const node = params.data
          return `
            <div style="padding: 10px; background-color: rgba(0,0,0,0.8); color: white; border-radius: 4px;">
              <strong>${node.name}</strong><br/>
              <span style="color: ${getNodeTypeColor(node.category)};">
                ${getNodeTypeName(node.category)}
              </span><br/>
              ${node.description || '暂无描述'}
            </div>
          `
        } else if (params.dataType === 'edge') {
          const link = params.data
          const relationConfig = getRelationConfig(link.relation_type || 'association')
          return `
            <div style="padding: 10px; background-color: rgba(0,0,0,0.8); color: white; border-radius: 4px;">
              <strong>关系类型：</strong>${relationConfig.name}<br/>
              <strong>源节点：</strong>${link.source}<br/>
              <strong>目标节点：</strong>${link.target}
            </div>
          `
        }
        return ''
      }
    },
    legend: [{
      data: nodeCategories.value.map(cat => getNodeTypeName(cat.code)),
      orient: 'horizontal',
      left: 'center',
      bottom: 20,
      textStyle: {
        fontSize: 12
      }
    }],
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quintInOut' as any,
    series: [{
      type: 'graph',
      layout: 'force',
      data: data.nodes.map((node: GraphNode & { highlight?: boolean }) => {
        const baseColor = getNodeTypeColor(String(node.category))
        const isFiltering = !!nodeFilter.value && nodeFilter.value.trim() !== ''
        const color = isFiltering
          ? (node.highlight
              ? baseColor
              : baseColor + (baseColor.length === 7 ? '33' : ''))
          : baseColor
        return {
          ...node,
          itemStyle: {
            color: color
          },
          label: {
            show: true,
            position: 'bottom',
            fontSize: 12,
            fontWeight: node.highlight ? 'bold' : 'normal',
            color: isImmersiveMode.value ? '#ffffff' : '#333333'
          },
          category: getNodeTypeName(String(node.category))
        }
      }),
      links: data.links.map((link: GraphLink) => {
        const relationConfig = getRelationConfig(link.relation_type || 'association')
        return {
          ...link,
          lineStyle: {
            color: relationConfig.color,
            width: 2,
            type: relationConfig.lineStyle === 'dashed' ? 'dashed' :
                  relationConfig.lineStyle === 'dotted' ? 'dotted' : 'solid'
          },
          label: {
            show: false
          }
        }
      }),
      categories: nodeCategories.value.map(cat => ({
        name: getNodeTypeName(cat.code),
        itemStyle: {
          color: cat.color
        }
      })),
      roam: true,
      focusNodeAdjacency: true,
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1,
        shadowBlur: 10,
        shadowColor: 'rgba(0, 0, 0, 0.3)'
      },
      label: {
        position: 'bottom',
        formatter: '{b}'
      },
      lineStyle: {
        color: 'source',
        curveness: 0.3
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      force: {
        repulsion: 2000,
        gravity: 0.1,
        edgeLength: [50, 200],
        layoutAnimation: true
      }
    }]
  }
}

// 修改图表初始化中的事件绑定
const initChartEvents = (chart: echarts.ECharts) => {
  chart.on('click', function(params: any) {
    if (params.dataType === 'node') {
      handleNodeSelect(params.data)
    } else if (params.dataType === 'edge') {
      handleEdgeSelect(params.data)
    }
  })
}

// 修改初始化函数
const initKnowledgeChart = async () => {
  await nextTick()
  const chartDom = document.getElementById('knowledge-graph-container')
  if (!chartDom) {
    console.warn('知识图谱容器元素不存在')
    return
  }
  chartDom.style.width = '100%'
  chartDom.style.height = '600px'
  chartDom.style.display = 'block'
  if (knowledgeChart) {
    knowledgeChart.dispose()
  }
  knowledgeChart = echarts.init(chartDom)
  const option = getChartOption(filteredGraphData.value)
  knowledgeChart.setOption(option, true)
  initChartEvents(knowledgeChart)
  // 先移除旧的 resizeHandler
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  resizeHandler = () => {
    if (knowledgeChart) {
      knowledgeChart.resize()
    }
  }
  window.addEventListener('resize', resizeHandler)
}

// 初始化沉浸模式图谱
const initImmersiveChart = async () => {
  await nextTick()
  const chartDom = document.getElementById('immersive-graph-container')
  if (!chartDom) {
    console.warn('沉浸模式图谱容器元素不存在')
    return
  }
  if (immersiveChart) {
    immersiveChart.dispose()
  }
  immersiveChart = echarts.init(chartDom)
  const option = {
    ...getChartOption(filteredGraphData.value),
    backgroundColor: 'transparent',
    title: {
      ...getChartOption(filteredGraphData.value).title,
      textStyle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#ffffff'
      }
    },
    legend: [{
      ...getChartOption(filteredGraphData.value).legend[0],
      textStyle: {
        fontSize: 14,
        color: '#ffffff'
      }
    }]
  }
  immersiveChart.setOption(option, true)
  initChartEvents(immersiveChart)
  // 先移除旧的 resizeHandler
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
  resizeHandler = () => {
    if (immersiveChart) {
      immersiveChart.resize()
    }
  }
  window.addEventListener('resize', resizeHandler)
}



// 监听器和清理函数
let resizeHandler: (() => void) | null = null

// 监听器
watch(nodeFilter, () => {
  if (knowledgeChart) {
    const option = getChartOption(filteredGraphData.value)
    knowledgeChart.setOption(option, true)
  }
  if (immersiveChart) {
    const option = {
      ...getChartOption(filteredGraphData.value),
      backgroundColor: 'transparent',
      title: {
        ...getChartOption(filteredGraphData.value).title,
        textStyle: {
          fontSize: 20,
          fontWeight: 'bold',
          color: '#ffffff'
        }
      },
      legend: [{
        ...getChartOption(filteredGraphData.value).legend[0],
        textStyle: {
          fontSize: 14,
          color: '#ffffff'
        }
      }]
    }
    immersiveChart.setOption(option, true)
  }
})

watch(selectedCourse, async (newValue) => {
  if (newValue) {
    if (newValue === 'platform') {
      // 获取平台知识图谱
      await fetchPlatformKnowledgeGraph()
    } else {
      // 获取特定课程的知识图谱
      await fetchCourseKnowledgeGraph(newValue)
    }
  } else {
    // 没有选择课程时清空数据
    actualGraphData.value = null
    loading.value.knowledge = false
  }
})

watch(currentTab, (newTab) => {
  if (newTab === 'knowledge') {
    nextTick(() => {
      initKnowledgeChart()
    })
  }
})

// 从路由参数初始化搜索
const initializeSearchFromRoute = () => {
  const searchParam = route.query.search
  if (searchParam && typeof searchParam === 'string') {
    nodeFilter.value = searchParam
  }
}

// 生命周期
onMounted(async () => {
  await fetchCourses()
  
  // 从路由参数初始化搜索
  initializeSearchFromRoute()
  
  // 初始化当前标签页对应的图表
  if (currentTab.value === 'knowledge') {
    // 根据默认选择的课程加载知识图谱数据
    if (selectedCourse.value === 'platform') {
      await fetchPlatformKnowledgeGraph()
    } else if (selectedCourse.value) {
      await fetchCourseKnowledgeGraph(selectedCourse.value)
    } else {
      // 如果没有选择课程，显示空状态
      loading.value.knowledge = false
      nextTick(() => {
        initKnowledgeChart()
      })
    }
  }
})

onBeforeUnmount(() => {
  if (knowledgeChart) {
    knowledgeChart.dispose()
  }
  if (immersiveChart) {
    immersiveChart.dispose()
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})

// router已在上面定义

// 跳转到视频页面
const jumpToVideo = (videoId: string, courseId: string) => {
  router.push(`/course/${courseId}/video/${videoId}`)
}

// 跳转到文档页面
const jumpToDocument = (documentId: string, courseId: string) => {
  router.push(`/course/${courseId}/document/${documentId}`)
}

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 获取知识点相关资源（视频+文档）
const fetchKeywordResources = async (keywordId: string) => {
  try {
    const response = await knowledgeMapService.getKeywordRelatedResources(keywordId)
    if (response.data.code === 200) {
      const keywordData = response.data.data
      if (selectedNode.value) {
        selectedNode.value = {
          ...selectedNode.value,
          relatedVideos: keywordData.videos.map((video: any) => ({
            id: video.id,
            title: video.title,
            courseName: video.course.name,
            courseId: video.course.id,
            viewCount: video.view_count,
            duration: video.duration,
            type: 'video'
          })),
          relatedDocuments: keywordData.documents.map((document: any) => ({
            id: document.id,
            title: document.title,
            courseName: document.course.name,
            courseId: document.course.id,
            fileType: document.file_type,
            fileSize: document.file_size,
            uploadTime: document.upload_time,
            type: 'document'
          })),
          allResources: keywordData.resources.map((resource: any) => ({
            id: resource.id,
            title: resource.title,
            courseName: resource.course.name,
            courseId: resource.course.id,
            type: resource.type,
            weight: resource.weight,
            ...(resource.type === 'video' ? {
              viewCount: resource.view_count,
              duration: resource.duration,
              coverUrl: resource.cover_url
            } : {
              fileType: resource.file_type,
              fileSize: resource.file_size,
              uploadTime: resource.upload_time
            })
          }))
        }
      }
    }
  } catch (error) {
    console.error('获取知识点相关资源失败:', error)
    if (selectedNode.value) {
      selectedNode.value.relatedVideos = []
      selectedNode.value.relatedDocuments = []
      selectedNode.value.allResources = []
    }
  }
}

// 添加 selectedEdgeInfo 状态
const selectedEdgeInfo = ref<GraphLink | null>(null)

// 修改图表点击事件处理
const handleNodeSelect = async (node: any) => {
  // 如果点击的是当前选中的节点，则取消选中
  if (selectedNode.value && selectedNode.value.id === node.id) {
    selectedNode.value = null
    return
  }
  
  selectedNode.value = node
  selectedEdgeInfo.value = null  // 清空边的信息
  if (node && node.id) {
    await fetchKeywordResources(node.id)
  }
  
  // 自动滚动到详情区域
  await nextTick()
  // 等待DOM更新完成后再滚动
  setTimeout(() => {
    const detailElement = document.getElementById('node-detail-card')
    if (detailElement) {
      detailElement.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start',
        inline: 'nearest'
      })
    }
  }, 100)
}

// 添加边的点击事件处理
const handleEdgeSelect = (edge: any) => {
  selectedEdgeInfo.value = edge
  selectedNode.value = null  // 清空节点信息
}

// 添加时间格式化函数
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 添加计算属性：节点特点
const nodeFeatures = computed(() => {
  if (!selectedNode.value || !actualGraphData.value) return []
  
  const features: Array<{ type: string; description: string }> = []
  
  // 遍历所有边
  actualGraphData.value.links.forEach((link: GraphLink) => {
    // 如果当前节点是源节点或目标节点
    if (link.source === selectedNode.value?.id || link.target === selectedNode.value?.id) {
      // 确保有描述
      if (link.description) {
        features.push({
          type: link.relation_type || 'related',
          description: link.description
        })
      }
    }
  })
  
  return features
})

// 在script部分添加视频选择对话框相关的状态
const showVideoDialog = ref(false)
const selectedVideo = ref<any>(null)
const pendingKeyword = ref<any>(null)

// 修改askAI函数
const askAI = (node: any) => {
  if (!node || !node.relatedVideos?.length) return
  
  // 如果只有一个相关视频，直接跳转
  if (node.relatedVideos.length === 1) {
    const video = node.relatedVideos[0]
    router.push({
      path: `/course/${video.courseId}/video/${video.id}`,
      query: {
        askAI: 'true',
        keyword: node.name
      }
    })
  } else {
    // 如果有多个相关视频，显示选择对话框
    pendingKeyword.value = node.name
    showVideoDialog.value = true
  }
}

// 添加处理视频选择的函数
const handleVideoSelect = (video: any) => {
  showVideoDialog.value = false
  if (video && pendingKeyword.value) {
    router.push({
      path: `/course/${video.courseId}/video/${video.id}`,
      query: {
        askAI: 'true',
        keyword: pendingKeyword.value
      }
    })
  }
  // 清空状态
  selectedVideo.value = null
  pendingKeyword.value = null
}

// 在 script setup 部分添加状态和方法
const showRelationDialog = ref(false)
// 删除关系弹窗状态
const showDeleteRelationSelectDialog = ref(false)
const deleteRelationDialog = ref(false)
const deleteRelationForm = ref({
  sourceKeywordId: '',
  targetKeywordId: ''
})
const relationCandidates = ref<Array<any>>([])
const relationForm = ref({
  sourceKeywordId: '',
  targetKeywordId: '',
  relationType: 'prerequisite',
  strength: 1,
  description: ''
})
const relationTypesOptions = [
  { value: 'prerequisite', label: '前置关系' },
  { value: 'related', label: '相关关系' },
  { value: 'contains', label: '包含关系' }
]
// 知识点下拉选项
const keywordOptions = computed(() => {
  const nodes = (actualGraphData.value?.nodes || sampleGraphData.nodes) as any[]
  return nodes.map(n => ({ label: n.name, value: n.id }))
})

const addRelation = async () => {
  if (!relationForm.value.sourceKeywordId || !relationForm.value.targetKeywordId || !relationForm.value.relationType) {
          snackbar.show({ text: '请完整填写关系信息', color: 'error' })
    return
  }
  try {
    // 添加关系前，强制刷新一次知识图谱，确保所有节点都已同步到后端
    if (actualGraphData.value) {
      if (selectedCourse.value === 'platform') {
        await fetchPlatformKnowledgeGraph()
        console.log('[前]课程知识图谱 nodes:', actualGraphData.value?.nodes)
      }
    }
    await knowledgeMapService.createRelation({
      sourceKeywordId: relationForm.value.sourceKeywordId,
      targetKeywordId: relationForm.value.targetKeywordId,
      relationType: relationForm.value.relationType,
      strength: relationForm.value.strength,
      description: relationForm.value.description
    })
            snackbar.show({ text: '关系添加成功', color: 'success' })
    showRelationDialog.value = false
    // 添加关系后再刷新一次，确保关系及时展示
    if (selectedCourse.value === 'platform') {
      await fetchPlatformKnowledgeGraph()
      // 打印平台知识图谱 nodes
      console.log('[后]平台知识图谱 nodes:', actualGraphData.value?.nodes)
    } else {
      await fetchCourseKnowledgeGraph(selectedCourse.value!)
      // 打印课程知识图谱 nodes
      console.log('[后]课程知识图谱 nodes:', actualGraphData.value?.nodes)
    }
    // 重置表单
    relationForm.value = {
      sourceKeywordId: '',
      targetKeywordId: '',
      relationType: 'prerequisite',
      strength: 1,
      description: ''
    }
  } catch (e: any) {
          snackbar.show({ text: e?.message || '添加关系失败', color: 'error' })
  }
}

// 确认生成知识图谱方法
const confirmGenerateKnowledgeGraph = async () => {
  if (!selectedCourse.value || selectedCourse.value === 'platform') {
    snackbar.show({ text: '请选择具体的课程来生成知识图谱', color: 'warning' })
    return
  }

  try {
    generateLoading.value = true
    showGenerateDialog.value = false
    
    const response = await knowledgeMapService.generateKnowledgeGraph({
      courseId: selectedCourse.value,
      forceRegenerate: generateOptions.value.forceRegenerate,
      incremental: generateOptions.value.incremental
    })

    if (response.data.code === 200) {
      const modeText = generateOptions.value.forceRegenerate ? '强制重新生成' : 
                      generateOptions.value.incremental ? '增量生成' : '完整生成'
      snackbar.show({ 
        text: `知识图谱${modeText}任务已启动，请稍后刷新查看结果`, 
        color: 'success' 
      })
      
      // 可选：轮询任务状态
      const taskId = response.data.data.taskId
      if (taskId) {
        pollTaskStatus(taskId)
      }
    } else {
      snackbar.show({ 
        text: response.data.msg || '生成知识图谱失败', 
        color: 'error' 
      })
    }
  } catch (error: any) {
    console.error('生成知识图谱错误:', error)
    snackbar.show({ 
      text: error?.response?.data?.msg || error?.message || '生成知识图谱失败', 
      color: 'error' 
    })
  } finally {
    generateLoading.value = false
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: string) => {
  const maxAttempts = 30 // 最多轮询30次
  let attempts = 0
  
  const poll = async () => {
    try {
      attempts++
      const response = await knowledgeMapService.getTaskStatus(taskId)
      
      if (response.data.code === 200) {
        const task = response.data.data
        
        if (task.status === 'completed') {
          snackbar.show({ 
            text: '知识图谱生成完成！正在刷新数据...', 
            color: 'success' 
          })
          // 重新加载知识图谱数据
          if (selectedCourse.value) {
            await fetchCourseKnowledgeGraph(selectedCourse.value)
          }
          return
        } else if (task.status === 'failed') {
          snackbar.show({ 
            text: `知识图谱生成失败: ${task.error_message || '未知错误'}`, 
            color: 'error' 
          })
          return
        } else if (task.status === 'processing' && attempts < maxAttempts) {
          // 继续轮询
          setTimeout(poll, 2000) // 2秒后再次检查
        } else if (attempts >= maxAttempts) {
          snackbar.show({ 
            text: '任务状态检查超时，请手动刷新页面查看结果', 
            color: 'warning' 
          })
        }
      }
    } catch (error) {
      console.error('轮询任务状态错误:', error)
      if (attempts < maxAttempts) {
        setTimeout(poll, 2000)
      }
    }
  }
  
  // 开始轮询
  setTimeout(poll, 2000)
}

// 删除节点弹窗状态
const deleteNodeDialog = ref(false)
// 强制删除节点弹窗状态
const showForceDeleteDialog = ref(false)
// 删除关系弹窗状态已在前面声明

// 删除节点方法
const deleteNode = async () => {
  if (!selectedNode.value) return
  const courseId = selectedCourse.value && selectedCourse.value !== 'platform' ? selectedCourse.value : undefined
  try {
    let res = await knowledgeMapService.deleteKeyword(selectedNode.value.id, { courseId })
    if (res?.data?.code === 200) {
      snackbar.show({ text: '节点删除成功', color: 'success' })
      deleteNodeDialog.value = false
      selectedNode.value = null
      selectedEdgeInfo.value = null  // 重置边的信息
      if (selectedCourse.value === 'platform') {
        await fetchPlatformKnowledgeGraph()
      } else if (selectedCourse.value) {
               await fetchCourseKnowledgeGraph(selectedCourse.value)
      }
    } else {
              snackbar.show({ text: res?.data?.msg || '删除失败', color: 'error' })
    }
  } catch (err: any) {
    // 409 冲突，强制删除
    if (err?.response?.data?.code =='409' ) {
  showForceDeleteDialog.value = true
}else {
      snackbar.show({ text: err?.response?.data?.msg || err?.message || '删除失败', color: 'error' })
    }
  }
}

// 强制删除确认
const forceDeleteNode = async () => {
  if (!selectedNode.value) return
  
  showForceDeleteDialog.value = false
  const courseId = selectedCourse.value && selectedCourse.value !== 'platform' ? selectedCourse.value : undefined
  let res = await knowledgeMapService.deleteKeyword(selectedNode.value.id, { courseId, force: true })
  if (res?.data?.code === 200) {
          snackbar.show({ text: '节点已强制删除', color: 'success' })
    deleteNodeDialog.value = false
    selectedNode.value = null
    selectedEdgeInfo.value = null  // 重置边的信息
    if (selectedCourse.value === 'platform') {
      await fetchPlatformKnowledgeGraph()
    } else if (selectedCourse.value) {
      await fetchCourseKnowledgeGraph(selectedCourse.value)
    }
  } else {
          snackbar.show({ text: res?.data?.msg || '强制删除失败', color: 'error' })
  }
}

// 打开删除关系对话框
const openDeleteRelationDialog = () => {
  // 重置表单数据
  deleteRelationForm.value = {
    sourceKeywordId: '',
    targetKeywordId: ''
  }
  // 清空关系候选列表
  relationCandidates.value = []
  // 打开对话框
  showDeleteRelationSelectDialog.value = true
}

// 删除关系方法
const fetchRelations = async () => {
  if (!deleteRelationForm.value.sourceKeywordId || !deleteRelationForm.value.targetKeywordId) {
    snackbar.show({ text: '请选择源知识点和目标知识点', color: 'warning' })
    return
  }
  
  try {
    const res = await knowledgeMapService.getRelationsBetweenKeywords(
      deleteRelationForm.value.sourceKeywordId,
      deleteRelationForm.value.targetKeywordId
    )
    
    // 检查响应结构
    if (res?.data?.code === 200) {
      const dataField = res.data.data
      
      // 检查data字段是否是数组或包含relations字段
      if (Array.isArray(dataField)) {
        relationCandidates.value = dataField
      } else if (dataField && Array.isArray(dataField.relations)) {
        relationCandidates.value = dataField.relations
      } else if (dataField && Array.isArray(dataField.list)) {
        relationCandidates.value = dataField.list
      } else {
        relationCandidates.value = dataField || []
      }
      
      if (relationCandidates.value.length === 0) {
        snackbar.show({ text: '未找到两个知识点之间的关系', color: 'info' })
      }
    } else {
      snackbar.show({ text: res?.data?.msg || '查询关系失败', color: 'error' })
      relationCandidates.value = []
    }
  } catch (error) {
    console.error('查询关系出错:', error)
    snackbar.show({ text: '查询关系出错', color: 'error' })
    relationCandidates.value = []
  }
}

const deleteRelation = async (relationId?: string) => {
  // 如果传入了relationId，使用传入的ID（来自选择对话框）
  // 否则使用selectedEdgeInfo中的ID（来自直接点击边）
  const targetRelationId = relationId || selectedEdgeInfo.value?.id
  
  if (!targetRelationId) {
    snackbar.show({ text: '未选中有效的关系', color: 'error' })
    return
  }
  
  try {
    const res = await knowledgeMapService.deleteRelation(targetRelationId)
    if (res?.data?.code === 200) {
      snackbar.show({ text: '关系删除成功', color: 'success' })
      
      // 关闭相关对话框
      deleteRelationDialog.value = false
      showDeleteRelationSelectDialog.value = false
      
      // 重置相关状态
      selectedEdgeInfo.value = null
      relationCandidates.value = []
      deleteRelationForm.value = {
        sourceKeywordId: '',
        targetKeywordId: ''
      }
      
      // 刷新知识图谱
      if (selectedCourse.value === 'platform') {
        await fetchPlatformKnowledgeGraph()
      } else if (selectedCourse.value) {
        await fetchCourseKnowledgeGraph(selectedCourse.value)
      }
    } else {
      snackbar.show({ text: res?.data?.msg || '删除关系失败', color: 'error' })
    }
  } catch (err: any) {
    snackbar.show({ text: err?.response?.data?.msg || err?.message || '删除关系失败', color: 'error' })
  }
}

// 跳转到知识点详情页面
const goToKnowledgePointDetail = (keywordId: string) => {
  if (!keywordId) {
    snackbar.show({ text: '知识点ID不存在', color: 'error' })
    return
  }
  
  // 根据用户角色跳转到不同的详情页面
  if (isTeacher.value) {
    router.push({
      name: 'TeacherKnowledgeDetail',
      params: { id: keywordId }
    })
  } else {
    router.push({
      name: 'KnowledgePointDetail',
      params: { id: keywordId }
    })
  }
}

</script>

<style scoped>
.knowledge-map-container {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

.graph-container {
  width: 100%;
  height: 600px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  position: relative;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255,  255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.empty-state {
  height: 400px;
  justify-content: center;
}

.legend-panel {
  border: 1px solid #e0e0e0;
}

.legend-section h4 {
  color: #6f23d1;
}

.legend-chip {
  margin: 2px !important;
}

.legend-node-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
  display: inline-block;
}

.relation-line-sample {
  width: 20px;
  height: 0;
  border-top: 2px solid;
  margin-right: 6px;
  display: inline-block;
}

/* 沉浸模式样式 */
.immersive-overlay {
  background: rgba(0, 0, 0, 0.95) !important;
}

.immersive-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.immersive-header {
  height: 80px;
  background: rgba(111, 35, 209, 0.9);
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(10px);
}

.immersive-graph {
  flex: 1;
  background: transparent;
}

/* 沉浸模式详情卡片样式 */
.immersive-detail-card {
  position: fixed;
  top: 100px;
  right: 24px;
  width: 380px;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  z-index: 10000;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.immersive-detail-card::-webkit-scrollbar {
  width: 6px;
}

.immersive-detail-card::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.immersive-detail-card::-webkit-scrollbar-thumb {
  background: rgba(111,  35, 209, 0.6);
  border-radius: 3px;
}

.immersive-detail-card::-webkit-scrollbar-thumb:hover {
  background: rgba(111, 35, 209, 0.8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .legend-chip {
    margin-bottom: 4px !important;
  }
 
  .immersive-header {
    flex-direction: column;
    height: auto;
    padding: 16px;
    gap: 16px;
  }
  
  /* 移动端沉浸模式详情卡片调整 */
  .immersive-detail-card {
    position: fixed;
    top: 120px;
    left: 16px;
    right: 16px;
    width: auto;
    max-height: calc(100vh - 160px);
  }
}

@media (max-width: 480px) {
  .immersive-detail-card {
    top: 140px;
    left: 8px;
          right: 8px;
    max-height: calc(100vh - 180px);
  }

}

/* 动画效果 */
.v-fade-transition-enter-active {
  transition: all 0.3s ease-out;
}

.v-fade-transition-leave-active {
  transition: all 0.3s ease-in;
}

.v-fade-transition-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.v-fade-transition-leave-to {
  opacity: 0;
  transform: scale(1.05);
}

/* 筛选状态样式 */
.graph-container.filtered {
  border-color: #6f23d1;
  box-shadow: 0 0 0 2px rgba(111, 35, 209, 0.2);
}

/* 视频选择对话框样式 */
.video-option {
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.video-option:hover {
  background-color: rgba(0, 0, 0, 0.03);
}



</style>
