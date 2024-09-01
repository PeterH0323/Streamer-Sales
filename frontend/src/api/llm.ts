import { request_handler, type ResultPackage } from '@/api/base'
import { header_authorization } from '@/api/user'

// 获取后端主播信息
const genSalesDocRequest = (productId_: number, streamerId_: number) => {
  return request_handler<ResultPackage<string>>({
    method: 'POST',
    url: '/llm/gen_sales_doc',
    data: { productId: productId_, streamerId: streamerId_ },
    headers: {
      Authorization: header_authorization.value
    }
  })
}

// 使用说明书总结生成商品信息接口
const genProductInfoByLlmRequest = (salesDoc: string) => {
  return request_handler({
    method: 'POST',
    url: '/llm/gen_product_info',
    data: salesDoc,
    headers: {
      Authorization: header_authorization.value
    }
  })
}

export { genSalesDocRequest, genProductInfoByLlmRequest }
