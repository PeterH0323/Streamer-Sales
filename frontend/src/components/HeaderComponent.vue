<template>
  <el-header>
    <!-- 菜单折叠图标 -->
    <el-icon @click="isCollapse = !isCollapse">
      <Fold v-show="isCollapse" />
      <Expand v-show="!isCollapse" />
    </el-icon>

    <!-- 导航栏左侧 -->
    <!-- 面包屑 -->
    <BreadCrumb />

    <!-- <div> -->
    <!-- 导航栏右边 -->
    <!-- 退出登录 -->
    <el-dropdown trigger="click">
      <!-- <span class="el-dropdown-link navbar-bg-hover">
        <img :src="userAvatar" :style="avatarsStyle" />
        <p v-if="username" class="dark:text-white">{{ username }}</p>
      </span> -->
      <el-avatar :size="40" :src="circleUrl" />
      <template #dropdown>
        <el-dropdown-menu class="logout">
          <el-dropdown-item>{{ username }}</el-dropdown-item>
          <el-dropdown-item>用户配置</el-dropdown-item>
          <el-dropdown-item @click="logout">
            <!-- <IconifyIconOffline :icon="LogoutCircleRLine" style="margin: 5px" /> -->
            退出系统
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </el-header>
</template>

<script lang="ts" setup>
import { Fold, Expand } from '@element-plus/icons-vue'

import { ref, reactive, toRefs } from 'vue'

import { isCollapse } from '@/utils/navbar'

import BreadCrumb from '@/components/BreadCrumb.vue'

const username = ref('小明')
const userAvatar = '@/assets/logo.png"'
const avatarsStyle = { marginRight: '10px' }

const state = reactive({
  circleUrl: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
})

const { circleUrl } = toRefs(state)
</script>

<style lang="scss" scoped>
.el-header {
  display: flex; // 水平显示
  align-items: center;
  background-color: #ffffff; // 背景颜色

  .el-icon {
    margin-right: 15px; // 折叠按钮右边预留空隙
  }
}

.el-dropdown {
  margin-left: auto; //让头像往右边靠
}
</style>
