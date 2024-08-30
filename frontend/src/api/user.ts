import { computed } from 'vue'
import { request_handler } from '@/api/base'
import { type TokenItem, useTokenStore } from '@/stores/userToken'

// 调用登录接口数据结构定义
type loginFormType = {
  username: string
  password: string
  vertify_code?: string
}

// pinia 保存的 token
const tokenStore = useTokenStore()

const header_authorization = computed(() => {
  console.log('Update token')
  return `${tokenStore.token.token_type} ${tokenStore.token.access_token}`
})

const loginRequest = (loginForm: loginFormType) => {
  const formData = new FormData()
  formData.append('username', loginForm.username)
  formData.append('password', loginForm.password)

  return request_handler<TokenItem>({
    method: 'POST',
    url: '/user/login',
    data: formData,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
}

export { loginRequest, header_authorization }
