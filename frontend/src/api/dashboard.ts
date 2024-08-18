import { request_handler, type ResultPackage } from '@/api/base'

interface DashboardItem {
  registeredBrandNum: number
  productNum: number
  dailyActivity: number
  todayOrder: number
  totalSales: number
  conversionRate: number

  newUser: number

  knowledgeBasesNum: number
  digitalHumanNum: number
  LiveRoomNum: number
}

// 获取主控大屏信息
const getDashboardInfoRequest = () => {
  return request_handler<ResultPackage<DashboardItem>>({
    method: 'POST',
    url: '/dashboard'
  })
}

export { getDashboardInfoRequest, type DashboardItem }
