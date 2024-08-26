<script lang="ts" setup>
import AslideComponent from '@/components/AslideComponent.vue'
import NavbarComponent from '@/components/NavbarComponent.vue'

import { RouterView } from 'vue-router'
</script>

<template>
  <el-container>
    <!-- 侧边栏 -->
    <el-scrollbar>
      <AslideComponent />
    </el-scrollbar>

    <el-container class="header-and-context-container">
      <!-- 导航栏 -->
      <NavbarComponent />

      <!-- 信息页 -->
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

<style lang="scss" scoped>
.header-and-context-container {
  flex-direction: column;
}

.el-main {
  background-color: #f6f8fe;
}
</style>
