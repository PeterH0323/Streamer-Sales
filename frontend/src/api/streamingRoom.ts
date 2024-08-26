import { request_handler, type ResultPackage } from '@/api/base'
import { type StreamerInfo, type ProductListItem } from '@/api/product'

interface StreamingRoomProductList {
  product_id: number
  start_time: string
  sales_doc: string
  start_video: string
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
  currentProductInfo: ProductListItem
  currentStreamerVideo: string
  currentProductIndex: number
  startTime: string
  currentPoductStartTime: string
  finalProduct: boolean
}

interface StreamingRoomInfo {
  roomId: number
  room_poster: string
  name: string
  streamer_id: number
  background_image: string
  prohibited_words_id: string
  product_list: StreamingRoomProductList[]
  status: StreamingRoomStatusItem
}

interface RoomProductData {
  currentPage: number
  pageSize: number
  totalSize: number
  product: ProductItem[]
}
interface ProductItem {
  name: string
  id: number
  image: string
  sales_doc: string
  start_video: string
  start_time: string
  selected: boolean
}

interface RoomDetailItem {
  currentPage?: number
  pageSize?: number
  totalSize?: number
  product: []
  streamerInfo: StreamerInfo
  roomId: number
  name: string
  room_poster: string
  streamer_id: string
  background_image: string
  prohibited_words_id: string
  liveStatus: number
  status: StreamingRoomStatusItem
}

// 获取后端主播信息
const streamerRoomListRequest = () => {
  return request_handler<ResultPackage<StreamingRoomInfo[]>>({
    method: 'POST',
    url: '/streaming-room/list'
  })
}

// 获取特定直播间的详情
const roomDetailRequest = (roomId_: string, currentPage_: number, pageSize_: number) => {
  return request_handler<ResultPackage<RoomDetailItem>>({
    method: 'POST',
    url: '/streaming-room/detail',
    data: { roomId: roomId_, currentPage: currentPage_, pageSize: pageSize_ }
  })
}

// 添加商品的时候，获取所有商品，内含选中商品
const roomPorductAddListRequest = (roomId_: number, currentPage_: number, pageSize_: number) => {
  return request_handler<ResultPackage<RoomProductData>>({
    method: 'POST',
    url: '/streaming-room/product-add',
    data: { roomId: roomId_, currentPage: currentPage_, pageSize: pageSize_ }
  })
}

// 添加或者更新直播间接口
const RoomCreadeOrEditRequest = async (params: RoomDetailItem) => {
  return request_handler<ResultPackage<number>>({
    method: 'POST',
    url: '/streaming-room/edit/form',
    data: params
  })
}

// 获取直播间实时信息：主播目前的视频地址，目前讲述的商品信息，聊天信息
const onAirRoomInfoRequest = (roomId_: number) => {
  return request_handler<ResultPackage<StreamingRoomStatusItem>>({
    method: 'POST',
    url: '/streaming-room/live-info',
    data: { roomId: roomId_ }
  })
}

// 用户发起对话
const onAirRoomChatRequest = async (roomId_: number, userId_: string, message_: string) => {
  return request_handler<ResultPackage<messageItem>>({
    method: 'POST',
    url: '/streaming-room/chat',
    data: { roomId: roomId_, userId: userId_, message: message_ }
  })
}

// 获取直播间实时信息：主播目前的视频地址，目前讲述的商品信息，聊天信息
const onAirRoomNextProductRequest = async (roomId_: number) => {
  return request_handler<ResultPackage<messageItem>>({
    method: 'POST',
    url: '/streaming-room/next-product',
    data: { roomId: roomId_ }
  })
}

export {
  type StreamingRoomInfo,
  type ProductItem,
  type RoomProductData,
  type RoomDetailItem,
  type StreamingRoomStatusItem,
  streamerRoomListRequest,
  roomDetailRequest,
  roomPorductAddListRequest,
  RoomCreadeOrEditRequest,
  onAirRoomInfoRequest,
  onAirRoomChatRequest,
  onAirRoomNextProductRequest
}
