<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

import StreamerInfoComponent from '@/components/StreamerInfoComponent.vue'
import {
  streamerDetailInfoRequest,
  streamerEditDetailRequest,
  type StreamerInfo
} from '@/api/streamerInfo'
import { AxiosError } from 'axios'

const dialogInfoVisible = ref(false)
const saveLoading = ref(false)
// 定义标题
const steamerInfo = ref({} as StreamerInfo)
const showItemInfoDialog = async (streamerId: number) => {
  console.log('streamerId = ', streamerId)
  dialogInfoVisible.value = true

  try {
    // 请求接口获取主播数据
    const { data } = await streamerDetailInfoRequest(streamerId)
    if (data.code === 0) {
      steamerInfo.value = data.data[0]
    } else {
      ElMessage.error('获取主播数据失败: ' + data.message)
    }
  } catch (error: unknown) {
    if (error instanceof AxiosError) {
      ElMessage.error('获取主播数据失败: ' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

const handelSaveClick = async () => {
  try {
    saveLoading.value = true
    const { data } = await streamerEditDetailRequest(steamerInfo.value)

    if (data.code === 0) {
      steamerInfo.value.id = data.data
      ElMessage.success('保存成功')
      saveLoading.value = false
    } else {
      saveLoading.value = false
      ElMessage.error('保存失败: ' + data.message)
    }
  } catch (error: unknown) {
    saveLoading.value = false
    if (error instanceof AxiosError) {
      ElMessage.error('保存失败: ' + error.message)
    } else {
      ElMessage.error('未知错误：' + error)
    }
  }
}

defineExpose({ showItemInfoDialog })
</script>

<template>
  <div class="dialog-container">
    <el-dialog v-model="dialogInfoVisible" title="主播详情" width="80%" destroy-on-close>
      <StreamerInfoComponent v-model="steamerInfo" />

      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="handelSaveClick" :loading="saveLoading">
            保存
          </el-button>
          <el-button @click="dialogInfoVisible = false" :disabled="saveLoading"> 关闭 </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
// 使用 ::v-deep 选择器来覆盖 el-dialog 的默认样式。
::v-deep(.el-dialog) {
  border-radius: 10px;
  padding: 20px;

  --el-dialog-bg-color: #f7f8fa;
  --el-dialog-title-font-size: 24px;
}
</style>
