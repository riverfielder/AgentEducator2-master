<template>
  <div class="blank-layout">
    <slot></slot>
  </div>
</template>

<style scoped>
.blank-layout {
  min-height: 100vh;
  width: 100%;
  padding: 0;
  margin: 0;
  overflow-x: hidden;
}

/* 确保移动端正常滚动 */
@media (max-width: 768px) {
  .blank-layout {
    overflow-x: hidden;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
