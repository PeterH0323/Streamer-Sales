import { request_handler, type ResultPackage } from '@/api/base'
import { header_authorization } from '@/api/user'

// 获取后端主播信息
const genSalesDocRequest = (productId: number, streamerId: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'GET',
    url: '/llm/gen_sales_doc',
    params: { streamer_id: streamerId, product_id: productId },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 使用说明书总结生成商品信息接口
const genProductInfoByLlmRequest = (productId: number) => {
  return request_handler({
    method: 'GET',
    url: '/llm/gen_product_info',
    params: { product_id: productId },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

export { genSalesDocRequest, genProductInfoByLlmRequest }
