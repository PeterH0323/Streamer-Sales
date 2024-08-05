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
      path: '/',
      redirect: {
        name: 'Home'
      },
      component: () => import('@/components/LayoutComponent.vue'),
      meta: {
        requiresAuth: true // 是否需要登录验证，配置根路由即可，子路由会继承
      },
      children: [
        {
          path: '/home',
          name: 'Home',
          component: () => import('@/views/HomeView.vue'),
          meta: {
            title: '主页' // 面包屑显示标题
          }
        },
        // ---------------------
        //       商品
        // ---------------------
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
        },
        // ---------------------
        //       系统配置
        // ---------------------
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
        },
        // ---------------------
        //       数字人配置
        // ---------------------
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
        },
        // ---------------------
        //       直播配置
        // ---------------------
        {
          path: '/streaming/overview',
          name: 'StreamingOverview',
          component: () => import('@/views/StreamingView.vue'),
          meta: { title: '开始直播' }
        },
        // ---------------------
        //       订单管理
        // ---------------------
        {
          path: '/order/overview',
          name: 'OrderOverview',
          component: () => import('@/views/OrderView.vue'),
          meta: { title: '订单管理' }
        },
        // ---------------------
        //       重定向
        // ---------------------
        {
          path: '/product',
          name: 'Product',
          redirect: { name: 'ProductList' }
        },
        {
          path: '/system',
          name: 'System',
          redirect: { name: 'productList' }
        },
        {
          path: '/digital-human',
          name: 'DigitalHuman',
          redirect: { name: 'DigitalHumanList' }
        },
        {
          path: '/streaming',
          name: 'Streaming',
          redirect: { name: 'StreamingOverview' }
        },
        {
          path: '/order',
          name: 'Order',
          redirect: { name: 'OrderOverview' }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue'),
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
