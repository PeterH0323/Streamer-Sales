import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    proxy: {
      '/user': {
        target: loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
        changeOrigin: true
      },
      '/product': {
        target: loadEnv('', process.cwd()).VITE_BASE_SERVER_URL,
        changeOrigin: true
      }
    }
  },
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
