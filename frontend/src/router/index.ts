import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/LoginView.vue'),
      meta: {
        title: '登录页' // 面包屑显示标题
      }
    },
    {
      path: '/',
      redirect: { name: 'Home' },
      component: () => import('@/layouts/BaseLayout.vue'),
      meta: {
        requiresAuth: true // 是否需要登录验证，配置根路由即可，子路由会继承
      },
      children: [
        {
          path: '/home',
          name: 'Home',
          component: () => import('@/views/home/HomeView.vue'),
          meta: { title: '主页' }
        },
        // ---------------------
        //       商品
        // ---------------------
        {
          path: '/product',
          name: 'Product',
          redirect: { name: 'ProductList' },
          meta: { title: '商品管理' },
          children: [
            {
              path: '/product/list',
              name: 'ProductList',
              component: () => import('@/views/product/ProductListView.vue'),
              meta: { title: '商品列表' }
            },
            {
              path: '/product/create',
              name: 'ProductCreate',
              component: () => import('@/views/product/ProductEditView.vue'),
              meta: { title: '新增商品' }
            },
            {
              path: '/product/:productId/edit',
              name: 'ProductEdit',
              component: () => import('@/views/product/ProductEditView.vue'),
              meta: { title: '商品修改' },
              props: true
            }
          ]
        },
        // ---------------------
        //       系统配置
        // ---------------------
        {
          path: '/system',
          name: 'System',
          redirect: { name: 'SystemModel' },
          meta: { title: '系统配置' },
          children: [
            {
              path: '/system/model',
              name: 'SystemModel',
              component: () => import('@/views/system/SystemView.vue'),
              meta: { title: '模型配置' }
            },
            {
              path: '/system/word',
              name: 'SystemWord',
              component: () => import('@/views/system/SystemView.vue'),
              meta: { title: '敏感词配置' }
            },
            {
              path: '/system/blacklist-question',
              name: 'SystemBlacklistQuestion',
              component: () => import('@/views/system/SystemView.vue'),
              meta: { title: '疑问黑名单' }
            }
          ]
        },
        // ---------------------
        //       数字人配置
        // ---------------------
        {
          path: '/digital-human',
          name: 'DigitalHuman',
          redirect: { name: 'DigitalHumanList' },
          meta: { title: '数字人配置' },
          children: [
            {
              path: '/digital-human/list',
              name: 'DigitalHumanList',
              component: () => import('@/views/digital-human/DigitalHumanView.vue'),
              meta: { title: '角色管理' }
            }
          ]
        },
        // ---------------------
        //       直播配置
        // ---------------------

        {
          path: '/streaming',
          name: 'Streaming',
          redirect: { name: 'StreamingOverview' },
          meta: { title: '直播配置' },
          children: [
            {
              path: '/streaming/overview',
              name: 'StreamingOverview',
              component: () => import('@/views/streaming/StreamingRoomListView.vue'),
              meta: { title: '直播间管理' }
            },
            {
              path: '/streaming/create',
              name: 'StreamingCreated',
              component: () => import('@/views/streaming/StreamingRoomeEditView.vue'),
              meta: { title: '新建直播间' }
            },
            {
              path: '/streaming/:roomId/edit',
              name: 'StreamingEdit',
              component: () => import('@/views/streaming/StreamingRoomeEditView.vue'),
              meta: { title: '编辑直播间' },
              props: true
            },
            {
              path: '/streaming/:roomId/on-air',
              name: 'StreamingOnAir',
              component: () => import('@/views/streaming/StreamingOnAirView.vue'),
              meta: { title: '直播间' },
              props: true
            }
          ]
        },
        // ---------------------
        //       订单管理
        // ---------------------
        {
          path: '/order',
          name: 'Order',
          redirect: { name: 'OrderOverview' },
          meta: { title: '订单管理' },
          children: [
            {
              path: '/order/overview',
              name: 'OrderOverview',
              component: () => import('@/views/order/OrderView.vue'),
              meta: { title: '订单管理' }
            }
          ]
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFound.vue'),
      meta: { title: '404' }
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
