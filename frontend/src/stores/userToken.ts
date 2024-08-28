import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

interface TokenItem {
  access_token: Object
}

export const useTokenStore = defineStore('user-token', {
  state: () => {
    const tokenJson = ref({} as TokenItem)
    const token = computed(() => {
      try {
        return tokenJson.value
      } catch (error) {
        ElMessage.error('接口错误')
        throw error
      }
    })

    function saveToken(data: TokenItem) {
      tokenJson.value = data
    }

    return { token, saveToken }
  },

  persist: {
    paths: ['token'], // 需要持久化保存的字段名
    storage: localStorage
  }
})
