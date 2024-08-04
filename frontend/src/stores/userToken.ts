import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'

interface TokenItem {
  access_token: Object
}

export const useTokenStore = defineStore('user-token', () => {
  const tokenJson = ref('')
  const token = computed<TokenItem>(() => {
    try {
      return tokenJson.value // 接口返回的已经是对象了，无需进行 json 转换，如需：JSON.parse(tokenJson.value || '{}')
    } catch (error) {
      ElMessage.error('接口错误')
      throw error
    }
  })

  function saveToken(data: string) {
    tokenJson.value = data
  }

  return { token, saveToken }
})
