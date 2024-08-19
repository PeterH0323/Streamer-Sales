<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

// 定义 URL ID 传参
const props = defineProps({
  roomId: {
    type: String,
    default: ''
  }
})

const onSubmit = () => {}
</script>

<template>
  <div>
    <!-- 返回栏 -->
    <el-page-header @back="router.push({ name: 'StreamingOverview' })" title="返回">
      <template #content>
        <div class="flex items-center">
          <span class="text-large font-600 mr-3">
            {{ props.roomId ? '编辑' : '新建' }} 直播间
          </span>
        </div>
      </template>
      <template #extra>
        <div class="flex items-center">
          <el-button type="primary" class="ml-2" @click="onSubmit">保存</el-button>
        </div>
      </template>
    </el-page-header>

    <el-card>
      <template #footer>
        <div class="form-bottom-btn"></div>
      </template>
    </el-card>
  </div>
</template>

<style lang="scss" scoped></style>
