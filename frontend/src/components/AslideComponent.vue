<template>
  <el-aside>
    <el-menu :router="true" :default-active="route.fullPath" :collapse="isCollapse">
      <!-- logo -->
      <div class="logo">
        <a herf="/">
          <img src="@/assets/logo.png" alt="" />
        </a>
      </div>
      <div class="logo">
        <h1>销冠 —— 卖货主播大模型</h1>
      </div>

      <el-menu-item index="/home">
        <el-icon> <House /> </el-icon> <span>首页</span>
      </el-menu-item>
      <el-sub-menu index="/product">
        <template #title>
          <el-icon> <present /> </el-icon><span>商品管理</span>
        </template>
        <el-menu-item index="/product/list"><span>商品列表</span></el-menu-item>
        <el-menu-item index="/product/add"><span>新增商品</span></el-menu-item>
      </el-sub-menu>
      <el-sub-menu index="/system">
        <template #title>
          <el-icon> <setting /> </el-icon><span>系统配置</span>
        </template>
        <el-menu-item index="/system/model"><span>模型配置</span></el-menu-item>
        <el-menu-item index="/system/word"><span>敏感词配置</span></el-menu-item>
        <el-menu-item index="/system/blacklist-question"><span>疑问黑名单</span></el-menu-item>
      </el-sub-menu>
      <el-sub-menu index="/digital-human">
        <template #title>
          <el-icon> <User /> </el-icon><span>数字人配置</span>
        </template>
        <el-menu-item index="/digital-human/list"><span>角色管理</span></el-menu-item>
        <el-menu-item index="/digital-human/upload"><span>角色上传</span></el-menu-item>
      </el-sub-menu>
      <el-sub-menu index="/streaming">
        <template #title>
          <el-icon> <Mic /> </el-icon><span>直播配置</span>
        </template>
        <el-menu-item index="/streaming/overview">开始直播<span></span></el-menu-item>
      </el-sub-menu>
      <el-sub-menu index="/order">
        <template #title>
          <el-icon> <ShoppingCart /> </el-icon><span>订单管理</span>
        </template>
        <el-menu-item index="/order/overview"><span>订单总览</span></el-menu-item>
      </el-sub-menu>
    </el-menu>
  </el-aside>
</template>

<script lang="ts" setup>
import { Menu as Present, User, Mic, Setting, House, ShoppingCart } from '@element-plus/icons-vue'

import { useRoute } from 'vue-router'
import { isCollapse } from '@/utils/navbar'

const route = useRoute()
</script>

<style lang="scss" scoped>
// logo 样式
.logo {
  display: flex;
  justify-content: center;
  align-items: center;
  // text-decoration: none;
  color: #000000;
  h1 {
    font-size: 15px;
  }
  img {
    width: 50px;
    height: 50px;
  }
}

/* 菜单样式 */
.el-menu {
  width: 200px;
  background-color: #ffffff;
  border-right: none; // 右边边界线取消

  // 折叠侧边栏样式
  // &.el-menu--collapse -> el-menu.el-menu--collapse
  &.el-menu--collapse {
    width: 60px; // 将宽度变小

    & h1 {
      display: none; // 折叠的时候隐藏 logo 隔壁的 h1 文字
    }
  }
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

/* 侧边栏样式配置 */
.el-aside {
  background-color: #ffffff;
  height: 100vh;
  width: auto;
}
</style>
