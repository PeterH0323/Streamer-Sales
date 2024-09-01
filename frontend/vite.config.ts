import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    proxy: {
      '/user': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/products': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/upload': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/streamer': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/llm': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/dashboard': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/streaming-room': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/plugins_info': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
      '/digital-human': loadEnv('', process.cwd()).VITE_BASE_SERVER_URL
    }
  },
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
