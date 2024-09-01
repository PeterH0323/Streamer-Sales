<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getSystemPluginsInfoRequest, type SystemPluginsInfo } from '@/api/system'

const pluginsInfo = ref([] as SystemPluginsInfo[])

onMounted(async () => {
  // 获取组件信息
  const { data } = await getSystemPluginsInfoRequest()
  if (data.code === 0) {
    pluginsInfo.value = data.data
    ElMessage.success('获取组件信息成功')
  } else {
    ElMessage.error(data.message)
  }
})
</script>

<template>
  <div class="plugin-item">
    <el-card v-for="(item, index) in pluginsInfo" :key="index" shadow="hover">
      <el-row :gutter="5">
        <el-col :span="4">
          <div class="plugins-ico">
            <el-avatar shape="square" :size="60" :style="{ backgroundColor: item.avatar_color }">
              {{ item.plugin_name }}
            </el-avatar>
          </div>
        </el-col>
        <el-col :span="20">
          <div class="item-content">
            <div>
              <p class="title">{{ item.plugin_name }}</p>
              <p class="content">{{ item.describe }}</p>
            </div>
            <div>
              <el-tag size="large" effect="dark" :type="item.enabled ? 'success' : 'danger'">
                {{ item.enabled ? '已启动' : '未启动' }}
              </el-tag>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.el-card {
  width: 800px;
  margin-top: 10px;
  margin-bottom: 20px;
  border-radius: 20px;
}

.plugin-item {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.plugins-ico {
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  height: 100%; /* 设置父容器的高度，可以根据需要调整 */

  font-weight: 600;
}

.item-content {
  display: flex;
  justify-content: space-between; // 将两个 div 放置在页面的两侧
  align-items: center;

  .title {
    font-size: 18px;
    font-weight: 600;
  }

  .content {
    font-size: 15px;
    color: #b1b3b8;
  }
}
</style>
