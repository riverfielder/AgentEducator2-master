<template>
  <v-card class="toolbar-card" elevation="2">
    <div class="toolbar-row">
      <div class="toolbar-label">题型：</div>
      <v-btn-toggle v-model="localType" class="toolbar-btn-group" rounded mandatory>
        <v-btn v-for="item in typeOptions" :key="item.value" :value="item.value" :color="localType === item.value ? 'primary' : ''" class="toolbar-btn">{{ item.label }}</v-btn>
      </v-btn-toggle>
    </div>
    <div class="toolbar-row">
      <div class="toolbar-label">难度：</div>
      <v-btn-toggle v-model="localDifficulty" class="toolbar-btn-group" rounded mandatory>
        <v-btn v-for="item in difficultyOptions" :key="item.value" :value="item.value" :color="localDifficulty === item.value ? 'primary' : ''" class="toolbar-btn">{{ item.label }}</v-btn>
      </v-btn-toggle>
    </div>
    <div class="toolbar-row">
      <div class="toolbar-label">课程：</div>
      <v-select
        v-model="localCourseId"
        :items="courseOptions"
        label="请选择课程"
        dense
        clearable
        class="toolbar-select-unified"
        variant="outlined"
        density="compact"
      />
    </div>
    <div class="toolbar-row">
      <div class="toolbar-label">知识点：</div>
      <v-select
        v-model="localTag"
        :items="tagOptions"
        label="请选择知识点"
        dense
        clearable
        class="toolbar-select-unified"
        variant="outlined"
        density="compact"
      />
    </div>
    <div class="toolbar-actions">
      <v-btn color="primary" @click="$emit('add')" class="toolbar-action-btn"><v-icon left>mdi-plus</v-icon>新增题目</v-btn>
      <v-btn color="secondary" class="ml-2 toolbar-action-btn" @click="$emit('import')"><v-icon left>mdi-upload</v-icon>批量导入</v-btn>
    </div>
  </v-card>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue';
const props = defineProps({
  courseOptions: { type: Array, default: () => [] },
  filterCourseId: { type: String, default: '' },
  tagOptions: { type: Array, default: () => [] },
  filterTag: { type: String, default: '' }
});
const emit = defineEmits(['update:filterCourseId', 'update:type', 'update:difficulty', 'update:filterTag', 'add', 'import']);

const typeOptions = [
  { label: '全部', value: '' },
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multiple' },
  { label: '填空题', value: 'blank' },
  { label: '简答题', value: 'essay' }
];
const difficultyOptions = [
  { label: '全部', value: '' },
  { label: '简单', value: 'easy' },
  { label: '普通', value: 'medium' },
  { label: '困难', value: 'hard' }
];

const localType = ref('');
const localDifficulty = ref('');
const localCourseId = ref(props.filterCourseId);
const localTag = ref(props.filterTag);

watch(localType, val => emit('update:type', val));
watch(localDifficulty, val => emit('update:difficulty', val));
watch(() => props.filterCourseId, v => localCourseId.value = v);
watch(localCourseId, v => {
  console.log('=== QuestionBankToolbar: 课程选择变化 ===');
  console.log('localCourseId变化为:', v);
  emit('update:filterCourseId', v);
});
watch(localTag, val => emit('update:filterTag', val));
</script>
<style scoped>
.toolbar-card {
  border-radius: 14px;
  padding: 24px 32px;
  margin-bottom: 16px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(60,60,60,0.06);
}
.toolbar-row {
  display: flex;
  align-items: center;
  margin-bottom: 18px;
}
.toolbar-label {
  font-weight: 500;
  font-size: 16px;
  margin-right: 18px;
  min-width: 56px;
  color: #333;
}
.toolbar-btn-group {
  margin-right: 12px;
}
.toolbar-btn {
  border-radius: 20px !important;
  min-width: 64px;
  margin-right: 8px;
  font-weight: 500;
}
.toolbar-select-unified {
  min-width: 280px;
  max-width: 280px;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  margin-top: 8px;
}
.toolbar-action-btn {
  border-radius: 20px;
  font-weight: 500;
  min-width: 120px;
  height: 40px;
}
</style>