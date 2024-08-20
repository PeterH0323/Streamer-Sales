import { request_handler, type ResultPackage } from '@/api/base'

// 获取后端主播信息
const genSalesDocRequest = (productId_: number, streamerId_: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/llm/gen_sales_doc',
    data: { productId: productId_, streamerId: streamerId_ }
  })
}

export { genSalesDocRequest }
