import { computed } from 'vue'
import { request_handler, type ResultPackage } from '@/api/base'
import { type TokenItem, useTokenStore } from '@/stores/userToken'

// 调用登录接口数据结构定义
type loginFormType = {
  username: string
  password: string
  vertify_code?: string
}

interface UserInfo {
  user_id: number
  username: string
  avatar: string
  email: string
  create_time: string
}

// pinia 保存的 token
const tokenStore = useTokenStore()

// jwt
const header_authorization = computed(() => {
  console.log('Update token')
  return `${tokenStore.token.token_type} ${tokenStore.token.access_token}`
})

// 登录接口
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

// 获取用户信息接口
const getUserInfoRequest = async () => {
  return request_handler<ResultPackage<UserInfo>>({
    method: 'GET',
    url: '/user/me',
    headers: {
      Authorization: header_authorization.value
    }
  })
}

export { loginRequest, header_authorization, getUserInfoRequest, type UserInfo }
