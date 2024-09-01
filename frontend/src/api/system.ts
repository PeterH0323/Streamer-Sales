import { request_handler, type ResultPackage } from '@/api/base'

interface SystemPluginsInfo {
  plugin_name: string
  describe: string
  avatar_color: string
  enabled: boolean
}

// 删除特定主播信息
const getSystemPluginsInfoRequest = () => {
  return request_handler<ResultPackage<SystemPluginsInfo[]>>({
    method: 'GET',
    url: '/plugins_info'
  })
}

export { type SystemPluginsInfo, getSystemPluginsInfoRequest }
