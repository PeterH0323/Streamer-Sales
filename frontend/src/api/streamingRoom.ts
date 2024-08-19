import { request_handler, type ResultPackage } from '@/api/base'

interface StreamingRoomProductList {
  product_id: number
  start_time: string
  sales_doc: string
  start_video: string
}

interface StreamingRoomInfo {
  id: number
  room_poster: string
  name: string
  streamer_id: number
  background_image: string
  prohibited_words_id: string
  product_list: StreamingRoomProductList[]
}

// 获取后端主播信息
const streamerRoomListRequest = () => {
  return request_handler<ResultPackage<StreamingRoomInfo[]>>({
    method: 'POST',
    url: '/streaming-room/list'
  })
}

// // 获取特定直播间信息
// const streamerDetailInfoRequest = (streamerId_: number) => {
//   return request_handler<ResultPackage<StreamerInfo[]>>({
//     method: 'POST',
//     url: '/streamer/info',
//     data: { streamerId: streamerId_ }
//   })
// }

export { type StreamingRoomInfo, streamerRoomListRequest }
