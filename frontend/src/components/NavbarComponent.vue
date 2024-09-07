<script lang="ts" setup>
import { Fold, Expand } from '@element-plus/icons-vue'
import { ref, onMounted } from 'vue'
import { isCollapse } from '@/utils/navbar'

import BreadCrumb from '@/components/BreadCrumb.vue'
import { getUserInfoRequest, type UserInfo } from '@/api/user'
import { ElMessage } from 'element-plus'
import { AxiosError } from 'axios'

const userInfoItem = ref({} as UserInfo)

onMounted(async () => {
  try {
    const { data } = await getUserInfoRequest()

    if (data.code === 0) {
      userInfoItem.value = data.data
    } else {
      ElMessage.error('获取用户信息失败: ' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取用户信息失败: ' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
})
</script>

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
      <el-avatar :src="userInfoItem.avatar" />
      <template #dropdown>
        <el-dropdown-menu class="logout">
          <el-dropdown-item>{{ userInfoItem.username }}</el-dropdown-item>
          <el-dropdown-item>用户配置</el-dropdown-item>
          <el-dropdown-item>
            <!-- <el-dropdown-item @click="logout"> -->
            <!-- <IconifyIconOffline :icon="LogoutCircleRLine" style="margin: 5px" /> -->
            退出系统
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </el-header>
</template>

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
