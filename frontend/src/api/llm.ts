import { request_handler, type ResultPackage } from '@/api/base'
import type { StreamerInfo } from '@/api/streamerInfo'
import type { ProductListItem } from '@/api/product'

// 获取后端主播信息
const genSalesDocRequest = (productInfo: ProductListItem, salesInfo: StreamerInfo) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/llm/gen_sales_doc',
    data: { product_info: productInfo, sales_info: salesInfo }
  })
}

export { genSalesDocRequest }
