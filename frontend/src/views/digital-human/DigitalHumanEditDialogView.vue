<script setup lang="ts">
import { ref } from 'vue'
import VideoComponent from '@/components/VideoComponent.vue'

import { streamerDetailInfoRequest, type StreamerInfo } from '@/api/streamerInfo'

const dialogInfoVisible = ref(false)

// 定义标题
const title = ref('')
const steamerInfo = ref({} as StreamerInfo)
const showItemInfoDialog = async (streamerId: number) => {
  console.log(streamerId)
  dialogInfoVisible.value = true

  // 请求接口获取说明书数据
  const { data } = await streamerDetailInfoRequest(streamerId)
  if (data.code === 0) {
    steamerInfo.value = data.data[0]
    title.value = '详情 - 主播' + steamerInfo.value.name
  } else {
    // ElMessage.error()
  }
}

const handelSaveClick = () => {}

defineExpose({ showItemInfoDialog })
</script>

<template>
  <div>
    <el-dialog v-model="dialogInfoVisible" :title="title" width="80%" center>
      <el-row :gutter="20">
        <el-col :span="12">
          <h2>主播基本信息</h2>
          <el-form-item label="姓名">
            <el-input v-model="steamerInfo.character" disabled />
          </el-form-item>
          <el-form-item label="主播性格">
            <el-input v-model="steamerInfo.character" disabled />
          </el-form-item>
          <el-divider />

          <h2>TTS 配置</h2>
          <el-form-item label="音频文件">
            <!-- TODO 支持新增？ -->
            <audio
              v-if="steamerInfo.tts_reference_audio"
              :src="steamerInfo.tts_reference_audio"
              controls
            ></audio>
            <div v-else>未找到音频</div>
          </el-form-item>
          <el-form-item label="声音参考文字">
            <el-input v-model="steamerInfo.tts_reference_sentence" />
          </el-form-item>
          <el-form-item label="TTS 权重">
            <el-input v-model="steamerInfo.tts_weight_path" />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <div>
            <!-- 数字人视频 -->
            <VideoComponent :src="steamerInfo.base_mp4_path" :key="steamerInfo.id" />
          </div>
        </el-col>
      </el-row>

      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="handelSaveClick"> 保存 </el-button>
          <el-button @click="dialogInfoVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.video-container {
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
