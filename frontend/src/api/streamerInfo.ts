import { request_handler, type ResultPackage } from '@/api/base'

interface StreamerInfo {
  id: number
  name: string
  character: string
  value: string
  imageUrl: string
  videoUrl: string
}

// 获取后端主播信息
const streamerInfoListRequest = () => {
  return request_handler<ResultPackage<StreamerInfo[]>>({
    method: 'POST',
    url: '/streamer/list'
  })
}

export { type StreamerInfo, streamerInfoListRequest }
