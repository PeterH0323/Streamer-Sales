import { request_handler } from '@/api/base'

// 生成数字人视频接口
const genDigitalHuamnVideoRequest = (salesDoc_: string) => {
  return request_handler({
    method: 'POST',
    url: '/digital-human/gen',
    data: { salesDoc: salesDoc_ }
  })
}

export { genDigitalHuamnVideoRequest }
