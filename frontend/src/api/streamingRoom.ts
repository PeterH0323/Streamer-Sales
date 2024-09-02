import { request_handler, type ResultPackage } from '@/api/base'
import type { StreamerInfo, ProductItem } from '@/api/product'
import { header_authorization } from '@/api/user'

interface StreamingRoomProductList extends ProductItem {
  product_id: number
  start_time: string
  sales_doc: string
  start_video: string
  selected: boolean
}

interface messageItem {
  role: string
  userId: string
  userName: string
  avater: string
  message: string
  datetime: string
}

interface StreamingRoomStatusItem {
  streamerInfo: StreamerInfo
  conversation: messageItem[]
  currentProductInfo: ProductItem
  currentStreamerVideo: string
  currentProductIndex: number
  start_time: string
  currentPoductStartTime: string
  finalProduct: boolean
  live_status: number
}

interface StreamingRoomInfo {
  room_id: number
  room_poster: string
  name: string
  streamer_id: number
  background_image: string
  prohibited_words_id: number
  product_list: StreamingRoomProductList[]
  streamer_info: StreamerInfo
  status: StreamingRoomStatusItem
}

interface RoomProductData {
  currentPage: number
  pageSize: number
  totalSize: number
  product_list: StreamingRoomProductList[]
}

interface RoomProductItem {
  name: string
  id: number
  image_path: string
  sales_doc: string
  start_video: string
  start_time: string
  selected: boolean
  heighlights: string
  selling_price: number
}

interface RoomDetailItem {
  currentPage: number
  pageSize: number
  totalSize: number
  product_list: StreamingRoomProductList[]
  streamer_info: StreamerInfo
  room_id: number
  name: string
  room_poster: string
  streamer_id: number
  background_image: string
  prohibited_words_id: number
  status: StreamingRoomStatusItem
}

// 获取后端主播信息
const streamerRoomListRequest = () => {
  return request_handler<ResultPackage<StreamingRoomInfo[]>>({
    method: 'POST',
    url: '/streaming-room/list',
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 获取特定直播间的详情
const roomDetailRequest = (roomId_: string, currentPage_: number, pageSize_: number) => {
  return request_handler<ResultPackage<RoomDetailItem>>({
    method: 'POST',
    url: '/streaming-room/detail',
    data: { roomId: roomId_, currentPage: currentPage_, pageSize: pageSize_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 添加商品的时候，获取所有商品，内含选中商品
const roomPorductAddListRequest = (roomId_: number, currentPage_: number, pageSize_: number) => {
  return request_handler<ResultPackage<RoomProductData>>({
    method: 'POST',
    url: '/streaming-room/product-add',
    data: { roomId: roomId_, currentPage: currentPage_, pageSize: pageSize_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 添加或者更新直播间接口
const RoomCreadeOrEditRequest = async (params: RoomDetailItem) => {
  return request_handler<ResultPackage<number>>({
    method: 'POST',
    url: '/streaming-room/edit/form',
    data: params,
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 获取直播间实时信息：主播目前的视频地址，目前讲述的商品信息，聊天信息
const onAirRoomInfoRequest = (roomId_: number) => {
  return request_handler<ResultPackage<StreamingRoomStatusItem>>({
    method: 'POST',
    url: '/streaming-room/live-info',
    data: { roomId: roomId_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 用户发起对话
const onAirRoomChatRequest = async (roomId_: number, userId_: string, message_: string) => {
  return request_handler<ResultPackage<messageItem>>({
    method: 'POST',
    url: '/streaming-room/chat',
    data: { roomId: roomId_, userId: userId_, message: message_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 获取直播间实时信息：主播目前的视频地址，目前讲述的商品信息，聊天信息
const onAirRoomNextProductRequest = async (roomId_: number) => {
  return request_handler<ResultPackage<StreamingRoomStatusItem>>({
    method: 'POST',
    url: '/streaming-room/next-product',
    data: { roomId: roomId_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 删除特定直播间信息
const deleteStreamingRoomByIdRequest = (roomId_: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/streaming-room/delete',
    data: { roomId: roomId_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 发送音频文件到服务器
const sendAudioToServer = async (blob: Blob) => {
  const formData = new FormData()
  formData.append('file', blob, 'recording.webm')

  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/upload/file',
    data: formData,
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 获取 ASR 结果
const genAsrResult = async (roomId_: number, userId_: string, asrFileUrl_: string) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/streaming-room/asr',
    data: { roomId: roomId_, userId: userId_, asrFileUrl: asrFileUrl_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 下播
const streamRoomOffline = (roomId_: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/streaming-room/offline',
    data: { roomId: roomId_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

export {
  type StreamingRoomInfo,
  type RoomProductItem,
  type RoomProductData,
  type RoomDetailItem,
  type StreamingRoomStatusItem,
  type StreamingRoomProductList,
  streamerRoomListRequest,
  roomDetailRequest,
  roomPorductAddListRequest,
  RoomCreadeOrEditRequest,
  onAirRoomInfoRequest,
  onAirRoomChatRequest,
  onAirRoomNextProductRequest,
  deleteStreamingRoomByIdRequest,
  sendAudioToServer,
  streamRoomOffline,
  genAsrResult
}
