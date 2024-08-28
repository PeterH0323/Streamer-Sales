import { request_handler, type ResultPackage } from '@/api/base'
import { type TokenItem } from '@/stores/userToken'

// 调用登录接口数据结构定义
type loginFormType = {
  username: string
  password: string
  vertify_code?: string
}

const loginRequest = (loginForm: loginFormType) => {
  return request_handler<ResultPackage<TokenItem>>({
    method: 'POST',
    url: '/user/login',
    data: loginForm
  })
}

export { loginRequest }
