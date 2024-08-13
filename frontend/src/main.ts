import { createApp } from 'vue'
import { createPinia } from 'pinia'

import ElementPlus from 'element-plus'

import 'element-plus/dist/index.css'
import 'xgplayer/dist/index.min.css'

import '@/style/index.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.use(ElementPlus)
app.mount('#app')
