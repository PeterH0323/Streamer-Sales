<script lang="ts" setup>
import { Menu as Present, User, Mic, Setting, House, ShoppingCart } from '@element-plus/icons-vue'

import { useRoute } from 'vue-router'
import { isCollapse } from '@/utils/navbar'

const route = useRoute()
</script>

<template>
  <div>
    <el-aside>
      <el-menu :router="true" :default-active="route.fullPath" :collapse="isCollapse">
        <!-- logo -->
        <div class="logo">
          <a herf="/">
            <img src="@/assets/logo.png" alt="" />
          </a>
        </div>
        <div class="logo">
          <h1>销冠 - AI 卖货主播大模型</h1>
        </div>
        <div class="logo" style="line-height: 0">
          <a href="https://github.com/PeterH0323/Streamer-Sales">
            <img src="@/assets/github.svg" alt="github repo" class="github-img" />
          </a>
        </div>

        <el-menu-item index="/home">
          <el-icon> <House /> </el-icon> <span>首页</span>
        </el-menu-item>
        <el-sub-menu index="/product">
          <template #title>
            <el-icon> <present /> </el-icon><span>商品管理</span>
          </template>
          <el-menu-item index="/product/list"><span>商品列表</span></el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/digital_human">
          <template #title>
            <el-icon> <User /> </el-icon><span>数字人管理</span>
          </template>
          <el-menu-item index="/digital_human/list"><span>角色管理</span></el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/streaming">
          <template #title>
            <el-icon> <Mic /> </el-icon><span>直播管理</span>
          </template>
          <el-menu-item index="/streaming/overview">直播间管理<span></span></el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/order">
          <template #title>
            <el-icon> <ShoppingCart /> </el-icon><span>订单管理</span>
          </template>
          <el-menu-item index="/order/overview"><span>订单总览</span></el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/system">
          <template #title>
            <el-icon> <setting /> </el-icon><span>系统配置</span>
          </template>
          <el-menu-item index="/system/plugins"><span>组件状态</span></el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>
  </div>
</template>

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

  .github-img {
    width: 30px;
    height: 30px;
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
  background-color: #337ecc !important;
  color: #ffffff;
  /* 圆角的半径 */
  border-radius: 10px;
}

/* 修改菜单项的形状 */
.el-menu-item {
  border-radius: 10px; /* 例如，增加圆角 */
  background-color: #ffffff;
}

/* 在 hover 状态下应用 */
.el-menu-item:hover {
  border-radius: 10px; /* 保持一致的圆角 */
  background-color: #dedfe0;
}

/* 侧边栏样式配置 */
.el-aside {
  background-color: #ffffff;
  height: 98.5vh;
  width: auto;
}
</style>
