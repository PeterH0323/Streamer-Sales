import { request_handler, type ResultPackage } from '@/api/base'

interface DashboardItem {
  registeredBrandNum: number //入驻品牌方
  productNum: number //商品数
  dailyActivity: number //日活
  todayOrder: number //订单量
  totalSales: number //销售额
  conversionRate: number //转化率

  orderNumList: number[] // 订单量
  totalSalesList: number[] // 销售额
  newUserList: number[] // 新增用户
  activityUserList: number[] // 活跃用户

  knowledgeBasesNum: number // 知识库数量
  digitalHumanNum: number // 数字人数量
  LiveRoomNum: number // 直播间数量
}

// 获取主控大屏信息
const getDashboardInfoRequest = () => {
  return request_handler<ResultPackage<DashboardItem>>({
    method: 'GET',
    url: '/dashboard'
  })
}

export { getDashboardInfoRequest, type DashboardItem }
