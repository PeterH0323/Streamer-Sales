import { request_handler, type ResultPackage } from '@/api/base'

interface StreamerInfo {
  id: number
  name: string
  value: string
  character: string[]
  avater: string
  tts_weight_tag: string
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

// 更新特定主播信息
const streamerEditDetailRequest = async (streamerItem: StreamerInfo) => {
  return request_handler<ResultPackage<number>>({
    method: 'POST',
    url: '/streamer/edit',
    data: streamerItem
  })
}

// 删除特定主播信息
const deleteStreamerByIdRequest = (streamerId_: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/streamer/delete',
    data: { streamerId: streamerId_ }
  })
}

export {
  type StreamerInfo,
  streamerInfoListRequest,
  streamerDetailInfoRequest,
  streamerEditDetailRequest,
  deleteStreamerByIdRequest
}
