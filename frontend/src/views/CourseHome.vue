<template>
  <div class="course-home">
    <!-- 课程头部横幅 -->
    <div class="course-banner">
      <v-container fluid class="pa-0">
        <div class="banner-overlay">
          <v-container>
            <v-row align="center">
              <v-col cols="12" md="8">
                <div class="course-info">
                  <v-breadcrumbs
                    :items="breadcrumbs"
                    class="pa-0 mb-2"
                    style="color: rgba(255,255,255,0.8);"
                  >
                    <template v-slot:item="{ item }">
                      <v-breadcrumbs-item :href="item.href" style="color: rgba(255,255,255,0.8);">
                        {{ item.title }}
                      </v-breadcrumbs-item>
                    </template>
                  </v-breadcrumbs>
                  
                  <h1 class="course-title text-white mb-3">{{ courseDetail.name }}</h1>
                  
                  <div class="course-meta d-flex flex-wrap gap-4 mb-4">
                    <div class="meta-item">
                      <v-icon color="white" size="small" class="mr-1">mdi-account</v-icon>
                      <span class="text-white">{{ courseDetail.teacherInfo?.name || '未知教师' }}</span>
                    </div>
                    <div class="meta-item">
                      <v-icon color="white" size="small" class="mr-1">mdi-account-group</v-icon>
                      <span class="text-white">{{ courseDetail.studentCount || 0 }}人学习</span>
                    </div>
                    <div class="meta-item">
                      <v-icon color="white" size="small" class="mr-1">mdi-clock-outline</v-icon>
                      <span class="text-white">{{ courseDetail.hours || 0 }}学时</span>
                    </div>
                    <div class="meta-item">
                      <v-icon color="white" size="small" class="mr-1">mdi-play-circle</v-icon>
                      <span class="text-white">{{ courseDetail.videoCount || 0 }}个视频</span>
                    </div>
                  </div>
                  
                  <p class="course-description text-white opacity-90 mb-4">
                    {{ parsedCourseDesc.description || '暂无课程描述' }}
                  </p>
                  
                  <div v-if="parsedCourseDesc.category && parsedCourseDesc.category.length" class="mb-4">
                    <v-chip v-for="cat in parsedCourseDesc.category" :key="cat" size="small" color="primary" class="mr-2" variant="tonal">
                      {{ cat }}
                    </v-chip>
                  </div>
                  
                  <div class="action-buttons">
                    <v-btn
                      color="primary"
                      size="large"
                      prepend-icon="mdi-play"
                      @click="startLearning"
                      :loading="starting"
                    >
                      开始学习
                    </v-btn>
                    <v-btn
                      variant="outlined"
                      color="white"
                      size="large"
                      prepend-icon="mdi-heart"
                      class="ml-3"
                      @click="toggleFavorite"
                    >
                      {{ isFavorite ? '已收藏' : '收藏课程' }}
                    </v-btn>
                    <v-btn
                      variant="outlined"
                      color="white"
                      size="large"
                      prepend-icon="mdi-graph"
                      class="ml-3"
                      @click="navigateToKnowledgeMap"
                    >
                      知识图谱
                    </v-btn>
                  </div>
                </div>
              </v-col>
              
              <v-col cols="12" md="4" class="text-center">
                <div class="course-thumbnail">
                  <v-img
                    :src="courseDetail.imageUrl || '/default-course.jpg'"
                    height="250"
                    border-radius="12"
                    cover
                  >
                    <div class="play-overlay" @click="startLearning">
                      <v-btn
                        icon
                        color="primary"
                        size="x-large"
                      >
                        <v-icon size="48">mdi-play</v-icon>
                      </v-btn>
                    </div>
                  </v-img>
                </div>
              </v-col>
            </v-row>
          </v-container>
        </div>
      </v-container>
    </div>
    
    <!-- 主要内容区域 -->
    <v-container class="content-area">
      <v-row>
        <!-- 左侧主要内容 -->
        <v-col cols="12" lg="8">
          <!-- 课程章节内容 -->
          <v-card class="mb-6" elevation="2">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-book-open-page-variant</v-icon>
              课程内容
              <v-spacer></v-spacer>
              <div class="d-flex gap-2">
                <v-chip size="small" color="primary" variant="outlined">
                  {{ courseDetail.chapterCount || 0 }} 个章节
                </v-chip>
                <v-chip size="small" color="success" variant="outlined">
                  {{ courseDetail.documentCount || 0 }} 个文档
                </v-chip>
                <v-chip size="small" color="info" variant="outlined">
                  {{ courseDetail.videoCount || 0 }} 个视频
                </v-chip>
              </div>
            </v-card-title>
            
            <v-divider></v-divider>
            
            <div class="chapter-content">
              <template v-if="loading">
                <div class="text-center pa-8">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                  <p class="mt-2 text-grey">加载课程内容中...</p>
                </div>
              </template>
              
              <template v-else-if="courseDetail.chapters && courseDetail.chapters.length > 0">
                <!-- 章节列表 -->
                <div class="chapters-container">
                  <v-expansion-panels
                    v-model="expandedChapters"
                    multiple
                    variant="accordion"
                  >
                    <v-expansion-panel
                      v-for="(chapter, chapterIndex) in courseDetail.chapters"
                      :key="chapter.id"
                      class="chapter-panel"
                    >
                      <v-expansion-panel-title class="chapter-header">
                        <div class="d-flex align-center w-100">
                          <div class="chapter-number-badge">
                            {{ chapter.chapterNumber }}
                          </div>
                          <div class="flex-grow-1 mx-3">
                            <div class="chapter-title">{{ chapter.title }}</div>
                            <div v-if="chapter.description" class="chapter-description">
                              {{ chapter.description }}
                            </div>
                          </div>
                          <div class="chapter-stats">
                            <v-chip 
                              size="small" 
                              color="primary" 
                              variant="tonal"
                              class="mr-2"
                            >
                              {{ chapter.totalResources }} 项内容
                            </v-chip>
                            <v-chip 
                              v-if="chapter.documents.length > 0"
                              size="small" 
                              color="success" 
                              variant="outlined"
                              class="mr-1"
                            >
                              {{ chapter.documents.length }} 文档
                            </v-chip>
                            <v-chip 
                              v-if="chapter.videos.length > 0"
                              size="small" 
                              color="info" 
                              variant="outlined"
                            >
                              {{ chapter.videos.length }} 视频
                            </v-chip>
                          </div>
                        </div>
                      </v-expansion-panel-title>
                      
                      <v-expansion-panel-text>
                        <div class="chapter-resources">
                          <v-expansion-panels 
                            multiple
                            v-model="expandedResources[chapterIndex]"
                          >
                            <!-- 文档下拉栏 -->
                            <v-expansion-panel v-if="chapter.documents.length > 0">
                              <v-expansion-panel-title>
                                <v-icon color="success" class="mr-2">mdi-file-document</v-icon>
                                课程文档
                                <v-chip size="x-small" color="success" variant="tonal" class="ml-2">
                                  {{ chapter.documents.length }}
                                </v-chip>
                              </v-expansion-panel-title>
                              <v-expansion-panel-text>
                                <div class="resource-section">
                                  <v-list class="resource-list">
                                    <v-list-item
                                      v-for="(doc, docIndex) in chapter.documents"
                                      :key="doc.id"
                                      @click="viewDocument(doc)"
                                      class="resource-item document-item"
                                    >
                                      <template v-slot:prepend>
                                        <v-avatar color="success" size="32">
                                          <v-icon color="white" size="16">mdi-file-document</v-icon>
                                        </v-avatar>
                                      </template>
                                      <v-list-item-title class="resource-title">
                                        {{ doc.title }}
                                      </v-list-item-title>
                                      <v-list-item-subtitle class="resource-meta">
                                        <span class="file-type">{{ doc.fileType?.toUpperCase() }}</span>
                                        <span class="file-size ml-2">{{ formatFileSize(doc.fileSize) }}</span>
                                        <span v-if="doc.downloadCount" class="download-count ml-2">
                                          <v-icon size="small" class="mr-1">mdi-download</v-icon>
                                          {{ doc.downloadCount }}次下载
                                        </span>
                                      </v-list-item-subtitle>
                                      <template v-slot:append>
                                        <v-btn
                                          icon
                                          variant="text"
                                          color="success"
                                          size="small"
                                          @click.stop="downloadDocument(doc)">
                                          <v-icon>mdi-download</v-icon>
                                        </v-btn>
                                      </template>
                                    </v-list-item>
                                  </v-list>
                                </div>
                              </v-expansion-panel-text>
                            </v-expansion-panel>
                            <!-- 视频下拉栏 -->
                            <v-expansion-panel v-if="chapter.videos.length > 0">
                              <v-expansion-panel-title>
                                <v-icon color="info" class="mr-2">mdi-play-circle</v-icon>
                                课程视频
                                <v-chip size="x-small" color="info" variant="tonal" class="ml-2">
                                  {{ chapter.videos.length }}
                                </v-chip>
                              </v-expansion-panel-title>
                              <v-expansion-panel-text>
                                <div class="resource-section">
                                  <v-list class="resource-list">
                                    <v-list-item
                                      v-for="(video, videoIndex) in chapter.videos"
                                      :key="video.id"
                                      @click="navigateToVideo(video.id)"
                                      class="resource-item video-item"
                                    >
                                      <template v-slot:prepend>
                                        <v-avatar color="info" size="32">
                                          <v-icon color="white" size="16">mdi-play</v-icon>
                                        </v-avatar>
                                      </template>
                                      <v-list-item-title class="resource-title">
                                        {{ video.title }}
                                      </v-list-item-title>
                                      <v-list-item-subtitle class="resource-meta">
                                        <span v-if="video.duration">
                                          <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
                                          {{ formatDuration(video.duration) }}
                                        </span>
                                        <span v-if="video.viewCount" class="ml-3">
                                          <v-icon size="small" class="mr-1">mdi-eye</v-icon>
                                          {{ video.viewCount }}次播放
                                        </span>
                                      </v-list-item-subtitle>
                                      <template v-slot:append>
                                        <v-btn
                                          icon
                                          variant="text"
                                          color="info"
                                          size="small"
                                        >
                                          <v-icon>mdi-play</v-icon>
                                        </v-btn>
                                      </template>
                                    </v-list-item>
                                  </v-list>
                                </div>
                              </v-expansion-panel-text>
                            </v-expansion-panel>
                          </v-expansion-panels>
                          <!-- 空章节提示 -->
                          <div v-if="chapter.totalResources === 0" class="empty-chapter text-center pa-4">
                            <v-icon size="48" color="grey-lighten-2">mdi-folder-open</v-icon>
                            <p class="text-grey mt-2">该章节暂无内容</p>
                          </div>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </div>
                
                <!-- 未分配资源 -->
                <div v-if="hasUnassignedResources" class="unassigned-section mt-4">
                  <v-card elevation="2">
                    <v-card-title class="d-flex align-center">
                      <v-icon color="warning" class="mr-2">mdi-folder-question</v-icon>
                      其他资源
                      <v-spacer></v-spacer>
                      <v-chip size="small" color="warning" variant="outlined">
                        {{ totalUnassignedResources }} 项未分类内容
                      </v-chip>
                    </v-card-title>
                    <v-card-text>
                      <v-expansion-panels 
                        multiple
                        v-model="expandedUnassignedResources"
                      >
                        <!-- 文档下拉栏 -->
                        <v-expansion-panel v-if="courseDetail.unassignedResources?.documents?.length > 0">
                          <v-expansion-panel-title>
                            <v-icon color="success" class="mr-2">mdi-file-document</v-icon>
                            未分类文档
                          </v-expansion-panel-title>
                          <v-expansion-panel-text>
                            <div class="resource-section">
                              <v-list class="resource-list">
                                <v-list-item
                                  v-for="doc in courseDetail.unassignedResources.documents"
                                  :key="doc.id"
                                  @click="viewDocument(doc)"
                                  class="resource-item document-item"
                                >
                                  <template v-slot:prepend>
                                    <v-avatar color="success" size="32">
                                      <v-icon color="white" size="16">mdi-file-document</v-icon>
                                    </v-avatar>
                                  </template>
                                  <v-list-item-title>{{ doc.title }}</v-list-item-title>
                                  <v-list-item-subtitle>
                                    {{ doc.fileType?.toUpperCase() }} · {{ formatFileSize(doc.fileSize) }}
                                  </v-list-item-subtitle>
                                  <template v-slot:append>
                                    <v-btn icon variant="text" color="success" size="small">
                                      <v-icon>mdi-download</v-icon>
                                    </v-btn>
                                  </template>
                                </v-list-item>
                              </v-list>
                            </div>
                          </v-expansion-panel-text>
                        </v-expansion-panel>
                        <!-- 视频下拉栏 -->
                        <v-expansion-panel v-if="courseDetail.unassignedResources?.videos?.length > 0">
                          <v-expansion-panel-title>
                            <v-icon color="info" class="mr-2">mdi-play-circle</v-icon>
                            未分类视频
                          </v-expansion-panel-title>
                          <v-expansion-panel-text>
                            <div class="resource-section">
                              <v-list class="resource-list">
                                <v-list-item
                                  v-for="video in courseDetail.unassignedResources.videos"
                                  :key="video.id"
                                  @click="navigateToVideo(video.id)"
                                  class="resource-item video-item"
                                >
                                  <template v-slot:prepend>
                                    <v-avatar color="info" size="32">
                                      <v-icon color="white" size="16">mdi-play</v-icon>
                                    </v-avatar>
                                  </template>
                                  <v-list-item-title>{{ video.title }}</v-list-item-title>
                                  <v-list-item-subtitle>
                                    {{ formatDuration(video.duration) }} · {{ video.viewCount }}次播放
                                  </v-list-item-subtitle>
                                  <template v-slot:append>
                                    <v-btn icon variant="text" color="info" size="small">
                                      <v-icon>mdi-play</v-icon>
                                    </v-btn>
                                  </template>
                                </v-list-item>
                              </v-list>
                            </div>
                          </v-expansion-panel-text>
                        </v-expansion-panel>
                      </v-expansion-panels>
                    </v-card-text>
                  </v-card>
                </div>
              </template>
              
              <template v-else>
                <div v-if="(courseDetail.unassignedResources?.documents?.length || 0) + (courseDetail.unassignedResources?.videos?.length || 0) > 0">
                  <v-expansion-panels 
                    multiple
                    v-model="expandedUnassignedResources"
                  >
                    <!-- 文档下拉栏 -->
                    <v-expansion-panel v-if="courseDetail.unassignedResources?.documents?.length > 0">
                      <v-expansion-panel-title>
                        <v-icon color="success" class="mr-2">mdi-file-document</v-icon>
                        课程文档
                        <v-chip size="x-small" color="success" variant="tonal" class="ml-2">
                          {{ courseDetail.unassignedResources.documents.length }}
                        </v-chip>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div class="resource-section">
                          <v-list class="resource-list">
                            <v-list-item
                              v-for="doc in courseDetail.unassignedResources.documents"
                              :key="doc.id"
                              @click="viewDocument(doc)"
                              class="resource-item document-item"
                            >
                              <template v-slot:prepend>
                                <v-avatar color="success" size="32">
                                  <v-icon color="white" size="16">mdi-file-document</v-icon>
                                </v-avatar>
                              </template>
                              <v-list-item-title>{{ doc.title }}</v-list-item-title>
                              <v-list-item-subtitle>
                                {{ doc.fileType?.toUpperCase() }} · {{ formatFileSize(doc.fileSize) }}
                              </v-list-item-subtitle>
                              <template v-slot:append>
                                <v-btn icon variant="text" color="success" size="small">
                                  <v-icon>mdi-download</v-icon>
                                </v-btn>
                              </template>
                            </v-list-item>
                          </v-list>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                    <!-- 视频下拉栏 -->
                    <v-expansion-panel v-if="courseDetail.unassignedResources?.videos?.length > 0">
                      <v-expansion-panel-title>
                        <v-icon color="info" class="mr-2">mdi-play-circle</v-icon>
                        课程视频
                        <v-chip size="x-small" color="info" variant="tonal" class="ml-2">
                          {{ courseDetail.unassignedResources.videos.length }}
                        </v-chip>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <div class="resource-section">
                          <v-list class="resource-list">
                            <v-list-item
                              v-for="video in courseDetail.unassignedResources.videos"
                              :key="video.id"
                              @click="navigateToVideo(video.id)"
                              class="resource-item video-item"
                            >
                              <template v-slot:prepend>
                                <v-avatar color="info" size="32">
                                  <v-icon color="white" size="16">mdi-play</v-icon>
                                </v-avatar>
                              </template>
                              <v-list-item-title>{{ video.title }}</v-list-item-title>
                              <v-list-item-subtitle>
                                {{ formatDuration(video.duration) }} · {{ video.viewCount }}次播放
                              </v-list-item-subtitle>
                              <template v-slot:append>
                                <v-btn icon variant="text" color="info" size="small">
                                  <v-icon>mdi-play</v-icon>
                                </v-btn>
                              </template>
                            </v-list-item>
                          </v-list>
                        </div>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </div>
                <div v-else class="text-center pa-8">
                  <v-icon size="64" color="grey-lighten-2">mdi-book-off</v-icon>
                  <p class="text-grey mt-2">该课程暂无章节内容</p>
                  <p class="text-grey">请联系教师添加课程资料</p>
                </div>
              </template>
            </div>
          </v-card>
          
          <!-- 课程介绍 -->
          <v-card class="mb-6" elevation="2">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-information</v-icon>
              课程介绍
            </v-card-title>
            
            <v-divider></v-divider>
            
            <v-card-text class="course-intro">
              <div v-if="parsedCourseDesc.description" class="description-content">
                <p>{{ parsedCourseDesc.description }}</p>
              </div>
              <div v-else class="text-grey text-center pa-4">
                暂无详细介绍
              </div>
            </v-card-text>
          </v-card>

          <!-- 作业列表 -->
          <v-card class="mb-6" elevation="2">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="deep-purple">mdi-clipboard-text</v-icon>
              作业列表
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <template v-if="assignmentLoading">
                <div class="text-center pa-8">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                  <p class="mt-2 text-grey">加载作业中...</p>
                </div>
              </template>
              <template v-else-if="assignments.length > 0">
                <v-list>
                  <v-list-item
                    v-for="assignment in assignments"
                    :key="assignment.id"
                    @click="goToAssignment(assignment.id)"
                    class="assignment-list-item"
                    style="cursor:pointer"
                  >
                    <template v-slot:prepend>
                      <v-avatar color="deep-purple" size="32">
                        <v-icon color="white" size="16">mdi-clipboard-text</v-icon>
                      </v-avatar>
                    </template>
                    <v-list-item-title>{{ assignment.title }}</v-list-item-title>
                    <v-list-item-subtitle>
                      截止：{{ assignment.dueDate ? assignment.dueDate.slice(0, 16).replace('T', ' ') : '未设置' }}
                    </v-list-item-subtitle>
                    <template v-slot:append>
                      <v-chip size="small" :color="new Date(assignment.dueDate) < new Date() ? 'error' : 'primary'">
                        {{ new Date(assignment.dueDate) < new Date() ? '已截止' : '进行中' }}
                      </v-chip>
                    </template>
                  </v-list-item>
                </v-list>
              </template>
              <template v-else>
                <div class="text-center pa-4 text-grey">暂无作业</div>
              </template>
            </v-card-text>
          </v-card>
        </v-col>
        
        <!-- 右侧边栏 -->
        <v-col cols="12" lg="4">
          <!-- 课程信息卡片 -->
          <v-card class="mb-4 sticky-sidebar" elevation="2">
            <v-card-title>课程信息</v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <div class="info-item mb-3">
                <div class="info-label">开课时间</div>
                <div class="info-value">{{ formatDate(courseDetail.startDate) }}</div>
              </div>
              <div class="info-item mb-3">
                <div class="info-label">结课时间</div>
                <div class="info-value">{{ formatDate(courseDetail.endDate) }}</div>
              </div>
              <div class="info-item mb-3">
                <div class="info-label">课程状态</div>
                <div class="info-value">
                  <v-chip 
                    :color="getStatusColor(courseDetail.status)" 
                    size="small"
                  >
                    {{ getStatusText(courseDetail.status) }}
                  </v-chip>
                </div>
              </div>
              <div class="info-item mb-3">
                <div class="info-label">学期</div>
                <div class="info-value">{{ courseDetail.semester || '未设置' }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">课程代码</div>
                <div class="info-value">{{ courseDetail.code }}</div>
              </div>
            </v-card-text>
          </v-card>
          <!-- 新增：课程分类卡片 -->
          <v-card class="mb-4" elevation="2" v-if="parsedCourseDesc.category && parsedCourseDesc.category.length">
            <v-card-title>课程分类</v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <v-chip v-for="cat in parsedCourseDesc.category" :key="cat" size="small" color="primary" class="mr-2" variant="tonal">
                {{ cat }}
              </v-chip>
            </v-card-text>
          </v-card>
          <!-- 教师信息卡片 -->
          <v-card class="mb-4" elevation="2" v-if="courseDetail.teacherInfo">
            <v-card-title>授课教师</v-card-title>
            <v-divider></v-divider>
            <v-card-text>              <div class="teacher-info d-flex align-center">
                <v-avatar size="60" class="mr-3" color="grey-lighten-3">
                  <img 
                    v-if="courseDetail.teacherInfo.avatar && !courseDetail.teacherInfo.avatarLoadError" 
                    :src="courseDetail.teacherInfo.avatar" 
                    @error="handleAvatarError($event, courseDetail.teacherInfo)"
                    @load="handleAvatarLoad($event, courseDetail.teacherInfo)"
                    style="width: 100%; height: 100%; object-fit: cover;" 
                  />
                  <div v-else-if="courseDetail.teacherInfo.name && courseDetail.teacherInfo.name.trim()" 
                       class="letter-avatar" 
                       :style="getLetterAvatarStyle(courseDetail.teacherInfo.name)">
                    {{ courseDetail.teacherInfo.name.charAt(0).toUpperCase() }}
                  </div>
                  <v-icon v-else size="32">mdi-account</v-icon>
                </v-avatar>
                <div>
                  <div class="teacher-name text-h6">{{ courseDetail.teacherInfo.name }}</div>
                  <div class="teacher-title text-grey">授课教师</div>
                </div>
              </div>
            </v-card-text>
          </v-card>
          
          <!-- 学习统计 -->
          <v-card elevation="2">
            <v-card-title>学习统计</v-card-title>
            <v-divider></v-divider>
            <v-card-text>
              <div class="stats-grid">
                <div class="stat-item text-center">
                  <div class="stat-number text-h5 text-primary">{{ courseDetail.studentCount || 0 }}</div>
                  <div class="stat-label text-grey">学习人数</div>
                </div>
                <div class="stat-item text-center">
                  <div class="stat-number text-h5 text-primary">{{ courseDetail.videoCount || 0 }}</div>
                  <div class="stat-label text-grey">视频数量</div>
                </div>
                <div class="stat-item text-center">
                  <div class="stat-number text-h5 text-primary">{{ courseDetail.documentCount || 0 }}</div>
                  <div class="stat-label text-grey">课程文档</div>
                </div>
                <div class="stat-item text-center">
                  <div class="stat-number text-h5 text-primary">{{ courseDetail.hours || 0 }}</div>
                  <div class="stat-label text-grey">课程学时</div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import courseService from '../api/courseService'
import { useSnackbar } from '../stores/snackbarStore'
import assignmentService from '../api/assignmentService'
import { parseCourseDescription } from '../utils/courseUtils'

const route = useRoute()
const router = useRouter()
const snackbar = useSnackbar()

// 响应式数据
const courseDetail = ref<any>({})
const loading = ref(true)
const starting = ref(false)
const isFavorite = ref(false)
const expandedChapters = ref<number[]>([]) // 展开的章节索引
const expandedResources = ref<Record<number, number[]>>({}) // 每个章节内部展开的资源面板索引
const expandedUnassignedResources = ref<number[]>([]) // 未分配资源的展开面板索引
const assignments = ref<any[]>([])
const assignmentLoading = ref(false)

// 面包屑导航
const breadcrumbs = computed(() => [
  { title: '首页', href: '/' },
  { title: '课程', href: '/all-courses' },
  { title: courseDetail.value.name || '课程详情', href: '' }
])

// 解析 description 字段
const parsedCourseDesc = computed(() => {
  return parseCourseDescription(courseDetail.value.description)
})

// 计算属性
const hasUnassignedResources = computed(() => {
  const unassigned = courseDetail.value.unassignedResources
  return unassigned && (
    (unassigned.documents && unassigned.documents.length > 0) ||
    (unassigned.videos && unassigned.videos.length > 0)
  )
})

const totalUnassignedResources = computed(() => {
  const unassigned = courseDetail.value.unassignedResources
  if (!unassigned) return 0
  return (unassigned.documents?.length || 0) + (unassigned.videos?.length || 0)
})

// 获取课程详情
const fetchCourseDetail = async () => {
  const courseId = route.params.courseId as string
  
  if (!courseId) {
    router.push('/')
    return
  }

  try {
    loading.value = true
    // 使用新的包含章节信息的API
    const response = await courseService.getCourseDetailsWithChapters(courseId)
    
    if (response.data?.code === 200) {
      courseDetail.value = response.data.data
      // 默认展开所有章节
      if (courseDetail.value.chapters && courseDetail.value.chapters.length > 0) {
        expandedChapters.value = courseDetail.value.chapters.map((_: any, index: number) => index)
        
        // 默认展开每个章节内部的文档和视频面板
        const resourceExpansions: Record<number, number[]> = {}
        courseDetail.value.chapters.forEach((chapter: any, chapterIndex: number) => {
          const panelIndices: number[] = []
          let panelIndex = 0
          
          // 如果有文档，添加文档面板索引
          if (chapter.documents && chapter.documents.length > 0) {
            panelIndices.push(panelIndex)
            panelIndex++
          }
          
          // 如果有视频，添加视频面板索引
          if (chapter.videos && chapter.videos.length > 0) {
            panelIndices.push(panelIndex)
          }
          
          resourceExpansions[chapterIndex] = panelIndices
        })
        
        expandedResources.value = resourceExpansions
      }
      
      // 默认展开未分配资源面板
      if (courseDetail.value.unassignedResources) {
        const unassignedPanels: number[] = []
        let panelIndex = 0
        
        // 如果有未分配文档，添加文档面板索引
        if (courseDetail.value.unassignedResources.documents && 
            courseDetail.value.unassignedResources.documents.length > 0) {
          unassignedPanels.push(panelIndex)
          panelIndex++
        }
        
        // 如果有未分配视频，添加视频面板索引
        if (courseDetail.value.unassignedResources.videos && 
            courseDetail.value.unassignedResources.videos.length > 0) {
          unassignedPanels.push(panelIndex)
        }
        
        expandedUnassignedResources.value = unassignedPanels
      }
    } else {
      snackbar.show({
        text: '获取课程信息失败',
        color: 'error'
      })
      setTimeout(() => router.push('/'), 2000)
    }
  } catch (error) {
    console.error('获取课程详情失败:', error)
    snackbar.show({
      text: '获取课程信息出错',
      color: 'error'
    })
    setTimeout(() => router.push('/'), 2000)
  } finally {
    loading.value = false
  }
}

// 开始学习（跳转到第一个视频）
const startLearning = async () => {
  // 寻找第一个视频
  let firstVideo = null
  
  // 先在章节中寻找
  if (courseDetail.value.chapters) {
    for (const chapter of courseDetail.value.chapters) {
      if (chapter.videos && chapter.videos.length > 0) {
        firstVideo = chapter.videos[0]
        break
      }
    }
  }
  
  // 如果章节中没有，尝试未分配的视频
  if (!firstVideo && courseDetail.value.unassignedResources?.videos?.length > 0) {
    firstVideo = courseDetail.value.unassignedResources.videos[0]
  }
  
  if (!firstVideo) {
    snackbar.show({
      text: '该课程暂无视频内容',
      color: 'warning'
    })
    return
  }
  
  starting.value = true
  
  try {
    await router.push(`/course/${route.params.courseId}/video/${firstVideo.id}`)
  } catch (error) {
    console.error('跳转失败:', error)
    snackbar.show({
      text: '跳转到视频播放页面失败',
      color: 'error'
    })
  } finally {
    starting.value = false
  }
}

// 跳转到指定视频
const navigateToVideo = async (videoId: string | number) => {
  try {
    await router.push(`/course/${route.params.courseId}/video/${videoId}`)
  } catch (error) {
    console.error('跳转视频失败:', error)
    snackbar.show({
      text: '跳转到视频失败',
      color: 'error'
    })
  }
}

// 跳转到知识图谱
const navigateToKnowledgeMap = async () => {
  try {
    await router.push({
      path: '/knowledge-map',
      query: { courseId: route.params.courseId }
    })
  } catch (error) {
    console.error('跳转知识图谱失败:', error)
    snackbar.show({
      text: '跳转到知识图谱失败',
      color: 'error'
    })
  }
}

// 切换收藏状态
const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  snackbar.show({
    text: isFavorite.value ? '已添加到收藏' : '已取消收藏',
    color: 'success'
  })
}

// 格式化时长
const formatDuration = (seconds: number): string => {
  if (!seconds) return '未知'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  }
  return `${minutes}分钟`
}

// 格式化日期
const formatDate = (timestamp: number): string => {
  if (!timestamp) return '未设置'
  
  const ts = timestamp > 1e12 ? timestamp : timestamp * 1000
  const date = new Date(ts)
    return date.toLocaleDateString('zh-CN')
}

// 获取状态颜色
const getStatusColor = (status: number): string => {
  switch (status) {
    case 1: return 'success'
    case 2: return 'warning'
    case 3: return 'error'
    default: return 'grey'
  }
}

// 获取状态文本
const getStatusText = (status: number): string => {
  switch (status) {
    case 1: return '进行中'
    case 2: return '已结束'
    case 3: return '未开始'
    default: return '未知'
  }
}

// 下载文档
const downloadDocument = async (doc: any) => {
  try {
    // 创建下载链接
    const link = document.createElement('a')
    link.href = doc.fileUrl
    link.download = doc.title
    link.target = '_blank'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    snackbar.show({
      text: '文档下载已开始',
      color: 'success'
    })
  } catch (error) {
    console.error('下载文档失败:', error)
    snackbar.show({
      text: '文档下载失败',
      color: 'error'
    })
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 新增方法：预览文档
const viewDocument = (document: any) => {
  router.push(`/document/${document.id}`)
}

const goToAssignment = (assignmentId: string) => {
  router.push(`/student-assignments/${assignmentId}`)
}

const fetchAssignments = async () => {
  assignmentLoading.value = true
  try {
    const res = await assignmentService.getAssignmentList({
      courseId: route.params.courseId as string,
      status: 'published',
      page: 1,
      pageSize: 100
    })
    if (res.data && res.data.code === 200) {
      assignments.value = res.data.data.list || []
    } else {
      assignments.value = []
    }
  } catch (e) {
    assignments.value = []
  } finally {
    assignmentLoading.value = false
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchCourseDetail()
  fetchAssignments()
})

// 监听课程ID变化，自动刷新数据
watch(
  () => route.params.courseId,
  (newId, oldId) => {
    if (newId !== oldId) {
      loading.value = true
      courseDetail.value = {}
      assignments.value = []
      expandedChapters.value = []
      expandedResources.value = {}
      expandedUnassignedResources.value = []
      fetchCourseDetail()
      fetchAssignments()
    }
  }
)

// 测试函数：输出展开状态的值
const testExpandedChapters = () => {
  console.log('expandedChapters:', expandedChapters.value)
  console.log('expandedResources:', expandedResources.value)
  console.log('expandedUnassignedResources:', expandedUnassignedResources.value)
  console.log('courseDetail.chapters:', courseDetail.value.chapters?.length)
}

// 头像处理方法
const getRandomColor = (username: string): string => {
  const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#95a5a6', '#16a085'
  ]
  let hash = 0
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

const getLetterAvatarStyle = (username: string) => {
  if (!username || !username.trim()) {
    return {
      backgroundColor: '#95a5a6',
      color: 'white',
      fontSize: '24px',
      fontWeight: 'bold',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100%'
    }
  }
  
  const bgColor = getRandomColor(username)
  return {
    backgroundColor: bgColor,
    color: 'white',
    fontSize: '24px',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    height: '100%'
  }
}

const handleAvatarError = (event: Event, teacherInfo: any) => {
  console.log('Avatar load error for teacher:', teacherInfo.name)
  teacherInfo.avatarLoadError = true
}

const handleAvatarLoad = (event: Event, teacherInfo: any) => {
  console.log('Avatar loaded successfully for teacher:', teacherInfo.name)
  teacherInfo.avatarLoadError = false
}
</script>

<style scoped>
.course-home {
  min-height: 100vh;
  background: #f5f5f5;
}

.course-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 400px;
  position: relative;
  overflow: hidden;
}

.banner-overlay {
  background: rgba(0, 0, 0, 0.3);
  min-height: 400px;
  display: flex;
  align-items: center;
}

.course-title {
  font-size: 2.5rem;
  font-weight: 600;
  line-height: 1.2;
}

.course-meta {
  gap: 24px;
}

.meta-item {
  display: flex;
  align-items: center;
}

.course-description {
  font-size: 1.1rem;
  line-height: 1.6;
  max-width: 600px;
}

.course-thumbnail {
  position: relative;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  cursor: pointer;
  border-radius: 12px;
}

.course-thumbnail:hover .play-overlay {
  opacity: 1;
}

.content-area {
  margin-top: -50px;
  position: relative;
  z-index: 1;
}

/* 章节内容样式 */
.chapter-content {
  max-height: none;
}

.chapters-container {
  margin-bottom: 16px;
}

.chapter-panel {
  margin-bottom: 8px;
  border-radius: 12px !important;
  border: 1px solid rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.chapter-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 16px !important;
}

.chapter-number-badge {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.chapter-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.chapter-description {
  font-size: 0.9rem;
  color: #718096;
  line-height: 1.4;
}

.chapter-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chapter-resources {
  padding: 8px 0;
}

.resource-section {
  margin-bottom: 20px;
}

resource-section:last-child {
  margin-bottom: 0;
}

.resource-section-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  border-left: 4px solid currentColor;
}

.resource-list {
  background: transparent;
}

.resource-item {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  margin-bottom: 4px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.resource-item:hover {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.document-item:hover {
  background: rgba(76, 175, 80, 0.05);
  border-color: rgba(76, 175, 80, 0.2);
}

.video-item:hover {
  background: rgba(33, 150, 243, 0.05);
  border-color: rgba(33, 150, 243, 0.2);
}

.resource-title {
  font-weight: 500;
  color: #2d3748;
}

.resource-meta {
  color: #718096;
  font-size: 0.875rem;
}

.file-type {
  font-weight: 500;
  padding: 2px 6px;
  background: rgba(76, 175, 80, 0.1);
  border-radius: 4px;
  font-size: 0.75rem;
}

.file-size, .download-count {
  color: #666;
}

.empty-chapter {
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  margin: 16px 0;
}

.unassigned-section {
  margin-top: 24px;
}

.sticky-sidebar {
  position: sticky;
  top: 24px;
  min-width: 320px;
  max-width: 380px;
  margin-bottom: 24px;
}

.v-col > .v-card {
  margin-bottom: 24px;
  box-sizing: border-box;
  width: 100%;
}

.v-card {
  padding-left: 0 !important;
  padding-right: 0 !important;
}

.v-card-title, .v-card-text {
  padding-left: 24px !important;
  padding-right: 24px !important;
}

.v-card-title {
  padding-top: 20px !important;
  padding-bottom: 12px !important;
}

.v-card-text {
  padding-top: 8px !important;
  padding-bottom: 20px !important;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-weight: 500;
  color: #666;
}

.info-value {
  font-weight: 400;
  color: #333;
}

.teacher-info {
  padding: 8px 0;
}

.teacher-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.teacher-title {
  font-size: 0.875rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

/* 字母头像样式 */
.letter-avatar {
  border-radius: 50%;
  background: linear-gradient(135deg, var(--bg-color, #3498db), var(--bg-color-light, #5dade2));
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  cursor: pointer;
}

.letter-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.description-content {
  line-height: 1.8;
  color: #333;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .course-title {
    font-size: 2rem;
  }
  
  .course-meta {
    gap: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .content-area {
    margin-top: -20px;
  }
}

@media (max-width: 1200px) {
  .sticky-sidebar {
    min-width: 0;
    max-width: 100%;
  }
}

.assignment-list-item {
  margin-bottom: 8px;
  border-radius: 8px;
  transition: background 0.2s;
}
.assignment-list-item:hover {
  background: #f3e8ff;
}
</style>