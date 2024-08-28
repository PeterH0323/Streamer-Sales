import { createApp } from 'vue'

import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import ElementPlus from 'element-plus'

import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import 'xgplayer/dist/index.min.css'

import '@/style/index.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate) // 持久化储存插件

app.use(pinia)
app.use(router)

app.use(ElementPlus, {
  locale: zhCn
})
app.mount('#app')
