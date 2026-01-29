<template>
  <v-dialog 
    :model-value="modelValue" 
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
    persistent
  >
    <v-card>
      <v-card-title class="d-flex align-center pa-4">
        <v-icon :color="material?.type === 'video' ? 'primary' : 'green'" class="me-2">
          {{ material?.type === 'video' ? 'mdi-video' : 'mdi-file-document' }}
        </v-icon>
        <span>编辑{{ material?.type === 'video' ? '视频' : '文档' }}信息</span>
        <v-spacer></v-spacer>
        <v-btn 
          icon 
          variant="text" 
          @click="close"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <v-form ref="formRef" v-model="formValid" @submit.prevent="save">
          <v-row>
            <!-- 标题 -->
            <v-col cols="12">
              <v-text-field
                v-model="form.title"
                label="标题"
                variant="outlined"
                density="comfortable"
                :rules="[rules.required]"
                prepend-inner-icon="mdi-format-title"
              ></v-text-field>
            </v-col>

            <!-- 描述 -->
            <v-col cols="12">
              <v-textarea
                v-model="form.description"
                label="描述"
                variant="outlined"
                density="comfortable"
                rows="3"
                prepend-inner-icon="mdi-text"
                placeholder="请输入资料描述..."
              ></v-textarea>
            </v-col>

            <!-- 标签 -->
            <v-col cols="12">
              <v-combobox
                v-model="form.tags"
                label="标签"
                variant="outlined"
                density="comfortable"
                multiple
                chips
                closable-chips
                prepend-inner-icon="mdi-tag-multiple"
                placeholder="添加标签，按回车确认"
              ></v-combobox>
            </v-col>

            <!-- 可见性设置 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.visibility"
                :items="visibilityOptions"
                label="可见性"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-eye"
              ></v-select>
            </v-col>

            <!-- 分类 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.category"
                :items="categoryOptions"
                label="分类"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-folder"
              ></v-select>
            </v-col>

            <!-- 视频特有字段 -->
            <template v-if="material?.type === 'video'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.duration"
                  label="时长（秒）"
                  variant="outlined"
                  density="comfortable"
                  type="number"
                  prepend-inner-icon="mdi-clock"
                  readonly
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.resolution"
                  label="分辨率"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-monitor"
                  readonly
                ></v-text-field>
              </v-col>

              <v-col cols="12">
                <v-text-field
                  v-model="form.thumbnailUrl"
                  label="缩略图URL"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-image"
                ></v-text-field>
              </v-col>
            </template>

            <!-- 文档特有字段 -->
            <template v-if="material?.type === 'document'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.pageCount"
                  label="页数"
                  variant="outlined"
                  density="comfortable"
                  type="number"
                  prepend-inner-icon="mdi-file-document"
                  readonly
                ></v-text-field>
              </v-col>

              <v-col cols="12" md="6">
                <v-text-field
                  v-model="form.fileType"
                  label="文件类型"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-file"
                  readonly
                ></v-text-field>
              </v-col>
            </template>

            <!-- 文件信息 -->
            <v-col cols="12" md="6">
              <v-text-field
                :model-value="formatFileSize(form.fileSize)"
                label="文件大小"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-harddisk"
                readonly
              ></v-text-field>
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                :model-value="formatDate(form.uploadTime || form.createTime)"
                label="上传时间"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-calendar"
                readonly
              ></v-text-field>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn 
          variant="text" 
          @click="close"
        >
          取消
        </v-btn>
        <v-btn 
          color="primary" 
          @click="save"
          :loading="saving"
          :disabled="!formValid"
        >
          保存
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import videoService from '../../../api/videoService'
import { documentService } from '../../../api/documentService'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  material: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

// 表单数据
const formRef = ref()
const formValid = ref(false)
const saving = ref(false)

const form = ref({
  title: '',
  description: '',
  tags: [],
  visibility: 'private',
  category: '',
  duration: 0,
  resolution: '',
  thumbnailUrl: '',
  pageCount: 0,
  fileType: '',
  fileSize: 0,
  uploadTime: '',
  createTime: ''
})

// 验证规则
const rules = {
  required: (value: any) => !!value || '此字段为必填项'
}

// 选项数据
const visibilityOptions = [
  { title: '私有', value: 'private' },
  { title: '课程内可见', value: 'course' },
  { title: '公开', value: 'public' }
]

const categoryOptions = [
  { title: '教学视频', value: 'teaching' },
  { title: '课件资料', value: 'courseware' },
  { title: '参考文献', value: 'reference' },
  { title: '作业练习', value: 'exercise' },
  { title: '其他', value: 'other' }
]

// 计算属性
const dialogTitle = computed(() => {
  return props.material?.type === 'video' ? '编辑视频信息' : '编辑文档信息'
})

// 监听器
watch(() => props.material, (newMaterial) => {
  if (newMaterial) {
    resetForm()
    Object.assign(form.value, {
      title: newMaterial.title || '',
      description: newMaterial.description || '',
      tags: newMaterial.tags || [],
      visibility: newMaterial.visibility || 'private',
      category: newMaterial.category || '',
      duration: newMaterial.duration || 0,
      resolution: newMaterial.resolution || '',
      thumbnailUrl: newMaterial.thumbnailUrl || '',
      pageCount: newMaterial.pageCount || 0,
      fileType: newMaterial.fileType || '',
      fileSize: newMaterial.fileSize || 0,
      uploadTime: newMaterial.uploadTime || '',
      createTime: newMaterial.createTime || ''
    })
  }
}, { immediate: true })

watch(() => props.modelValue, (newValue) => {
  if (!newValue) {
    resetForm()
  }
})

// 方法
function resetForm() {
  form.value = {
    title: '',
    description: '',
    tags: [],
    visibility: 'private',
    category: '',
    duration: 0,
    resolution: '',
    thumbnailUrl: '',
    pageCount: 0,
    fileType: '',
    fileSize: 0,
    uploadTime: '',
    createTime: ''
  }
  if (formRef.value) {
    formRef.value.resetValidation()
  }
}

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (!formRef.value?.validate()) {
    return
  }

  saving.value = true

  try {
    const updateData = {
      title: form.value.title,
      description: form.value.description,
      tags: form.value.tags,
      visibility: form.value.visibility,
      category: form.value.category
    }

    // 视频特有字段
    if (props.material?.type === 'video') {
      Object.assign(updateData, {
        thumbnailUrl: form.value.thumbnailUrl
      })
      await videoService.updateVideo(props.material.id, updateData)
    } 
    // 文档特有字段
    else {
      await documentService.updateDocument(props.material.id, updateData)
    }

    emit('saved')
    close()
  } catch (error) {
    console.error('保存失败:', error)
    // 这里可以添加错误提示
  } finally {
    saving.value = false
  }
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateString: string): string {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.v-dialog > .v-card {
  border-radius: 12px;
}
</style> 