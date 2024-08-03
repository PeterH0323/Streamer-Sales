<template>
  <el-container>
    <!-- 侧边栏 -->
    <el-scrollbar>
      <AslideComponent />
    </el-scrollbar>

    <el-container class="header-and-context-container">
      <!-- 导航栏 -->
      <NavbarComponent />

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
import AslideComponent from '@/components/AslideComponent.vue'
import NavbarComponent from '@/components/NavbarComponent.vue'
</script>

<style scoped lang="scss">
.header-and-context-container {
  flex-direction: column;
}
</style>
