import axios from 'axios'

const request_handler = axios.create({
  // baseURL: import.meta.env.BASE_SERVER_URL
})

export default request_handler
