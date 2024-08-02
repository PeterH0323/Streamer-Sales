<template>
  <el-container class="layout-container-demo" style="height: 100vh">
    <el-aside width="200px">
      <el-scrollbar>
        <el-menu :router="true" :default-active="route.fullPath">
          <el-menu-item index="/home">
            <el-icon> <House /> </el-icon>首页
          </el-menu-item>
          <el-sub-menu index="/product">
            <template #title>
              <el-icon> <present /> </el-icon>商品管理
            </template>
            <el-menu-item index="/product/list">商品列表</el-menu-item>
            <el-menu-item index="/product/add">新增商品</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/system">
            <template #title>
              <el-icon> <setting /> </el-icon>系统配置
            </template>
            <el-menu-item index="/system/model">模型配置</el-menu-item>
            <el-menu-item index="/system/word">敏感词配置</el-menu-item>
            <el-menu-item index="/system/blacklist-question">疑问黑名单</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/digital-human">
            <template #title>
              <el-icon> <User /> </el-icon>数字人配置
            </template>
            <el-menu-item index="/digital-human/list">角色管理</el-menu-item>
            <el-menu-item index="/digital-human/upload">角色上传</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/streaming">
            <template #title>
              <el-icon> <Mic /> </el-icon>直播配置
            </template>
            <el-menu-item index="/streaming/overview">开始直播</el-menu-item>
          </el-sub-menu>
          <el-sub-menu index="/order">
            <template #title>
              <el-icon> <ShoppingCart /> </el-icon>订单管理
            </template>
            <el-menu-item index="/order/overview">订单总览</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header style="text-align: right; font-size: 12px">
        <div>
          <!-- 导航栏左侧 -->
          <!-- 面包屑 -->
          <BreadCrumb />
        </div>

        <div>
          <!-- 导航栏右边 -->
          <!-- 退出登录 -->
          <el-dropdown trigger="click">
            <span class="el-dropdown-link navbar-bg-hover">
              <img :src="userAvatar" :style="avatarsStyle" />
              <p v-if="username" class="dark:text-white">{{ username }}</p>
            </span>
            <template #dropdown>
              <el-dropdown-menu class="logout">
                <el-dropdown-item @click="logout">
                  <IconifyIconOffline :icon="LogoutCircleRLine" style="margin: 5px" />
                  退出系统
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
        <el-scrollbar>
          <router-view v-slot="{ Component }">
            <transition name="slide-fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-scrollbar>
      </el-main>
    </el-container>
  </el-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { Menu as Present, User, Mic, Setting, House, ShoppingCart } from '@element-plus/icons-vue'

import { useRoute } from 'vue-router'
import BreadCrumb from '@/components/BreadCrumb.vue'

const username = ref('小明')
const userAvatar = '@/assets/logo.png"'
const avatarsStyle = { marginRight: '10px' }

const route = useRoute()
</script>

<style scoped>
/*
  进入和离开动画可以使用不同
  持续时间和速度曲线。
*/
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.8s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

/* .layout-container-demo .el-header {
  position: relative;
  background-color: var(--el-color-primary-light-7);
  color: var(--el-text-color-primary);
} */

/* .layout-container-demo .el-aside {
  color: var(--el-text-color-primary);
  background: var(--el-color-primary-light-8);
} */

.layout-container-demo .el-menu {
  border-right: none;
}

.layout-container-demo .el-main {
  padding: 0;
}

.layout-container-demo .toolbar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  right: 20px;
}

/* 设置选中菜单项的背景色 */
.el-menu-item.is-active {
  background-color: #9997ee !important;
  color: #ffffff;
  /* 圆角的半径 */
  border-radius: 10px;
  /* 内边距 */
  padding: -10px;
}

/* 
.el-menu.hover {
  background-color: #ffffff;
} */
</style>
