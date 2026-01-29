/// <reference types="vite/client" />
/// <reference types="vue/dist/vue.d.ts" />
/// <reference types="vuetify/dist/vuetify.d.ts" />

declare module '*.vue' {
  import type { ComponentOptions } from 'vue'
  const component: ComponentOptions
  export default component
}

// 确保 TypeScript 识别 Vue 的全局类型
import 'vue/jsx'