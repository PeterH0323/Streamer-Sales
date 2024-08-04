import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录页' }
    },
    {
      path: '/home',
      name: 'Home',
      component: () => import('@/components/LayoutComponent.vue'),
      meta: {
        title: '主页', // 面包屑显示标题
        requiresAuth: true // 是否需要登录验证，配置根路由即可，子路由会继承
      }
    },
    {
      path: '/product',
      name: 'Product',
      component: () => import('@/views/ProductInfoView.vue'),
      meta: { title: '商品管理', requiresAuth: true },
      children: [
        {
          path: '/product/list',
          name: 'ProductList',
          component: () => import('@/views/ProductInfoView.vue'),
          meta: { title: '商品列表' }
        },
        {
          path: '/product/add',
          name: 'ProductAdd',
          component: () => import('@/views/ProductInfoView.vue'),
          meta: { title: '新增商品' }
        }
      ],
      redirect: {
        name: 'ProductList'
      }
    },
    {
      path: '/system',
      name: 'System',
      component: () => import('@/views/SystemView.vue'),
      meta: { title: '系统配置', requiresAuth: true },
      children: [
        {
          path: '/system/model',
          name: 'SystemModel',
          component: () => import('@/views/SystemView.vue'),
          meta: { title: '模型配置' }
        },
        {
          path: '/system/word',
          name: 'SystemWord',
          component: () => import('@/views/SystemView.vue'),
          meta: { title: '敏感词配置' }
        },
        {
          path: '/system/blacklist-question',
          name: 'SystemBlacklistQuestion',
          component: () => import('@/views/SystemView.vue'),
          meta: { title: '疑问黑名单' }
        }
      ],
      redirect: {
        name: 'productList'
      }
    },
    {
      path: '/digital-human',
      name: 'DigitalHuman',
      component: () => import('@/views/DigitalHumanView.vue'),
      meta: { title: '数字人配置', requiresAuth: true },
      children: [
        {
          path: '/digital-human/list',
          name: 'DigitalHumanList',
          component: () => import('@/views/DigitalHumanView.vue'),
          meta: { title: '角色管理' }
        },
        {
          path: '/digital-human/upload',
          name: 'DigitalHumanUpload',
          component: () => import('@/views/DigitalHumanView.vue'),
          meta: { title: '角色上传' }
        }
      ],
      redirect: {
        name: 'DigitalHumanList'
      }
    },
    {
      path: '/streaming',
      name: 'Streaming',
      meta: { title: '直播配置', requiresAuth: true },
      component: () => import('@/views/StreamingView.vue'),
      children: [
        {
          path: '/streaming/overview',
          name: 'StreamingOverview',
          component: () => import('@/views/StreamingView.vue'),
          meta: { title: '开始直播' }
        }
      ],
      redirect: {
        name: 'StreamingOverview'
      }
    },
    {
      path: '/order',
      name: 'Order',
      component: () => import('@/views/OrderView.vue'),
      meta: { title: '订单总览', requiresAuth: true },
      children: [
        {
          path: '/order/overview',
          name: 'OrderOverview',
          component: () => import('@/views/OrderView.vue'),
          meta: { title: '订单管理' }
        }
      ],
      redirect: {
        name: 'OrderOverview'
      }
    },
    {
      path: '/',
      redirect: {
        name: 'Home'
      }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue')
    }
  ]
})

import { useTokenStore } from '@/stores/userToken'

router.beforeEach((to, from, next) => {
  //TODO 加入登录验证
  if (to.matched.some((r) => r.meta?.requiresAuth)) {
    // 登录状态缓存
    const tokenStore = useTokenStore()

    if (!tokenStore.token.access_token) {
      // 没有登录，跳转登录页面，同时记录 想去的地址 to.fullPath，方便执行登陆后跳转回去
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  // 动态更改页面 title
  to.matched.some((item) => {
    if (!item.meta.title) return ''

    const Title = '销冠——卖货主播大模型'
    if (Title) document.title = `${item.meta.title} | ${Title}`
    else document.title = item.meta.title as string
  })

  next()
})

export default router
