import { request_handler, type ResultPackage } from '@/api/base'
import { header_authorization } from '@/api/user'

interface StreamerInfo {
  user_id: number

  streamer_id: number
  name: string
  value: string
  character: string
  avatar: string

  tts_weight_tag: string
  tts_reference_audio: string
  tts_reference_sentence: string

  poster_image: string
  base_mp4_path: string

  delete: boolean
}

// 获取后端主播信息
const streamerInfoListRequest = () => {
  return request_handler<ResultPackage<StreamerInfo[]>>({
    method: 'GET',
    url: '/streamer/list',
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 获取特定主播信息
const streamerDetailInfoRequest = (streamerId: number) => {
  return request_handler<ResultPackage<StreamerInfo>>({
    method: 'GET',
    url: `/streamer/info/${streamerId}`,
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 更新特定主播信息
const streamerEditDetailRequest = async (streamerItem: StreamerInfo) => {
  if (typeof streamerItem.streamer_id != 'number' || streamerItem.streamer_id === 0) {
    // 新建
    console.info(streamerItem)
    return request_handler<ResultPackage<number>>({
      method: 'POST',
      url: '/streamer/create',
      data: streamerItem,
      headers: {
        Authorization: header_authorization.value
      }
    })
  } else {
    return request_handler<ResultPackage<number>>({
      method: 'PUT',
      url: `/streamer/edit/${streamerItem.streamer_id}`,
      data: streamerItem,
      headers: {
        Authorization: header_authorization.value
      }
    })
  }
}

// 删除特定主播信息
const deleteStreamerByIdRequest = (streamerId: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'DELETE',
    url: `/streamer/delete/${streamerId}`,
    headers: {
      Authorization: header_authorization.value
    }
  })
}

export {
  type StreamerInfo,
  streamerInfoListRequest,
  streamerDetailInfoRequest,
  streamerEditDetailRequest,
  deleteStreamerByIdRequest
}
