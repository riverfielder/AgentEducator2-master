<template>
  <div>
    <!-- 编辑标题对话框 -->
    <v-dialog v-model="editDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">编辑对话标题</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editingTitle"
            label="对话标题"
            variant="outlined"
            dense
            :counter="50"
            :rules="[(v: string) => !!v || '标题不能为空', (v: string) => v.length <= 50 || '标题不能超过50个字符']"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="editDialog = false">取消</v-btn>
          <v-btn color="primary" @click="$emit('save-edit-title', editingTitle)">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 确认删除对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400px">
      <v-card>
        <v-card-title class="text-h5">确认删除</v-card-title>
        <v-card-text>
          确定要删除对话"{{ deletingChat?.title }}"吗？此操作不可撤销，将同时删除对话中的所有消息。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="$emit('confirm-delete')">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 内容审核警告弹窗 -->
    <v-dialog v-model="contentWarningDialog" max-width="500px">
      <v-card>
        <v-card-title class="text-h5 d-flex align-center">
          <v-icon color="warning" left>mdi-alert</v-icon>
          内容审核警告
        </v-card-title>
        <v-card-text>
          <div class="warning-content">
            <p class="text-body-1 mb-3">{{ contentWarningMessage }}</p>
            <v-alert type="warning" variant="tonal" class="mb-0">
              <div class="text-body-2">
                为了营造良好的学习环境，请使用文明用语进行交流。我们鼓励：
                <ul class="mt-2 ml-4">
                  <li>礼貌友善的提问方式</li>
                  <li>具体清晰的问题描述</li>
                  <li>积极正面的学习态度</li>
                </ul>
              </div>
            </v-alert>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="contentWarningDialog = false">我知道了</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Chat } from '../../types/chat'

interface Props {
  showEditDialog: boolean
  showDeleteDialog: boolean
  showContentWarning: boolean
  editingChat: Chat | null
  deletingChat: Chat | null
  contentWarningMessage: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:showEditDialog': [value: boolean]
  'update:showDeleteDialog': [value: boolean]
  'update:showContentWarning': [value: boolean]
  'save-edit-title': [title: string]
  'confirm-delete': []
}>()

const editDialog = ref(false)
const deleteDialog = ref(false)
const contentWarningDialog = ref(false)
const editingTitle = ref('')

// 监听props变化并同步到本地ref
watch(() => props.showEditDialog, (val) => {
  editDialog.value = val
  if (val && props.editingChat) {
    editingTitle.value = props.editingChat.title
  }
})

watch(() => props.showDeleteDialog, (val) => {
  deleteDialog.value = val
})

watch(() => props.showContentWarning, (val) => {
  contentWarningDialog.value = val
})

// 监听本地ref变化并通知父组件
watch(editDialog, (val) => {
  if (!val) {
    emit('update:showEditDialog', false)
  }
})

watch(deleteDialog, (val) => {
  if (!val) {
    emit('update:showDeleteDialog', false)
  }
})

watch(contentWarningDialog, (val) => {
  if (!val) {
    emit('update:showContentWarning', false)
  }
})
</script>

<style scoped>
/* 内容审核警告弹窗样式 */
.warning-content {
  line-height: 1.6;
}

.warning-content ul {
  margin: 0;
  padding-left: 1.2em;
}

.warning-content li {
  margin: 0.3em 0;
}
</style>
