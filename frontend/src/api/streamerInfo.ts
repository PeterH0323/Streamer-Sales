import { request_handler, type ResultPackage } from '@/api/base'

interface StreamerInfo {
  id: number
  name: string
  value: string
  character: string
  tts_weight_path: string
  tts_tag: string
  tts_reference_audio: string
  tts_reference_sentence: string
  poster_image: string
  base_mp4_path: string
}

// 获取后端主播信息
const streamerInfoListRequest = () => {
  return request_handler<ResultPackage<StreamerInfo[]>>({
    method: 'POST',
    url: '/streamer/list'
  })
}

// 获取特定主播信息
const streamerDetailInfoRequest = (streamerId_: number) => {
  return request_handler<ResultPackage<StreamerInfo[]>>({
    method: 'POST',
    url: '/streamer/info',
    data: { streamerId: streamerId_ }
  })
}

export { type StreamerInfo, streamerInfoListRequest, streamerDetailInfoRequest }
