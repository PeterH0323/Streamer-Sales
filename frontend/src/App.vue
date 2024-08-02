<template>
  <el-container class="layout-container-demo">
    <!-- 侧边栏 -->
    <el-scrollbar>
      <AslideComponent />
    </el-scrollbar>

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

import AslideComponent from '@/components/AslideComponent.vue'
import BreadCrumb from '@/components/BreadCrumb.vue'

const username = ref('小明')
const userAvatar = '@/assets/logo.png"'
const avatarsStyle = { marginRight: '10px' }
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

.layout-container-demo .toolbar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  right: 20px;
}

/* 
.el-menu.hover {
  background-color: #ffffff;
} */
</style>
