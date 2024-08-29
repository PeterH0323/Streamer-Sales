import { request_handler } from '@/api/base'

// 生成数字人视频接口
const genDigitalHuamnVideoRequest = (streamerId_: number, salesDoc_: string) => {
  return request_handler({
    method: 'POST',
    url: '/digital-human/gen',
    data: { streamerId: streamerId_, salesDoc: salesDoc_ }
  })
}

export { genDigitalHuamnVideoRequest }
