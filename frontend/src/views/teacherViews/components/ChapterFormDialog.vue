<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="600">
    <v-card>
      <v-card-title class="d-flex align-center py-4 px-6">
        <v-icon start color="primary">{{ isEditing ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
        {{ isEditing ? '编辑章节' : '新建章节' }}
        <v-spacer></v-spacer>
        <v-btn icon @click="close">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text class="pa-6">
        <v-form ref="formRef" v-model="formValid">
          <v-text-field
            v-model="form.chapterNumber"
            label="章节编号"
            type="number"
            variant="outlined"
            density="comfortable"
            required
            :rules="[(v: any) => !!v || '请输入章节编号', (v: any) => v > 0 || '章节编号必须大于0']"
            hint="例如：1, 2, 3..."
            persistent-hint
            class="mb-4"
          ></v-text-field>
          
          <v-text-field
            v-model="form.title"
            label="章节标题"
            variant="outlined"
            density="comfortable"
            required
                         :rules="[(v: any) => !!v || '请输入章节标题']"
            placeholder="例如：第一章 概述"
            class="mb-4"
          ></v-text-field>
          
          <v-textarea
            v-model="form.description"
            label="章节描述"
            variant="outlined"
            density="comfortable"
            rows="4"
            placeholder="请输入章节的详细描述..."
            hint="可选，描述该章节的主要内容"
            persistent-hint
          ></v-textarea>
        </v-form>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="pa-6">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="close">
          取消
        </v-btn>
        <v-btn
          color="primary"
          :disabled="!formValid"
          :loading="saving"
          @click="save"
        >
          {{ isEditing ? '保存' : '创建' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface Chapter {
  id?: string
  title: string
  description?: string
  chapterNumber: number
}

interface Props {
  modelValue: boolean
  chapter?: Chapter | null
  isEditing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  chapter: null,
  isEditing: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [chapter: Omit<Chapter, 'id'> & { id?: string }]
}>()

const formRef = ref()
const formValid = ref(false)
const saving = ref(false)

const form = ref<Chapter>({
  title: '',
  description: '',
  chapterNumber: 1
})

// 监听章节数据变化，重置表单
watch(() => props.chapter, (newChapter) => {
  if (newChapter) {
    form.value = { ...newChapter }
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听对话框打开状态
watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    if (formRef.value) {
      formRef.value.resetValidation()
    }
  }
})

function resetForm() {
  form.value = {
    title: '',
    description: '',
    chapterNumber: 1
  }
}

function close() {
  emit('update:modelValue', false)
  if (!props.isEditing) {
    resetForm()
  }
}

async function save() {
  if (!formRef.value) return
  
  const { valid } = await formRef.value.validate()
  if (!valid) return
  
  saving.value = true
  
  try {
    const chapterData = {
      ...form.value,
      chapterNumber: parseInt(form.value.chapterNumber.toString())
    }
    
    if (props.isEditing && props.chapter?.id) {
      chapterData.id = props.chapter.id
    }
    
    emit('save', chapterData)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
:deep(.v-input__details) {
  margin-top: 4px;
}
</style> 