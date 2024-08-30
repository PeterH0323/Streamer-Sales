import { ref } from 'vue'
import { defineStore } from 'pinia'

interface TokenItem {
  access_token: string
  token_type: string
}

const useTokenStore = defineStore('user-token', {
  state: () => {
    const token = ref({} as TokenItem)

    function saveToken(data: TokenItem) {
      token.value = data
    }

    return { token, saveToken }
  },

  persist: {
    paths: ['token'], // 需要持久化保存的字段名
    storage: localStorage
  }
})

export { type TokenItem, useTokenStore }
