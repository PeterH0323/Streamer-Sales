import axios from 'axios'

const request_handler = axios.create({
  // baseURL: import.meta.env.BASE_SERVER_URL
})

interface ResultPackage<T> {
  success: boolean
  code: number
  message: string
  data: T
  timestamp: number
}

export { request_handler }
export { type ResultPackage }
