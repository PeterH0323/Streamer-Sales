import request_handler from '@/api/base'

// 调用登录接口数据结构定义
type loginFormType = {
  name: string
  password: string
  vertify_code?: string
}

// 登录接口返回数据结构定义
type loginResultType = {
  success: boolean
  state: number
  message: string
  content: string
}

const login_request = (loginForm: loginFormType) => {
  return request_handler<loginResultType>({
    method: 'POST',
    url: '/user/login',
    data: loginForm
  })

  // return true
}

export { login_request }
