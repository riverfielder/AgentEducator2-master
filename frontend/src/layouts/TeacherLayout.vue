<template>
  <div class="teacher-layout-wrapper">
    <v-container fluid class="teacher-layout pa-0">
      <v-row no-gutters style="height: calc(100vh - 56px);">
        <v-col cols="auto">
          <Sidebar />
        </v-col>
        <v-col class="content-area">
          <router-view></router-view>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '../components/Sidebar.vue';
</script>

<style scoped>
.teacher-layout-wrapper {
  width: 100%;
  height: calc(100vh - 56px);  /* 减去Header高度 */
  overflow: hidden;
  background-color: #f5f7fa;
}

.teacher-layout {
  height: 100%;
}

.content-area {
  height: calc(100vh - 56px);  /* 减去Header高度 */
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

/* 确保router-view占满整个内容区域 */
.content-area :deep(> *) {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
