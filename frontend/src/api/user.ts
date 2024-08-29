import { request_handler, type ResultPackage } from '@/api/base'
import { type TokenItem } from '@/stores/userToken'

// 调用登录接口数据结构定义
type loginFormType = {
  username: string
  password: string
  vertify_code?: string
}

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

export { loginRequest }
