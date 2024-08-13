import request_handler from '@/api/base'

interface StreamerInfo {
  id: number
  name: string
  character: string
  value: string
  imageUrl: string
  videoUrl: string
}

// 登录接口返回数据结构定义
interface StreamerInfoResultType<T> {
  status: number
  message: string
  data: T
  timestamp: string
}

// 获取后端主播信息
const streamerInfoListRequest = () => {
  return request_handler<StreamerInfoResultType<StreamerInfo[]>>({
    method: 'POST',
    url: '/streamer/list'
  })
}

export { type StreamerInfo, streamerInfoListRequest }
