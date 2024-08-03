<template>
  <el-container class="layout-container-demo">
    <!-- 侧边栏 -->
    <el-scrollbar>
      <AslideComponent />
    </el-scrollbar>

    <el-container class="header-and-context-container">
      <HeaderComponent />

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
import HeaderComponent from '@/components/HeaderComponent.vue'
</script>

<style scoped lang="scss">
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

.header-and-context-container {
  flex-direction: column;
}
</style>
