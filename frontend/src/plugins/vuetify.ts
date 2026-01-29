import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

// 移除直接导入，改为在main.ts中导入
// import '@mdi/font/css/materialdesignicons.min.css'
// import '@fortawesome/fontawesome-free/css/all.css'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#6B46C1',
          secondary: '#805AD5',
          accent: '#9F7AEA',
          background: '#F7FAFC',
          surface: '#FFFFFF',
          error: '#E53E3E',
          info: '#4299E1',
          success: '#48BB78',
          warning: '#ECC94B',
        },
      },
    },
  },
  defaults: {
    VBtn: {
      color: 'primary',
      variant: 'flat',
    },
    VCard: {
      elevation: 2,
      rounded: 'lg',
    },
  },
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
}) 