import { request_handler, type ResultPackage } from '@/api/base'
import { type StreamerInfo } from '@/api/product'

interface StreamingRoomProductList {
  product_id: number
  start_time: string
  sales_doc: string
  start_video: string
}

interface StreamingRoomInfo {
  roomId: number
  room_poster: string
  name: string
  streamer_id: number
  background_image: string
  prohibited_words_id: string
  product_list: StreamingRoomProductList[]
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
  start_stramer_video: string
  start_time: string
  selected: boolean
}

interface RoomDetailItem {
  currentPage: number
  pageSize: number
  totalSize: number
  product: []
  streamerInfo: StreamerInfo
  roomId: number
  name: string
  room_poster: string
  streamer_id: string
  background_image: string
  prohibited_words_id: string
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
const RoomCreadeOrEditRequest = (params: RoomDetailItem) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/streaming-room/edit/form',
    data: params
  })
}

export {
  type StreamingRoomInfo,
  type ProductItem,
  type RoomProductData,
  type RoomDetailItem,
  streamerRoomListRequest,
  roomDetailRequest,
  roomPorductAddListRequest,
  RoomCreadeOrEditRequest
}
